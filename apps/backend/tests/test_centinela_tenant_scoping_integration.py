"""
Integration tests for Centinela tenant-scoped alert writes/reads against a
real Supabase project (centinela-tenant-scoped-alerts, Stage 7).

Hermetic two-tenant fixture pattern, mirroring
test_financials_endpoint_tenant_scoping.py: disposable `tenants` rows,
teardown deletes `centinela_alerts` then `tenants`.

Gated by RUN_CENTINELA_TENANT=1 + SUPABASE_SERVICE_ROLE_KEY (this repo's
established RUN_*-env-var convention for tests that hit live Supabase) since
save_alerts writes via the service-role client. Skips locally by default —
this environment's .env has no SUPABASE_SERVICE_ROLE_KEY (documented in the
Stage 10 DB-verification report).
"""

from __future__ import annotations

import os
import uuid

import pytest

from core.supabase_client import get_supabase
from services.centinela_service import CentinelaService

pytestmark = pytest.mark.skipif(
    not (os.environ.get("RUN_CENTINELA_TENANT") == "1" and os.environ.get("SUPABASE_SERVICE_ROLE_KEY")),
    reason="Set RUN_CENTINELA_TENANT=1 and SUPABASE_SERVICE_ROLE_KEY to run against live Supabase",
)


@pytest.fixture
def two_test_tenants():
    """Two hermetic, throwaway tenants sharing the same company_id."""
    supabase = get_supabase()
    tenant_ids = []
    for label in ("A", "B"):
        nit = f"TEST-CENTINELA-{label}-{uuid.uuid4().hex[:10]}"
        inserted = (
            supabase.table("tenants")
            .insert({"nit": nit, "legal_name": f"Hermetic Centinela Tenant {label} (pytest)", "is_cliente_cero": False})
            .execute()
        )
        tenant_ids.append(inserted.data[0]["id"])

    yield tenant_ids

    for tenant_id in tenant_ids:
        supabase.table("centinela_alerts").delete().eq("tenant_id", tenant_id).execute()
        supabase.table("tenants").delete().eq("id", tenant_id).execute()


class TestCentinelaTenantScopingIntegration:
    def test_two_tenants_alerts_do_not_leak(self, two_test_tenants):
        tenant_a, tenant_b = two_test_tenants
        service = CentinelaService()
        shared_company_id = f"ctx-shared-{uuid.uuid4().hex[:8]}"

        saved_ids = service.save_alerts(
            [{"rule_id": "R001", "company_id": shared_company_id, "severity": "warning", "title": "t", "description": "d", "evidence": {}}],
            tenant_id=tenant_a,
        )
        assert len(saved_ids) == 1

        alerts_for_a = service.get_alerts_for_company(shared_company_id, tenant_id=tenant_a)
        alerts_for_b = service.get_alerts_for_company(shared_company_id, tenant_id=tenant_b)

        assert len(alerts_for_a) == 1
        assert len(alerts_for_b) == 0

    def test_saved_alert_row_has_correct_tenant_id(self, two_test_tenants):
        tenant_a, _ = two_test_tenants
        service = CentinelaService()
        company_id = f"ctx-{uuid.uuid4().hex[:8]}"

        saved_ids = service.save_alerts(
            [{"rule_id": "R001", "company_id": company_id, "severity": "warning", "title": "t", "description": "d", "evidence": {}}],
            tenant_id=tenant_a,
        )

        row = (
            get_supabase()
            .table("centinela_alerts")
            .select("tenant_id")
            .eq("id", saved_ids[0])
            .single()
            .execute()
        )
        assert row.data["tenant_id"] == tenant_a
