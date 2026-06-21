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
