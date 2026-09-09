"""Contexia's official price catalog — the single source of truth for what things cost.

Before this module the prices existed nowhere in the repo. The consequences were concrete:
commercial names drifted in the PWA, and `taty-whatsapp-renta-sales-capability` had to instruct
Taty's system prompt to refuse to state a price at all, in a change whose own findings document
the model confidently inventing figures when it lacks grounding. An undefined price is not a
neutral gap.

**Two revenue lines, two entities** (`.antigravity/GROUND_TRUTH.md`, which governs):

- **Entidad B** (Contexia S.A.S., TIC company) licenses *software*. Fixed tiers, keyed by the
  same `plan_tier` values as `core/plan_features.py`.
- **Entidad A** (the regulated accounting practice, JCC-registered) sells a *professional
  service*. Priced in a **band** by real workload — never a tier. Pro Micro and Pro Estándar are
  the identical software product; what differs is the human load.

That is why `plan_features.py` is deliberately untouched by this module: feature access and price
are separate concerns, and conflating them is what would let a pricing change silently alter what
a client can open.

**Why code and not a table**, given that the immediately preceding change argued the UVT *must*
live in a table: the UVT is republished by DIAN every December, so a code constant becomes wrong
on a calendar with nobody touching the repo. A price is a decision, not a drifting external fact
— it stays correct until someone changes it, and routing that change through review and tests is
desirable. See the change's design.md Decision 1.

**Units.** Everything here is COP **minor units** and every identifier says so (`_cents`),
because these values are compared against `b2b_clients.monthly_fee_cents`. Note the deliberate
contrast with `uvt_values.value_cop`, which is whole pesos because it is a legal figure published
that way and is compared against revenue converted to whole pesos. The invariant is the naming
discipline, not a single global unit — a bare `price` would be genuinely ambiguous in this repo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SoftwareTier:
    """One Entidad B software tier.

    `price_cents is None` is only legal together with `is_quoted=True`: a tier with no price
    and no marker would read as free.
    """

    commercial_name: str
    price_cents: Optional[int]
    is_quoted: bool
    #: Whether the tier includes a licensed accountant (i.e. carries an Entidad A component).
    #: Recorded because the entity split is the reason two revenue lines exist at all.
    includes_accountant: bool
    #: True when `price_cents` is a FLOOR, not a flat fee — found live 2026-09-09 by running
    #: Taty's production prompt: Contexia Pro's official listing is "desde $1.490.000" (the
    #: Estándar band's floor), but nothing recorded that, so the formatter stated it as a flat
    #: price. Callers must render "desde $X" rather than "$X" when this is True.
    starts_from: bool = False


@dataclass(frozen=True)
class QuotedPricing:
    """A floor-only offering, quoted case by case — no invented ceiling.

    Distinct from `ServiceBandPrice` (which can also represent a genuine bounded range, like
    Estándar) because this shape additionally names WHY the price varies (`price_drivers`),
    which the Renta Natural offer needs so Taty can tell a prospect what drives their number up
    without inventing a figure for it.
    """

    label: str
    min_cents: int
    max_cents: Optional[int]
    is_quoted: bool
    price_drivers: tuple[str, ...]


@dataclass(frozen=True)
class ServiceBandPrice:
    """One Entidad A professional-service band.

    Both bounds are optional, and `is_quoted=True` means "no published bound at all" rather
    than "bounds not recorded yet". Complejo is quoted case by case: giving it an invented
    floor would make legitimate quotes register as incoherent, which is the opposite of what
    the coherence check is for.

    Micro is a FIXED price, not a range, so its min and max are equal — a Micro client priced
    at anything else is a real deviation worth seeing.
    """

    label: str
    min_cents: Optional[int]
    max_cents: Optional[int]
    is_quoted: bool = False


#: Keyed by `plan_tier` — must cover exactly `core/plan_features.py`'s PLAN_FEATURES keys.
#: A test asserts that, so adding a tier without pricing it fails loudly.
SOFTWARE_TIERS: dict[str, SoftwareTier] = {
    "freemium": SoftwareTier(
        commercial_name="Pulso",
        price_cents=0,
        is_quoted=False,
        includes_accountant=False,
    ),
    "starter": SoftwareTier(
        commercial_name="GPS",
        price_cents=249_000_00,
        is_quoted=False,
        # The client keeps their own accountant — this is software only.
        includes_accountant=False,
    ),
    "growth": SoftwareTier(
        commercial_name="Contexia Pro",
        # "desde $1.490.000" — deliberately the SAME value as the Estándar band's floor,
        # referenced below rather than retyped, so the two cannot drift apart.
        price_cents=1_490_000_00,
        is_quoted=False,
        starts_from=True,
        includes_accountant=True,
    ),
    "enterprise": SoftwareTier(
        commercial_name="Contexia Total",
        price_cents=None,
        is_quoted=True,
        # Accountant plus revisoría fiscal.
        includes_accountant=True,
    ),
}


#: Keyed by service band — must cover exactly `services/pricing_service.py`'s SERVICE_BANDS.
SERVICE_BAND_PRICING: dict[str, ServiceBandPrice] = {
    # The documented exception: minimal movement, no labour load. A FIXED price, so both
    # bounds are the same value.
    "micro": ServiceBandPrice(
        label="Micro", min_cents=890_000_00, max_cents=890_000_00
    ),
    # The deliberate majority case — the only genuine range.
    "estandar": ServiceBandPrice(
        label="Estándar", min_cents=1_490_000_00, max_cents=2_400_000_00
    ),
    # Quoted case by case. Deliberately UNBOUNDED on both ends: the founder published no
    # floor for it, and inventing one (e.g. "starts where Estándar ends") would flag a
    # legitimate $2.000.000 complex quote as incoherent. No bound means nothing to contradict.
    "complejo": ServiceBandPrice(
        label="Complejo", min_cents=None, max_cents=None, is_quoted=True
    ),
}


#: Entidad A's THIRD revenue line (alongside the B2B software tiers and service bands):
#: Renta Natural persona-natural tax filing, sold through the WhatsApp funnel
#: (`taty_lead_router.RENTA_OFFER_CONTEXT`). Founder-given (2026-09-09): "desde 350.000 pesos
#: teniendo en cuenta cantidad de trámites, movimientos, patrimonio... según el caso" — a floor
#: with NO ceiling, because none was given and none exists; inventing one would repeat the exact
#: risk `taty-whatsapp-renta-sales-capability` documented (the model fabricating figures when
#: ungrounded).
RENTA_NATURAL_PRICING = QuotedPricing(
    label="Declaración de Renta Persona Natural",
    min_cents=35_000_000,
    max_cents=None,
    is_quoted=True,
    price_drivers=("cantidad_de_tramites", "movimientos", "patrimonio"),
)


def band_price_range_cents(service_band: Optional[str]) -> tuple[Optional[int], Optional[int]]:
    """(min, max) for a band, or (None, None) for a missing/unknown band.

    Returns rather than raises: read paths (a roster listing, a pre-quote) must never blow up
    on stale or unexpected data. The database CHECK constraint is what rejects a bad band.
    """
    entry = SERVICE_BAND_PRICING.get(service_band or "")
    if entry is None:
        return None, None
    return entry.min_cents, entry.max_cents


def check_fee_band_coherence(
    monthly_fee_cents: Optional[int], service_band: Optional[str]
) -> Optional[str]:
    """Return a human-readable warning if the recorded fee contradicts the recorded band.

    **Advisory only — never blocks a write.** Micro is explicitly an exception band and
    Complejo is quoted case by case, so legitimate off-range fees exist by construction.
    Rejecting them would force an operator to mis-record the band in order to record the true
    fee, destroying exactly the data these two columns were added to capture (design.md
    Decision 5).

    Returns None when there is nothing to contradict: no fee, no band, an unrecognised band,
    or a band with no published bound on the side being tested (Complejo has neither).
    """
    if monthly_fee_cents is None or not service_band:
        return None

    entry = SERVICE_BAND_PRICING.get(service_band)
    if entry is None:
        return None

    if entry.min_cents is not None and monthly_fee_cents < entry.min_cents:
        return (
            f"Honorario por debajo de la banda {entry.label}: "
            f"${monthly_fee_cents // 100:,.0f} < ${entry.min_cents // 100:,.0f}"
        ).replace(",", ".")

    if entry.max_cents is not None and monthly_fee_cents > entry.max_cents:
        return (
            f"Honorario por encima de la banda {entry.label}: "
            f"${monthly_fee_cents // 100:,.0f} > ${entry.max_cents // 100:,.0f}"
        ).replace(",", ".")

    return None
