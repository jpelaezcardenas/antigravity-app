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


def _fake_decision(
    id_="decision-1",
    draft_type="campaign_package",
    status="approved",
    payload=None,
    tenant_id=None,
):
    """`tenant_id` defaults to None explicitly — a bare MagicMock auto-attribute is truthy, so
    every call site that doesn't intend to exercise the real-tenant dispatch path must not leave
    `decision.tenant_id` as an un-set Mock attribute (it would silently short-circuit the Cliente
    Cero fallback path in every existing test)."""
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
    decision.tenant_id = tenant_id
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

    def test_explicit_valid_tenant_id_is_stamped_directly(self):
        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "task-1", "task_type": "research", "status": "pending", "payload": {}}
        ]
        with patch(
            "services.operator_task_service.get_service_supabase", return_value=mock_client
        ), patch(
            "services.operator_task_service.tenant_exists", return_value=True
        ) as mock_tenant_exists, patch(
            "services.operator_task_service._resolve_cliente_cero_tenant_id"
        ) as mock_resolver:
            success, row, error = create_task(
                task_type="research", payload={}, tenant_id="real-tenant-uuid"
            )

        assert success is True
        assert error is None
        mock_tenant_exists.assert_called_once_with(mock_client, "real-tenant-uuid")
        mock_resolver.assert_not_called()
        insert_call_args = mock_client.table.return_value.insert.call_args[0][0]
        assert insert_call_args["tenant_id"] == "real-tenant-uuid"

    def test_unknown_tenant_id_is_rejected_without_insert(self):
        mock_client = MagicMock()
        with patch(
            "services.operator_task_service.get_service_supabase", return_value=mock_client
        ), patch("services.operator_task_service.tenant_exists", return_value=False):
            success, row, error = create_task(
                task_type="research", payload={}, tenant_id="does-not-exist"
            )

        assert success is False
        assert row is None
        assert "does-not-exist" in error
        assert "not found" in error
        mock_client.table.return_value.insert.assert_not_called()

    def test_omitted_tenant_id_falls_back_to_cliente_cero_with_warning(self, caplog):
        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "task-1", "task_type": "research", "status": "pending", "payload": {}}
        ]
        with patch(
            "services.operator_task_service.get_service_supabase", return_value=mock_client
        ), patch(
            "services.operator_task_service._resolve_cliente_cero_tenant_id", return_value="cliente-cero-tenant"
        ):
            with caplog.at_level("WARNING"):
                success, row, error = create_task(task_type="research", payload={})

        assert success is True
        insert_call_args = mock_client.table.return_value.insert.call_args[0][0]
        assert insert_call_args["tenant_id"] == "cliente-cero-tenant"
        assert any(
            "no tenant_id supplied" in record.message for record in caplog.records
        )

    def test_omitted_tenant_id_and_no_cliente_cero_tenant_is_rejected(self):
        mock_client = MagicMock()
        with patch(
            "services.operator_task_service.get_service_supabase", return_value=mock_client
        ), patch(
            "services.operator_task_service._resolve_cliente_cero_tenant_id", return_value=None
        ):
            success, row, error = create_task(task_type="research", payload={})

        assert success is False
        assert row is None
        assert error is not None
        mock_client.table.return_value.insert.assert_not_called()


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

    def test_uses_explicit_column_projection_not_star(self):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = []
        with patch("services.operator_task_service.get_service_supabase", return_value=mock_client):
            list_pending_tasks()

        select_call_args = mock_client.table.return_value.select.call_args[0][0]
        assert select_call_args == "id, tenant_id, task_type, payload, status, created_at"

    def test_applies_tenant_filter_when_provided(self):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value.data = []
        with patch("services.operator_task_service.get_service_supabase", return_value=mock_client):
            list_pending_tasks(tenant_id="tenant-1")

        eq_calls = mock_client.table.return_value.select.return_value.eq.call_args_list
        assert eq_calls[0][0] == ("status", "pending")
        second_eq = mock_client.table.return_value.select.return_value.eq.return_value.eq
        second_eq.assert_called_once_with("tenant_id", "tenant-1")

    def test_no_tenant_filter_applied_when_omitted(self):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = []
        with patch("services.operator_task_service.get_service_supabase", return_value=mock_client):
            list_pending_tasks()

        second_eq = mock_client.table.return_value.select.return_value.eq.return_value.eq
        second_eq.assert_not_called()


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

    @pytest.mark.asyncio
    async def test_real_tenant_id_on_decision_is_stamped_directly(self):
        decision = _fake_decision(status="approved", tenant_id="real-tenant-uuid")
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
            "services.operator_task_service._resolve_cliente_cero_tenant_id"
        ) as mock_resolver:
            success, row, error = await dispatch_campaign_package("decision-1")

        assert success is True
        mock_resolver.assert_not_called()
        insert_call_args = mock_client.table.return_value.insert.call_args[0][0]
        assert insert_call_args["tenant_id"] == "real-tenant-uuid"

    @pytest.mark.asyncio
    async def test_legacy_decision_without_tenant_id_falls_back_with_warning(self, caplog):
        decision = _fake_decision(status="approved", tenant_id=None)
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
            "services.operator_task_service._resolve_cliente_cero_tenant_id", return_value="cliente-cero-tenant"
        ):
            with caplog.at_level("WARNING"):
                success, row, error = await dispatch_campaign_package("decision-1")

        assert success is True
        insert_call_args = mock_client.table.return_value.insert.call_args[0][0]
        assert insert_call_args["tenant_id"] == "cliente-cero-tenant"
        assert any("no tenant_id" in record.message for record in caplog.records)
