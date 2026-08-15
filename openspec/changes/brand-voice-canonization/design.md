## Context

`content_evaluator.py` is the Content Critic in the Sell Machine creative loop
(`sell-machine-creative-swarm`): it evaluates a generated hook and either approves it or sends it
back for one rewrite pass. Today its rubric is two hardcoded pieces of Python living directly in
that file — `BRAND_RUBRIC_SYSTEM_PROMPT` (an LLM tone check) and `_HARD_BAN_PHRASES` (5 literal
strings, unconditional rejection, non-overridable by the LLM). Both are explicitly *not* read from
`ai-specs/social-content-ops/content_ops_rules.md` at runtime, because that folder is untracked
and would not exist in a deployed environment (documented as Decision 4 in this file's own
docstring) — that reasoning is sound and this change preserves it.

The gap: the hard-ban list only catches *identity* claims (Contexia claiming to be a regulated
accounting firm). It has no mechanism for a *factual* claim — a hook can state any peso amount as
DIAN fact and nothing checks it. That's exactly what happened: `POST-01-TOPES-RENTA-2026` shipped
$471.000 as the minimum sanction (10× the 2024 UVT) instead of $523.740 (10× the 2026 UVT,
`core/constants.py::UVT_2026`). The correct constants already exist and are already used elsewhere
(`centinela_service.py` imports `UVT_2026`) — the defect was that the copy pipeline never checked
against them.

## Goals / Non-Goals

**Goals:**
- Move the rubric out of `content_evaluator.py` into a dedicated, tracked, importable module
  (`brand_rubric.py`) so `copywriter_service.py` can share the same source instead of maintaining
  an independent `_SYSTEM_PROMPT`.
- Add a deterministic Claim Ledger gate: any hook citing a peso/UVT/percentage figure must trace
  to a known constant; unrecognized numeric claims are rejected unconditionally, same tier as the
  identity hard-bans (not the LLM tone check, which is soft and has a fail-open fallback).
- Fix the copywriter's voseo/tuteo inconsistency in its deterministic fallback hook.

**Non-Goals:**
- Not building a general NLP entity-extraction system. The Claim Ledger is a narrow regex-based
  check against a small, explicit allowlist of known figures (starting with the UVT constants) —
  it is deliberately conservative (see Risks).
- Not changing `evaluate_hook()`'s existing control flow (hard-ban → LLM tone check → fallback);
  the Claim Ledger slots into the same non-overridable position the hard-ban check already
  occupies, it does not introduce a new flow.
- Not touching `taty_service.py` or WhatsApp copy — this change is scoped to the Sell Machine
  creative loop (`copywriter_service.py` + `content_evaluator.py`), not the conversational agent.

## Decisions

**1. New module, not a config file (JSON/YAML) or a re-read of the untracked `content_ops_rules.md`.**
A plain Python module is the smallest change that satisfies "importable by two services, one
source of truth, tracked in git, no runtime dependency on an untracked folder." A config file would
add a load step and a validation layer for no real benefit at this size — see CLAUDE.md's
anti-overengineering guidance. Re-pointing at `content_ops_rules.md` was rejected explicitly (it's
untracked, would not exist post-deploy — same reasoning as the existing Decision 4).

**2. Claim Ledger checks numbers via regex extraction + a known-value allowlist, not an LLM call.**
A deterministic check is testable, has zero latency/cost, and — critically — cannot be talked out
of rejecting a wrong number the way an LLM tone check already has a documented fail-open fallback
(`evaluate_hook()`'s `except Exception` path approves on tone-check failure). The Claim Ledger must
never fail open: if a hook contains a peso/UVT figure that isn't in the allowlist, it is rejected,
full stop.

**3. The allowlist sources from `core/constants.py`, not a hardcoded copy inside `brand_rubric.py`.**
`UVT_2025`/`UVT_2026` and the derived thresholds already live there and are already the values
`centinela_service.py` treats as canonical. Duplicating them into `brand_rubric.py` would recreate
the exact class of bug this change exists to prevent (two copies of a number, one goes stale).
`brand_rubric.py` imports from `core.constants` and derives the allowlist (raw UVT values + a small
set of pre-computed common multiples like the minimum-sanction figure) at import time.

**4. Scope of "numeric claim" is peso amounts and UVT references only, not all numbers.**
A hook can legitimately contain non-factual numbers (e.g., "3 razones para...", "en 5 minutos").
The regex specifically targets `$<digits>` (COP formatting, with thousand separators) and
`<digits> UVT` patterns — the two shapes a DIAN-fact claim actually takes in this copy.

## Risks / Trade-offs

- **[Risk] Regex under/over-matches** a peso figure written in an unexpected format (e.g. "471 mil"
  instead of "$471.000") → claim slips through unchecked. **Mitigation**: start with the two
  formats actually observed in shipped copy (`$X.XXX.XXX` and `X UVT`); log any hook where a
  `$`/`UVT` token appears but doesn't match either pattern as a warning for manual review, rather
  than silently passing it — narrow correctness over broad guessing.
- **[Risk] Legitimate new correct figures get rejected** because the allowlist hasn't been extended
  yet (e.g. a 2027 UVT value once it's published). **Mitigation**: this is the intended behavior —
  fail closed, force a deliberate constants.py update — not a bug. The rejection reason string
  names the unrecognized figure so a human can immediately see why and add it if legitimate.
- **[Trade-off] Narrower than a general fact-checker.** Accepted: matches the existing rubric's
  philosophy (hard-ban is a small explicit list, not a general classifier) and the actual defect
  observed was in exactly this category (DIAN peso figures).

## Migration Plan

1. Write failing tests for `brand_rubric.py` (hard-bans re-exported correctly, Claim Ledger accepts
   known UVT-derived figures, rejects unknown ones) before writing the module.
2. Create `brand_rubric.py`; make those tests pass.
3. Update `content_evaluator.py` to import from it and add the Claim Ledger check to
   `evaluate_hook()`; update its existing tests as needed, add a test for the new rejection path.
4. Fix `copywriter_service.py`'s fallback CTA text and re-point `_SYSTEM_PROMPT`; update its tests.
5. Sync the `sell-machine-creative-swarm` spec delta (Claim Ledger requirement) — per CLAUDE.md §7,
   spec update happens alongside code, not after.
6. Stage 11: deploy, verify a hook with a stale sanction figure is rejected in the live evaluator
   (or via a Railway log check), report, archive.

No data migration, no API contract change, no rollback complexity beyond a normal revert.

## Open Questions

None blocking — this is a self-contained backend module with no external dependency or founder
decision required.
