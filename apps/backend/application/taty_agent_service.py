"""
Taty fiscal agent service.

MVP scope:
- Lightweight RAG over curated Contexia + official tax sources.
- Compatible response shape for the current dashboard.
- Latency, source citations, and human-review flags for regulated answers.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import re
import time
from typing import Literal

from pydantic import BaseModel, Field

from agents.llm_engine import get_ai_response
from core.model_selector import choose_model_for_task, get_task_description

logger = logging.getLogger(__name__)


Channel = Literal["dashboard", "telegram", "whatsapp", "api"]


class TatyAgentRequest(BaseModel):
    company_id: str
    question: str
    channel: Channel = "dashboard"
    conversation_id: str | None = None
    user_id: str | None = None
    context: str = ""


class Citation(BaseModel):
    id: str
    title: str
    source_type: str
    url: str | None = None
    excerpt: str


class TatyAgentResponse(BaseModel):
    answer: str
    result: str
    response: str
    citations: list[Citation]
    latency_ms: int
    confidence: float = Field(ge=0, le=1)
    requires_human_review: bool
    model_used: str
    task_type: str
    tier: str
    success: bool = True


@dataclass(frozen=True)
class KnowledgeChunk:
    id: str
    title: str
    source_type: str
    content: str
    url: str | None = None
    tags: tuple[str, ...] = ()


STOPWORDS = {
    "a", "al", "ante", "con", "como", "cual", "cuando", "de", "del", "debo",
    "el", "en", "es", "esta", "este", "la", "las", "lo", "los", "me", "mi",
    "mis", "no", "para", "por", "que", "se", "si", "sobre", "soy", "su",
    "sus", "tengo", "tu", "un", "una", "y",
}


KNOWLEDGE_BASE = [
    KnowledgeChunk(
        id="uvt-2026",
        title="DIAN Resolucion 000238 de 2025 - UVT 2026",
        source_type="official",
        url="https://normograma.dian.gov.co/dian/compilacion/docs/resolucion_dian_0238_2025.htm",
        tags=("uvt", "2026", "dian", "topes", "renta", "iva"),
        content=(
            "La DIAN fijo la Unidad de Valor Tributario UVT aplicable durante "
            "2026 en $52.374 COP mediante la Resolucion 000238 de 2025. "
            "Los topes expresados en UVT para 2026 deben multiplicarse por "
            "52.374 COP, no por el valor de 2025."
        ),
    ),
    KnowledgeChunk(
        id="estatuto-simple",
        title="Estatuto Tributario - Regimen Simple articulos 903 a 916",
        source_type="official",
        url="https://normograma.dian.gov.co/dian/compilacion/docs/paneles/estatuto_tributario_indice.html",
        tags=("simple", "regimen", "tributacion", "formalizacion", "ica"),
        content=(
            "El Libro Octavo del Estatuto Tributario regula el Impuesto "
            "Unificado bajo el Regimen Simple de Tributacion para la "
            "formalizacion y generacion de empleo. Incluye creacion, hecho "
            "generador, base gravable, sujetos pasivos, exclusiones y reglas "
            "de procedimiento."
        ),
    ),
    KnowledgeChunk(
        id="estatuto-rut",
        title="Estatuto Tributario - RUT y NIT articulos 555-1 y 555-2",
        source_type="official",
        url="https://normograma.dian.gov.co/dian/compilacion/docs/paneles/estatuto_tributario_indice.html",
        tags=("rut", "nit", "dian", "registro", "formalizacion"),
        content=(
            "El Estatuto Tributario contiene las reglas generales sobre NIT "
            "y Registro Unico Tributario RUT, indispensables para formalizar "
            "operaciones, facturacion y obligaciones ante la DIAN."
        ),
    ),
    KnowledgeChunk(
        id="calendario-2026",
        title="DIAN Calendario de obligaciones tributarias 2026",
        source_type="official",
        url="https://www.dian.gov.co/Contribuyentes-Plus/Paginas/Calendario-de-obligaciones.aspx",
        tags=("calendario", "vencimiento", "renta", "iva", "obligaciones"),
        content=(
            "La DIAN publica el calendario tributario 2026 para consultar "
            "vencimientos y obligaciones. Las fechas concretas dependen del "
            "tipo de contribuyente y de los digitos del NIT."
        ),
    ),
    KnowledgeChunk(
        id="contexia-claridad",
        title="Contexia - Claridad Predictiva y Pulso Diario",
        source_type="contexia",
        tags=("contexia", "pulso", "caja", "dian", "provision"),
        content=(
            "Contexia entrega claridad predictiva: traduce datos financieros "
            "en caja real diaria, provision DIAN estimada y alertas accionables "
            "para que el empresario no confunda ingresos brutos con dinero "
            "disponible."
        ),
    ),
    KnowledgeChunk(
        id="contexia-taty",
        title="Contexia - Taty amiga contadora",
        source_type="contexia",
        tags=("taty", "tono", "asesoria", "contador", "humano"),
        content=(
            "Taty es el agente front-stage de Contexia. Debe explicar en "
            "lenguaje claro, cercano y accionable, sin sustituir la firma "
            "del contador publico ni la representacion formal ante la DIAN."
        ),
    ),
]


REVIEW_PATTERNS = (
    "requerimiento", "emplazamiento", "liquidacion oficial", "sancion",
    "correccion", "demanda", "abogado", "representacion", "firmar",
    "presentar declaracion", "debo declarar", "me llego la dian",
    "notificacion dian", "cierre", "embargo", "saldo a pagar",
)


def _normalize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [token for token in tokens if len(token) > 2 and token not in STOPWORDS]


class TatyKnowledgeRetriever:
    def retrieve(self, question: str, limit: int = 4) -> tuple[list[KnowledgeChunk], float]:
        query_terms = _normalize(question)
        if not query_terms:
            return KNOWLEDGE_BASE[:2], 0.45

        scored: list[tuple[int, KnowledgeChunk]] = []
        for chunk in KNOWLEDGE_BASE:
            haystack = " ".join([chunk.title, chunk.content, " ".join(chunk.tags)]).lower()
            score = 0
            for term in query_terms:
                if term in chunk.title.lower():
                    score += 4
                if term in chunk.tags:
                    score += 3
                score += haystack.count(term)
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        chunks = [chunk for _, chunk in scored[:limit]]
        if not chunks:
            chunks = [KNOWLEDGE_BASE[0], KNOWLEDGE_BASE[4], KNOWLEDGE_BASE[5]]

        best_score = scored[0][0] if scored else 1
        confidence = min(0.92, 0.45 + (0.1 * len(chunks)) + min(best_score, 8) / 40)
        return chunks, round(confidence, 2)


class TatyAgentService:
    def __init__(self, retriever: TatyKnowledgeRetriever | None = None):
        self.retriever = retriever or TatyKnowledgeRetriever()

    def ask(self, request: TatyAgentRequest) -> TatyAgentResponse:
        start = time.perf_counter()
        task_type = "taty_fiscal_rag"
        model = choose_model_for_task(task_type)
        task_desc = get_task_description(task_type)

        chunks, confidence = self.retriever.retrieve(request.question)
        citations = [self._citation(index, chunk) for index, chunk in enumerate(chunks, start=1)]
        requires_review = self._requires_human_review(request.question, confidence)

        system_prompt = self._build_system_prompt()
        prompt = self._build_prompt(request, chunks, requires_review)

        logger.info(
            "taty_agent_request company_id=%s channel=%s conversation_id=%s chunks=%s review=%s",
            request.company_id,
            request.channel,
            request.conversation_id,
            [chunk.id for chunk in chunks],
            requires_review,
        )

        raw_answer = get_ai_response(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format="text",
            max_tokens=900,
            temperature=0.35,
            preferred_provider=model,
        )
        answer = self._finalize_answer(str(raw_answer), citations, requires_review)
        latency_ms = int((time.perf_counter() - start) * 1000)

        logger.info(
            "taty_agent_response company_id=%s channel=%s latency_ms=%s confidence=%.2f review=%s",
            request.company_id,
            request.channel,
            latency_ms,
            confidence,
            requires_review,
        )

        return TatyAgentResponse(
            answer=answer,
            result=answer,
            response=answer,
            citations=citations,
            latency_ms=latency_ms,
            confidence=confidence,
            requires_human_review=requires_review,
            model_used=model.value,
            task_type=task_type,
            tier=task_desc["tier"],
            success=True,
        )

    def _build_system_prompt(self) -> str:
        return (
            "Eres Taty, la amiga contadora fiscal de Contexia para PyMEs "
            "colombianas. Responde en espanol claro, cercano y preciso. "
            "Usa solo el contexto entregado y conocimiento tributario general "
            "prudente. No inventes fechas, tarifas ni articulos. Si falta un "
            "dato del cliente, dilo y pide el dato minimo. Incluye referencias "
            "a las fuentes como [S1], [S2] cuando sustenten la respuesta. "
            "Nunca prometas representacion ante la DIAN ni sustituyas al "
            "contador publico. Para decisiones de declaracion, sanciones, "
            "requerimientos o casos concretos, recomienda revision humana."
        )

    def _build_prompt(
        self,
        request: TatyAgentRequest,
        chunks: list[KnowledgeChunk],
        requires_review: bool,
    ) -> str:
        context_lines = []
        for index, chunk in enumerate(chunks, start=1):
            context_lines.append(
                f"[S{index}] {chunk.title}\nTipo: {chunk.source_type}\nContenido: {chunk.content}"
            )

        review_instruction = (
            "Esta pregunta debe marcarse como orientacion y escalar a revision humana."
            if requires_review
            else "Esta pregunta puede responderse como orientacion general."
        )

        return (
            f"Company ID: {request.company_id}\n"
            f"Canal: {request.channel}\n"
            f"Contexto de cliente: {request.context or 'No disponible'}\n\n"
            "Fuentes recuperadas:\n"
            + "\n\n".join(context_lines)
            + "\n\n"
            f"Politica de riesgo: {review_instruction}\n\n"
            f"Pregunta del usuario: {request.question}\n\n"
            "Responde en maximo 180 palabras. Cierra con una accion concreta."
        )

    def _citation(self, index: int, chunk: KnowledgeChunk) -> Citation:
        return Citation(
            id=f"S{index}",
            title=chunk.title,
            source_type=chunk.source_type,
            url=chunk.url,
            excerpt=chunk.content[:260],
        )

    def _requires_human_review(self, question: str, confidence: float) -> bool:
        normalized = question.lower()
        return confidence < 0.55 or any(pattern in normalized for pattern in REVIEW_PATTERNS)

    def _finalize_answer(
        self,
        raw_answer: str,
        citations: list[Citation],
        requires_review: bool,
    ) -> str:
        answer = raw_answer.strip()
        if requires_review and "revision humana" not in answer.lower():
            answer += (
                "\n\nNota: esto es orientacion inicial. Para decidir o presentar "
                "una declaracion, conviene que lo revise el equipo humano de Contexia."
            )
        if "fuentes:" not in answer.lower() and citations:
            compact_sources = "; ".join(
                f"[{citation.id}] {citation.title}" for citation in citations[:3]
            )
            answer += f"\n\nFuentes: {compact_sources}."
        return answer


taty_agent_service = TatyAgentService()
