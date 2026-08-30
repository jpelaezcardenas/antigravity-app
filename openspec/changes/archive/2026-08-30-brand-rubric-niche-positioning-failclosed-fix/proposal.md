## Why

The GTM master plan (Envigado Emprende, Campaña 1) requires the Sell Machine's Content Critic
and Copywriter to (1) lead with "contadoras tituladas con licencia + tecnología" instead of the
regulatory disclaimer, (2) balance hook output 60% nicho/valor / 25% claridad financiera / 15%
protección-cumplimiento instead of defaulting to DIAN-fear copy, and (3) never approve a hook
when the LLM tone check is unavailable. Manus (external research agent) initially built these
changes inside a separate, unauthorized "Contexia Content OS" system on n8n — explicitly
forbidden by `AGENTES.md` Regla 4 ("No Volver a n8n Legacy"). After being redirected, Manus
ported the same fixes into the real canonical modules (`agents/brand_rubric.py`,
`agents/content_evaluator.py`, `services/copywriter_service.py`). This change formally applies
that ported work to the repository, following the standard OpenSpec/Stage-11 path instead of an
informal drop-in.

Independently, this also fixes a real production bug: `content_evaluator.evaluate_hook()` was
**fail-open** — when the LLM tone check raised an exception, it returned `approved: True`,
letting a hook reach the Approval Queue without ever completing a real Content Critic
evaluation. Only the deterministic hard-ban and Claim Ledger checks still applied. This
contradicts Modo A's fail-closed principle (documented in `manus-gate-hitl-decision` and
`ARCHITECTURE.md`'s HITL commitments) and was confirmed live in the current test suite, whose
`test_llm_provider_failure_falls_back_to_hard_ban_check_only` explicitly asserts
`approved is True` on LLM failure.

## What Changes

- `agents/brand_rubric.py`: `BRAND_RUBRIC_SYSTEM_PROMPT` rewritten to lead with "contadoras
  tituladas con licencia + tecnología", add the 60/25/15 hook-mix rule, and instruct that DIAN
  appears only as practical context, never as a fear-driven protagonist. `HARD_BAN_PHRASES` and
  the Claim Ledger (`check_claims`, `_RECOGNIZED_MARKET_SOURCES`) are unchanged.
- `agents/content_evaluator.py`: **BREAKING** (behavior) — `evaluate_hook()`'s LLM-failure path
  now returns `approved: False` ("fail-closed") instead of `approved: True`. The two
  non-overridable gates (hard-ban, Claim Ledger) are unchanged and still run first.
- `services/copywriter_service.py`: `_SYSTEM_PROMPT` and `_GENERIC_GROUNDING_QUERY` repointed
  from Renta-Natural/DIAN-fear defaults to niche/value defaults (dropshipping margin, creator
  multi-platform income, freelancer honorarios); `_DETERMINISTIC_FALLBACK_HOOKS` rewritten to
  match. `_llm_generate_hooks()`'s prompt now states the 60/25/15 distribution explicitly.
- Test files updated to match: `test_content_evaluator.py` (fail-closed assertion, renamed
  test), `test_copywriter_service.py` (niche-value grounding-query assertion, renamed test).
- No changes to `check_claims()`/Claim Ledger logic, no changes to the Approval Queue, HITL gate,
  or Modo A state machine — those were already correct.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `sell-machine-creative-swarm`: the Content Critic's fail-closed requirement is now actually
  enforced when the LLM is unavailable (previously documented/assumed but not implemented); the
  brand rubric and hook-generation defaults reflect the niche/value positioning instead of the
  original Renta-Natural-only defaults.

## Impact

- `apps/backend/agents/brand_rubric.py`
- `apps/backend/agents/content_evaluator.py`
- `apps/backend/services/copywriter_service.py`
- `apps/backend/tests/test_content_evaluator.py`
- `apps/backend/tests/test_copywriter_service.py`
- Requires a Railway redeploy (Stage 11) for the fix to take effect in production — this change
  does not modify data, migrations, or frontend.
