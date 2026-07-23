"""
Tests for POST/GET /api/v1/agents/ask tenant resolution (taty-per-tenant-profiles, task 3).

Before this change, the endpoint had ZERO auth and trusted a client-supplied
`company_id` to select the profile — any caller could read any tenant's Taty
config by guessing/spoofing that id. These tests verify the endpoint now
mirrors the `financials_endpoints.py` resolution pattern:
  1. An authenticated caller with a resolved tenant is scoped to THEIR OWN
     tenant, regardless of any `company_id` in the request body.
  2. The unauthenticated/local-dev staging identity still falls back to
     Cliente Cero (back-compat).
  3. An authenticated caller with NO resolved tenant gets an in-band
     `error_code="tenant_not_resolved"` response — NEVER Cliente Cero.
  4. A spoofed `company_id` belonging to a different tenant is ignored.

Mirrors the direct-function-call pattern of
`test_financials_endpoint_tenant_scoping.py` — calls the endpoint functions
directly with hand-built `user` dicts, monkeypatching `get_taty_service()`
(so this tests the endpoint's resolution logic, not the full `ask()` -> LLM
flow) and `_resolve_cliente_cero_tenant_id()`.
"""

import asyncio

import pytest

from core.deps import _STAGING_USER
from presentation.taty_endpoints import ask_taty, ask_taty_get, TatyAskRequest


def run(coro):
    return asyncio.run(coro)


class _FakeTatyService:
    """Records the kwargs `ask()` was called with and returns a fixed response."""

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


@pytest.fixture
def fake_taty(monkeypatch):
    import presentation.taty_endpoints as endpoints_module

    fake = _FakeTatyService()
    monkeypatch.setattr(endpoints_module, "get_taty_service", lambda: fake)
    return fake


class TestAskTatyEndpointTenantScoping:
    def test_resolved_user_is_scoped_to_own_tenant(self, fake_taty):
        user = {
            "id": "user-a",
            "email": "a@client.co",
            "resolved_user_id": "uuid-a",
            "resolved_tenant_id": "tenant-a-uuid",
        }
        request = TatyAskRequest(question="¿Cuál es el UVT 2026?")

        response = run(ask_taty(request=request, user=user))

        assert len(fake_taty.ask_calls) == 1
        assert fake_taty.ask_calls[0]["tenant_id"] == "tenant-a-uuid"
        assert response.error_code is None

    def test_staging_identity_falls_back_to_cliente_cero(self, fake_taty, monkeypatch):
        import presentation.taty_endpoints as endpoints_module

        called = {"cliente_cero": False}

        async def fake_resolve_cliente_cero():
            called["cliente_cero"] = True
            return "cliente-cero-tenant-uuid"

        monkeypatch.setattr(
            endpoints_module, "_resolve_cliente_cero_tenant_id", fake_resolve_cliente_cero
        )

        request = TatyAskRequest(question="¿Cuál es el UVT 2026?")
        response = run(ask_taty(request=request, user=dict(_STAGING_USER)))

        assert called["cliente_cero"] is True
        assert len(fake_taty.ask_calls) == 1
        assert fake_taty.ask_calls[0]["tenant_id"] == "cliente-cero-tenant-uuid"
        assert response.error_code is None

    def test_authenticated_unresolved_caller_gets_error_and_never_calls_cliente_cero(
        self, fake_taty, monkeypatch
    ):
        import presentation.taty_endpoints as endpoints_module

        async def must_not_be_called():
            raise AssertionError(
                "Cliente Cero fallback must not be used for an authenticated, unresolved caller"
            )

        monkeypatch.setattr(
            endpoints_module, "_resolve_cliente_cero_tenant_id", must_not_be_called
        )

        user = {
            "id": "76680e1f-2943-4235-8501-18b090d59257",
            "email": "growth@contexia.online",
            "resolved_user_id": None,
            "resolved_tenant_id": None,
        }
        request = TatyAskRequest(question="¿Cuál es el UVT 2026?")

        response = run(ask_taty(request=request, user=user))

        assert response.error_code == "tenant_not_resolved"
        assert response.requires_human_review is True
        assert len(fake_taty.ask_calls) == 0

    def test_spoofed_company_id_is_ignored(self, fake_taty):
        """Resolved user A supplies a company_id that looks like it belongs to
        another tenant — the endpoint must still resolve tenant A's own id."""
        user = {
            "id": "user-a",
            "email": "a@client.co",
            "resolved_user_id": "uuid-a",
            "resolved_tenant_id": "tenant-a-uuid",
        }
        request = TatyAskRequest(
            question="¿Cuál es el UVT 2026?", company_id="tenant-b-fake-spoofed-id"
        )

        response = run(ask_taty(request=request, user=user))

        assert len(fake_taty.ask_calls) == 1
        assert fake_taty.ask_calls[0]["tenant_id"] == "tenant-a-uuid"
        assert response.error_code is None

    def test_get_handler_shares_resolution_logic(self, fake_taty):
        """Smoke test: GET delegates to the same resolution path as POST."""
        user = {
            "id": "user-a",
            "email": "a@client.co",
            "resolved_user_id": "uuid-a",
            "resolved_tenant_id": "tenant-a-uuid",
        }

        response = run(
            ask_taty_get(
                question="¿Cuál es el UVT 2026?",
                channel="dashboard",
                conversation_id=None,
                user_id=None,
                company_id="ignored-spoofed-id",
                user=user,
            )
        )

        assert len(fake_taty.ask_calls) == 1
        assert fake_taty.ask_calls[0]["tenant_id"] == "tenant-a-uuid"
        assert response.error_code is None
