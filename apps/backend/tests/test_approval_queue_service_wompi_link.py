"""Tests for the wompi_payment_link approval branch (taty-wompi-link-hitl-gate).

Real bug found live: route_lead_message used to generate and send a real, production Wompi
checkout link with zero human review, against a merchant account confirmed to be Contexia's own
(Entidad B, tech) rather than the regulated accounting firm's — the highest-severity risk the
earlier legal review flagged. Approval is now the only path that generates/delivers the real
link; these tests cover that path directly (the enqueue side is covered in
test_taty_lead_router.py::TestEnqueueWompiLinkApproval).
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.approval_decisions import ApprovalStatus, VectorizationStatus
from services.approval_queue_service import ApprovalQueueService


def _existing_row(draft_type="wompi_payment_link", payload=None):
    return {
        "id": "decision-1",
        "draft_id": "lead-1",
        "draft_type": draft_type,
        "status": ApprovalStatus.PENDING_APPROVAL.value,
        "reason": "",
        "approved_by": "",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "vectorization_status": VectorizationStatus.PENDING.value,
        "payload": payload if payload is not None else {"lead_id": "lead-1"},
        "tenant_id": "tenant-abc",
    }


class _Chainable:
    """`.eq()` returns itself (however many times chained), so a query that conditionally
    chains `.eq()` a second time for tenant scoping still converges on the same configured
    `.execute()` result — matching approve_draft's real query-building shape."""

    def __init__(self, execute_result):
        self._execute_result = execute_result

    def eq(self, *_a, **_k):
        return self

    def select(self, *_a, **_k):
        return self

    def update(self, *_a, **_k):
        return self

    def execute(self):
        return self._execute_result


def _table_for(name, draft_type="wompi_payment_link"):
    if name != "approval_queue":
        return MagicMock()

    select_result = MagicMock()
    select_result.data = [_existing_row(draft_type=draft_type)]

    approved_row = _existing_row(draft_type=draft_type)
    approved_row["status"] = ApprovalStatus.APPROVED.value
    update_result = MagicMock()
    update_result.data = [approved_row]

    table_mock = MagicMock()
    table_mock.select.side_effect = lambda *a, **k: _Chainable(select_result)
    table_mock.update.side_effect = lambda *a, **k: _Chainable(update_result)
    return table_mock


@pytest.fixture
def fake_supabase():
    client = MagicMock()
    client.table.side_effect = lambda name: _table_for(name)
    with patch(
        "services.approval_queue_service.get_service_supabase", return_value=client
    ):
        yield client


class TestApprovingWompiPaymentLinkSendsTheRealLink:
    @pytest.mark.asyncio
    async def test_approval_generates_and_sends_the_link(self, fake_supabase) -> None:
        with patch(
            "services.approval_queue_service.get_lead_phone", return_value="573001234567"
        ), patch(
            "services.approval_queue_service.generate_wompi_link",
            return_value="https://checkout.wompi.co/p/?reference=abc",
        ) as mock_link, patch(
            "services.approval_queue_service.send_whatsapp_message",
            new=AsyncMock(return_value=True),
        ) as mock_send, patch.object(
            ApprovalQueueService, "_vectorize_and_persist", new=AsyncMock()
        ):
            success, decision, error = await ApprovalQueueService.approve_draft(
                "decision-1", "se ve bien", "asesor@contexia.online", tenant_id="tenant-abc"
            )

        assert success is True
        assert error is None
        mock_link.assert_called_once_with("lead-1")
        mock_send.assert_awaited_once()
        args, _ = mock_send.call_args
        assert args[0] == "573001234567"
        assert "checkout.wompi.co" in args[1]

    @pytest.mark.asyncio
    async def test_missing_phone_skips_send_without_failing_the_approval(
        self, fake_supabase
    ) -> None:
        with patch(
            "services.approval_queue_service.get_lead_phone", return_value=None
        ), patch(
            "services.approval_queue_service.generate_wompi_link",
            return_value="https://checkout.wompi.co/p/?reference=abc",
        ), patch(
            "services.approval_queue_service.send_whatsapp_message",
            new=AsyncMock(return_value=True),
        ) as mock_send, patch.object(
            ApprovalQueueService, "_vectorize_and_persist", new=AsyncMock()
        ):
            success, decision, error = await ApprovalQueueService.approve_draft(
                "decision-1", "ok", "asesor@contexia.online", tenant_id="tenant-abc"
            )

        assert success is True
        mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_delivery_failure_does_not_undo_the_approval(self, fake_supabase) -> None:
        with patch(
            "services.approval_queue_service.get_lead_phone", return_value="573001234567"
        ), patch(
            "services.approval_queue_service.generate_wompi_link",
            return_value="https://checkout.wompi.co/p/?reference=abc",
        ), patch(
            "services.approval_queue_service.send_whatsapp_message",
            new=AsyncMock(side_effect=Exception("Meta API down")),
        ), patch.object(
            ApprovalQueueService, "_vectorize_and_persist", new=AsyncMock()
        ):
            success, decision, error = await ApprovalQueueService.approve_draft(
                "decision-1", "ok", "asesor@contexia.online", tenant_id="tenant-abc"
            )

        assert success is True
        assert error is None
        assert decision.status == ApprovalStatus.APPROVED

    @pytest.mark.asyncio
    async def test_other_draft_types_are_unaffected(self, fake_supabase) -> None:
        """tax_correction's existing outbox-job branch must keep working unmodified."""
        fake_supabase.table.side_effect = lambda name: _table_for(name, "tax_correction")

        with patch(
            "services.approval_queue_service.send_whatsapp_message"
        ) as mock_send, patch.object(
            ApprovalQueueService, "_create_outbox_job_sync"
        ) as mock_outbox, patch.object(
            ApprovalQueueService, "_vectorize_and_persist", new=AsyncMock()
        ):
            await ApprovalQueueService.approve_draft(
                "decision-1", "ok", "asesor@contexia.online", tenant_id="tenant-abc"
            )

        mock_send.assert_not_called()
        mock_outbox.assert_called_once()
