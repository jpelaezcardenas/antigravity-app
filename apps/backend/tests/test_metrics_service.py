"""Unit tests for metrics_service — all Supabase calls are patched."""
from unittest.mock import MagicMock, patch

import pytest

from services.metrics_service import (
    get_auto_approval_metrics,
    get_csv_ingestion_metrics,
    get_queue_health,
    get_top_vendors,
)

TENANT = "00000000-0000-0000-0000-000000000001"


def _mock_sb(rows):
    """Return a mock supabase client whose .execute() yields rows."""
    result = MagicMock()
    result.data = rows
    chain = MagicMock()
    chain.execute.return_value = result
    chain.select.return_value = chain
    chain.eq.return_value = chain
    chain.order.return_value = chain
    chain.limit.return_value = chain
    sb = MagicMock()
    sb.table.return_value = chain
    return sb


@patch("services.metrics_service.get_service_supabase")
def test_auto_approval_empty(mock_sb):
    mock_sb.return_value = _mock_sb([])
    result = get_auto_approval_metrics(TENANT, days=7)
    assert result["total_auto_approved"] == 0
    assert result["false_positives"] == 0
    assert result["daily"] == []


@patch("services.metrics_service.get_service_supabase")
def test_auto_approval_aggregates(mock_sb):
    rows = [
        {
            "snapshot_date": "2026-08-31",
            "auto_approved_total": 10,
            "auto_approved_recurring": 6,
            "auto_approved_vendor": 3,
            "auto_approved_micro": 1,
            "false_positive_count": 2,
        },
        {
            "snapshot_date": "2026-08-30",
            "auto_approved_total": 5,
            "auto_approved_recurring": 3,
            "auto_approved_vendor": 2,
            "auto_approved_micro": 0,
            "false_positive_count": 0,
        },
    ]
    mock_sb.return_value = _mock_sb(rows)
    result = get_auto_approval_metrics(TENANT, days=7)
    assert result["total_auto_approved"] == 15
    assert result["by_rule"]["recurring"] == 9
    assert result["by_rule"]["vendor"] == 5
    assert result["by_rule"]["micro"] == 1
    assert result["false_positives"] == 2
    assert len(result["daily"]) == 2


@patch("services.metrics_service.get_service_supabase")
def test_csv_ingestion_empty(mock_sb):
    mock_sb.return_value = _mock_sb([])
    result = get_csv_ingestion_metrics(TENANT, days=7)
    assert result["batches"] == 0
    assert result["rows_processed"] == 0
    assert result["rows_error"] == 0


@patch("services.metrics_service.get_service_supabase")
def test_queue_health_no_snapshot(mock_sb):
    mock_sb.return_value = _mock_sb([])
    result = get_queue_health(TENANT)
    assert result["pending"] == 0
    assert result["avg_review_seconds"] is None


@patch("services.metrics_service.get_service_supabase")
def test_queue_health_with_data(mock_sb):
    mock_sb.return_value = _mock_sb(
        [{"queue_pending_count": 7, "queue_avg_review_seconds": 245.5}]
    )
    result = get_queue_health(TENANT)
    assert result["pending"] == 7
    assert result["avg_review_seconds"] == 245.5


@patch("services.metrics_service.get_service_supabase")
def test_top_vendors_empty(mock_sb):
    mock_sb.return_value = _mock_sb([{"top_vendors": []}])
    result = get_top_vendors(TENANT, limit=10)
    assert result == []


@patch("services.metrics_service.get_service_supabase")
def test_top_vendors_returns_limit(mock_sb):
    vendors = [{"vendor": f"V{i}", "count": 10 - i} for i in range(15)]
    mock_sb.return_value = _mock_sb([{"top_vendors": vendors}])
    result = get_top_vendors(TENANT, limit=5)
    assert len(result) == 5
    assert result[0]["vendor"] == "V0"
