"""
Agent 4: Editor / Legal Reviewer - LÍNEA 3
Polishes responses, enforces brand voice, validates fiscal/legal compliance.

Aligns with Sight AI 2026 "Editor (Legal Reviewer)" role: every piece of content
that touches Colombian fiscal/regulatory matters is reviewed for compliance
before downstream consumption.

Output contract:
  - is_compliant: bool          (binary gate for Distribution agent)
  - polished_content: str       (brand-voice corrected version)
  - issues: List[Dict]          (each: {severity, category, description, fix_suggestion})
  - confidence: float           (0.0–1.0, LLM's self-reported certainty)
"""

from typing import Dict, List
import logging
from agents.base_agent import BaseAgent, AgentRole

logger = logging.getLogger(__name__)


COMPLIANCE_CATEGORIES = [
    "fiscal_accuracy",     # DIAN-aligned numbers, UVT references, régimen names
    "legal_disclaimer",    # No tax advice without "consulta a tu contador"
    "pii_exposure",        # No NITs, emails, phones in outbound text
    "brand_voice",         # Contexia tone: calm authority, plain Spanish, no jargon
    "factual_grounding",   # Claims must be traceable to KB source
]


class EditorAgent(BaseAgent):
    """
    Editor / Legal Reviewer Agent

    Input: {
        "draft_content": str,
        "source_citations": List[Dict],   # optional, from Taty/Analyst
        "company_context": Dict,           # optional, brand voice profile
        "channel": str                     # "telegram" | "dashboard" | "email"
    }

    Output: compliance flag + polished text + issue list.
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.EDITOR,
            name="Editor Agent",
            version="1.0"
        )

    def execute(self, input_data: Dict) -> Dict:
        if not self.validate_input(input_data, ["draft_content"]):
            return {
                "is_compliant": False,
                "polished_content": "",
                "issues": [{"severity": "error", "category": "input", "description": "Missing draft_content"}],
                "confidence": 0.0,
            }

        draft = input_data["draft_content"]
        citations = input_data.get("source_citations", [])
        company_ctx = input_data.get("company_context", {})
        channel = input_data.get("channel", "dashboard")

        review = self._review_with_llm(draft, citations, company_ctx, channel)
        return review

    def _review_with_llm(
        self,
        draft: str,
        citations: List[Dict],
        company_ctx: Dict,
        channel: str,
    ) -> Dict:
        brand_tone = company_ctx.get("tone", "calmada, autoritativa, español claro sin tecnicismos innecesarios")
        cite_summary = "; ".join([c.get("source", "?") for c in citations[:5]]) or "ninguna"

        prompt = f"""Revisa el siguiente borrador como Editor/Revisor Legal de Contexia.

Borrador:
\"\"\"{draft}\"\"\"

Canal de salida: {channel}
Tono de marca: {brand_tone}
Fuentes citadas: {cite_summary}

Evalúa las siguientes categorías de cumplimiento:
{chr(10).join(f"- {c}" for c in COMPLIANCE_CATEGORIES)}

Reglas no negociables:
1. Toda afirmación fiscal debe ser trazable a una fuente DIAN o KB; si no, marcar issue.
2. Si el texto da consejo fiscal sin disclaimer "consulta a tu contador", marcar issue legal_disclaimer.
3. No exponer NITs, emails ni teléfonos (la anonimización ya corrió, pero verifica).
4. Pulir tono a brand voice sin alterar hechos.

Devuelve JSON con:
- is_compliant: bool (true solo si NO hay issues de severidad "error")
- polished_content: str (texto corregido)
- issues: list de objetos {{severity, category, description, fix_suggestion}}
- confidence: float 0-1

Devuelve SOLO JSON válido."""

        system_prompt = (
            "Eres un editor y revisor legal especializado en contenido fiscal colombiano. "
            "Tu trabajo: garantizar precisión, cumplimiento y tono de marca. Devuelve solo JSON válido."
        )

        response = self.call_llm(
            prompt,
            system_prompt,
            response_format="json",
            required_keys=["is_compliant", "polished_content", "issues"],
            max_json_retries=2,
        )

        if not isinstance(response, dict) or response.get("parsing_error"):
            logger.warning("Editor LLM parsing failed, returning conservative fallback")
            return self._fallback_review(draft)

        # Coerce types defensively
        response.setdefault("is_compliant", False)
        response.setdefault("polished_content", draft)
        response.setdefault("issues", [])
        response.setdefault("confidence", 0.5)
        return response

    def _fallback_review(self, draft: str) -> Dict:
        return {
            "is_compliant": False,
            "polished_content": draft,
            "issues": [{
                "severity": "warning",
                "category": "fallback",
                "description": "LLM no pudo revisar; se requiere revisión humana",
                "fix_suggestion": "Reintentar o asignar a revisor humano",
            }],
            "confidence": 0.0,
        }
