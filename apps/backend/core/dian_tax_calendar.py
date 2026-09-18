"""
DIAN 2026 tax calendar — real, official deadlines by last digit of NIT.

Source (verified live, 2026-09-18): Decreto 1625 de 2016, modificado por el
Decreto 2229 de 2023 (arts. 1.6.1.13.2.30 IVA bimestral / 1.6.1.13.2.33
retención en la fuente mensual). Tables cross-checked against
actualicese.com's published calendar for 2026.

This is the SAME kind of fixed, externally-published reference data as
uvt_values (migration 0048) — a regulatory calendar, not something Contexia
computes or infers. It backs "Próximos Hitos" (pwa-v2): real declaration
DEADLINES for a tenant's real NIT, never a peso amount — no table in this
repo tracks per-tenant CxC/CxP with a due date (see ARCHITECTURE.md), so an
amount next to these dates would be fabricated. These tiles are date-only.
"""

from datetime import date
from typing import Optional

# retencion_en_la_fuente[month_1_indexed][last_digit] -> day of that month
RETENCION_FUENTE_2026: dict[int, dict[int, int]] = {
    1: {1: 10, 2: 11, 3: 12, 4: 13, 5: 16, 6: 17, 7: 18, 8: 19, 9: 20, 0: 23},
    2: {1: 10, 2: 11, 3: 12, 4: 13, 5: 16, 6: 17, 7: 18, 8: 19, 9: 20, 0: 24},
    3: {1: 13, 2: 14, 3: 15, 4: 16, 5: 20, 6: 21, 7: 22, 8: 23, 9: 24, 0: 27},
    4: {1: 12, 2: 13, 3: 14, 4: 15, 5: 19, 6: 20, 7: 21, 8: 22, 9: 25, 0: 26},
    5: {1: 10, 2: 11, 3: 12, 4: 16, 5: 17, 6: 18, 7: 19, 8: 22, 9: 23, 0: 24},
    6: {1: 9, 2: 10, 3: 13, 4: 14, 5: 15, 6: 16, 7: 17, 8: 21, 9: 22, 0: 23},
    7: {1: 12, 2: 13, 3: 14, 4: 18, 5: 19, 6: 20, 7: 21, 8: 24, 9: 25, 0: 26},
    8: {1: 9, 2: 10, 3: 11, 4: 14, 5: 15, 6: 16, 7: 17, 8: 18, 9: 21, 0: 22},
    9: {1: 9, 2: 13, 3: 14, 4: 15, 5: 16, 6: 19, 7: 20, 8: 21, 9: 22, 0: 23},
    10: {1: 11, 2: 12, 3: 13, 4: 17, 5: 18, 6: 19, 7: 20, 8: 23, 9: 24, 0: 25},
    11: {1: 10, 2: 11, 3: 14, 4: 15, 5: 16, 6: 17, 7: 18, 8: 21, 9: 22, 0: 23},
    12: {1: 13, 2: 14, 3: 15, 4: 18, 5: 19, 6: 20, 7: 21, 8: 22, 9: 25, 0: 26},
}

# IVA bimestral: bimester end month (2,4,6,8,10,12 — the "Jan" row is Nov-Dic of the
# PRIOR year, declared in Jan 2026) -> {last_digit: (deadline_month, deadline_day)}.
# Keyed by the bimester's SECOND month for lookup convenience.
IVA_BIMESTRAL_2026: dict[int, dict[int, tuple[int, int]]] = {
    2: {1: (3, 10), 2: (3, 11), 3: (3, 12), 4: (3, 13), 5: (3, 16), 6: (3, 17), 7: (3, 18), 8: (3, 19), 9: (3, 20), 0: (3, 24)},
    4: {1: (5, 12), 2: (5, 13), 3: (5, 14), 4: (5, 15), 5: (5, 19), 6: (5, 20), 7: (5, 21), 8: (5, 22), 9: (5, 25), 0: (5, 26)},
    6: {1: (7, 9), 2: (7, 10), 3: (7, 13), 4: (7, 14), 5: (7, 15), 6: (7, 16), 7: (7, 17), 8: (7, 21), 9: (7, 22), 0: (7, 23)},
    8: {1: (9, 9), 2: (9, 10), 3: (9, 11), 4: (9, 14), 5: (9, 15), 6: (9, 16), 7: (9, 17), 8: (9, 18), 9: (9, 21), 0: (9, 22)},
    10: {1: (11, 11), 2: (11, 12), 3: (11, 13), 4: (11, 17), 5: (11, 18), 6: (11, 19), 7: (11, 20), 8: (11, 23), 9: (11, 24), 0: (11, 25)},
    12: {1: (2027, 1, 13), 2: (2027, 1, 14), 3: (2027, 1, 15), 4: (2027, 1, 18), 5: (2027, 1, 19), 6: (2027, 1, 20), 7: (2027, 1, 21), 8: (2027, 1, 22), 9: (2027, 1, 25), 0: (2027, 1, 26)},
}


def _nit_last_digit(nit: Optional[str]) -> Optional[int]:
    """Last digit of the NIT, excluding the verification digit (the DIAN
    calendar convention) — this repo stores the raw NIT string, digits only
    expected; returns None if unusable rather than guessing."""
    if not nit:
        return None
    digits = "".join(ch for ch in nit if ch.isdigit())
    if not digits:
        return None
    return int(digits[-1])


def next_retencion_fuente_deadline(nit: Optional[str], today: date) -> Optional[date]:
    """Next monthly retención en la fuente deadline strictly after `today`."""
    digit = _nit_last_digit(nit)
    if digit is None:
        return None

    year = today.year
    for month in range(today.month, 13):
        day = RETENCION_FUENTE_2026.get(month, {}).get(digit)
        if day is None:
            continue
        candidate = date(year, month, day)
        if candidate >= today:
            return candidate
    return None


def next_iva_bimestral_deadline(nit: Optional[str], today: date) -> Optional[date]:
    """Next bimonthly IVA deadline strictly after `today`."""
    digit = _nit_last_digit(nit)
    if digit is None:
        return None

    for bimester_end_month in sorted(IVA_BIMESTRAL_2026.keys()):
        entry = IVA_BIMESTRAL_2026[bimester_end_month].get(digit)
        if entry is None:
            continue
        if len(entry) == 2:
            candidate = date(today.year, entry[0], entry[1])
        else:
            candidate = date(entry[0], entry[1], entry[2])
        if candidate >= today:
            return candidate
    return None


def next_tax_milestones(nit: Optional[str], today: date) -> list[dict]:
    """Real upcoming DIAN deadlines for this tenant's NIT — date only, no
    peso amount (no real per-tenant amount exists for either obligation
    today). Empty list if NIT is missing/unusable."""
    milestones = []

    ret_date = next_retencion_fuente_deadline(nit, today)
    if ret_date is not None:
        milestones.append({
            "id": "retencion_fuente",
            "label": "Retención en la fuente",
            "date": ret_date.isoformat(),
        })

    iva_date = next_iva_bimestral_deadline(nit, today)
    if iva_date is not None:
        milestones.append({
            "id": "iva_bimestral",
            "label": "Declaración de IVA",
            "date": iva_date.isoformat(),
        })

    milestones.sort(key=lambda m: m["date"])
    return milestones
