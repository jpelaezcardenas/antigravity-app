"""
Agent 5: Repurposer - LÍNEA 3
Transforms approved content into channel-specific formats.

Channels supported (MVP):
  - telegram      → short, emoji-light, 1-2 paragraphs max, plain text
  - dashboard     → rich, markdown allowed, sections + bullets OK
  - sms           → ultra-short, ≤160 chars, no markdown, no emojis
  - email         → formal, salutation + body + signature placeholder

Output is a dict keyed by channel name.
"""

from typing import Dict, List
import logging
from agents.base_agent import BaseAgent, AgentRole

logger = logging.getLogger(__name__)


CHANNEL_CONSTRAINTS = {
    "telegram": {"max_chars": 1000, "markdown": False, "emojis": "light"},
    "dashboard": {"max_chars": 4000, "markdown": True, "emojis": "none"},
    "sms": {"max_chars": 160, "markdown": False, "emojis": "none"},
    "email": {"max_chars": 3000, "markdown": False, "emojis": "none"},
}


class RepurposerAgent(BaseAgent):
    """
    Repurposer Agent

    Input: {
        "source_content": str,             # approved by Editor
        "target_channels": List[str],      # subset of CHANNEL_CONSTRAINTS keys
        "metadata": Dict                   # optional: company_name, alert_level, etc.
    }

    Output: {
        "variants": {channel_name: str, ...},
        "skipped_channels": List[str],     # channels that failed to format
    }
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.REPURPOSER,
            name="Repurposer Agent",
            version="1.0"
        )

    def execute(self, input_data: Dict) -> Dict:
        if not self.validate_input(input_data, ["source_content", "target_channels"]):
            return {"variants": {}, "skipped_channels": [], "error": "Missing source_content or target_channels"}

        source = input_data["source_content"]
        channels = input_data["target_channels"]
        metadata = input_data.get("metadata", {})

        variants: Dict[str, str] = {}
        skipped: List[str] = []

        for ch in channels:
            if ch not in CHANNEL_CONSTRAINTS:
                logger.warning(f"Repurposer: unknown channel '{ch}', skipping")
                skipped.append(ch)
                continue

            formatted = self._format_for_channel(source, ch, metadata)
            if formatted:
                variants[ch] = formatted
            else:
                skipped.append(ch)

        return {"variants": variants, "skipped_channels": skipped}

    def _format_for_channel(self, source: str, channel: str, metadata: Dict) -> str:
        constraints = CHANNEL_CONSTRAINTS[channel]
        company = metadata.get("company_name", "tu empresa")

        prompt = f"""Reformula el siguiente contenido para el canal "{channel}".

Contenido original:
\"\"\"{source}\"\"\"

Restricciones del canal {channel}:
- Máximo {constraints['max_chars']} caracteres
- Markdown permitido: {constraints['markdown']}
- Uso de emojis: {constraints['emojis']}

Contexto: empresa = {company}

Reglas:
1. Conserva hechos y números exactos.
2. Ajusta tono y longitud al canal.
3. No agregues información nueva.
4. Si es SMS, prioriza la acción más urgente.

Devuelve JSON: {{"formatted_content": "..."}}.
Solo JSON válido."""

        system_prompt = f"Eres un experto en adaptación de contenido para {channel}. Devuelve solo JSON válido."

        response = self.call_llm(
            prompt,
            system_prompt,
            response_format="json",
            required_keys=["formatted_content"],
            max_json_retries=2,
        )

        if not isinstance(response, dict) or response.get("parsing_error"):
            logger.warning(f"Repurposer LLM failed for {channel}, using truncation fallback")
            return self._truncate_fallback(source, constraints["max_chars"])

        formatted = response.get("formatted_content", "").strip()
        if not formatted:
            return self._truncate_fallback(source, constraints["max_chars"])

        # Enforce hard char limit defensively
        if len(formatted) > constraints["max_chars"]:
            formatted = formatted[: constraints["max_chars"] - 3] + "..."
        return formatted

    def _truncate_fallback(self, source: str, max_chars: int) -> str:
        if len(source) <= max_chars:
            return source
        return source[: max_chars - 3] + "..."
