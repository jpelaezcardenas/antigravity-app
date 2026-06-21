"""
Agent 6: Analyst / Reporting - LÍNEA 3
Summarizes fiscal health, identifies risks, produces executive bullets.

Sits downstream of Centinela rules engine: takes alerts + raw fiscal metrics,
synthesizes them into an actionable digest for the Pulso 8AM semáforo.

Output contract:
  - status_level: "sana" | "vigilancia" | "alerta" | "crítica"
  - executive_summary: str (≤3 sentences)
  - top_risks: List[Dict]   ({title, impact, recommendation})
  - opportunities: List[str] (≤3 bullets)
  - key_metrics: Dict        (passed through for dashboard)
"""

from typing import Dict, List
import logging
from agents.base_agent import BaseAgent, AgentRole

logger = logging.getLogger(__name__)


STATUS_THRESHOLDS = {
    # severity-weighted alert score → status_level
    "sana": (0, 1),          # 0-1 active issues
    "vigilancia": (2, 4),    # 2-4 active issues OR 1 high-severity
    "alerta": (5, 9),
    "crítica": (10, 999),
}


class AnalystAgent(BaseAgent):
    """
    Analyst / Reporting Agent

    Input: {
        "company_id": str,
        "alerts": List[Dict],           # from centinela_service (rule-based)
        "metrics": Dict,                # cash_flow, tax_provisions, etc.
        "period": str                   # "2026-05" or similar
    }

    Output: status_level + summary + risks + opportunities.
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.ANALYST,
            name="Analyst Agent",
            version="1.0"
        )

    def execute(self, input_data: Dict) -> Dict:
        if not self.validate_input(input_data, ["company_id", "alerts", "metrics"]):
            return self._empty_report("Missing required fields")

        alerts = input_data["alerts"]
        metrics = input_data["metrics"]
        period = input_data.get("period", "current")

        status = self._compute_status(alerts)
        narrative = self._narrate_with_llm(alerts, metrics, status, period)

        return {
            "status_level": status,
            "executive_summary": narrative.get("executive_summary", ""),
            "top_risks": narrative.get("top_risks", []),
            "opportunities": narrative.get("opportunities", []),
            "key_metrics": metrics,
            "period": period,
            "alert_count": len(alerts),
        }

    def _compute_status(self, alerts: List[Dict]) -> str:
        # Severity weights from Centinela alert shape
        weights = {"crítica": 5, "alta": 3, "media": 2, "baja": 1}
        score = sum(weights.get(a.get("severity", "baja"), 1) for a in alerts)

        for level, (lo, hi) in STATUS_THRESHOLDS.items():
            if lo <= score <= hi:
                return level
        return "vigilancia"

    def _narrate_with_llm(
        self,
        alerts: List[Dict],
        metrics: Dict,
        status: str,
        period: str,
    ) -> Dict:
        # Compact alert summary for prompt
        alert_lines = [
            f"- [{a.get('severity', 'baja')}] {a.get('title', '?')}: {a.get('description', '')[:120]}"
            for a in alerts[:10]
        ]
        alert_block = "\n".join(alert_lines) if alert_lines else "Sin alertas activas."

        metrics_lines = [f"- {k}: {v}" for k, v in list(metrics.items())[:10]]
        metrics_block = "\n".join(metrics_lines) if metrics_lines else "Sin métricas."

        prompt = f"""Como Analista Fiscal de Contexia, sintetiza el estado financiero del periodo {period}.

Status calculado (semáforo): {status}

Alertas activas:
{alert_block}

Métricas clave:
{metrics_block}

Genera:
1. executive_summary: máximo 3 frases en español claro, sin jerga. Dirige al dueño de la empresa.
2. top_risks: lista de hasta 3 riesgos, cada uno con {{title, impact (alto/medio/bajo), recommendation}}.
3. opportunities: lista de hasta 3 oportunidades concretas (ahorro fiscal, optimización, etc.).

Reglas:
- No inventes números. Solo usa los provistos.
- Si status es "sana", el tono es de mantenimiento, no de urgencia.
- Si status es "crítica", primer riesgo debe ser el más urgente con plazo en días.

Devuelve SOLO JSON válido."""

        system_prompt = (
            "Eres un analista fiscal senior. Tu rol: traducir alertas técnicas a lenguaje de dueño "
            "de empresa colombiano. Conservador con números, claro con acciones. Solo JSON."
        )

        response = self.call_llm(
            prompt,
            system_prompt,
            response_format="json",
            required_keys=["executive_summary", "top_risks", "opportunities"],
            max_json_retries=2,
        )

        if not isinstance(response, dict) or response.get("parsing_error"):
            logger.warning("Analyst LLM parsing failed, returning skeletal report")
            return self._fallback_narrative(status, len(alerts))
        return response

    def _fallback_narrative(self, status: str, alert_count: int) -> Dict:
        return {
            "executive_summary": f"Estado fiscal: {status}. {alert_count} alertas activas. Revisión humana recomendada.",
            "top_risks": [],
            "opportunities": [],
        }

    def _empty_report(self, reason: str) -> Dict:
        return {
            "status_level": "vigilancia",
            "executive_summary": f"No se pudo generar reporte: {reason}",
            "top_risks": [],
            "opportunities": [],
            "key_metrics": {},
            "period": "n/a",
            "alert_count": 0,
        }
