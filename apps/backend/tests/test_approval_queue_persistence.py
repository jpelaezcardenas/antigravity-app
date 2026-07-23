"""
Integration tests for real Approval Queue persistence (FASE 4, Slice 2).

Prior to this change, ApprovalQueueService.enqueue_draft/approve_draft/
reject_draft were in-memory stubs with no database table. Gated by
RUN_APPROVAL_QUEUE_DB=1 since they hit the real Supabase project, mirroring
the RUN_SHADOW_GL/RUN_KB_PGVECTOR convention.
"""

from __future__ import annotations

import os
import uuid
import pytest

from core.supabase_client import get_supabase
from services.approval_queue_service import ApprovalQueueService

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_APPROVAL_QUEUE_DB") != "1",
    reason="Set RUN_APPROVAL_QUEUE_DB=1 to run Approval Queue persistence tests against Supabase",
)


@pytest.fixture(scope="module")
def supabase():
    return get_supabase()


@pytest.fixture(autouse=True)
def _cleanup(supabase):
    created_ids: list[str] = []
    yield created_ids
    for decision_id in created_ids:
        supabase.table("approval_queue").delete().eq("id", decision_id).execute()


def _balanced_journal_entry() -> dict:
    return {
        "lines": [
            {"account": "1105", "debit": 100000, "credit": 0},
            {"account": "4135", "debit": 0, "credit": 100000},
        ],
        "memo": "test balanced entry",
    }


def _unbalanced_journal_entry() -> dict:
    return {
        "lines": [
            {"account": "1105", "debit": 100000, "credit": 0},
            {"account": "4135", "debit": 0, "credit": 90000},
        ],
        "memo": "test unbalanced entry",
    }


class TestEnqueuePersistence:
    @pytest.mark.asyncio
    async def test_balanced_draft_persists_to_table(self, supabase, _cleanup) -> None:
        draft_id = str(uuid.uuid4())
        success, decision, error = await ApprovalQueueService.enqueue_draft(
            draft_id=draft_id,
            draft_type="tax_correction",
            journal_entry=_balanced_journal_entry(),
        )
        assert success is True
        assert error is None
        _cleanup.append(decision.id)

        row = (
            supabase.table("approval_queue")
            .select("*")
            .eq("id", decision.id)
            .single()
            .execute()
        )
        assert row.data["draft_id"] == draft_id
        assert row.data["draft_type"] == "tax_correction"
        assert row.data["status"] == "pending_approval"
        assert row.data["payload"]["memo"] == "test balanced entry"

    @pytest.mark.asyncio
    async def test_unbalanced_draft_is_not_persisted(self, supabase, _cleanup) -> None:
        draft_id = str(uuid.uuid4())
        success, decision, error = await ApprovalQueueService.enqueue_draft(
            draft_id=draft_id,
            draft_type="tax_correction",
            journal_entry=_unbalanced_journal_entry(),
        )
        assert success is False
        assert decision is None
        assert error is not None

        row = supabase.table("approval_queue").select("id").eq("draft_id", draft_id).execute()
        assert row.data == []

    @pytest.mark.asyncio
    async def test_non_journal_draft_type_skips_balance_validation(self, supabase, _cleanup) -> None:
        draft_id = str(uuid.uuid4())
        success, decision, error = await ApprovalQueueService.enqueue_draft(
            draft_id=draft_id,
            draft_type="risk_review",
            journal_entry={"risk_score": 92, "forecast_30d_minor": -500000},
        )
        assert success is True
        assert error is None
        _cleanup.append(decision.id)
        assert decision.draft_type == "risk_review"


class TestListDrafts:
    @pytest.mark.asyncio
    async def test_list_returns_pending_drafts_across_draft_types(self, supabase, _cleanup) -> None:
        _, tax_decision, _ = await ApprovalQueueService.enqueue_draft(
            draft_id=str(uuid.uuid4()),
            draft_type="tax_correction",
            journal_entry=_balanced_journal_entry(),
        )
        _, risk_decision, _ = await ApprovalQueueService.enqueue_draft(
            draft_id=str(uuid.uuid4()),
            draft_type="risk_review",
            journal_entry={"risk_score": 91},
        )
        _cleanup.append(tax_decision.id)
        _cleanup.append(risk_decision.id)

        rows = await ApprovalQueueService.list_drafts(status="pending_approval")
        ids = {row.id for row in rows}
        assert tax_decision.id in ids
        assert risk_decision.id in ids

    @pytest.mark.asyncio
    async def test_list_filters_by_draft_type(self, supabase, _cleanup) -> None:
        _, tax_decision, _ = await ApprovalQueueService.enqueue_draft(
            draft_id=str(uuid.uuid4()),
            draft_type="tax_correction",
            journal_entry=_balanced_journal_entry(),
        )
        _, risk_decision, _ = await ApprovalQueueService.enqueue_draft(
            draft_id=str(uuid.uuid4()),
            draft_type="risk_review",
            journal_entry={"risk_score": 91},
        )
        _cleanup.append(tax_decision.id)
        _cleanup.append(risk_decision.id)

        rows = await ApprovalQueueService.list_drafts(draft_type="risk_review")
        ids = {row.id for row in rows}
        assert risk_decision.id in ids
        assert tax_decision.id not in ids

    @pytest.mark.asyncio
    async def test_list_excludes_resolved_drafts_when_status_filtered(self, supabase, _cleanup) -> None:
        _, decision, _ = await ApprovalQueueService.enqueue_draft(
            draft_id=str(uuid.uuid4()),
            draft_type="tax_correction",
            journal_entry=_balanced_journal_entry(),
        )
        _cleanup.append(decision.id)
        await ApprovalQueueService.approve_draft(
            decision_id=decision.id,
            approval_reason="ok",
            approved_by="contador@contexia.com",
        )

        rows = await ApprovalQueueService.list_drafts(status="pending_approval")
        ids = {row.id for row in rows}
        assert decision.id not in ids


class TestApproveRejectPersistence:
    @pytest.mark.asyncio
    async def test_approve_updates_row_and_returns_immediately(self, supabase, _cleanup) -> None:
        draft_id = str(uuid.uuid4())
        _, decision, _ = await ApprovalQueueService.enqueue_draft(
            draft_id=draft_id,
            draft_type="tax_correction",
            journal_entry=_balanced_journal_entry(),
        )
        _cleanup.append(decision.id)

        success, approved, error = await ApprovalQueueService.approve_draft(
            decision_id=decision.id,
            approval_reason="Matches DIAN invoice, contador confirmed",
            approved_by="contador@contexia.com",
        )
        assert success is True
        assert error is None
        assert approved.status.value == "approved"

        row = (
            supabase.table("approval_queue")
            .select("status, approved_by, reason")
            .eq("id", decision.id)
            .single()
            .execute()
        )
        assert row.data["status"] == "approved"
        assert row.data["approved_by"] == "contador@contexia.com"

    @pytest.mark.asyncio
    async def test_reject_updates_row(self, supabase, _cleanup) -> None:
        draft_id = str(uuid.uuid4())
        _, decision, _ = await ApprovalQueueService.enqueue_draft(
            draft_id=draft_id,
            draft_type="tax_correction",
            journal_entry=_balanced_journal_entry(),
        )
        _cleanup.append(decision.id)

        success, rejected, error = await ApprovalQueueService.reject_draft(
            decision_id=decision.id,
            rejection_reason="Needs more documentation",
            rejected_by="contador@contexia.com",
        )
        assert success is True
        assert rejected.status.value == "rejected"

        row = (
            supabase.table("approval_queue")
            .select("status, reason")
            .eq("id", decision.id)
            .single()
            .execute()
        )
        assert row.data["status"] == "rejected"
        assert row.data["reason"] == "Needs more documentation"

    @pytest.mark.asyncio
    async def test_approve_unknown_decision_id_fails(self, supabase, _cleanup) -> None:
        success, decision, error = await ApprovalQueueService.approve_draft(
            decision_id=str(uuid.uuid4()),
            approval_reason="x",
            approved_by="contador@contexia.com",
        )
        assert success is False
        assert decision is None
        assert error is not None


@pytest.fixture
def two_test_tenants(supabase):
    """Two hermetic, throwaway tenants (approval-queue-tenant-scoping, Task 4.5).

    Mirrors the pattern in test_financials_endpoint_tenant_scoping.py's
    `two_test_tenants` fixture.
    """
    tenant_ids = []
    for label in ("A", "B"):
        nit = f"TEST-AQ-SCOPE-{label}-{uuid.uuid4().hex[:10]}"
        inserted = (
            supabase.table("tenants")
            .insert({"nit": nit, "legal_name": f"Hermetic AQ Tenant {label} (pytest)", "is_cliente_cero": False})
            .execute()
        )
        tenant_ids.append(inserted.data[0]["id"])

    yield tenant_ids

    for tenant_id in tenant_ids:
        supabase.table("tenants").delete().eq("id", tenant_id).execute()


class TestTenantScopedRoundTrip:
    """Task 4.5: a real Supabase round trip proving tenant isolation end to end —
    enqueue under tenant A is invisible to (and unreachable by) a caller scoped
    to tenant B, and reachable by a caller scoped to tenant A itself."""

    @pytest.mark.asyncio
    async def test_two_tenant_round_trip_is_isolated(
        self, supabase, _cleanup, two_test_tenants
    ) -> None:
        tenant_a, tenant_b = two_test_tenants
        draft_id = str(uuid.uuid4())

        success, decision, error = await ApprovalQueueService.enqueue_draft(
            draft_id=draft_id,
            draft_type="risk_review",
            journal_entry={"risk_score": 77},
            tenant_id=tenant_a,
        )
        assert success is True
        assert error is None
        _cleanup.append(decision.id)

        # Tenant-B-scoped list excludes tenant A's draft.
        tenant_b_rows = await ApprovalQueueService.list_drafts(tenant_id=tenant_b)
        assert decision.id not in {row.id for row in tenant_b_rows}

        # Tenant-B-scoped approve returns "not found" — never reveals the row
        # exists under a different tenant.
        b_success, b_decision, b_error = await ApprovalQueueService.approve_draft(
            decision_id=decision.id,
            approval_reason="cross-tenant attempt",
            approved_by="b@other-tenant.co",
            tenant_id=tenant_b,
        )
        assert b_success is False
        assert b_decision is None
        assert b_error == f"Decision {decision.id} not found"

        # Tenant-A-scoped approve succeeds.
        a_success, a_decision, a_error = await ApprovalQueueService.approve_draft(
            decision_id=decision.id,
            approval_reason="own-tenant approval",
            approved_by="a@own-tenant.co",
            tenant_id=tenant_a,
        )
        assert a_success is True
        assert a_error is None
        assert a_decision.status.value == "approved"
