"""UVT (Unidad de Valor Tributario) lookup — pricing-quote-engine.

The UVT is re-published by DIAN resolution every December. A hardcoded value is therefore
wrong every 1 January and would silently misclassify every lead arriving after that date,
so this module reads `uvt_values` (migration 0048) and deliberately contains **no UVT
amount of its own** — `tests/test_uvt_service.py` asserts that by reading this source.

Two UVT values are simultaneously in force during 2026 and govern different things: UVT
2025 applies to año-gravable-2025 filing-obligation thresholds, UVT 2026 to sanctions and
withholding accrued in 2026. Hence a table keyed by year and a required `year` parameter
on every lookup — there is no "current UVT" concept here, because there isn't one in law.

Unit contract: `value_cop` is in WHOLE Colombian pesos, unlike the Shadow GL's `*_minor`
columns. Callers convert minor units to whole COP before calling `cop_to_uvt`
(see openspec/changes/pricing-quote-engine/design.md Decision #1).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from core.supabase_client import get_supabase


class UvtNotFoundError(LookupError):
    """No `uvt_values` row exists for the requested tax year.

    Raised rather than falling back to an adjacent year: substituting one year's UVT for
    another produces a confidently wrong threshold, which is worse than an explicit
    "we don't know this year yet".
    """


@dataclass(frozen=True)
class UvtValue:
    """One tax year's UVT, carrying the resolution that set it so the figure stays
    auditable to its source rather than being trusted on sight."""

    year: int
    value_cop: int
    resolution: str


def get_uvt_for_year(year: int, supabase_client: Optional[Any] = None) -> UvtValue:
    """Return the UVT in force for `year`.

    Raises:
        UvtNotFoundError: if `uvt_values` has no row for that year.
    """
    supabase = supabase_client if supabase_client is not None else get_supabase()

    result = (
        supabase.table("uvt_values")
        .select("year, value_cop, resolution")
        .eq("year", year)
        .maybe_single()
        .execute()
    )
    row = getattr(result, "data", None)

    if not row:
        raise UvtNotFoundError(
            f"No UVT value registered for tax year {year}. Seed it in the uvt_values "
            "table (migration 0048) citing its DIAN resolution — never hardcode it."
        )

    return UvtValue(
        year=int(row["year"]),
        value_cop=int(row["value_cop"]),
        resolution=row["resolution"],
    )


def cop_to_uvt(amount_cop: int, uvt_value_cop: int) -> float:
    """Express `amount_cop` (WHOLE pesos, not minor units) in UVT.

    Raises:
        ValueError: if `uvt_value_cop` is not positive — guards the divide-by-zero a
            corrupt or missing row would otherwise cause.
    """
    if uvt_value_cop <= 0:
        raise ValueError(f"UVT value must be positive, got {uvt_value_cop!r}")
    return amount_cop / uvt_value_cop
