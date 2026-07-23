"""
Tests for POST/GET /api/v1/agents/ask tenant resolution (taty-per-tenant-profiles, task 3;
migrated onto the canonical `resolve_request_tenant_scope` helper by
agent-endpoints-real-tenant-filtering, Stage 4).

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
flow) and `core.tenant_context.resolve_cliente_cero_tenant_id` (the endpoint's
own file-local async `_resolve_cliente_cero_tenant_id` was removed in the
Stage 4 migration onto the shared helper).

Note: `resolve_request_tenant_scope` always calls `resolve_cliente_cero_tenant_id` first
(to detect the Contexia-operator case), unlike the removed file-local helper, which was
only invoked for the staging identity. The autouse fixture below stubs it to a value that
never matches any test's `resolved_tenant_id`, so the operator/all_tenants branch is never
accidentally taken — the property under test is "the caller never receives Cliente Cero's
tenant_id", not "the lookup was never invoked".
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


@pytest.fixture(autouse=True)
def _stub_cliente_cero_lookup(monkeypatch):
    import core.tenant_context as tenant_context_module

    monkeypatch.setattr(
        tenant_context_module, "resolve_cliente_cero_tenant_id",
        lambda client: "unrelated-cliente-cero-id",
    )


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
        import core.tenant_context as tenant_context_module

        monkeypatch.setattr(
            tenant_context_module, "resolve_cliente_cero_tenant_id",
            lambda client: "cliente-cero-tenant-uuid",
        )

        request = TatyAskRequest(question="¿Cuál es el UVT 2026?")
        response = run(ask_taty(request=request, user=dict(_STAGING_USER)))

        assert len(fake_taty.ask_calls) == 1
        assert fake_taty.ask_calls[0]["tenant_id"] == "cliente-cero-tenant-uuid"
        assert response.error_code is None

    def test_authenticated_unresolved_caller_gets_error_and_never_calls_cliente_cero(
        self, fake_taty
    ):
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
