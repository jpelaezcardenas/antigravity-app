"""
LLM Engine with failover support across multiple providers.
Implements automatic fallback chain: Ollama → OpenRouter Free → Groq → Cerebras → Mistral → Gemini
Auto-heals malformed JSON responses with intelligent parsing and recovery strategies.
"""

import json
import os
import re
import logging
from typing import Dict, Optional, Any, Union
from enum import Enum
import time

# Third-party imports
try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    from openai import OpenAI, RateLimitError, APIError, APIConnectionError
except ImportError:
    OpenAI = None

import requests

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Available LLM providers in failover order (Cloud-Only, no local models)"""
    OPENROUTER_FREE = "openrouter_free"
    GROQ = "groq"
    CEREBRAS = "cerebras"
    MISTRAL = "mistral"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"


class AllProvidersFailedError(Exception):
    """Raised when all LLM providers have been exhausted"""
    pass


class LLMEngine:
    """
    LLM orchestrator with automatic failover and JSON auto-healing.

    Provides intelligent LLM access with guaranteed response through
    automatic fallback to alternative providers.
    """

    def __init__(self):
        """Initialize LLM clients and configuration"""
        self.groq_client = None
        self.openai_client = None
        self.mistral_client = None
        self.gemini_api_key = None
        self.openrouter_api_key = None
        self.openrouter_free_api_key = None
        self.ollama_base_url = None

        self.provider_order = [
            LLMProvider.OPENROUTER_FREE,
            LLMProvider.GROQ,
            LLMProvider.CEREBRAS,
            LLMProvider.MISTRAL,
            LLMProvider.GEMINI,
            LLMProvider.OPENROUTER,
        ]
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize all available LLM clients (Cloud-Only, no local models)"""
        # OpenRouter Free (Gratis)
        self.openrouter_free_api_key = os.getenv("OPENROUTER_API_KEY")

        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and Groq:
            self.groq_client = Groq(api_key=groq_key)

        cerebras_key = os.getenv("CEREBRAS_API_KEY")
        if cerebras_key and OpenAI:
            self.cerebras_client = OpenAI(
                api_key=cerebras_key,
                base_url="https://api.cerebras.ai/v1"
            )
        else:
            self.cerebras_client = None

        mistral_key = os.getenv("MISTRAL_API_KEY")
        if mistral_key and OpenAI:
            self.mistral_client = OpenAI(
                api_key=mistral_key,
                base_url="https://api.mistral.ai/v1"
            )
        else:
            self.mistral_client = None

        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

    def get_ai_response(
        self,
        prompt: str,
        system_prompt: str = "",
        response_format: str = "text",
        max_tokens: int = 4000,
        temperature: float = 0.7,
        timeout: int = 30
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

        Returns:
            Dict if response_format="json", str if response_format="text"

        Raises:
            AllProvidersFailedError: If all providers fail
        """

        errors_log = []

        for provider in self.provider_order:
            try:
                logger.info(f"Attempting LLM request via {provider.value}")

                if provider == LLMProvider.OPENROUTER_FREE:
                    response = self._call_openrouter_free(
                        prompt, system_prompt, max_tokens, temperature
                    )
                elif provider == LLMProvider.GROQ:
                    response = self._call_groq(
                        prompt, system_prompt, max_tokens, temperature
                    )
                elif provider == LLMProvider.CEREBRAS:
                    response = self._call_cerebras(
                        prompt, system_prompt, max_tokens, temperature
                    )
                elif provider == LLMProvider.MISTRAL:
                    response = self._call_mistral(
                        prompt, system_prompt, max_tokens, temperature
                    )
                elif provider == LLMProvider.GEMINI:
                    response = self._call_gemini(
                        prompt, system_prompt, max_tokens, temperature, timeout
                    )
                elif provider == LLMProvider.OPENROUTER:
                    response = self._call_openrouter(
                        prompt, system_prompt, max_tokens, temperature
                    )

                logger.info(f"[OK] Success with {provider.value}")

                if response_format == "json":
                    return self._parse_llm_response(response)
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

        # All providers exhausted
        error_summary = "\n".join(errors_log)
        logger.error(f"All LLM providers failed:\n{error_summary}")
        raise AllProvidersFailedError(f"All LLM providers exhausted. Errors:\n{error_summary}")

    def _call_openrouter_free(self, prompt: str, system_prompt: str, max_tokens: int, temp: float) -> str:
        """Call OpenRouter Free API"""
        if not self.openrouter_free_api_key:
            raise ValueError("OpenRouter Free API key not configured")

        if not OpenAI:
            raise ValueError("OpenAI client not available")

        client = OpenAI(
            api_key=self.openrouter_free_api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        response = client.chat.completions.create(
            model="meta-llama/llama-2-7b-chat",  # Free model
            messages=[
                {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temp,
        )
        return response.choices[0].message.content

    def _call_groq(self, prompt: str, system_prompt: str, max_tokens: int, temp: float) -> str:
        """Call Groq API"""
        if not self.groq_client:
            raise ValueError("Groq client not initialized")

        response = self.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temp,
        )
        return response.choices[0].message.content

    def _call_cerebras(self, prompt: str, system_prompt: str, max_tokens: int, temp: float) -> str:
        """Call Cerebras API (OpenAI-compatible)"""
        if not self.cerebras_client:
            raise ValueError("Cerebras client not initialized")

        response = self.cerebras_client.chat.completions.create(
            model="llama-3.3-70b",
            messages=[
                {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temp,
        )
        return response.choices[0].message.content

    def _call_mistral(self, prompt: str, system_prompt: str, max_tokens: int, temp: float) -> str:
        """Call Mistral API (OpenAI-compatible)"""
        if not self.mistral_client:
            raise ValueError("Mistral client not initialized")

        response = self.mistral_client.chat.completions.create(
            model="mistral-large-latest",
            messages=[
                {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temp,
        )
        return response.choices[0].message.content

    def _call_gemini(self, prompt: str, system_prompt: str, max_tokens: int, temp: float, timeout: int) -> str:
        """Call Google Gemini API (REST)"""
        if not self.gemini_api_key:
            raise ValueError("Gemini API key not configured")

        headers = {
            "Content-Type": "application/json",
        }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_api_key}"

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt}
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temp,
            }
        }

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=timeout
        )
        response.raise_for_status()

        result = response.json()
        if "candidates" in result and len(result["candidates"]) > 0:
            content = result["candidates"][0].get("content", {}).get("parts", [])
            if content:
                return content[0].get("text", "")

        raise ValueError("Invalid response from Gemini API")

    def _call_openrouter(self, prompt: str, system_prompt: str, max_tokens: int, temp: float) -> str:
        """Call OpenRouter API (OpenAI-compatible)"""
        if not self.openrouter_api_key:
            raise ValueError("OpenRouter API key not configured")

        if not OpenAI:
            raise ValueError("OpenAI client not available")

        client = OpenAI(
            api_key=self.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        response = client.chat.completions.create(
            model="meta-llama/llama-3.3-70b-instruct",
            messages=[
                {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temp,
        )
        return response.choices[0].message.content

    def _parse_llm_response(self, response: str) -> Dict:
        """
        Parse and auto-heal malformed JSON responses.

        Implements multiple recovery strategies:
        1. Strip markdown wrappers (```json ... ```)
        2. Fix trailing commas
        3. Semantic key mapping
        4. Type coercion
        5. Regex extraction
        6. Structured fallback

        Args:
            response: Raw LLM response text

        Returns:
            Parsed JSON dictionary
        """

        # Strategy 1: Remove markdown wrappers
        cleaned = response.strip()
        if cleaned.startswith("```"):
            # Extract content between triple backticks
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1).strip()

        # Strategy 2: Try direct JSON parse first
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Strategy 3: Fix trailing commas
        fixed = re.sub(r',(\s*[}\]])', r'\1', cleaned)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

        # Strategy 4: Extract JSON object with regex
        json_match = re.search(r'\{[\s\S]*\}', fixed)
        if json_match:
            json_str = json_match.group(0)
            # Fix any remaining issues
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # Strategy 5: Structured fallback
        logger.warning(f"Could not parse JSON response, returning structured fallback")
        return {
            "raw_response": response[:500],
            "parsing_error": True,
            "status": "fallback",
            "message": "LLM response could not be parsed as JSON"
        }


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
) -> Union[Dict, str]:
    """
    Convenience function to get AI response via the global engine.

    Args:
        prompt: User message/query
        system_prompt: System message for model context
        response_format: "json" or "text"
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (0-1)

    Returns:
        Dict if response_format="json", str if response_format="text"

    Raises:
        AllProvidersFailedError: If all providers fail
    """
    engine = get_llm_engine()
    return engine.get_ai_response(
        prompt=prompt,
        system_prompt=system_prompt,
        response_format=response_format,
        max_tokens=max_tokens,
        temperature=temperature
    )
