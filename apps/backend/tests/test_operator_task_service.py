"""
Unit tests for operator_task_service.py (hermes-manus-execution-bridge, Change F).

All Supabase access is mocked at the module's `get_service_supabase` call point (no credentials
needed), matching the pattern used by test_crm_service_grid_logic.py / test_sell_machine_service.py.
Approval Queue reads are mocked via `ApprovalQueueService.list_drafts` directly, never modifying
approval_queue_service.py itself.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.operator_task_service import (
    SIDE_EFFECTING_TASK_TYPES,
    create_task,
    dispatch_campaign_package,
    list_pending_tasks,
    mark_dispatched,
    report_result,
)


def _fake_decision(id_="decision-1", draft_type="campaign_package", status="approved", payload=None):
    decision = MagicMock()
    decision.id = id_
    decision.draft_type = draft_type
    decision.status = status
    decision.payload = payload or {
        "hooks": [{"headline": "H1", "body": "B1", "cta": "C", "pain_tag": "multa_dian"}],
        "creative_brief": "brief",
        "target_segment": "asalariados",
        "budget_cents": None,
    }
    return decision


class TestCreateTask:
    def test_rejects_side_effecting_task_types_directly(self):
        for task_type in SIDE_EFFECTING_TASK_TYPES:
            success, row, error = create_task(task_type=task_type, payload={})
            assert success is False
            assert row is None
            assert error is not None

    def test_accepts_read_only_task_types(self):
        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "task-1", "task_type": "research", "status": "pending", "payload": {}}
        ]
        with patch(
            "services.operator_task_service.get_service_supabase", return_value=mock_client
        ), patch("services.operator_task_service._resolve_cliente_cero_tenant_id", return_value="tenant-1"):
            success, row, error = create_task(task_type="research", payload={"q": "SimilarWeb data"})

        assert success is True
        assert error is None
        assert row["task_type"] == "research"


class TestListPendingTasks:
    def test_returns_pending_rows(self):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = [
            {"id": "task-1", "task_type": "research", "status": "pending"}
        ]
        with patch("services.operator_task_service.get_service_supabase", return_value=mock_client):
            result = list_pending_tasks()

        assert len(result) == 1
        assert result[0]["status"] == "pending"


class TestMarkDispatched:
    def test_pending_to_dispatched_succeeds(self):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "id": "task-1",
            "status": "pending",
        }
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
            {"id": "task-1", "status": "dispatched"}
        ]
        with patch("services.operator_task_service.get_service_supabase", return_value=mock_client):
            success, row, error = mark_dispatched("task-1")

        assert success is True
        assert row["status"] == "dispatched"

    def test_already_dispatched_is_rejected(self):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "id": "task-1",
            "status": "dispatched",
        }
        with patch("services.operator_task_service.get_service_supabase", return_value=mock_client):
            success, row, error = mark_dispatched("task-1")

        assert success is False
        assert row is None
        assert error is not None


class TestReportResult:
    def test_dispatched_to_completed_succeeds(self):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "id": "task-1",
            "status": "dispatched",
        }
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
            {"id": "task-1", "status": "completed", "result": {"post_url": "https://..."}}
        ]
        with patch("services.operator_task_service.get_service_supabase", return_value=mock_client):
            success, row, error = report_result(
                "task-1", status="completed", result={"post_url": "https://..."}
            )

        assert success is True
        assert row["status"] == "completed"

    def test_pending_task_cannot_receive_a_result(self):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "id": "task-1",
            "status": "pending",
        }
        with patch("services.operator_task_service.get_service_supabase", return_value=mock_client):
            success, row, error = report_result("task-1", status="completed", result={})

        assert success is False
        assert row is None
        assert error is not None


class TestDispatchCampaignPackage:
    @pytest.mark.asyncio
    async def test_dispatches_an_approved_campaign_package(self):
        decision = _fake_decision(status="approved")
        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "task-1", "task_type": "post_content", "status": "pending"}
        ]
        with patch(
            "services.operator_task_service.ApprovalQueueService.list_drafts",
            new=AsyncMock(return_value=[decision]),
        ), patch(
            "services.operator_task_service.get_service_supabase", return_value=mock_client
        ), patch(
            "services.operator_task_service._resolve_cliente_cero_tenant_id", return_value="tenant-1"
        ):
            success, row, error = await dispatch_campaign_package("decision-1")

        assert success is True
        assert row["task_type"] == "post_content"
        insert_call_args = mock_client.table.return_value.insert.call_args[0][0]
        assert insert_call_args["payload"]["source_decision_id"] == "decision-1"

    @pytest.mark.asyncio
    async def test_dispatches_run_ads_ab_when_budget_cents_is_set(self):
        decision = _fake_decision(
            status="approved",
            payload={
                "hooks": [{"headline": "H1", "body": "B1", "cta": "C", "pain_tag": "multa_dian"}],
                "creative_brief": "brief",
                "target_segment": "asalariados",
                "budget_cents": 500000,
            },
        )
        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "task-1", "task_type": "run_ads_ab", "status": "pending"}
        ]
        with patch(
            "services.operator_task_service.ApprovalQueueService.list_drafts",
            new=AsyncMock(return_value=[decision]),
        ), patch(
            "services.operator_task_service.get_service_supabase", return_value=mock_client
        ), patch(
            "services.operator_task_service._resolve_cliente_cero_tenant_id", return_value="tenant-1"
        ):
            success, row, error = await dispatch_campaign_package("decision-1")

        assert success is True
        assert row["task_type"] == "run_ads_ab"
        insert_call_args = mock_client.table.return_value.insert.call_args[0][0]
        assert insert_call_args["task_type"] == "run_ads_ab"

    @pytest.mark.asyncio
    async def test_dispatches_post_content_when_budget_cents_is_zero(self):
        decision = _fake_decision(
            status="approved",
            payload={
                "hooks": [{"headline": "H1", "body": "B1", "cta": "C", "pain_tag": "multa_dian"}],
                "creative_brief": "brief",
                "target_segment": "asalariados",
                "budget_cents": 0,
            },
        )
        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "task-1", "task_type": "post_content", "status": "pending"}
        ]
        with patch(
            "services.operator_task_service.ApprovalQueueService.list_drafts",
            new=AsyncMock(return_value=[decision]),
        ), patch(
            "services.operator_task_service.get_service_supabase", return_value=mock_client
        ), patch(
            "services.operator_task_service._resolve_cliente_cero_tenant_id", return_value="tenant-1"
        ):
            success, row, error = await dispatch_campaign_package("decision-1")

        assert success is True
        insert_call_args = mock_client.table.return_value.insert.call_args[0][0]
        assert insert_call_args["task_type"] == "post_content"

    @pytest.mark.asyncio
    async def test_rejects_a_decision_that_is_not_approved(self):
        decision = _fake_decision(status="pending_approval")
        with patch(
            "services.operator_task_service.ApprovalQueueService.list_drafts",
            new=AsyncMock(return_value=[decision]),
        ):
            success, row, error = await dispatch_campaign_package("decision-1")

        assert success is False
        assert row is None
        assert error is not None

    @pytest.mark.asyncio
    async def test_rejects_a_decision_that_is_not_a_campaign_package(self):
        decision = _fake_decision(draft_type="tax_correction", status="approved")
        with patch(
            "services.operator_task_service.ApprovalQueueService.list_drafts",
            new=AsyncMock(return_value=[decision]),
        ):
            success, row, error = await dispatch_campaign_package("decision-1")

        assert success is False
        assert row is None
        assert error is not None

    @pytest.mark.asyncio
    async def test_rejects_an_unknown_decision_id(self):
        with patch(
            "services.operator_task_service.ApprovalQueueService.list_drafts",
            new=AsyncMock(return_value=[]),
        ):
            success, row, error = await dispatch_campaign_package("does-not-exist")

        assert success is False
        assert row is None
        assert error is not None
