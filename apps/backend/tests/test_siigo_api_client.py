"""
TDD tests for SiigoApiClient (services/siigo_api_client.py).

These tests never call the real Siigo API — they mock httpx and os.environ.
All fixtures use synthetic data that resembles the Siigo API response shape.
"""

from __future__ import annotations

import os
from datetime import date, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Credential helpers
# ---------------------------------------------------------------------------


class TestGetSiigoCredentials:
    def test_returns_none_when_vars_missing(self):
        from services.siigo_api_client import get_siigo_credentials

        with patch.dict(os.environ, {}, clear=False):
            # Env vars not set for this fake UUID
            result = get_siigo_credentials("00000000-0000-0000-0000-000000000099")
        assert result is None

    def test_returns_tuple_when_vars_present(self):
        from services.siigo_api_client import get_siigo_credentials

        tenant_id = "aabbccdd-0000-0000-0000-aabbccddee00"
        suffix = "AABBCCDD_0000_0000_0000_AABBCCDDEE00"
        env = {
            f"SIIGO_USERNAME_{suffix}": "user@empresa.com",
            f"SIIGO_ACCESS_KEY_{suffix}": "test-key-123",
        }
        with patch.dict(os.environ, env):
            result = get_siigo_credentials(tenant_id)

        assert result is not None
        username, access_key = result
        assert username == "user@empresa.com"
        assert access_key == "test-key-123"

    def test_returns_none_when_only_username_set(self):
        from services.siigo_api_client import get_siigo_credentials

        tenant_id = "aabbccdd-0000-0000-0000-aabbccddee01"
        suffix = "AABBCCDD_0000_0000_0000_AABBCCDDEE01"
        with patch.dict(os.environ, {f"SIIGO_USERNAME_{suffix}": "user@empresa.com"}):
            result = get_siigo_credentials(tenant_id)

        assert result is None


# ---------------------------------------------------------------------------
# Row mappers (pure functions, no network)
# ---------------------------------------------------------------------------


class TestJournalEntryToRows:
    def test_maps_journal_items_to_rows(self):
        from services.siigo_api_client import _journal_entry_to_rows

        entry = {
            "id": "JNL-001",
            "date": "2026-09-01T00:00:00",
            "items": [
                {"account": {"code": "1100"}, "description": "AR", "debit": 1190.0, "credit": 0},
                {"account": {"code": "4100"}, "description": "Sales", "debit": 0, "credit": 1190.0},
            ],
        }
        rows = _journal_entry_to_rows(entry)

        assert len(rows) == 2
        assert rows[0]["referencia_externa"] == "JNL-001"
        assert rows[0]["fecha"] == "2026-09-01"
        assert rows[0]["codigo_cuenta"] == "1100"
        assert rows[0]["debito_cents"] == 119000
        assert rows[0]["credito_cents"] == 0

    def test_returns_empty_list_for_no_items(self):
        from services.siigo_api_client import _journal_entry_to_rows

        entry = {"id": "JNL-002", "date": "2026-09-01", "items": []}
        assert _journal_entry_to_rows(entry) == []


class TestInvoiceToRows:
    def test_maps_invoice_to_ar_and_revenue_rows(self):
        from services.siigo_api_client import _invoice_to_rows

        invoice = {"id": "42", "date": "2026-09-01", "total": 500.0}
        rows = _invoice_to_rows(invoice)

        assert len(rows) == 2
        assert rows[0]["codigo_cuenta"] == "1300"
        assert rows[0]["debito_cents"] == 50000
        assert rows[1]["codigo_cuenta"] == "4100"
        assert rows[1]["credito_cents"] == 50000

    def test_returns_empty_for_zero_total(self):
        from services.siigo_api_client import _invoice_to_rows

        invoice = {"id": "43", "date": "2026-09-01", "total": 0}
        assert _invoice_to_rows(invoice) == []


# ---------------------------------------------------------------------------
# SiigoApiClient
# ---------------------------------------------------------------------------


class TestSiigoApiClientForTenant:
    def test_returns_none_when_no_credentials(self):
        from services.siigo_api_client import SiigoApiClient

        with patch("services.siigo_api_client.get_siigo_credentials", return_value=None):
            client = SiigoApiClient.for_tenant("fake-tenant-id")

        assert client is None

    def test_returns_client_when_credentials_present(self):
        from services.siigo_api_client import SiigoApiClient

        with patch(
            "services.siigo_api_client.get_siigo_credentials",
            return_value=("user@test.com", "key-xyz"),
        ):
            client = SiigoApiClient.for_tenant("fake-tenant-id")

        assert client is not None
        assert client.tenant_id == "fake-tenant-id"


class TestSiigoApiClientAuth:
    @pytest.mark.asyncio
    async def test_authenticate_caches_token(self):
        from services.siigo_api_client import SiigoApiClient

        client = SiigoApiClient("t1", "user@test.com", "key-abc")

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"access_token": "tok-123", "expires_in": 3600}

        mock_httpx_client = AsyncMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        await client._authenticate(mock_httpx_client)

        assert client._token == "tok-123"
        assert client._token_expires_at is not None

    @pytest.mark.asyncio
    async def test_token_is_valid_after_auth(self):
        from services.siigo_api_client import SiigoApiClient

        client = SiigoApiClient("t1", "user@test.com", "key-abc")
        assert not client._token_is_valid()

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"access_token": "tok-456", "expires_in": 3600}

        mock_httpx = AsyncMock()
        mock_httpx.post = AsyncMock(return_value=mock_response)
        await client._authenticate(mock_httpx)

        assert client._token_is_valid()
