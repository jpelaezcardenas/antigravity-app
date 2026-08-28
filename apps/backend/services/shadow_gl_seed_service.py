"""
Minimal synthetic Shadow GL seed for a brand-new freemium tenant (freemium-tenant-minimum-seed).

Reuses the exact SYNTH-{nit}-OPEN / "SYNTH:per-tenant-client-access" naming convention from
migration 0028 (per-tenant-client-access), but seeds ONLY an opening-balance entry — never a
synthetic "yesterday's sale/expense" (design.md D2: an opening balance is honest ("your starting
capital"), a fabricated sale is not, for a lead who hasn't operated in the product yet). An
-OPEN entry is never matched by the rolling-reseed cron (migration 0035, which only re-dates
-SALE/-EXPENSE suffixes), so this requires no new infrastructure.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any


def seed_freemium_opening_balance(
    client: Any,
    tenant_id: str,
    nit: str,
    name: str,
    opening_balance_cents: int,
) -> None:
    """Seeds a single opening-balance journal entry (Dr 1110 Bancos / Cr 3105 Capital) into
    the given tenant's own Shadow GL. No-op if opening_balance_cents <= 0, or if a matching
    entry already exists for this tenant (idempotent, mirrors migration 0028's own guard)."""
    if opening_balance_cents <= 0:
        return

    external_reference_id = f"SYNTH-{nit}-OPEN"

    existing = (
        client.table("erp_journal_entries")
        .select("id")
        .eq("tenant_id", tenant_id)
        .eq("external_reference_id", external_reference_id)
        .execute()
    )
    if existing.data:
        return

    entry_result = (
        client.table("erp_journal_entries")
        .insert(
            {
                "tenant_id": tenant_id,
                "memo": f"SYNTH:per-tenant-client-access opening balance — {name}",
                "entry_date": (date.today() - timedelta(days=180)).isoformat(),
                "source": "manual",
                "external_reference_id": external_reference_id,
            }
        )
        .execute()
    )
    entry_id = entry_result.data[0]["id"]

    client.table("erp_journal_lines").insert(
        [
            {
                "entry_id": entry_id,
                "tenant_id": tenant_id,
                "account_code": "1110",
                "debit_minor": opening_balance_cents,
                "credit_minor": 0,
                "memo": "Saldo inicial sintético",
            },
            {
                "entry_id": entry_id,
                "tenant_id": tenant_id,
                "account_code": "3105",
                "debit_minor": 0,
                "credit_minor": opening_balance_cents,
                "memo": "Capital — saldo inicial sintético",
            },
        ]
    ).execute()
