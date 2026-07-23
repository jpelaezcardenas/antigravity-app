"""
Integration tests for Approval Queue with Agent Critic validation.
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend"))

from services.approval_queue_service import ApprovalQueueService

# Real Cliente Cero tenant UUID — matches the pre-tenant-scoping default behavior
# these tests originally exercised (enqueue_draft used to resolve Cliente Cero
# internally; approval-queue-tenant-scoping, Section 5). No FK constraint on
# approval_queue.tenant_id (migration 0001), so this is a plain UUID, not a
# live-DB dependency.
_TEST_TENANT_ID = "e2d30d09-6b96-4ebe-a79a-c6aff7a5df34"


@pytest.mark.asyncio
async def test_balanced_draft_enqueued():
    """Balanced draft passes Critic and is enqueued."""
    success, decision, error = await ApprovalQueueService.enqueue_draft(
        draft_id="draft-001",
        draft_type="tax_correction",
        journal_entry={
            "lines": [
                {"account": "1105", "debit": 1000000, "credit": 0},
                {"account": "2105", "debit": 0, "credit": 1000000},
            ],
            "memo": "DIAN correction",
        },
        tenant_id=_TEST_TENANT_ID,
    )

    assert success is True
    assert decision is not None
    assert decision.status.value == "pending_approval"
    assert error is None


@pytest.mark.asyncio
async def test_unbalanced_draft_rejected():
    """Unbalanced draft fails Critic validation and is rejected from queue."""
    success, decision, error = await ApprovalQueueService.enqueue_draft(
        draft_id="draft-002",
        draft_type="tax_correction",
        journal_entry={
            "lines": [
                {"account": "1105", "debit": 1000000, "credit": 0},
                {"account": "2105", "debit": 0, "credit": 900000},  # 100k short
            ],
            "memo": "Wrong amount",
        },
        tenant_id=_TEST_TENANT_ID,
    )

    assert success is False
    assert decision is None
    assert "Unbalanced" in error


@pytest.mark.asyncio
async def test_draft_approved_after_enqueue():
    """Draft is approved after being enqueued."""
    # First enqueue
    enqueue_success, decision, enqueue_error = await ApprovalQueueService.enqueue_draft(
        draft_id="draft-003",
        draft_type="tax_correction",
        journal_entry={
            "lines": [
                {"account": "1105", "debit": 500000, "credit": 0},
                {"account": "2105", "debit": 0, "credit": 500000},
            ],
        },
        tenant_id=_TEST_TENANT_ID,
    )

    assert enqueue_success is True
    assert decision.status.value == "pending_approval"

    # Then approve
    approve_success, approved_decision, approve_error = (
        await ApprovalQueueService.approve_draft(
            decision_id=decision.id,
            approval_reason="Contexia's own invoice, matches DIAN",
            approved_by="contador@contexia.com",
            tenant_id=_TEST_TENANT_ID,
        )
    )

    assert approve_success is True
    assert approved_decision.status.value == "approved"
    assert approved_decision.reason == "Contexia's own invoice, matches DIAN"
    assert approve_error is None
