"""Tier-to-feature map governing PWA feature access (plan-tier-feature-gating).

Pure logic — this module never queries Supabase itself. Callers resolve a tenant's
`plan_tier` (the `tenants`/`b2b_clients` column added in migration 0043) separately and
pass the string in.

Not the same concept as the dead `plan_type` Postgres ENUM (migration 0010, applied to the
unrelated `customer_invites` table) or the legacy `usuarios.plan` text column — see
openspec/changes/plan-tier-feature-gating/design.md for why those aren't reused here.
"""

from __future__ import annotations

from typing import Optional

_ALL_FEATURES = frozenset({"pulso_diario", "centinela_alerts", "liquidity_bridge"})

PLAN_FEATURES: dict[str, frozenset[str]] = {
    "freemium": frozenset({"pulso_diario"}),
    "starter": _ALL_FEATURES,
    "growth": _ALL_FEATURES,
    "enterprise": _ALL_FEATURES,
}


def has_feature(plan_tier: Optional[str], feature: str) -> bool:
    """True iff `plan_tier` includes `feature`.

    An unrecognized or missing `plan_tier` fails OPEN (returns True) — see design.md D2:
    this is a product gate, not an auth boundary, and the failure mode this repo's
    tenant-scoping history warns hardest against is silently locking out an existing
    paying client, not over-granting a hypothetical bad tier value.
    """
    if not plan_tier:
        return True
    return feature in PLAN_FEATURES.get(plan_tier, _ALL_FEATURES)
