## Why

`content_evaluator.py`'s brand rubric is a hardcoded string ("condensed from
`ai-specs/social-content-ops/content_ops_rules.md`", an untracked folder) with 5 hard-ban phrases
that only cover unregulated-firm identity claims. It has no mechanism to catch a false *fact* — a
generated hook can cite any peso figure, and nothing checks it against a source. That gap produced
a real defect: `POST-01-TOPES-RENTA-2026` shipped the minimum sanction as $471.000 (10× UVT 2024)
instead of $523.740 (10× UVT 2026) — a wrong number published to prospective clients about DIAN
penalties. Separately, `copywriter_service.py`'s deterministic fallback hook mixes `tú`/`vos`
conjugation ("Habla con Taty y **salé** de dudas" — voseo — next to otherwise-tuteo copy), a small
but visible inconsistency in a channel meant to sound like one consistent person.

## What Changes

- New tracked module `apps/backend/agents/brand_rubric.py`: hard-ban phrases (supersedes
  `content_evaluator.py`'s inline `_HARD_BAN_PHRASES`, same 5 + room to extend), the
  `BRAND_RUBRIC_SYSTEM_PROMPT` tone rubric, and a new deterministic **Claim Ledger** validator —
  any hook citing a peso/UVT/percentage figure must match a known, sourced constant (starting with
  the existing `UVT_2025`/`UVT_2026` fiscal constants); an unrecognized number is a hard rejection,
  same non-overridable tier as the identity hard-bans.
- `content_evaluator.py` imports `BRAND_RUBRIC_SYSTEM_PROMPT` and the hard-ban list from
  `brand_rubric.py` instead of defining them inline. `evaluate_hook()` gains a Claim Ledger check
  in the same non-overridable position as the existing hard-ban check.
- `copywriter_service.py`: fix the voseo/tuteo mix in the fallback hook CTA, and point
  `_SYSTEM_PROMPT` at the same rubric module so tone guidance has one source instead of two
  independently-drifting copies.
- TDD: failing tests first for each hard-ban phrase, for the voseo/tuteo fix, and for the Claim
  Ledger rejecting an unsourced number / accepting a correctly-sourced one.

## Capabilities

### New Capabilities
(none — this extends the rubric that `sell-machine-creative-swarm` already owns)

### Modified Capabilities
- `sell-machine-creative-swarm`: the Content Critic's rejection criteria gain a deterministic
  Claim Ledger check (numeric claims must be sourced), and the rubric's storage location moves
  from inline-in-`content_evaluator.py` to a dedicated tracked module it imports from.

## Impact

- `apps/backend/agents/brand_rubric.py` (new)
- `apps/backend/agents/content_evaluator.py` (import rubric instead of inline constants; add
  Claim Ledger gate to `evaluate_hook()`)
- `apps/backend/services/copywriter_service.py` (fix fallback CTA text; import `_SYSTEM_PROMPT`
  from `brand_rubric.py`)
- `openspec/specs/sell-machine-creative-swarm/spec.md` (delta: Claim Ledger requirement)
- No API surface change, no migration, no new external dependency.
