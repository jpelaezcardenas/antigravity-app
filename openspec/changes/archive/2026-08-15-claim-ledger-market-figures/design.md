## Context

`check_claims()` scans hook text with `_PESO_PATTERN`/`_UVT_PATTERN`, parses each matched figure,
and rejects it unless it exact-matches `_KNOWN_COP_VALUES` (fiscal constants derived from
`core.constants`). Market figures have no path to pass at all — confirmed live, real Manus hooks
citing CCCE data were rejected.

## Goals / Non-Goals

**Goals:** let a hook keep a market figure that's genuinely sourced (source name + figure visibly
adjacent in the text, matching how Manus already writes citations); keep the gate deterministic —
no LLM judgment call on "is this a real source."

**Non-Goals:** not validating that the cited source *actually* published that number (no external
fact-check call — that's what "sourced" means here: a human/Manus-visible citation the founder can
audit, not an automated truth oracle); not accepting arbitrary parentheticals as citations.

## Decisions

**1. Citation must name a recognized source, from a small explicit allowlist.** An arbitrary
parenthetical (`($999.999.999 (mi opinion))`) must NOT pass — that defeats the gate. The allowlist
starts with the sources actually seen in this session's real research (CCCE, DANE, Cámara Aburrá
Sur) plus a few adjacent legitimate ones (Colombia Fintech, MinTIC, Superintendencia de
Sociedades). Extending it later is a one-line addition, not a design change.

**2. Citation detection is proximity-based first, then whole-hook fallback — not full-sentence
NLP.** First tries a nearby parenthetical (same window as the figure) — matches
`"$191.850 (−7,6% anual, CCCE)"`. **Adjusted during implementation** (real Manus text,
`ad6d3fcf…`, cites a source once per paragraph covering multiple stats, e.g.
`"...movió $105,4 billones (+26,7% vs 2023, CCCE) y en el 2T2025 ya fueron $26,9 billones..."` —
the second figure has no nearby parenthetical of its own): if no nearby citation is found, fall
back to "does a recognized source name appear anywhere in the hook's text at all." Still
deterministic and testable; a hook with zero recognized source names anywhere still fails exactly
as before.

**3. Fiscal constants keep their unconditional pass (no citation required).** Those are Contexia's
own canonical numbers (`core.constants`), not something that needs re-citing every time — changing
that would be a regression, not an improvement.

## Risks / Trade-offs

- **[Risk] A hook could cite a real source name near an unrelated/wrong figure** (e.g. mention
  "CCCE" near a fabricated number in the same sentence, by coincidence or intentional gaming).
  **Accepted for now**: the founder/Content Critic's LLM tone pass and human review at the
  Approval Queue gate remain the backstop for this; the Claim Ledger's job is catching the
  *common* failure mode (fully unsourced invented figures), not adversarial gaming — same
  threat model as before this change.

## Migration Plan

1. Failing tests first, using the real captured Manus hook text (CCCE $105,4 billones, $191.850)
   as regression fixtures — confirm they currently fail.
2. Implement the citation-detection acceptance path in `check_claims()`.
3. Confirm the real Manus hooks now pass, and confirm existing fiscal-constant + unsourced-figure
   tests still behave identically (no regression).
4. Sync spec delta, Stage 11 deploy, archive.

## Open Questions

None blocking.
