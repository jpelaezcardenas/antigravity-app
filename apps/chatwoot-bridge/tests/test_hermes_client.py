"""Tests for hermes_client.py (Task Group 8): OpenAI-compatible chat completions
call shape, fail-soft on timeout/non-200, startup liveness check. respx-mocked."""

from __future__ import annotations

import json

import httpx
import respx
import pytest
from httpx import Response

from config import settings

HERMES_URL = "http://localhost:8642"


@pytest.fixture(autouse=True)
def _configure(monkeypatch):
    monkeypatch.setattr(settings, "HERMES_GATEWAY_URL", HERMES_URL)
    monkeypatch.setattr(settings, "HERMES_MODEL", "taty-v1")
    monkeypatch.setattr(settings, "HERMES_API_KEY", "test-hermes-key")


class TestInvokeChatCompletion:
    @respx.mock
    @pytest.mark.asyncio
    async def test_sends_correct_request_shape(self):
        import hermes_client

        route = respx.post(f"{HERMES_URL}/v1/chat/completions").mock(
            return_value=Response(
                200,
                json={
                    "choices": [{"message": {"role": "assistant", "content": "Hola!"}}]
                },
            )
        )

        history = [{"role": "user", "content": "previo"}]
        result = await hermes_client.invoke_chat_completion(history, "Hola Taty")

        assert result == "Hola!"
        request = route.calls[0].request
        assert request.headers["authorization"] == "Bearer test-hermes-key"
        body = json.loads(request.content)
        assert body["model"] == "taty-v1"
        assert body["stream"] is False
        assert body["messages"] == [
            {"role": "user", "content": "previo"},
            {"role": "user", "content": "Hola Taty"},
        ]

    @respx.mock
    @pytest.mark.asyncio
    async def test_timeout_returns_none_without_raising(self):
        import hermes_client

        respx.post(f"{HERMES_URL}/v1/chat/completions").mock(
            side_effect=httpx.TimeoutException("timed out")
        )

        result = await hermes_client.invoke_chat_completion([], "hola")

        assert result is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_non_200_returns_none_without_raising(self):
        import hermes_client

        respx.post(f"{HERMES_URL}/v1/chat/completions").mock(
            return_value=Response(500, json={"error": "boom"})
        )

        result = await hermes_client.invoke_chat_completion([], "hola")

        assert result is None


class TestCheckModels:
    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_parsed_response_on_success(self):
        import hermes_client

        respx.get(f"{HERMES_URL}/v1/models").mock(
            return_value=Response(200, json={"data": [{"id": "taty-v1"}]})
        )

        result = await hermes_client.check_models()

        assert result == {"data": [{"id": "taty-v1"}]}

    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_none_on_failure_without_raising(self):
        import hermes_client

        respx.get(f"{HERMES_URL}/v1/models").mock(
            side_effect=httpx.ConnectError("refused")
        )

        result = await hermes_client.check_models()

        assert result is None
