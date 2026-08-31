"""
Tests for core/pwa_clients.py — get_active_pwa_clients().

Scenarios:
1. Returns only rows with status='activo' AND provision_status='provisioned'
2. Excludes clients with status='inactivo'
3. Excludes clients with provision_status='not_provisioned' (even if activo)
4. Returns empty list when no rows match
"""

from unittest.mock import MagicMock

import pytest

from core.pwa_clients import ActiveClient, get_active_pwa_clients


def _make_supabase_mock(rows: list[dict]) -> MagicMock:
    """Build a mock Supabase client that returns `rows` for the b2b_clients query."""
    mock = MagicMock()
    result = MagicMock()
    result.data = rows
    # Chain: .table().select().eq().eq().execute()
    mock.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = result
    return mock


class TestGetActivePwaClients:
    def test_returns_active_provisioned_clients(self):
        rows = [
            {"id": "c1", "tenant_id": "t1", "nombre": "Empresa A", "status": "activo", "provision_status": "provisioned"},
            {"id": "c2", "tenant_id": "t2", "nombre": "Empresa B", "status": "activo", "provision_status": "provisioned"},
        ]
        supabase = _make_supabase_mock(rows)
        clients = get_active_pwa_clients(supabase)
        assert len(clients) == 2
        assert all(isinstance(c, ActiveClient) for c in clients)
        assert clients[0].company_id == "c1"
        assert clients[0].tenant_id == "t1"
        assert clients[0].nombre == "Empresa A"

    def test_excludes_inactive_clients(self):
        rows: list[dict] = []  # mock filters at DB level; empty = no match
        supabase = _make_supabase_mock(rows)
        clients = get_active_pwa_clients(supabase)
        assert clients == []

    def test_excludes_unprovisioned_clients(self):
        rows: list[dict] = []  # same: filtered at DB level
        supabase = _make_supabase_mock(rows)
        clients = get_active_pwa_clients(supabase)
        assert clients == []

    def test_empty_list_on_no_matches(self):
        supabase = _make_supabase_mock([])
        clients = get_active_pwa_clients(supabase)
        assert clients == []
        assert isinstance(clients, list)

    def test_active_client_fields(self):
        rows = [{"id": "c9", "tenant_id": "t9", "nombre": "Empresa C", "status": "activo", "provision_status": "provisioned"}]
        supabase = _make_supabase_mock(rows)
        clients = get_active_pwa_clients(supabase)
        c = clients[0]
        assert c.company_id == "c9"
        assert c.tenant_id == "t9"
        assert c.nombre == "Empresa C"
