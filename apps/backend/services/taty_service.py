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

from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
import time
import json

from agents.llm_engine import get_ai_response
from agents.anonymizer import Anonymizer

logger = logging.getLogger(__name__)


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

    # MVP agent profiles (hardcoded; later: load from Supabase)
    AGENT_PROFILES = {
        "ctx-001": {
            "company_id": "ctx-001",
            "nit": "9.867.082-4",
            "nombre_empresa": "Contexia",
            "sector": "Servicios Digitales",
            "regimen": "Régimen Común",
            "tono": "Profesional y accesible, orientado a founders y CFOs",
            "fuentes_habilitadas": ["dian_normograma", "contexia_fiscal"],
            "escalamiento_criterios": [
                "planificación fiscal específica",
                "interpretación legal",
                "cambio de régimen",
                "situaciones no estandarizadas"
            ]
        },
        "ferez-001": {
            "company_id": "ferez-001",
            "nit": "900.123.456-7",
            "nombre_empresa": "FEREZ SAS",
            "sector": "Comercio",
            "regimen": "Régimen Común",
            "tono": "Corporativo y preciso",
            "fuentes_habilitadas": ["dian_normograma"],
            "escalamiento_criterios": [
                "comercio exterior",
                "retenciones complejas",
                "cambio de régimen"
            ]
        },
        "martinez-001": {
            "company_id": "martinez-001",
            "nit": "800.456.789-0",
            "nombre_empresa": "Importaciones Martinez",
            "sector": "Comercio",
            "regimen": "Régimen Común",
            "tono": "Accesible, pequeña/mediana empresa",
            "fuentes_habilitadas": ["dian_normograma"],
            "escalamiento_criterios": ["situaciones complejas"]
        }
    }

    def __init__(self):
        """Initialize Taty service."""
        self.name = "Taty"
        logger.info("TatyAgentService initialized")

    def ask(
        self,
        company_id: str,
        question: str,
        channel: str = "dashboard",
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict:
        """
        Answer a fiscal question with RAG, LLM, and client-specific config.

        Args:
            company_id: Client identifier
            question: User's fiscal question
            channel: "telegram", "dashboard", "whatsapp"
            conversation_id: For multi-turn conversations
            user_id: For audit logging

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
            # 1. Load agent profile for this company
            profile = self._get_agent_profile(company_id)
            if not profile:
                logger.warning(f"No agent profile for company_id={company_id}")
                return self._error_response("Cliente no configurado", start_time)

            # 2. Retrieve relevant chunks from knowledge sources
            chunks, sources_used = self._retrieve_chunks(question, profile)

            # 3. Build fiscal prompt with context
            prompt = self._build_prompt(question, chunks, profile)

            # 4. Anonymize prompt (SOSP rule)
            masked_prompt, mask_map = Anonymizer.mask(prompt)

            # 5. Call LLM with failover
            logger.debug(f"Calling LLM for Taty question (masked)")
            response = get_ai_response(
                prompt=masked_prompt,
                system_prompt=self._build_system_prompt(profile),
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
                company_id=company_id,
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

    def _get_agent_profile(self, company_id: str) -> Optional[Dict]:
        """Load agent profile for company (MVP: hardcoded; later: Supabase)."""
        profile = self.AGENT_PROFILES.get(company_id)
        if profile:
            logger.debug(f"Loaded agent profile for {company_id}")
        return profile

    def _retrieve_chunks(
        self, question: str, profile: Dict
    ) -> Tuple[List[Dict], List[str]]:
        """
        Retrieve relevant knowledge chunks (MVP: keyword match; later: embeddings).

        Returns:
            (chunks, sources_used)
        """
        chunks = []
        sources_used = []

        # MVP: Simple keyword matching
        question_lower = question.lower()
        keywords = {
            "uvt": ["dian_normograma"],
            "régimen simple": ["dian_normograma"],
            "renta": ["dian_normograma"],
            "retención": ["dian_normograma"],
            "iva": ["dian_normograma"],
            "facturación electrónica": ["dian_normograma"],
            "cambio de régimen": ["dian_normograma"],
            "matriz financiera": ["contexia_fiscal"],
            "índice braille": ["contexia_fiscal"],
        }

        for keyword, source_ids in keywords.items():
            if keyword in question_lower:
                for source_id in source_ids:
                    if source_id in profile["fuentes_habilitadas"]:
                        if source_id not in sources_used:
                            sources_used.append(source_id)
                        # Add all chunks from this source
                        for chunk in self.KNOWLEDGE_SOURCES[source_id]["chunks"]:
                            chunks.append(chunk)

        logger.debug(f"Retrieved {len(chunks)} chunks from {len(sources_used)} sources")
        return chunks, sources_used

    def _build_prompt(self, question: str, chunks: List[Dict], profile: Dict) -> str:
        """Build RAG prompt with question + context."""
        context = "\n".join([f"- {c['source']}: {c['text']}" for c in chunks])

        if context:
            return f"""Eres Taty, una asesora fiscal para {profile['nombre_empresa']} (Régimen {profile['regimen']}).

Contexto fiscal (fuentes oficiales):
{context}

Pregunta del cliente:
{question}

Responde en tono {profile['tono']}. Si no estás seguro, di "No tengo información suficiente para responder con precisión".
Siempre cita las fuentes que usaste."""
        else:
            return f"""Eres Taty, una asesora fiscal para {profile['nombre_empresa']}.

Pregunta del cliente:
{question}

Si no tienes información suficiente, di "No tengo información suficiente para responder con precisión"."""

    def _build_system_prompt(self, profile: Dict) -> str:
        """Build system prompt for LLM."""
        return (
            f"Eres Taty Contadora, asesora fiscal de {profile['nombre_empresa']}. "
            "Responde en español. Sé preciso, cita fuentes, y advierte si necesita asesoría legal."
        )

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
        company_id: str,
        conversation_id: Optional[str],
        user_id: Optional[str],
        channel: str,
        question: str,
        answer: str,
        latency_ms: int,
        requires_human_review: bool
    ):
        """Log conversation (MVP: logs only; later: Supabase)."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "company_id": company_id,
            "channel": channel,
            "latency_ms": latency_ms,
            "requires_human_review": requires_human_review,
            "conversation_id": conversation_id,
            "user_id": user_id,
        }
        logger.info(f"Taty conversation: {json.dumps(log_entry)}")

    def _error_response(self, error: str, start_time: float) -> Dict:
        """Format error response."""
        latency_ms = int((time.time() - start_time) * 1000)
        return {
            "answer": error,
            "citations": [],
            "latency_ms": latency_ms,
            "confidence": 0.0,
            "requires_human_review": True,
            "result": error,  # Backward compat
        }


# Singleton instance
_taty_service = None


def get_taty_service() -> TatyAgentService:
    """Get or create Taty service singleton."""
    global _taty_service
    if _taty_service is None:
        _taty_service = TatyAgentService()
    return _taty_service
