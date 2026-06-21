"""Tests for T16: /wizard/auditoria-sombra onboarding endpoint."""
import pytest
from unittest.mock import patch

from services.wizard_service import (
    derive_company_id,
    build_synthetic_profile,
    build_next_steps,
    run_auditoria_sombra,
)


class TestDeriveCompanyId:
    def test_strips_verification_digit(self):
        assert derive_company_id("900123456-1") == "ctx-900123456"

    def test_handles_no_dash(self):
        assert derive_company_id("9001234561") == "ctx-900123456"

    def test_handles_short_nit(self):
        assert derive_company_id("12345") == "ctx-12345"

    def test_handles_empty(self):
        assert derive_company_id("") == "ctx-unknown"


class TestSyntheticProfile:
    def test_default_sector_renders(self):
        p = build_synthetic_profile("Servicios Digitales", "Régimen Simple", 80_000_000)
        assert p["annual_revenue"] == 80_000_000 * 12
        assert p["gross_margin_percent"] == 55
        assert p["total_assets"] > 0

    def test_unknown_sector_falls_back(self):
        p = build_synthetic_profile("Sector Inventado", "Régimen Común", 50_000_000)
        # Falls back to default profile, doesn't crash
        assert "annual_revenue" in p
        assert p["regime"] == "Régimen Común"


class TestNextSteps:
    def test_critica_includes_urgency(self):
        steps = build_next_steps("crítica", 5)
        assert any("72h" in s for s in steps)

    def test_sana_is_calm(self):
        steps = build_next_steps("sana", 0)
        assert any("zona sana" in s for s in steps)


class TestRunAuditoriaSombra:
    def test_e2e_returns_expected_shape(self):
        """Full wizard flow with mocked LLM (Analyst falls back to skeletal)."""
        # Force Analyst LLM into fallback path so test doesn't depend on real LLM
        with patch(
            "agents.base_agent.BaseAgent.call_llm",
            return_value={"parsing_error": True},
        ):
            report = run_auditoria_sombra(
                nit="900123456-1",
                razon_social="Acme S.A.S.",
                email="dueno@acme.co",
                sector="Servicios Digitales",
                regime="Régimen Simple",
                monthly_revenue_cop=80_000_000,
            )

        assert report["company_id"] == "ctx-900123456"
        assert report["razon_social"] == "Acme S.A.S."
        assert report["status_level"] in ("sana", "vigilancia", "alerta", "crítica")
        assert isinstance(report["alerts_preview"], list)
        assert isinstance(report["next_steps"], list)
        assert len(report["next_steps"]) >= 2
        assert report["audit_duration_seconds"] >= 0
        assert "generated_at" in report

    def test_high_revenue_simple_regime_triggers_uvt_alert(self):
        """Empresa en Régimen Simple con ingresos altos debe activar UVT Excedido."""
        with patch(
            "agents.base_agent.BaseAgent.call_llm",
            return_value={"parsing_error": True},
        ):
            report = run_auditoria_sombra(
                nit="901999888-2",
                razon_social="MegaCorp",
                email="ceo@mega.co",
                sector="Comercio",
                regime="Régimen Simple",
                monthly_revenue_cop=1_500_000_000,  # 18B anual → excede 160 UVT
            )

        assert report["alert_count"] >= 1
        rule_ids = [a["rule_id"] for a in report["alerts_preview"]]
        assert "R001" in rule_ids  # UVT Excedido


class TestWizardEndpoint:
    def test_endpoint_returns_200(self):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        with patch(
            "agents.base_agent.BaseAgent.call_llm",
            return_value={"parsing_error": True},
        ):
            resp = client.post(
                "/api/v1/wizard/auditoria-sombra",
                json={
                    "nit": "900123456-1",
                    "razon_social": "Test S.A.S.",
                    "email": "test@test.co",
                    "sector": "Servicios Digitales",
                    "regime": "Régimen Simple",
                    "monthly_revenue_cop": 80_000_000,
                },
            )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["company_id"] == "ctx-900123456"
        assert "status_level" in body
        assert "next_steps" in body

    def test_endpoint_validates_email(self):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        resp = client.post(
            "/api/v1/wizard/auditoria-sombra",
            json={
                "nit": "900123456-1",
                "razon_social": "Test",
                "email": "not-an-email",
            },
        )
        assert resp.status_code == 422
