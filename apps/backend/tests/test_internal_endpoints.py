"""
Tests for /internal/ aggregator endpoints.

Uses httpx.AsyncClient + ASGITransport (repo-standard pattern — TestClient(app)
is broken in this environment due to httpx>=0.28 / starlette 0.27 mismatch).
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import FastAPI

os.environ.setdefault("HERMES_BRIDGE_TOKEN", "test-hermes-secret")

VALID_TOKEN = "test-hermes-secret"
HEADERS = {"Authorization": f"Bearer {VALID_TOKEN}"}

ACTIVE_CLIENTS = [
    MagicMock(company_id="c1", tenant_id="t1", nombre="Empresa A"),
    MagicMock(company_id="c2", tenant_id="t2", nombre="Empresa B"),
]


@pytest.fixture
def internal_client():
    import importlib, sys
    for key in list(sys.modules.keys()):
        if "hermes_auth" in key or "routers.internal" in key:
            del sys.modules[key]
    os.environ["HERMES_BRIDGE_TOKEN"] = VALID_TOKEN
    from routers.internal import router
    app = FastAPI()
    app.include_router(router)
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class TestInternalAuth:
    @pytest.mark.asyncio
    async def test_health_no_token_returns_403(self, internal_client):
        async with internal_client as client:
            r = await client.get("/internal/health")
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_health_valid_token_returns_200(self, internal_client):
        async with internal_client as client:
            r = await client.get("/internal/health", headers=HEADERS)
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Pulso
# ---------------------------------------------------------------------------

class TestPulsoAllActive:
    @pytest.mark.asyncio
    async def test_returns_all_clients(self, internal_client):
        pulso_payload = {"caja_real": 1000000}
        with patch("routers.internal.get_active_pwa_clients", return_value=ACTIVE_CLIENTS), \
             patch("routers.internal.get_pulso_summary", new_callable=AsyncMock, return_value=pulso_payload):
            async with internal_client as client:
                r = await client.get("/internal/pulso/all-active", headers=HEADERS)
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 2
        assert len(body["clientes"]) == 2
        assert body["clientes"][0]["company_id"] == "c1"
        assert body["clientes"][0]["nombre"] == "Empresa A"
        assert body["clientes"][0]["pulso"] == pulso_payload
        assert "timestamp" in body

    @pytest.mark.asyncio
    async def test_empty_clients_returns_valid_response(self, internal_client):
        with patch("routers.internal.get_active_pwa_clients", return_value=[]):
            async with internal_client as client:
                r = await client.get("/internal/pulso/all-active", headers=HEADERS)
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 0
        assert body["clientes"] == []


# ---------------------------------------------------------------------------
# Centinela
# ---------------------------------------------------------------------------

class TestCentinelaAllActive:
    @pytest.mark.asyncio
    async def test_returns_all_clients(self, internal_client):
        alerts_payload = {"alerts": [{"rule_id": "R1", "severity": "warning"}]}
        with patch("routers.internal.get_active_pwa_clients", return_value=ACTIVE_CLIENTS), \
             patch("routers.internal.get_centinela_alerts", new_callable=AsyncMock, return_value=alerts_payload):
            async with internal_client as client:
                r = await client.get("/internal/centinela/all-active", headers=HEADERS)
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 2
        assert body["clientes"][0]["centinela"] == alerts_payload


# ---------------------------------------------------------------------------
# Radar
# ---------------------------------------------------------------------------

class TestRadarAllActive:
    @pytest.mark.asyncio
    async def test_returns_all_clients(self, internal_client):
        radar_payload = {"risk_score": 42}
        with patch("routers.internal.get_active_pwa_clients", return_value=ACTIVE_CLIENTS), \
             patch("routers.internal.get_radar_summary", new_callable=AsyncMock, return_value=radar_payload):
            async with internal_client as client:
                r = await client.get("/internal/radar/all-active", headers=HEADERS)
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 2
        assert body["clientes"][0]["radar"] == radar_payload


# ---------------------------------------------------------------------------
# Auditoría Sombra
# ---------------------------------------------------------------------------

class TestAuditoriaSombraAllActive:
    @pytest.mark.asyncio
    async def test_triggers_nightly_for_all_clients(self, internal_client):
        audit_payload = {"status": "queued"}
        with patch("routers.internal.get_active_pwa_clients", return_value=ACTIVE_CLIENTS), \
             patch("routers.internal.run_auditoria_nightly", new_callable=AsyncMock, return_value=audit_payload):
            async with internal_client as client:
                r = await client.post("/internal/auditoria-sombra/all-active", headers=HEADERS)
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 2
        assert body["clientes"][0]["auditoria_sombra"] == audit_payload


# ---------------------------------------------------------------------------
# Social Ops
# ---------------------------------------------------------------------------

class TestSocialOpsAllActive:
    @pytest.mark.asyncio
    async def test_returns_all_clients(self, internal_client):
        social_payload = {"pipeline": []}
        with patch("routers.internal.get_active_pwa_clients", return_value=ACTIVE_CLIENTS), \
             patch("routers.internal.get_social_ops_briefing", new_callable=AsyncMock, return_value=social_payload):
            async with internal_client as client:
                r = await client.get("/internal/social-ops/all-active", headers=HEADERS)
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 2
        assert body["clientes"][0]["social_ops"] == social_payload

    @pytest.mark.asyncio
    async def test_error_resilience(self, internal_client):
        """One client throws → null payload + error field; others unaffected."""
        call_count = 0

        async def _side_effect(company_id, tenant_id):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Service unavailable")
            return {"pipeline": []}

        with patch("routers.internal.get_active_pwa_clients", return_value=ACTIVE_CLIENTS), \
             patch("routers.internal.get_social_ops_briefing", side_effect=_side_effect):
            async with internal_client as client:
                r = await client.get("/internal/social-ops/all-active", headers=HEADERS)
        assert r.status_code == 200
        body = r.json()
        assert body["clientes"][0]["social_ops"] is None
        assert "error" in body["clientes"][0]
        assert body["clientes"][1]["social_ops"] == {"pipeline": []}
