"""
Unit tests for the telemetry-loop read functions (sell-machine-telemetry-loop, Change G):
operator_task_service.list_completed_tasks and crm_service's funnel snapshot helper.

Supabase mocked directly, no credentials needed.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from services.crm_service import get_funnel_snapshot
from services.operator_task_service import list_completed_tasks


class TestListCompletedTasks:
    def test_returns_only_completed_rows(self):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = [
            {"id": "task-1", "task_type": "post_content", "status": "completed", "result": {"impressions": 100}}
        ]
        with patch("services.operator_task_service.get_service_supabase", return_value=mock_client):
            result = list_completed_tasks()

        assert len(result) == 1
        assert result[0]["status"] == "completed"

    def test_filters_by_task_type_when_provided(self):
        mock_client = MagicMock()
        chain = mock_client.table.return_value.select.return_value.eq.return_value
        chain.eq.return_value.order.return_value.execute.return_value.data = [
            {"id": "task-2", "task_type": "research", "status": "completed"}
        ]
        with patch("services.operator_task_service.get_service_supabase", return_value=mock_client):
            result = list_completed_tasks(task_type="research")

        assert len(result) == 1
        chain.eq.assert_called_once_with("task_type", "research")


class TestGetFunnelSnapshot:
    def test_returns_counts_per_stage(self):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.execute.return_value.data = [
            {"stage": "NUEVOS"},
            {"stage": "NUEVOS"},
            {"stage": "PROSPECTOS"},
        ]
        with patch("services.crm_service.get_service_supabase", return_value=mock_client):
            snapshot = get_funnel_snapshot()

        assert snapshot["NUEVOS"] == 2
        assert snapshot["PROSPECTOS"] == 1
        assert snapshot["POR_APROBAR"] == 0
        assert snapshot["LISTOS_CONTADORA"] == 0

    def test_empty_leads_table_returns_all_zeros(self):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.execute.return_value.data = []
        with patch("services.crm_service.get_service_supabase", return_value=mock_client):
            snapshot = get_funnel_snapshot()

        assert snapshot == {"NUEVOS": 0, "PROSPECTOS": 0, "POR_APROBAR": 0, "LISTOS_CONTADORA": 0}
