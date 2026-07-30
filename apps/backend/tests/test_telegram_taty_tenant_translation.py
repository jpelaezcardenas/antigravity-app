"""
Tests for Telegram webhook -> Taty tenant translation (taty-per-tenant-profiles, task 4).

`telegram_chat_mappings` stores a legacy `company_id`. Before this task,
`telegram_webhook()` passed that raw `company_id` straight into
`taty.ask(company_id=...)`, which now raises `TypeError` since `ask()` was
renamed to take `tenant_id` (task 2). These tests verify a translation step:
`_resolve_tenant_for_company_id(company_id)` looks up `tenants.company_id` and
returns the matching tenant uuid (or None), and the webhook uses that uuid to
call `taty.ask(tenant_id=...)` — or, if untranslatable, sends the existing
"chat no configurado" reply and never calls `ask()` at all.

Calls `telegram_webhook()` directly with a hand-built fake `Request` (async
`.body()`), monkeypatching `get_supabase`, `get_social_ops_service`,
`get_taty_service`, and `send_telegram_message` — mirrors the direct-call
pattern already used by `test_taty_endpoints_tenant_scoping.py`.
"""

import asyncio
import json
from types import SimpleNamespace

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


def _telegram_update(chat_id: int = 12345, text: str = "¿Cuál es el UVT 2026?") -> dict:
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


class _FakeTable:
    """Chainable fake for `supabase.table(name).select(...).eq(...).execute()`."""

    def __init__(self, rows):
        self._rows = rows

    def select(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def execute(self):
        return SimpleNamespace(data=self._rows)


class _FakeSupabase:
    """Routes `.table("telegram_chat_mappings")` and `.table("tenants")` to
    distinct fixture rows, matching the two real queries the webhook makes."""

    def __init__(self, mapping_rows, tenant_rows):
        self._mapping_rows = mapping_rows
        self._tenant_rows = tenant_rows

    def table(self, name):
        if name == "telegram_chat_mappings":
            return _FakeTable(self._mapping_rows)
        if name == "tenants":
            return _FakeTable(self._tenant_rows)
        raise AssertionError(f"Unexpected table queried in this test: {name}")


class _FakeSocialOpsService:
    """Bypasses the Social Ops command branch and onboarding branch (out of
    scope for this task) so the webhook reaches the Taty call site."""

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


class _ForbiddenTatyService:
    """Raises hard if `ask()` is ever invoked — used to prove the
    untranslatable-company_id path never reaches Taty."""

    def ask(self, **kwargs):
        raise AssertionError("taty.ask() must NOT be called for an untranslatable company_id")


@pytest.fixture
def fake_social_ops(monkeypatch):
    fake = _FakeSocialOpsService()
    monkeypatch.setattr(telegram_module, "get_social_ops_service", lambda: fake)
    return fake


@pytest.fixture
def fake_sent_messages(monkeypatch):
    sent = []

    async def fake_send(chat_id, text):
        sent.append({"chat_id": chat_id, "text": text})

    monkeypatch.setattr(telegram_module, "send_telegram_message", fake_send)
    return sent


class TestTelegramCompanyIdToTenantTranslation:
    def test_mapped_company_id_resolves_and_calls_ask_with_tenant_id(
        self, fake_social_ops, fake_sent_messages, monkeypatch
    ):
        fake_supabase = _FakeSupabase(
            mapping_rows=[{"company_id": "acme-co"}],
            tenant_rows=[{"id": "11111111-1111-1111-1111-111111111111"}],
        )
        monkeypatch.setattr(telegram_module, "get_supabase", lambda: fake_supabase)
        monkeypatch.setattr(telegram_module, "get_service_supabase", lambda: fake_supabase)

        fake_taty = _FakeTatyService()
        monkeypatch.setattr(telegram_module, "get_taty_service", lambda: fake_taty)

        request = _FakeRequest(_telegram_update())

        result = run(telegram_webhook(request))

        assert result == {"ok": True}
        assert len(fake_taty.ask_calls) == 1
        assert fake_taty.ask_calls[0]["tenant_id"] == "11111111-1111-1111-1111-111111111111"
        assert "company_id" not in fake_taty.ask_calls[0]
        # Success path replies with the answer, not the "no configurado" message.
        assert fake_sent_messages
        assert "no está configurado" not in fake_sent_messages[-1]["text"]

    def test_untranslatable_company_id_sends_no_configurado_and_never_calls_ask(
        self, fake_social_ops, fake_sent_messages, monkeypatch
    ):
        fake_supabase = _FakeSupabase(
            mapping_rows=[{"company_id": "orphan-co"}],
            tenant_rows=[],  # no tenant row matches this company_id
        )
        monkeypatch.setattr(telegram_module, "get_supabase", lambda: fake_supabase)
        monkeypatch.setattr(telegram_module, "get_service_supabase", lambda: fake_supabase)

        forbidden_taty = _ForbiddenTatyService()
        monkeypatch.setattr(telegram_module, "get_taty_service", lambda: forbidden_taty)

        request = _FakeRequest(_telegram_update())

        result = run(telegram_webhook(request))

        assert result == {"ok": True}
        assert len(fake_sent_messages) == 1
        assert "no está configurado" in fake_sent_messages[0]["text"]


class TestResolveTenantForCompanyIdHelper:
    def test_returns_tenant_id_when_matching_row_exists(self, monkeypatch):
        fake_supabase = _FakeSupabase(
            mapping_rows=[],
            tenant_rows=[{"id": "22222222-2222-2222-2222-222222222222"}],
        )
        monkeypatch.setattr(telegram_module, "get_supabase", lambda: fake_supabase)
        monkeypatch.setattr(telegram_module, "get_service_supabase", lambda: fake_supabase)

        result = telegram_module._resolve_tenant_for_company_id("acme-co")

        assert result == "22222222-2222-2222-2222-222222222222"

    def test_returns_none_when_no_matching_row(self, monkeypatch):
        fake_supabase = _FakeSupabase(mapping_rows=[], tenant_rows=[])
        monkeypatch.setattr(telegram_module, "get_supabase", lambda: fake_supabase)
        monkeypatch.setattr(telegram_module, "get_service_supabase", lambda: fake_supabase)

        result = telegram_module._resolve_tenant_for_company_id("orphan-co")

        assert result is None

    def test_returns_none_on_lookup_error_without_raising(self, monkeypatch):
        class _ExplodingSupabase:
            def table(self, name):
                raise RuntimeError("connection refused")

        monkeypatch.setattr(telegram_module, "get_supabase", lambda: _ExplodingSupabase())
        monkeypatch.setattr(telegram_module, "get_service_supabase", lambda: _ExplodingSupabase())

        result = telegram_module._resolve_tenant_for_company_id("acme-co")

        assert result is None
