"""
Taty Contadora - Fiscal AI Agent Service.

Taty is an orchestrated sub-agent within Contexia that provides fiscal advice
using RAG over DIAN sources, LLM failover, SOSP anonymization, and per-client
configuration (agent_profiles).

Architecture:
- Not an independent agent, but a service called by presentation layer (API, Telegram, Dashboard)
- Shares LLM engine, anonymization, logging with other agents
- Multi-channel: Telegram webhook, Dashboard API, future WhatsApp
- Multi-client: Each client has own agent_profile config (tone, sources, escalation rules)

Performance target: P95 < 4 seconds for common questions (IVA, renta, UVT)
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import logging
import os
import re
import time
import json
import unicodedata

import uuid

from agents.llm_engine import get_llm_engine
from agents.anonymizer import Anonymizer
from core.supabase_client import get_supabase
from services.kb_seeding_service import retrieve_similar, ensure_dian_loaded

logger = logging.getLogger(__name__)

# Load DIAN seed into the KB store at module import (idempotent, no-op if already loaded)
ensure_dian_loaded()


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _normalize_for_search(text: str) -> str:
    return _strip_accents(text).lower()


# Common Spanish function words that carry no retrieval signal — dropped from the query so the
# keyword fallback scores on meaningful terms (renta, declarar, plazos, retencion, iva...) only.
_KB_STOPWORDS = frozenset(
    {
        # 3-letter function words (kept short so fiscal acronyms UVT/IVA/RUT/NIT survive the
        # length filter, which is why these must be listed explicitly)
        "que", "los", "las", "una", "del", "con", "sin", "sus", "por", "son", "les", "nos",
        "hay", "ese", "eso", "esa", "fue", "voy", "vas", "mis", "tus", "muy", "mas", "dia",
        # longer function words
        "hola", "cual", "cuales", "como", "para", "uno", "unos", "unas", "este", "esta", "esto",
        "esos", "esas", "tengo", "tiene", "tienen", "quiero", "necesito", "puedo", "podria",
        "porque", "cuando", "donde", "sobre", "entre", "hasta", "desde", "pero", "todo", "toda",
        "todos", "todas", "algun", "alguna", "ustedes", "nosotros", "gracias", "favor", "info",
        "informacion", "ayuda", "ayudame", "saber", "decir", "dime", "senor", "senora", "cuanto",
        "cuanta", "cuantos", "cuantas",
    }
)


def _load_kb_fallback_corpus() -> List[Dict[str, str]]:
    """Load the older, token-free fiscal knowledge base for the keyword fallback.

    Why this exists (taty-whatsapp-renta-sales-capability, 2026-08-12, found live): the pgvector KB
    needs an embedding provider both to SEED and to QUERY, and both configured providers were
    simultaneously out of quota (OpenAI: "no credits remaining"; Gemini: daily free quota
    exceeded), so `retrieve_similar` returns nothing and Taty answers every fiscal question with
    "No tengo información suficiente". Contexia already ships a curated fiscal corpus as plain JSON
    (`kb/dian_chunks_expanded.json`, 79 chunks of Estatuto Tributario / DIAN facts, plus
    `kb/renta_natural_chunks.json`, 5 price-free renta-persona-natural facts) — the same files the
    KB is seeded from. This loads them once at import so a simple keyword search (see
    `_keyword_fallback_search`) can ground answers WITHOUT any embedding/token call, used only when
    live semantic retrieval returns nothing. Renta facts are loaded first so they win ties for the
    campaign's core questions. Reading fails soft to whatever loaded — a missing/corrupt file must
    never break the reply path.
    """
    corpus: List[Dict[str, str]] = []
    seen: set = set()
    kb_dir = os.path.join(os.path.dirname(__file__), "..", "kb")
    for filename in ("renta_natural_chunks.json", "dian_chunks_expanded.json"):
        try:
            with open(os.path.join(kb_dir, filename), encoding="utf-8") as f:
                raw = json.load(f)
        except Exception as e:  # noqa: BLE001 - fallback must never raise
            logger.warning("Could not load KB fallback file %s: %s", filename, e)
            continue
        for chunk in raw if isinstance(raw, list) else raw.get("chunks", []):
            content = (chunk.get("content") or "").strip()
            source = (chunk.get("source") or "").strip()
            if not content or not source or content in seen:
                continue
            seen.add(content)
            corpus.append(
                {
                    "text": content,
                    "source": source,
                    "_blob": _normalize_for_search(f"{source} {content}"),
                }
            )
    logger.info("Loaded %d chunks into the token-free KB fallback corpus", len(corpus))
    return corpus


KB_FALLBACK_CORPUS: List[Dict[str, str]] = _load_kb_fallback_corpus()


def _keyword_fallback_search(question: str, top_k: int = 5) -> List[Dict[str, str]]:
    """Token-free keyword retrieval over KB_FALLBACK_CORPUS.

    Scores each chunk by how many distinct meaningful query terms appear in it (source + content),
    weighted by occurrence count. Returns the top_k chunks with a non-zero score, so a greeting or
    an off-topic message that matches nothing simply yields no context (Taty answers
    conversationally) rather than dragging in irrelevant fiscal text. No network, no embeddings.
    """
    if not KB_FALLBACK_CORPUS:
        return []
    query_terms = {
        term
        for term in re.findall(r"[a-z0-9]+", _normalize_for_search(question))
        if len(term) >= 3 and term not in _KB_STOPWORDS
    }
    if not query_terms:
        return []
    scored: List[Tuple[int, Dict[str, str]]] = []
    for chunk in KB_FALLBACK_CORPUS:
        blob = chunk["_blob"]
        score = sum(blob.count(term) for term in query_terms if term in blob)
        if score:
            scored.append((score, chunk))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [{"text": c["text"], "source": c["source"]} for _, c in scored[:top_k]]


# Template for profile fields NOT sourced from the `tenants` table.
# `regimen` is intentionally None — Taty must never assert an unverified tax
# regime for a real client (see .antigravity/GROUND_TRUTH.md and design.md D1).
DEFAULT_PROFILE: Dict = {
    "tono": "Profesional, clara y accesible, orientada a founders y equipos financieros de PyMEs",
    "fuentes_habilitadas": ["dian_normograma"],
    "escalamiento_criterios": [
        "planificación fiscal específica",
        "interpretación legal",
        "cambio de régimen",
        "situaciones no estandarizadas",
        "comercio exterior",
        "retenciones complejas",
        "situaciones complejas",
    ],
    "regimen": None,
}


class TatyAgentService:
    """Fiscal advisor agent - RAG + LLM + per-client config."""

    # MVP knowledge sources (hardcoded; later: load from Supabase)
    KNOWLEDGE_SOURCES = {
        "dian_normograma": {
            "name": "Normograma DIAN",
            "chunks": [
                # UVT 2026
                {
                    "text": "El UVT para 2026 es de $52.374 según Resolución DIAN 238 de 2025.",
                    "source": "Resolución DIAN 238/2025"
                },
                # Régimen Simple
                {
                    "text": "El Régimen Simple está destinado a personas naturales cuyo ingreso bruto no supera 160 UVT anual.",
                    "source": "Normograma DIAN - Régimen Simple"
                },
                # Retención en la fuente
                {
                    "text": "La retención en la fuente por servicios es del 3% a 8% según el tipo de prestador.",
                    "source": "Estatuto Tributario - Retención en la Fuente"
                },
                # IVA
                {
                    "text": "El IVA general en Colombia es del 19% sobre la base gravable.",
                    "source": "Estatuto Tributario - IVA"
                },
                # Facturación electrónica
                {
                    "text": "Desde 2022, todos los regímenes deben facturación electrónica. Obligatorio transmitir al INVIMA/DIAN.",
                    "source": "Resolución DIAN - Facturación Electrónica"
                },
                # Cambio de régimen
                {
                    "text": "El cambio de régimen tributario requiere solicitud formal a DIAN y puede afectar retenciones y obligaciones.",
                    "source": "Normograma DIAN - Cambios de Régimen"
                },
            ]
        },
        "contexia_fiscal": {
            "name": "Documentos Contexia",
            "chunks": [
                {
                    "text": "La Matriz Financiera de Contexia evalúa: liquidez, solvencia, rentabilidad, y escalabilidad.",
                    "source": "Contexia - Matriz Financiera"
                },
                {
                    "text": "El Índice Braille mide patrimonio neto / activos totales. Indica salud financiera.",
                    "source": "Contexia - Índice Braille"
                },
            ]
        }
    }

    def __init__(self):
        """Initialize Taty service."""
        self.name = "Taty"
        logger.info("TatyAgentService initialized")

    def ask(
        self,
        tenant_id: str,
        question: str,
        channel: str = "dashboard",
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        hermes_profile: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        lead_context: Optional[Dict[str, Any]] = None,
    ) -> Dict:
        """
        Answer a fiscal question with RAG, LLM, and client-specific config.

        Args:
            tenant_id: Tenant identifier (uuid, resolved from the caller's session)
            question: User's fiscal question
            channel: "telegram", "dashboard", "whatsapp"
            conversation_id: For multi-turn conversations
            user_id: For audit logging
            conversation_history: Recent turns, oldest first, shape
                [{"role": "user"|"assistant", "text": "..."}, ...]. Additive — omitted (None) for
                every existing caller, so Telegram/PWA prompts are byte-identical to before this
                parameter existed. Introduced for the WhatsApp sales-lead channel
                (taty-whatsapp-renta-sales-capability), which is genuinely multi-turn; the shared
                LLM engine only accepts a flat (system_prompt, prompt) pair, not a messages array,
                so history is flattened into the built prompt text rather than threaded through
                the engine as separate turns.
            lead_context: WhatsApp sales-funnel context — {"lead_stage": str,
                "persona_fields": {"es_asalariado": bool, "topes": {...},
                "obligado_declarar": bool}, "offer": {"documentos_requeridos": [...],
                "precio_confirmado": bool}}. Additive, same reasoning as conversation_history.

        Returns:
            {
                "answer": "...",
                "citations": [{"source": "...", "fragment": "..."}],
                "latency_ms": 1234,
                "confidence": 0.92,
                "requires_human_review": False,
                "result": "answer"  # Temporal alias for backward compat
            }
        """
        start_time = time.time()

        try:
            # 1. Load tenant profile
            profile = self._get_tenant_profile(tenant_id)
            if not profile:
                logger.warning(f"No tenant profile for tenant_id={tenant_id}")
                return self._error_response(
                    "Cliente no configurado", start_time, error_code="tenant_not_found"
                )

            # 2. Retrieve relevant chunks from knowledge sources
            chunks, sources_used = self._retrieve_chunks(question, profile)

            # 3. Build fiscal prompt with context
            prompt = self._build_prompt(
                question, chunks, profile, conversation_history=conversation_history
            )

            # 4. Anonymize prompt (SOSP rule)
            masked_prompt, mask_map = Anonymizer.mask(prompt)

            # 5. Call LLM with failover (using profile-based routing)
            # Use Hermes profile if provided, otherwise default to taty-v1
            profile_name = hermes_profile or "taty-v1"
            logger.debug(f"Calling LLM for Taty question (masked) with profile={profile_name}")
            llm_engine = get_llm_engine()
            response = llm_engine.get_ai_response_with_profile(
                prompt=masked_prompt,
                profile_name=profile_name,
                system_prompt=self._build_system_prompt(profile, lead_context=lead_context),
                response_format="text",
                max_tokens=2000,
                temperature=0.3,  # Lower temp for fiscal = more precise
            )

            # 6. Rehydrate response (unmask PII)
            if mask_map:
                response = Anonymizer.unmask(response, mask_map)

            # 7. Extract citations
            citations = self._extract_citations(sources_used, chunks)

            # 8. Determine if requires human review
            requires_review = self._check_escalation(question, response, profile)

            # 9. Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # 10. Log conversation
            self._log_conversation(
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                user_id=user_id,
                channel=channel,
                question=question,
                answer=response,
                latency_ms=latency_ms,
                requires_human_review=requires_review
            )

            return {
                "answer": response,
                "citations": citations,
                "latency_ms": latency_ms,
                "confidence": 0.85 if sources_used else 0.6,
                "requires_human_review": requires_review,
                "result": response,  # Backward compat alias
            }

        except Exception as e:
            logger.error(f"Error in Taty.ask(): {str(e)}", exc_info=True)
            return self._error_response(f"Error: {str(e)}", start_time)

    def _get_tenant_profile(self, tenant_id: str) -> Optional[Dict]:
        """Resolve a Taty client profile from the `tenants` table.

        Merges identity fields (`legal_name`, `nit`) from the tenant row onto
        `DEFAULT_PROFILE` (tone, enabled sources, escalation criteria). Returns
        None (never raises) when the tenant does not exist or `tenant_id` is not
        a valid uuid (e.g. a retired legacy demo key like "ferez-001").
        """
        try:
            uuid.UUID(str(tenant_id))
        except (ValueError, TypeError, AttributeError):
            logger.warning(f"_get_tenant_profile called with a non-uuid key: {tenant_id!r}")
            return None

        try:
            result = (
                get_supabase()
                .table("tenants")
                .select("id, nit, legal_name, is_cliente_cero, company_id")
                .eq("id", tenant_id)
                .execute()
            )
        except Exception as e:
            logger.error(f"Error resolving tenant profile for {tenant_id}: {e}", exc_info=True)
            return None

        rows = result.data or []
        if not rows:
            logger.warning(f"No tenant found for tenant_id={tenant_id}")
            return None

        row = rows[0]
        fuentes_habilitadas = list(DEFAULT_PROFILE["fuentes_habilitadas"])
        if row.get("is_cliente_cero"):
            fuentes_habilitadas.append("contexia_fiscal")

        profile = {
            **DEFAULT_PROFILE,
            "fuentes_habilitadas": fuentes_habilitadas,
            "tenant_id": row["id"],
            "nit": row.get("nit"),
            "nombre_empresa": row.get("legal_name"),
            "company_id": row.get("company_id"),
            "kb_client_id": row.get("company_id") or row["id"],
        }
        logger.debug(f"Loaded tenant profile for tenant_id={tenant_id}")
        return profile

    def _retrieve_chunks(
        self, question: str, profile: Dict
    ) -> Tuple[List[Dict], List[str]]:
        """
        Retrieve relevant knowledge chunks via kb_seeding_service.

        Backend selection (pgvector vs in-memory) is handled by the service.
        Falls back to legacy KNOWLEDGE_SOURCES dict if the service returns nothing.

        Returns:
            (chunks, sources_used) where chunks have shape {source, content/text, ...}
        """
        client_id = profile["kb_client_id"]
        results = retrieve_similar(query=question, client_id=client_id, top_k=5)

        # Normalize chunk shape: kb_seeding uses 'content', legacy used 'text'
        chunks: List[Dict] = []
        sources_used: List[str] = []
        for r in results:
            text = r.get("content") or r.get("text") or ""
            source = r.get("source", "DIAN")
            chunks.append({"text": text, "source": source})
            if source not in sources_used:
                sources_used.append(source)

        # Legacy fallback for chunks not yet in KB (Matriz Financiera, Índice Braille keywords)
        if not chunks:
            question_lower = question.lower()
            legacy_keywords = {
                "matriz financiera": "contexia_fiscal",
                "índice braille": "contexia_fiscal",
            }
            for kw, src_id in legacy_keywords.items():
                if kw in question_lower and src_id in profile.get("fuentes_habilitadas", []):
                    for chunk in self.KNOWLEDGE_SOURCES[src_id]["chunks"]:
                        chunks.append(chunk)
                        if chunk["source"] not in sources_used:
                            sources_used.append(chunk["source"])

        # Token-free keyword fallback over the older curated fiscal corpus (DIAN expanded + renta):
        # only when live semantic retrieval AND the legacy dict both return nothing — i.e. while the
        # embedding providers are out of quota and the pgvector KB cannot be queried. Self-deactivates
        # the moment retrieve_similar returns real chunks again. See _load_kb_fallback_corpus /
        # _keyword_fallback_search for the full rationale.
        if not chunks:
            keyword_chunks = _keyword_fallback_search(question, top_k=5)
            for chunk in keyword_chunks:
                chunks.append(chunk)
                if chunk["source"] not in sources_used:
                    sources_used.append(chunk["source"])
            if keyword_chunks:
                logger.info(
                    "Using %d token-free keyword-fallback chunks (semantic KB returned nothing)",
                    len(keyword_chunks),
                )

        logger.debug(f"Retrieved {len(chunks)} chunks via kb_seeding_service")
        return chunks, sources_used

    def _build_prompt(
        self,
        question: str,
        chunks: List[Dict],
        profile: Dict,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Build RAG prompt with question + context.

        `regimen` is only interpolated when the profile actually resolved one.
        Taty must never assert an unverified tax regime for a real client (see
        .antigravity/GROUND_TRUTH.md and design.md D1) — when `regimen` is
        `None`, the clause is omitted entirely rather than rendered as
        "Régimen None" or left as a dangling label.

        `conversation_history` is flattened into the prompt text (the shared LLM engine takes a
        single system+user prompt pair, not a messages array — see ask()'s docstring). Omitted by
        every caller except the WhatsApp channel, so this is a no-op for Telegram/PWA.
        """
        context = "\n".join([f"- {c['source']}: {c['text']}" for c in chunks])
        regimen = profile.get("regimen")
        regimen_clause = f" (Régimen {regimen})" if regimen else ""

        history_block = ""
        if conversation_history:
            turns = "\n".join(
                f"{'Cliente' if turn.get('role') == 'user' else 'Taty'}: {turn.get('text', '')}"
                for turn in conversation_history
            )
            history_block = f"\nConversación reciente:\n{turns}\n"

        if context:
            return f"""Eres Taty, la amiga de confianza en temas de contabilidad de {profile['nombre_empresa']}{regimen_clause}.

Contexto fiscal (fuentes oficiales):
{context}
{history_block}
Pregunta del cliente:
{question}

Responde en tono {profile['tono']}. Si no estás seguro, di "No tengo información suficiente para responder con precisión".
Siempre cita las fuentes que usaste."""
        else:
            return f"""Eres Taty, la amiga de confianza en temas de contabilidad de {profile['nombre_empresa']}.
{history_block}
Pregunta del cliente:
{question}

Si no tienes información suficiente, di "No tengo información suficiente para responder con precisión"."""

    def _build_system_prompt(self, profile: Dict, lead_context: Optional[Dict[str, Any]] = None) -> str:
        """Build system prompt for LLM.

        `lead_context` (WhatsApp sales-funnel channel only — see ask()'s docstring) appends an
        addendum with the lead's known persona/stage and the offer's document requirements. It
        deliberately never states a price unless `offer.precio_confirmado` is explicitly true —
        pricing tiers are undefined as of this change (founder decision 2026-08-11, deferred);
        Taty must not invent one (mirrors the "never invent a fiscal figure" rule this change's
        A/B testing showed is safety-critical, applied here to commercial figures too)."""
        base = (
            f"Eres Taty, la amiga de confianza en temas de contabilidad de {profile['nombre_empresa']}. "
            "Responde en español, con calidez y cercanía, como alguien que de verdad quiere ayudar — "
            "nunca con tono formal/legal de asesor fiscal certificado. "
            "Sé precisa, cita fuentes, y sugiere hablar con un asesor humano cuando el tema lo amerite."
        )
        if not lead_context:
            return base

        parts = [base, "\nContexto adicional de este lead de WhatsApp (declaración de renta persona natural):"]
        stage = lead_context.get("lead_stage")
        if stage:
            parts.append(f"- Etapa actual en el embudo: {stage}.")

        persona = lead_context.get("persona_fields") or {}
        if "es_asalariado" in persona:
            parts.append(
                "- Es asalariado." if persona["es_asalariado"] else "- Es independiente/freelancer."
            )
        if persona.get("obligado_declarar") is not None:
            parts.append(
                "- Según lo que ha contado, "
                + ("SÍ" if persona["obligado_declarar"] else "probablemente NO")
                + " está obligado a declarar (señal preliminar, no una determinación legal — "
                "acláraselo si lo mencionas)."
            )

        offer = lead_context.get("offer") or {}
        docs = offer.get("documentos_requeridos")
        if docs:
            parts.append(f"- Documentos que Contexia pide para armar la declaración: {', '.join(docs)}.")
        if not offer.get("precio_confirmado"):
            parts.append(
                "- El precio para este caso todavía no está definido en el sistema. Si el cliente "
                "pregunta cuánto cuesta, NO inventes ni menciones un número — dile que un asesor "
                "de Contexia le confirma el valor exacto según su caso."
            )
        # Unconditional (unlike the price flag above, there's no "confirmed" contact-info source
        # to check): found live 2026-08-11 that without this instruction, the model fabricates
        # a plausible-looking Contexia email, phone number and website when asked how to make
        # contact — none of them real. Same class of risk as inventing a fiscal figure.
        parts.append(
            "- No inventes un correo, teléfono o sitio web de contacto — no tienes esa "
            "información confirmada. Si preguntan cómo contactar a alguien más, di que pueden "
            "seguir escribiendo por este mismo chat de WhatsApp y que un asesor de Contexia se "
            "vincula a la conversación."
        )

        return "\n".join(parts)

    def _extract_citations(self, sources_used: List[str], chunks: List[Dict]) -> List[Dict]:
        """Extract citations from used chunks."""
        citations = []
        seen = set()
        for chunk in chunks:
            key = (chunk["source"], chunk["text"][:50])
            if key not in seen:
                citations.append({
                    "source": chunk["source"],
                    "fragment": chunk["text"][:150] + "..." if len(chunk["text"]) > 150 else chunk["text"]
                })
                seen.add(key)
        return citations

    def _check_escalation(self, question: str, response: str, profile: Dict) -> bool:
        """Determine if response requires human review."""
        escalation_keywords = profile.get("escalamiento_criterios", [])
        question_lower = question.lower()

        for keyword in escalation_keywords:
            if keyword.lower() in question_lower:
                logger.info(f"Escalation triggered: {keyword}")
                return True

        # Also escalate if response says "no sé"
        if "no tengo información" in response.lower() or "no estoy seguro" in response.lower():
            return True

        return False

    def _log_conversation(
        self,
        tenant_id: str,
        conversation_id: Optional[str],
        user_id: Optional[str],
        channel: str,
        question: str,
        answer: str,
        latency_ms: int,
        requires_human_review: bool
    ):
        """Log a Taty conversation.

        MVP: writes to the application log only — conversations are NOT persisted
        to a database. TODO: persist to Supabase (e.g. a `taty_conversations`
        table) once a client is wired into this service.
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tenant_id": tenant_id,
            "channel": channel,
            "latency_ms": latency_ms,
            "requires_human_review": requires_human_review,
            "conversation_id": conversation_id,
            "user_id": user_id,
        }
        logger.info(f"Taty conversation: {json.dumps(log_entry)}")

    def _error_response(
        self, error: str, start_time: float, error_code: Optional[str] = None
    ) -> Dict:
        """Format error response.

        `error_code` is optional and only included in the returned dict when
        provided, so existing callers that don't pass it keep the exact same
        response shape (backward compatible within this file).
        """
        latency_ms = int((time.time() - start_time) * 1000)
        response = {
            "answer": error,
            "citations": [],
            "latency_ms": latency_ms,
            "confidence": 0.0,
            "requires_human_review": True,
            "result": error,  # Backward compat
        }
        if error_code is not None:
            response["error_code"] = error_code
        return response


# Singleton instance
_taty_service = None


def get_taty_service() -> TatyAgentService:
    """Get or create Taty service singleton."""
    global _taty_service
    if _taty_service is None:
        _taty_service = TatyAgentService()
    return _taty_service
