"""
Integration tests for approval → executor_outbox workflow (FASE 4, Slice 2, task 2.13).

When a tax_correction draft is approved, an executor_outbox row is created
immediately (non-blocking, fire-and-forget). Gated by RUN_APPROVAL_QUEUE_DB=1.
"""

from __future__ import annotations

import os
import uuid

import pytest

from core.supabase_client import get_supabase
from services.approval_queue_service import ApprovalQueueService

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_APPROVAL_QUEUE_DB") != "1",
    reason="Set RUN_APPROVAL_QUEUE_DB=1 to run approval→outbox integration tests",
)


@pytest.fixture(scope="module")
def supabase():
    return get_supabase()


@pytest.fixture(autouse=True)
def _cleanup(supabase):
    created_ids: dict = {"decisions": [], "outbox": []}
    yield created_ids
    for decision_id in created_ids["decisions"]:
        supabase.table("approval_queue").delete().eq("id", decision_id).execute()
    for outbox_id in created_ids["outbox"]:
        supabase.table("executor_outbox").delete().eq("id", outbox_id).execute()


def _balanced_journal_entry() -> dict:
    return {
        "lines": [
            {"account": "1105", "debit": 100000, "credit": 0},
            {"account": "4135", "debit": 0, "credit": 100000},
        ],
        "memo": "test balanced entry for outbox",
    }


class TestApprovalToOutbox:
    @pytest.mark.asyncio
    async def test_approving_tax_correction_creates_executor_outbox_row(
        self, supabase, _cleanup
    ) -> None:
        """
        Enqueue a tax_correction draft, approve it, and verify that an
        executor_outbox row is created with status='pending'.
        """
        # Enqueue draft
        draft_id = str(uuid.uuid4())
        success, decision, error = await ApprovalQueueService.enqueue_draft(
            draft_id=draft_id,
            draft_type="tax_correction",
            journal_entry=_balanced_journal_entry(),
        )
        assert success is True
        _cleanup["decisions"].append(decision.id)

        # Approve draft
        success, approved, error = await ApprovalQueueService.approve_draft(
            decision_id=decision.id,
            approval_reason="test approval for outbox",
            approved_by="test@example.com",
        )
        assert success is True

        # Query executor_outbox for this approval
        outbox_rows = (
            supabase.table("executor_outbox")
            .select("*")
            .eq("approval_decision_id", decision.id)
            .execute()
        )
        assert len(outbox_rows.data) == 1
        outbox_row = outbox_rows.data[0]
        _cleanup["outbox"].append(outbox_row["id"])

        # Verify outbox row structure
        assert outbox_row["approval_decision_id"] == decision.id
        assert outbox_row["status"] == "pending"
        assert outbox_row["attempts"] == 0
        assert outbox_row["payload"] is not None

    @pytest.mark.asyncio
    async def test_approve_returns_immediately_without_blocking(
        self, supabase, _cleanup
    ) -> None:
        """
        Verify that approve_draft() returns immediately, not blocking on
        executor_outbox creation (should be fire-and-forget).
        """
        import time

        draft_id = str(uuid.uuid4())
        success, decision, error = await ApprovalQueueService.enqueue_draft(
            draft_id=draft_id,
            draft_type="tax_correction",
            journal_entry=_balanced_journal_entry(),
        )
        assert success is True
        _cleanup["decisions"].append(decision.id)

        # Time the approve call
        start = time.time()
        success, approved, error = await ApprovalQueueService.approve_draft(
            decision_id=decision.id,
            approval_reason="test approval timing",
            approved_by="test@example.com",
        )
        elapsed = time.time() - start

        assert success is True
        # Approve should be fast (<1s) since outbox creation is non-blocking (not multi-second)
        assert elapsed < 1.0, f"approve_draft took {elapsed}s, expected <1.0s"

        # Verify outbox row exists after approve returns
        outbox_rows = (
            supabase.table("executor_outbox")
            .select("*")
            .eq("approval_decision_id", decision.id)
            .execute()
        )
        assert len(outbox_rows.data) == 1
        _cleanup["outbox"].append(outbox_rows.data[0]["id"])

    @pytest.mark.asyncio
    async def test_non_tax_correction_draft_does_not_create_outbox_row(
        self, supabase, _cleanup
    ) -> None:
        """
        Only tax_correction drafts create outbox rows. Other draft types
        (risk_review, etc.) should skip this behavior.
        """
        draft_id = str(uuid.uuid4())
        success, decision, error = await ApprovalQueueService.enqueue_draft(
            draft_id=draft_id,
            draft_type="risk_review",
            journal_entry={"risk_score": 92},
        )
        assert success is True
        _cleanup["decisions"].append(decision.id)

        # Approve the risk_review draft
        success, approved, error = await ApprovalQueueService.approve_draft(
            decision_id=decision.id,
            approval_reason="risk approved",
            approved_by="test@example.com",
        )
        assert success is True

        # Verify NO outbox row was created
        outbox_rows = (
            supabase.table("executor_outbox")
            .select("*")
            .eq("approval_decision_id", decision.id)
            .execute()
        )
        assert len(outbox_rows.data) == 0
