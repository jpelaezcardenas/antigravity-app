"""
Unit tests for core/tenant_context.py's `tenant_exists` helper
(hermes-task-queue-tenant-scoping).

Additive-only file — does not touch `resolve_cliente_cero_tenant_id`, which is owned by the
concurrently active `hermes-multi-tenant-wrapper` change.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from core.tenant_context import tenant_exists


class TestTenantExists:
    def test_returns_true_when_tenant_row_found(self):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
            data={"id": "tenant-1"}
        )

        assert tenant_exists(mock_client, "tenant-1") is True

    def test_returns_false_when_no_tenant_row_found(self):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = None

        assert tenant_exists(mock_client, "does-not-exist") is False
