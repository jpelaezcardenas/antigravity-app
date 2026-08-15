## Why

Confirmed live 2026-08-15 (postmortem of Manus's niche research task, operator_task `ad6d3fcf…`):
Manus produced 3 excellent, on-brief hooks with real market figures cited with source and date
(CCCE: e-commerce $105,4 billones +26,7% vs 2023; ticket promedio $191.850 −7,6% anual) — and the
Claim Ledger (`brand_rubric.py::check_claims`) rejected 2 of the 3 as "unsourced peso figure",
because `_KNOWN_COP_VALUES` is a fixed allowlist of **fiscal** constants only (UVT, sanciones). It
has no concept of a sourced *market* figure at all — any peso amount not in that exact set fails,
even when the hook visibly cites its source.

This is a real false-positive, not overly-cautious behavior: it will keep rejecting the best
hooks (the ones grounded in real market research) while passing generic, sourceless copy that
happens to avoid numbers. Left unfixed, every Manus research sprint targeting Contexia's niche
(e-commerce/dropshipping segments, not fiscal topics) will lose its strongest hooks to this gap.

## What Changes

- `check_claims()` gains a second acceptance path for peso/UVT figures: a figure is accepted if
  either (a) it exact-matches a known fiscal constant (today's behavior, unconditionally trusted,
  no citation needed since those are canonical), **or** (b) it is followed by an inline
  parenthetical citation naming a recognized market-data source (e.g. `(CCCE, 2026)`,
  `(+26,7% vs 2023, CCCE)`, `(DANE)`) from a small allowlist of legitimate Colombian
  market-research sources.
- The source-name allowlist starts small and explicit (CCCE, DANE, Cámara de Comercio Aburrá Sur,
  Colombia Fintech, MinTIC, Superintendencia de Sociedades) — not "any parenthetical passes",
  which would defeat the gate's purpose.
- A peso/UVT figure with **no** citation and **no** fiscal-constant match still fails exactly as
  today — this change only adds a second way to pass, never removes the existing one.

## Capabilities

### Modified Capabilities
- `sell-machine-creative-swarm`: the Claim Ledger gains a sourced-market-figure acceptance path
  alongside its existing fiscal-constant allowlist.

## Impact

- `apps/backend/agents/brand_rubric.py` (modified: `check_claims`, new source-allowlist constant)
- `apps/backend/tests/test_brand_rubric.py` (new tests, including a regression fixture using the
  exact real Manus hooks that triggered this)
- No API/schema change, no migration, no new dependency.
