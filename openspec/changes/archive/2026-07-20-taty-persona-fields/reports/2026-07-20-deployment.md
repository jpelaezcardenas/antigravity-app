# Deployment report — taty-persona-fields

Date: 2026-07-20

## Summary

Change deployed and verified live in production. Taty now detects and persists `topes`
(consignaciones/ingresos/compras/patrimonio amounts) and a preliminary `obligado_declarar` signal
alongside the existing `es_asalariado` detection — closing the last unclosed sliver of gap #8 from
the plan-vs-build audit. A real, pre-existing production bug (surfaced by this change, not
introduced by it) was found and fixed during Stage 11.

## Commits deployed

- `4ef3df8` — feat(taty): detect and persist topes/obligado_declarar persona fields
- `2fe9854` — fix(crm): get_tax_profile raised PGRST116 for leads with no tax profile row

## Stage 11 steps executed

1. Merged `feature/taty-persona-fields` to `main` (fast-forward, confirmed via `git merge-base`),
   pushed. Railway deploy of `4ef3df8` reached `SUCCESS`.
2. **Live smoke test, first attempt: 500 Internal Server Error.** POSTed a fabricated WhatsApp
   text-message webhook mentioning `"el año pasado me consignaron 80000000 en el banco"` for a
   real disposable test lead (`stage=PROSPECTOS`, no tax profile row yet — the common state for
   any lead that hasn't reached `CrmService.approve_payment`). Railway logs showed the real
   traceback:
   `postgrest.exceptions.APIError: {'code': 'PGRST116', ... 'Cannot coerce the result to a single
   JSON object'}`, raised from `CrmService.get_tax_profile`'s `.single()` call via
   `route_lead_message`.
   **Root cause**: `get_tax_profile` used `.single()`, which raises when 0 rows match — a
   pre-existing bug in `crm_service.py` since it was written, never caught by mocked unit tests
   (mocks don't reproduce postgrest's exception-on-empty behavior) and never exercised live before,
   because the only caller (`route_lead_message`) previously called `get_tax_profile` **only**
   inside the `if persona_fields:` branch. This change's design (reading `existing_topes` before
   detection, to merge rather than overwrite `topes`) required calling `get_tax_profile`
   **unconditionally** on every inbound message — which is what finally exposed this bug for the
   very common "lead has no tax profile yet" case.
   **Fix**: switched to `.maybe_single()`, which returns `None` (confirmed by reading
   `postgrest`'s installed source directly, not assumed) instead of raising on 0 rows;
   `get_tax_profile` now correctly returns `{}` in that case, as its docstring always claimed.
   Added a regression test (`test_get_tax_profile_returns_empty_dict_when_none_exists`), re-ran the
   full suite (70/70 green), committed (`2fe9854`), pushed, redeployed.
3. **Live smoke test, re-run after the fix — both cases confirmed via Supabase SQL:**
   - Lead A: fabricated message mentioning consignaciones of 80,000,000 → `200`,
     `crm_tax_profiles.topes = {"consignaciones": 80000000}`, `obligado_declarar = true` (80M ≥
     `UMBRAL_RENTA_COP` ≈ 69.7M).
   - Lead B: fabricated message mentioning ingresos of 10,000,000 → `200`,
     `topes = {"ingresos": 10000000}`, `obligado_declarar = false` (below threshold).
   - Both disposable test leads + tax-profile rows cleaned up afterward.
4. Railway needed the usual slow-boot wait (a few `502`s before `200`) at each deploy — no crash
   signature in the logs beyond the real traceback above; consistent with this session's recurring
   platform pattern, not a new issue.

## Accepted risks / limitations (carried from design.md)

- **`obligado_declarar` is a preliminary internal signal, not a legal determination** — never
  surfaced to the lead directly in this change; for Taty/human-contadora use only, per
  `.antigravity/GROUND_TRUTH.md`'s Entidad B framing.
- **Only `ingresos`/`consignaciones` are checked against a threshold** — `compras`/`patrimonio`
  amounts are detected and stored in `topes` but don't yet drive `obligado_declarar` (documented
  Open Question in design.md, deferred pending confirmed DIAN 2026 UVT multipliers for those
  categories).
- **No proactive qualifying questions** — Taty only reacts to whatever the lead volunteers.

## Verification evidence

- Railway deployment (final: `2fe9854`): `SUCCESS`, confirmed responding.
- Live webhook smoke test: both above-threshold and below-threshold cases return `200` and produce
  the correct `topes`/`obligado_declarar` values in Supabase.
- Full regression suite: 70/70 green (this change's 11 new tests + 1 new regression test + 58
  pre-existing), zero regression.
