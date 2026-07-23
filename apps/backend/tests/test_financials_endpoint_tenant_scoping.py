"""
Tests for GET /api/v1/financials tenant resolution (per-tenant-client-access).

Before this change, the endpoint hardcoded Cliente Cero regardless of the caller,
so every PWA login saw Contexia's own Caja Real. These tests verify:
  1. An authenticated caller with a resolved tenant sees THEIR OWN data.
  2. Two different authenticated clients see two different, non-leaking snapshots.
  3. The unauthenticated/local-dev staging identity still falls back to Cliente Cero
     (back-compat for the existing Contexia overview + local dev).
  4. An authenticated caller with NO resolved tenant gets an empty snapshot — NOT
     Cliente Cero (no leak to an unwired client login).

Uses the same hermetic, throwaway-tenant pattern as test_financials_aggregation.py.
"""

import asyncio
import uuid

import pytest
from datetime import date, timedelta

from core.supabase_client import get_supabase
from core.deps import _STAGING_USER
from presentation.financials_endpoints import get_financials
from tests.test_financials_aggregation import insert_test_entry


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def two_test_tenants():
    """Two hermetic, throwaway tenants with different Caja Real balances."""
    supabase = get_supabase()
    tenant_ids = []
    for label in ("A", "B"):
        nit = f"TEST-SCOPE-{label}-{uuid.uuid4().hex[:10]}"
        inserted = (
            supabase.table("tenants")
            .insert({"nit": nit, "legal_name": f"Hermetic Tenant {label} (pytest)", "is_cliente_cero": False})
            .execute()
        )
        tenant_ids.append(inserted.data[0]["id"])

    yield tenant_ids

    for tenant_id in tenant_ids:
        supabase.table("erp_journal_lines").delete().eq("tenant_id", tenant_id).execute()
        supabase.table("erp_journal_entries").delete().eq("tenant_id", tenant_id).execute()
        supabase.table("tenants").delete().eq("id", tenant_id).execute()


@pytest.fixture
def cleanup_test_entries():
    created_ids = []
    yield created_ids
    supabase = get_supabase()
    for entry_id in created_ids:
        supabase.table("erp_journal_lines").delete().eq("entry_id", entry_id).execute()
        supabase.table("erp_journal_entries").delete().eq("id", entry_id).execute()


class TestFinancialsEndpointTenantScoping:
    def test_authenticated_caller_sees_own_tenant_snapshot(
        self, two_test_tenants, cleanup_test_entries
    ):
        tenant_a, _ = two_test_tenants
        today = date.today()

        entry_id = insert_test_entry(
            get_supabase(),
            tenant_a,
            "SCOPE-A-001",
            today,
            [
                {"account_code": "1110", "debit_minor": 777000000, "memo": "Tenant A cash"},
                {"account_code": "1205", "credit_minor": 777000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(entry_id)

        user = {"id": "user-a", "email": "a@client.co", "resolved_user_id": "uuid-a", "resolved_tenant_id": tenant_a}
        snapshot = run(get_financials(user=user))

        assert snapshot["caja_real"] == 777000000

    def test_two_clients_see_different_non_leaking_snapshots(
        self, two_test_tenants, cleanup_test_entries
    ):
        tenant_a, tenant_b = two_test_tenants
        today = date.today()

        entry_a = insert_test_entry(
            get_supabase(), tenant_a, "SCOPE-DIFF-A", today,
            [
                {"account_code": "1110", "debit_minor": 100000000, "memo": "A cash"},
                {"account_code": "1205", "credit_minor": 100000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(entry_a)

        entry_b = insert_test_entry(
            get_supabase(), tenant_b, "SCOPE-DIFF-B", today,
            [
                {"account_code": "1110", "debit_minor": 250000000, "memo": "B cash"},
                {"account_code": "1205", "credit_minor": 250000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(entry_b)

        user_a = {"id": "user-a", "email": "a@client.co", "resolved_user_id": "uuid-a", "resolved_tenant_id": tenant_a}
        user_b = {"id": "user-b", "email": "b@client.co", "resolved_user_id": "uuid-b", "resolved_tenant_id": tenant_b}

        snapshot_a = run(get_financials(user=user_a))
        snapshot_b = run(get_financials(user=user_b))

        assert snapshot_a["caja_real"] == 100000000
        assert snapshot_b["caja_real"] == 250000000
        assert snapshot_a["caja_real"] != snapshot_b["caja_real"]

    def test_staging_identity_falls_back_to_cliente_cero(self, monkeypatch):
        """Unauthenticated/local-dev caller (AUTH_ENFORCED=False, no token) still
        resolves to Cliente Cero — back-compat for the existing overview + local dev."""
        import presentation.financials_endpoints as endpoints_module

        called = {"cliente_cero": False}

        async def fake_resolve_cliente_cero():
            called["cliente_cero"] = True
            return "fake-cliente-cero-tenant-id"

        monkeypatch.setattr(endpoints_module, "_resolve_cliente_cero_tenant_id", fake_resolve_cliente_cero)
        monkeypatch.setattr(
            endpoints_module,
            "compute_pulso_daily_snapshot",
            lambda tenant_id, as_of: {"caja_real": 0, "dinero_disponible": 0, "ventas_ayer": 0, "gastos_ayer": 0, "status": "empty"},
        )

        snapshot = run(get_financials(user=dict(_STAGING_USER)))

        assert called["cliente_cero"] is True

    def test_authenticated_unresolved_tenant_returns_empty_not_cliente_cero(self, monkeypatch):
        """An authenticated caller (not the staging identity) with NO resolved
        tenant must get an empty snapshot, and Cliente Cero resolution must
        NEVER be invoked — that would leak Contexia's data to an unwired login."""
        import presentation.financials_endpoints as endpoints_module

        async def must_not_be_called():
            raise AssertionError("Cliente Cero fallback must not be used for an authenticated, unresolved caller")

        monkeypatch.setattr(endpoints_module, "_resolve_cliente_cero_tenant_id", must_not_be_called)

        user = {"id": "76680e1f-2943-4235-8501-18b090d59257", "email": "growth@contexia.online", "resolved_user_id": None, "resolved_tenant_id": None}
        snapshot = run(get_financials(user=user))

        assert snapshot["status"] == "empty"
        assert snapshot["caja_real"] == 0
