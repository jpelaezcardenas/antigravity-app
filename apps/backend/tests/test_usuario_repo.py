"""Tests for UsuarioRepository's Supabase client choice (RLS-hardening follow-up).

`usuarios` had RLS disabled entirely (Supabase advisory: fully exposed to anon/authenticated).
This repo used `infrastructure.supabase_client.supabase_client` (the "anon" client) directly —
the one path in the codebase that read `usuarios` without the service-role key already used by
`identity_resolver.py`/`crm_service.py` for the same table. Enabling RLS with no policy (matching
the pattern already used for e.g. `whatsapp_inbound_events`) is only safe once every reader goes
through the service-role client, which bypasses RLS deliberately and explicitly.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def fake_service_client():
    client = MagicMock()
    with patch(
        "infrastructure.repositories.usuario_repo.get_service_supabase", return_value=client
    ) as mock_getter:
        yield client, mock_getter


class TestUsuarioRepositoryUsesServiceRole:
    @pytest.mark.asyncio
    async def test_get_by_email_uses_the_service_role_client(self, fake_service_client):
        from infrastructure.repositories.usuario_repo import UsuarioRepository

        client, mock_getter = fake_service_client
        client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            MagicMock(data=[{"id": "u1", "email": "a@b.co"}])
        )

        repo = UsuarioRepository()
        result = await repo.get_by_email("a@b.co")

        mock_getter.assert_called()
        assert result == {"id": "u1", "email": "a@b.co"}

    @pytest.mark.asyncio
    async def test_get_by_id_uses_the_service_role_client(self, fake_service_client):
        from infrastructure.repositories.usuario_repo import UsuarioRepository

        client, mock_getter = fake_service_client
        client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            MagicMock(data=[{"id": "u1"}])
        )

        repo = UsuarioRepository()
        result = await repo.get_by_id("u1")

        mock_getter.assert_called()
        assert result == {"id": "u1"}

    def test_module_no_longer_imports_the_anon_client(self) -> None:
        """The anon client import must be gone, not merely unused — a stray import is one
        careless edit away from being reintroduced."""
        import inspect

        from infrastructure.repositories import usuario_repo

        source = inspect.getsource(usuario_repo)
        assert "supabase_client" not in source or "get_service_supabase" in source
        assert "from infrastructure.supabase_client import supabase_client" not in source
