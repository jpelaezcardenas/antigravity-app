"""
LLM Engine — free-tier failover cascade for automated backend requests.
Order (reordered 2026-08-28 to match what's actually confirmed working against
production Railway keys — see config.py for the full verification notes):
  1. Groq (openai/gpt-oss-120b) — confirmed live.
  2. OpenRouter free (nvidia/nemotron-3-super-120b-a12b:free) — confirmed live.
  3. Cerebras (gpt-oss-120b) — code correct, but the account still 402s (no active
     free tier, confirmed again with a fresh key 2026-08-28); fixing that is an
     account action, not a code fix.
  4. NVIDIA NIM (openai/gpt-oss-120b) — fixed 2026-08-28: key added to Railway,
     model swapped after the old one hit end-of-life. Confirmed live.
MiniMax M3, GLM 5.3, and MiMo are not used here — this backend serves
automated/production traffic, none of those plans are paid for it, and MiMo's ToS
explicitly forbids "application backend" use (2026-08-18 / 2026-08-28).
Auto-heals malformed JSON responses with intelligent parsing and recovery strategies.
"""

import json
import re
import logging
from typing import Dict, Optional, Any, Union
from enum import Enum

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    from openai import OpenAI, RateLimitError, APIError, APIConnectionError
except ImportError:
    OpenAI = None
    class RateLimitError(Exception): pass
    class APIError(Exception): pass
    class APIConnectionError(Exception): pass

import requests
try:
    from ..config import settings
except ImportError:
    from config import settings

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    GROQ = "groq"
    OPENROUTER_FREE = "openrouter_free"
    CEREBRAS = "cerebras"
    NVIDIA = "nvidia"


class AllProvidersFailedError(Exception):
    """Raised when all LLM providers have been exhausted"""
    pass


class LLMEngine:
    """
    LLM orchestrator with automatic failover and JSON auto-healing.
    Free-tier cascade: Groq -> Cerebras -> OpenRouter free -> NVIDIA NIM.
    """

    def __init__(self):
        self.groq_client = None
        self.cerebras_client = None
        self.openrouter_client = None
        self.nvidia_client = None
        self.provider_order = [
            LLMProvider.GROQ,
            LLMProvider.OPENROUTER_FREE,
            LLMProvider.CEREBRAS,
            LLMProvider.NVIDIA,
        ]
        self._initialize_clients()

    def _initialize_clients(self):
        groq_key = settings.GROQ_API_KEY
        if groq_key and Groq:
            self.groq_client = Groq(api_key=groq_key)

        cerebras_key = settings.CEREBRAS_API_KEY
        if cerebras_key and OpenAI:
            self.cerebras_client = OpenAI(
                api_key=cerebras_key,
                base_url="https://api.cerebras.ai/v1",
            )

        openrouter_key = settings.OPENROUTER_API_KEY
        if openrouter_key and OpenAI:
            self.openrouter_client = OpenAI(
                api_key=openrouter_key,
                base_url=settings.OPENROUTER_BASE_URL,
            )

        nvidia_key = settings.NVIDIA_API_KEY
        if nvidia_key and OpenAI:
            self.nvidia_client = OpenAI(
                api_key=nvidia_key,
                base_url=settings.NVIDIA_BASE_URL,
            )

    def get_ai_response(
        self,
        prompt: str,
        system_prompt: str = "",
        response_format: str = "text",
        max_tokens: int = 4000,
        temperature: float = 0.7,
        timeout: int = 30,
        synonyms: Optional[Dict[str, str]] = None,
        list_keys: Optional[set] = None,
        required_keys: Optional[set] = None,
        max_json_retries: int = 1,
    ) -> Union[Dict, str]:
        """
        Get AI response with automatic failover and JSON auto-healing.

        Args:
            prompt: User message/query
            system_prompt: System message for model context
            response_format: "json" or "text"
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)
            timeout: Request timeout in seconds
            synonyms: Optional alias-to-canonical map applied after JSON parse
            list_keys: Optional set of keys whose values must be lists
            required_keys: Optional set of keys whose absence triggers re-prompt
            max_json_retries: How many times to re-prompt on json validation failure

        Returns:
            Dict if response_format="json", str if response_format="text"

        Raises:
            AllProvidersFailedError: If all providers fail
        """
        if response_format == "json":
            return self._get_json_with_retry(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout,
                synonyms=synonyms or {},
                list_keys=list_keys or set(),
                required_keys=required_keys or set(),
                max_retries=max_json_retries,
            )

        return self._call_with_failover(
            prompt, system_prompt, max_tokens, temperature, timeout
        )

    def get_ai_response_with_profile(
        self,
        prompt: str,
        profile_name: str = None,
        system_prompt: str = "",
        response_format: str = "text",
        max_tokens: int = 4000,
        temperature: float = 0.7,
        timeout: int = 30,
        synonyms: Optional[Dict[str, str]] = None,
        list_keys: Optional[set] = None,
        required_keys: Optional[set] = None,
        max_json_retries: int = 1,
    ) -> Union[Dict, str]:
        """
        Get AI response using a profile name. All profiles now route to the
        same Groq -> Cerebras -> OpenRouter free -> NVIDIA cascade; profile_name
        is accepted for backward compatibility but does not change routing.
        """
        if profile_name:
            logger.info(f"Profile '{profile_name}' requested — routing to default free-tier cascade")
        return self.get_ai_response(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format=response_format,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
            synonyms=synonyms,
            list_keys=list_keys,
            required_keys=required_keys,
            max_json_retries=max_json_retries,
        )

    def _get_json_with_retry(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int,
        temperature: float,
        timeout: int,
        synonyms: Dict[str, str],
        list_keys: set,
        required_keys: set,
        max_retries: int,
    ) -> Dict:
        """Run JSON request with up to `max_retries` re-prompts on validation failure."""
        current_prompt = prompt
        parsed: Dict = {}

        for attempt in range(max_retries + 1):
            raw = self._call_with_failover(
                current_prompt, system_prompt, max_tokens, temperature, timeout
            )
            parsed = self._parse_llm_response(raw, synonyms=synonyms, list_keys=list_keys)

            valid, missing = self._validate_required(parsed, required_keys)
            parse_failed = isinstance(parsed, dict) and parsed.get("parsing_error") is True

            if valid and not parse_failed:
                return parsed

            last_error = (
                f"Missing required keys: {sorted(missing)}"
                if missing
                else "Response was not valid JSON; fallback structure returned"
            )
            logger.warning(
                f"JSON validation failed (attempt {attempt + 1}/{max_retries + 1}): {last_error}"
            )

            if attempt < max_retries:
                current_prompt = (
                    f"{prompt}\n\n"
                    f"IMPORTANT: Your previous response failed validation: {last_error}. "
                    f"Return ONLY a valid JSON object containing keys "
                    f"{sorted(required_keys) if required_keys else 'as specified above'}. "
                    f"No prose, no markdown fences."
                )

        return parsed

    @staticmethod
    def _validate_required(parsed: Dict, required_keys: set) -> tuple:
        """Return (is_valid, missing_keys)."""
        if not required_keys:
            return True, set()
        missing = {k for k in required_keys if k not in parsed}
        return (len(missing) == 0), missing

    def _call_with_failover(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int,
        temperature: float,
        timeout: int,
    ) -> str:
        """Run the provider failover loop and return raw text response."""
        errors_log = []

        for provider in self.provider_order:
            try:
                logger.info(f"Attempting LLM request via {provider.value}")

                if provider == LLMProvider.GROQ:
                    response = self._call_groq(
                        prompt, system_prompt, max_tokens, temperature
                    )
                elif provider == LLMProvider.CEREBRAS:
                    response = self._call_cerebras(
                        prompt, system_prompt, max_tokens, temperature
                    )
                elif provider == LLMProvider.OPENROUTER_FREE:
                    response = self._call_openrouter_free(
                        prompt, system_prompt, max_tokens, temperature
                    )
                elif provider == LLMProvider.NVIDIA:
                    response = self._call_nvidia(
                        prompt, system_prompt, max_tokens, temperature
                    )
                else:
                    continue

                logger.info(f"[OK] Success with {provider.value}")
                return response

            except (RateLimitError, APIError, APIConnectionError, requests.RequestException, TimeoutError) as e:
                error_msg = f"{provider.value}: {str(e)}"
                errors_log.append(error_msg)
                logger.warning(f"Provider {provider.value} failed: {str(e)}, trying next...")
                continue
            except Exception as e:
                error_msg = f"{provider.value}: {str(e)}"
                errors_log.append(error_msg)
                logger.warning(f"Unexpected error with {provider.value}: {str(e)}")
                continue

        error_summary = "\n".join(errors_log)
        logger.error(f"All LLM providers failed:\n{error_summary}")
        raise AllProvidersFailedError(f"All LLM providers exhausted. Errors:\n{error_summary}")

    def _call_groq(self, prompt: str, system_prompt: str, max_tokens: int, temp: float) -> str:
        """Call Groq API — openai/gpt-oss-120b, free tier."""
        if not self.groq_client:
            raise ValueError("Groq client not initialized (GROQ_API_KEY not configured)")

        response = self.groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temp,
        )
        return response.choices[0].message.content

    def _call_cerebras(self, prompt: str, system_prompt: str, max_tokens: int, temp: float) -> str:
        """Call Cerebras API (OpenAI-compatible), free tier."""
        if not self.cerebras_client:
            raise ValueError("Cerebras client not initialized (CEREBRAS_API_KEY not configured)")

        response = self.cerebras_client.chat.completions.create(
            model=settings.CEREBRAS_MODEL,
            messages=[
                {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temp,
        )
        return response.choices[0].message.content

    def _call_openrouter_free(self, prompt: str, system_prompt: str, max_tokens: int, temp: float) -> str:
        """Call OpenRouter free-tier model."""
        if not self.openrouter_client:
            raise ValueError("OpenRouter client not initialized (OPENROUTER_API_KEY not configured)")

        response = self.openrouter_client.chat.completions.create(
            model=settings.OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temp,
        )
        return response.choices[0].message.content

    def _call_nvidia(self, prompt: str, system_prompt: str, max_tokens: int, temp: float) -> str:
        """Call NVIDIA NIM API (OpenAI-compatible), free tier."""
        if not self.nvidia_client:
            raise ValueError("NVIDIA client not initialized (NVIDIA_API_KEY not configured)")

        response = self.nvidia_client.chat.completions.create(
            model=settings.NVIDIA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temp,
        )
        return response.choices[0].message.content

    def _parse_llm_response(
        self,
        response: str,
        synonyms: Optional[Dict[str, str]] = None,
        list_keys: Optional[set] = None,
    ) -> Dict:
        """
        Parse and auto-heal malformed JSON responses.

        Recovery layers (in order):
        1. Strip markdown wrappers (```json ... ```)
        2. Direct json.loads
        3. Fix trailing commas
        4. Regex extraction of {...} block
        5. Synonym key remapping (caller-provided)
        6. Type coercion (dict -> [dict] for list_keys)
        7. Safe fallback structure with parsing_error=True
        """
        synonyms = synonyms or {}
        list_keys = list_keys or set()

        parsed = self._try_parse_layers(response)

        if parsed is None:
            logger.warning("Could not parse JSON response, returning structured fallback")
            return {
                "raw_response": response[:500],
                "parsing_error": True,
                "status": "fallback",
                "message": "LLM response could not be parsed as JSON",
            }

        if synonyms:
            parsed = self._apply_synonyms(parsed, synonyms)
        if list_keys:
            parsed = self._coerce_lists(parsed, list_keys)
        return parsed

    @staticmethod
    def _try_parse_layers(response: str) -> Optional[Dict]:
        """Run the regex-only repair layers. Returns parsed dict or None."""
        cleaned = response.strip()
        if cleaned.startswith("```"):
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        fixed = re.sub(r",(\s*[}\]])", r"\1", cleaned)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

        json_match = re.search(r"\{[\s\S]*\}", fixed)
        if json_match:
            candidate = re.sub(r",(\s*[}\]])", r"\1", json_match.group(0))
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        return None

    @staticmethod
    def _apply_synonyms(parsed: Dict, synonyms: Dict[str, str]) -> Dict:
        """Rename alias keys to canonical keys (alias wins only if canonical absent)."""
        for alias, canonical in synonyms.items():
            if alias in parsed and canonical not in parsed:
                parsed[canonical] = parsed.pop(alias)
        return parsed

    @staticmethod
    def _coerce_lists(parsed: Dict, list_keys: set) -> Dict:
        """For each key in list_keys, wrap a dict value into a single-item list."""
        for key in list_keys:
            value = parsed.get(key)
            if isinstance(value, dict):
                parsed[key] = [value]
        return parsed


# Global LLM engine instance
_llm_engine = None


def get_llm_engine() -> LLMEngine:
    """Get or create global LLM engine instance"""
    global _llm_engine
    if _llm_engine is None:
        _llm_engine = LLMEngine()
    return _llm_engine


def get_ai_response(
    prompt: str,
    system_prompt: str = "",
    response_format: str = "text",
    max_tokens: int = 4000,
    temperature: float = 0.7,
    synonyms: Optional[Dict[str, str]] = None,
    list_keys: Optional[set] = None,
    required_keys: Optional[set] = None,
    max_json_retries: int = 1,
) -> Union[Dict, str]:
    """Convenience wrapper around the global LLM engine."""
    engine = get_llm_engine()
    return engine.get_ai_response(
        prompt=prompt,
        system_prompt=system_prompt,
        response_format=response_format,
        max_tokens=max_tokens,
        temperature=temperature,
        synonyms=synonyms,
        list_keys=list_keys,
        required_keys=required_keys,
        max_json_retries=max_json_retries,
    )
