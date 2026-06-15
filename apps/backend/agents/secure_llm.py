"""SOSP-compliant wrapper around the LLM engine.

Masks every prompt (and system prompt) with the SOSP Anonymizer before it
reaches a cloud provider, then rehydrates the model's response. API endpoints
and services that may send client fiscal data or PII MUST use this instead of
calling ``get_ai_response`` directly.

Compliance rule (see contexia-ground-truth memory): anonimización pre-LLM —
every prompt routed through llm_engine must be anonymized.
"""

from __future__ import annotations

from typing import Any

from agents.anonymizer import Anonymizer, AnonymizationMap
from agents.llm_engine import get_ai_response

# Separator used to mask prompt + system_prompt under one shared token map, so
# an identical value maps to the same token across both. The NUL byte ensures it
# never collides with anonymizer patterns or real prompt content.
_SPLIT = "\x00__SOSP_SPLIT__\x00"


def _rehydrate(response: Any, mapping: AnonymizationMap) -> Any:
    """Restore original values inside a str/dict/list response."""
    if isinstance(response, str):
        return Anonymizer.unmask(response, mapping)
    if isinstance(response, dict):
        return {k: _rehydrate(v, mapping) for k, v in response.items()}
    if isinstance(response, list):
        return [_rehydrate(v, mapping) for v in response]
    return response


def get_anonymized_ai_response(
    prompt: str,
    system_prompt: str = "",
    **kwargs: Any,
) -> Any:
    """Anonymize prompt + system_prompt, call the LLM, then rehydrate the result.

    Both ``prompt`` and ``system_prompt`` are masked under a single shared token
    map (so the same original value yields the same token in both), the masked
    text is sent to the failover chain, and the response is rehydrated with that
    map before being returned.

    Returns the same shape ``get_ai_response`` would (dict for JSON, str for
    text), with anonymization tokens replaced by their original values.
    """
    combined = f"{system_prompt}{_SPLIT}{prompt}"
    masked_combined, mask_map = Anonymizer.mask(combined)
    masked_system, _, masked_prompt = masked_combined.partition(_SPLIT)

    response = get_ai_response(
        prompt=masked_prompt,
        system_prompt=masked_system,
        **kwargs,
    )
    return _rehydrate(response, mask_map)
