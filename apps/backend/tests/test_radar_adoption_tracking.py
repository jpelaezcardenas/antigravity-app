"""
Tests for Radar de Caja adoption tracking (radar-adoption-tracking).

Closes the one acceptance criterion `radar-cash-projection-13w` descoped: an
adoption event feeding the ">=40% of active users open Radar de Caja weekly" KPI.

Fully mocked — no live Supabase connection, same style as
test_radar_cash_projection.py.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from services.radar_service import record_module_open


def _mock_client():
    client = MagicMock()
    table = MagicMock()
    table.upsert.return_value = table
    table.insert.return_value = table
    table.execute.return_value.data = [{"id": "row-1"}]
    client.table.return_value = table
    return client, table


class TestRecordModuleOpen:
    def test_writes_one_row_scoped_to_tenant_and_user(self):
        client, table = _mock_client()

        asyncio.run(
            record_module_open("tenant-abc", "user-1", supabase_client=client)
        )

        client.table.assert_called_with("radar_module_opens")
        assert table.insert.called, "expected an insert (dedupe is enforced by the partial unique indexes)"
        payload = table.insert.call_args[0][0]
        assert payload["tenant_id"] == "tenant-abc"
        assert payload["user_id"] == "user-1"
        assert "opened_on" in payload

    def test_staging_identity_without_user_id_still_records(self):
        client, table = _mock_client()

        asyncio.run(record_module_open("tenant-abc", None, supabase_client=client))

        payload = table.insert.call_args[0][0]
        assert payload["tenant_id"] == "tenant-abc"
        assert payload["user_id"] is None

    def test_never_raises_when_the_write_fails(self):
        """Telemetry must never degrade a financial read (design.md Decision #3)."""
        client = MagicMock()
        table = MagicMock()
        table.insert.return_value = table
        table.execute.side_effect = RuntimeError(
            'relation "public.radar_module_opens" does not exist'
        )
        client.table.return_value = table

        # Must not raise.
        asyncio.run(record_module_open("tenant-abc", "user-1", supabase_client=client))


    def test_uses_the_service_role_client_not_the_anon_one(self):
        """Regression guard, found against the real database.

        With the anon key this write evaluates the table's tenant-isolation
        policy, which reads user_tenants, whose policy chain hits a pre-existing
        "infinite recursion detected in policy for relation user_roles" error.
        Fail-soft would then swallow it and tracking would silently record
        nothing forever. Pin the service-role client so a refactor cannot
        regress it.
        """
        _, table = _mock_client()
        service = MagicMock()
        service.table.return_value = table

        with patch("services.radar_service.get_service_supabase", return_value=service) as svc,              patch("services.radar_service.get_supabase") as anon:
            asyncio.run(record_module_open("tenant-abc", "user-1"))

        svc.assert_called_once()
        anon.assert_not_called()


class TestEndpointRecordsTheOpen:
    def test_records_when_tenant_resolves(self, monkeypatch):
        from presentation import radar_endpoints as mod

        monkeypatch.setattr(
            mod,
            "resolve_request_tenant_scope",
            lambda user, client: mod.TenantScope(tenant_id="tenant-abc", all_tenants=False),
        )

        async def fake_projection(tenant_id, supabase_client=None):
            return {
                "client_tenant_id": tenant_id,
                "generado_en": "2026-09-05T08:00:00Z",
                "metodologia": "solo_historico",
                "impuesto_futuro_estimado": None,
                "estado": "sin_historico_suficiente",
                "semanas": None,
            }

        monkeypatch.setattr(mod, "calculate_cash_projection_13w", fake_projection)
        recorder = AsyncMock()
        monkeypatch.setattr(mod, "record_module_open", recorder)

        user = {"id": "user-1", "resolved_tenant_id": "tenant-abc"}
        response = asyncio.run(mod.get_cash_projection(user=user))

        assert response.estado == "sin_historico_suficiente"
        recorder.assert_awaited_once()
        assert recorder.await_args[0][0] == "tenant-abc"

    def test_does_not_record_when_tenant_unresolved(self, monkeypatch):
        from presentation import radar_endpoints as mod

        monkeypatch.setattr(mod, "resolve_request_tenant_scope", lambda user, client: None)
        recorder = AsyncMock()
        monkeypatch.setattr(mod, "record_module_open", recorder)

        response = asyncio.run(mod.get_cash_projection(user={"id": "u", "resolved_tenant_id": None}))

        assert response.estado == "tenant_no_resuelto"
        recorder.assert_not_awaited()

    def test_projection_still_returned_when_recording_raises(self, monkeypatch):
        from presentation import radar_endpoints as mod

        monkeypatch.setattr(
            mod,
            "resolve_request_tenant_scope",
            lambda user, client: mod.TenantScope(tenant_id="tenant-abc", all_tenants=False),
        )

        async def fake_projection(tenant_id, supabase_client=None):
            return {
                "client_tenant_id": tenant_id,
                "generado_en": "2026-09-05T08:00:00Z",
                "metodologia": "solo_historico",
                "impuesto_futuro_estimado": None,
                "estado": "ok",
                "semanas": [
                    {
                        "semana": i,
                        "fecha_inicio": "2026-09-07",
                        "caja_proyectada": 1_000_000,
                        "confianza": "media" if i <= 4 else "baja",
                    }
                    for i in range(1, 14)
                ],
            }

        monkeypatch.setattr(mod, "calculate_cash_projection_13w", fake_projection)

        async def boom(*args, **kwargs):
            raise RuntimeError("telemetry backend down")

        monkeypatch.setattr(mod, "record_module_open", boom)

        response = asyncio.run(
            mod.get_cash_projection(user={"id": "user-1", "resolved_tenant_id": "tenant-abc"})
        )

        assert response.estado == "ok"
        assert len(response.semanas) == 13
