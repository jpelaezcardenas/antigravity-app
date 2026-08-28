"""
Credential-free unit tests for shadow_gl_seed_service (freemium-tenant-minimum-seed).
Mocks the Supabase service-role client entirely, mirroring test_crm_service_b2b_writes.py.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from services.shadow_gl_seed_service import seed_freemium_opening_balance


def _fake_client(existing_entry=None):
    client = MagicMock()
    entries_table = MagicMock()
    lines_table = MagicMock()

    entries_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
        MagicMock(data=[existing_entry] if existing_entry else [])
    )
    entries_table.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": "entry-1"}]
    )
    lines_table.insert.return_value.execute.return_value = MagicMock(data=[{}])

    def table_side_effect(name):
        if name == "erp_journal_entries":
            return entries_table
        if name == "erp_journal_lines":
            return lines_table
        raise AssertionError(f"unexpected table {name!r}")

    client.table.side_effect = table_side_effect
    return client, entries_table, lines_table


class TestSeedFreemiumOpeningBalance:
    def test_seeds_one_entry_and_two_lines(self):
        client, entries_table, lines_table = _fake_client()

        seed_freemium_opening_balance(
            client, tenant_id="tenant-1", nit="SYN-ABC123", name="Nuevo Freemium",
            opening_balance_cents=500_000,
        )

        entries_table.insert.assert_called_once()
        entry_payload = entries_table.insert.call_args[0][0]
        assert entry_payload["tenant_id"] == "tenant-1"
        assert entry_payload["external_reference_id"] == "SYNTH-SYN-ABC123-OPEN"
        assert entry_payload["memo"].startswith("SYNTH:per-tenant-client-access")

        lines_table.insert.assert_called_once()
        lines_payload = lines_table.insert.call_args[0][0]
        assert len(lines_payload) == 2
        debit_line = next(l for l in lines_payload if l["debit_minor"] > 0)
        credit_line = next(l for l in lines_payload if l["credit_minor"] > 0)
        assert debit_line["account_code"] == "1110"
        assert debit_line["debit_minor"] == 500_000
        assert credit_line["account_code"] == "3105"
        assert credit_line["credit_minor"] == 500_000
        assert all(l["tenant_id"] == "tenant-1" for l in lines_payload)

    def test_idempotent_when_entry_already_exists(self):
        client, entries_table, lines_table = _fake_client(
            existing_entry={"id": "already-there"}
        )

        seed_freemium_opening_balance(
            client, tenant_id="tenant-1", nit="SYN-ABC123", name="Nuevo Freemium",
            opening_balance_cents=500_000,
        )

        entries_table.insert.assert_not_called()
        lines_table.insert.assert_not_called()

    def test_zero_amount_does_not_seed(self):
        client, entries_table, lines_table = _fake_client()

        seed_freemium_opening_balance(
            client, tenant_id="tenant-1", nit="SYN-ABC123", name="Nuevo Freemium",
            opening_balance_cents=0,
        )

        entries_table.insert.assert_not_called()
        lines_table.insert.assert_not_called()
