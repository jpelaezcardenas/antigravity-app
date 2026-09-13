"""
Tests for D1 (hermes-jarvis-contexia, 2026-09-13 re-scope): a single Telegram bot.

Before this change, the founder's personal "Jarvis" assistant lived behind a SECOND
Telegram bot (`jarvis_endpoints.py::jarvis_telegram_webhook`, its own token/secret).
D1 merges that routing into Taty's existing webhook (`telegram_endpoints.py`):
before the `telegram_chat_mappings` lookup, a message from the founder's own
`chat_id` (`TELEGRAM_JUAN_DAVID_CHAT_ID`) is proxied to Hermes instead of Taty —
any other `chat_id` keeps the exact pre-existing behavior (contract is additive,
byte-identical for non-founder chats).

Mirrors the direct-call pattern of test_telegram_taty_tenant_translation.py.
"""

import asyncio
import json

import pytest

import presentation.telegram_endpoints as telegram_module
from presentation.telegram_endpoints import telegram_webhook


def run(coro):
    return asyncio.run(coro)


class _FakeRequest:
    """Minimal stand-in for fastapi.Request — only `.body()` is used."""

    def __init__(self, payload: dict):
        self._body = json.dumps(payload).encode("utf-8")

    async def body(self):
        return self._body


def _telegram_update(chat_id: int, text: str = "¿cómo va la caja hoy?") -> dict:
    return {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "date": 1700000000,
            "text": text,
            "from": {"id": 999, "is_bot": False, "first_name": "Test"},
            "chat": {"id": chat_id, "type": "private"},
        },
    }


class _ExplodingSupabase:
    """Proves the Jarvis routing branch never touches Supabase at all —
    neither `telegram_chat_mappings` nor `tenants`."""

    def table(self, name):
        raise AssertionError(
            f"Jarvis routing must return before querying Supabase table {name!r}"
        )


class _ForbiddenSocialOpsService:
    """Proves the Jarvis routing branch runs before the Social Ops command check."""

    def is_social_ops_command(self, text: str) -> bool:
        raise AssertionError("Jarvis routing must short-circuit before the Social Ops check")


class _ForbiddenTatyService:
    def ask(self, **kwargs):
        raise AssertionError("taty.ask() must NOT be called for the founder's Jarvis chat_id")


@pytest.fixture
def fake_sent_messages(monkeypatch):
    sent = []

    async def fake_send(chat_id, text):
        sent.append({"chat_id": chat_id, "text": text})

    monkeypatch.setattr(telegram_module, "send_telegram_message", fake_send)
    return sent


class TestJarvisSingleBotRouting:
    """Task 1.1 — a founder chat_id routes to Hermes, never touching Taty/Supabase."""

    def test_founder_chat_id_routes_to_hermes_not_taty(self, fake_sent_messages, monkeypatch):
        monkeypatch.setattr(telegram_module, "TELEGRAM_JUAN_DAVID_CHAT_ID", "555")
        monkeypatch.setattr(telegram_module, "get_supabase", lambda: _ExplodingSupabase())
        monkeypatch.setattr(telegram_module, "get_service_supabase", lambda: _ExplodingSupabase())
        monkeypatch.setattr(telegram_module, "get_social_ops_service", lambda: _ForbiddenSocialOpsService())
        monkeypatch.setattr(telegram_module, "get_taty_service", lambda: _ForbiddenTatyService())

        async def fake_hermes_call(user_text: str) -> str:
            assert user_text == "¿cómo va la caja hoy?"
            return "La caja real de hoy es $1.200.000."

        monkeypatch.setattr(telegram_module, "_call_hermes_api", fake_hermes_call)

        request = _FakeRequest(_telegram_update(chat_id=555))

        result = run(telegram_webhook(request))

        assert result == {"ok": True, "jarvis": True}
        assert len(fake_sent_messages) == 1
        assert fake_sent_messages[0]["chat_id"] == 555
        assert fake_sent_messages[0]["text"] == "La caja real de hoy es $1.200.000."

    def test_founder_chat_id_hermes_failure_sends_error_and_never_raises(
        self, fake_sent_messages, monkeypatch
    ):
        monkeypatch.setattr(telegram_module, "TELEGRAM_JUAN_DAVID_CHAT_ID", "555")
        monkeypatch.setattr(telegram_module, "get_supabase", lambda: _ExplodingSupabase())
        monkeypatch.setattr(telegram_module, "get_service_supabase", lambda: _ExplodingSupabase())
        monkeypatch.setattr(telegram_module, "get_social_ops_service", lambda: _ForbiddenSocialOpsService())

        async def failing_hermes_call(user_text: str) -> str:
            raise RuntimeError("Hermes gateway unreachable")

        monkeypatch.setattr(telegram_module, "_call_hermes_api", failing_hermes_call)

        request = _FakeRequest(_telegram_update(chat_id=555))

        result = run(telegram_webhook(request))

        assert result == {"ok": True, "jarvis": True}
        assert len(fake_sent_messages) == 1
        assert "Hermes" in fake_sent_messages[0]["text"]


class TestNonFounderChatUnaffected:
    """Task 1.2 — a non-founder chat_id keeps the exact pre-existing behavior."""

    def test_non_founder_chat_id_still_goes_through_taty_flow(self, monkeypatch):
        from types import SimpleNamespace

        monkeypatch.setattr(telegram_module, "TELEGRAM_JUAN_DAVID_CHAT_ID", "555")

        class _FakeTable:
            def __init__(self, rows):
                self._rows = rows

            def select(self, *args, **kwargs):
                return self

            def eq(self, *args, **kwargs):
                return self

            def execute(self):
                return SimpleNamespace(data=self._rows)

        class _FakeSupabase:
            def table(self, name):
                if name == "telegram_chat_mappings":
                    return _FakeTable([{"company_id": "acme-co"}])
                if name == "tenants":
                    return _FakeTable([{"id": "11111111-1111-1111-1111-111111111111"}])
                raise AssertionError(f"Unexpected table: {name}")

        class _FakeSocialOpsService:
            def is_social_ops_command(self, text: str) -> bool:
                return False

            def get_active_onboarding_for_company(self, company_id: str):
                return None

        class _FakeTatyService:
            def __init__(self):
                self.ask_calls = []

            def ask(self, **kwargs):
                self.ask_calls.append(kwargs)
                return {
                    "answer": "Respuesta de prueba",
                    "citations": [],
                    "latency_ms": 5,
                    "confidence": 0.9,
                    "requires_human_review": False,
                    "result": "Respuesta de prueba",
                }

        fake_supabase = _FakeSupabase()
        fake_taty = _FakeTatyService()
        sent = []

        async def fake_send(chat_id, text):
            sent.append({"chat_id": chat_id, "text": text})

        monkeypatch.setattr(telegram_module, "get_supabase", lambda: fake_supabase)
        monkeypatch.setattr(telegram_module, "get_service_supabase", lambda: fake_supabase)
        monkeypatch.setattr(telegram_module, "get_social_ops_service", lambda: _FakeSocialOpsService())
        monkeypatch.setattr(telegram_module, "get_taty_service", lambda: fake_taty)
        monkeypatch.setattr(telegram_module, "send_telegram_message", fake_send)

        # A different chat_id (999) than the founder's (555) — must be unaffected.
        request = _FakeRequest(_telegram_update(chat_id=999))

        result = run(telegram_webhook(request))

        assert result == {"ok": True}
        assert len(fake_taty.ask_calls) == 1
        assert fake_taty.ask_calls[0]["tenant_id"] == "11111111-1111-1111-1111-111111111111"
