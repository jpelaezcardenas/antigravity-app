"""Tests for T15: GET /centinela/alerts/{company_id} (Pulso feed)."""
import pytest
from unittest.mock import patch, MagicMock

from services.centinela_service import CentinelaService, get_centinela_service


class TestGetAlertsForCompany:
    def test_falls_back_to_demo_when_supabase_unavailable(self):
        service = CentinelaService()
        with patch(
            "services.centinela_service.get_supabase",
            side_effect=Exception("supabase not configured"),
        ):
            alerts = service.get_alerts_for_company("ctx-001", limit=20)
        # Demo profile is engineered to trigger multiple rules
        assert len(alerts) > 0
        assert all("rule_id" in a for a in alerts)
        assert all(a.get("company_id") == "ctx-001" for a in alerts)

    def test_severity_filter_demo_fallback(self):
        service = CentinelaService()
        with patch(
            "services.centinela_service.get_supabase",
            side_effect=Exception("offline"),
        ):
            critical = service.get_alerts_for_company("ctx-001", severity="critical")
        assert all(a["severity"] == "critical" for a in critical)

    def test_returns_supabase_data_when_available(self):
        service = CentinelaService()
        mock_data = [
            {
                "rule_id": "R001",
                "rule_name": "UVT Excedido",
                "severity": "warning",
                "title": "Test",
                "description": "Test desc",
                "evidence": {},
                "created_at": "2026-05-27T10:00:00Z",
            }
        ]
        mock_response = MagicMock()
        mock_response.data = mock_data
        mock_query = MagicMock()
        mock_query.execute.return_value = mock_response
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.select.return_value = mock_query

        mock_supabase = MagicMock()
        mock_supabase.table.return_value = mock_query

        with patch(
            "services.centinela_service.get_supabase",
            return_value=mock_supabase,
        ):
            alerts = service.get_alerts_for_company("ctx-001")
        assert alerts == mock_data


class TestGetAlertsEndpoint:
    """Smoke test against FastAPI router using TestClient."""

    def test_endpoint_returns_200_and_shape(self):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        # Force fallback path so we don't need Supabase configured for the test
        with patch(
            "services.centinela_service.get_supabase",
            side_effect=Exception("offline"),
        ):
            resp = client.get("/api/v1/centinela/alerts/ctx-001")

        assert resp.status_code == 200
        body = resp.json()
        assert body["company_id"] == "ctx-001"
        assert "alerts" in body
        assert "risk_level" in body
        assert body["source"] == "demo_fallback"
        assert body["alert_count"] == len(body["alerts"])
