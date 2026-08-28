# Implementer report — freemium-tenant-minimum-seed

- Date: 2026-08-28
- Scope: full change (Sections 1-5 of tasks.md), TDD throughout.

## Design decision resolved (master plan's open question)

Read `apps/backend/migrations/0028_seed_client_tenants_and_shadow_gl.sql` (SYNTH seed pattern)
and `0035_rolling_reseed_synthetic_shadow_gl.sql` (pg_cron reseed, matches only `-SALE`/`-EXPENSE`
suffixes, never `-OPEN`) in full before writing design.md. Confirmed via grep of
`financials_service.py` that `caja_real` is the running balance of account `1110` — an `-OPEN`
entry alone makes it non-zero, no dependency on Subdomain 6. Decision: seed only an opening
balance (account 1110/3105), never a synthetic "yesterday's sale/expense" — avoids fabricating
business activity for a lead who hasn't operated yet, and requires zero interaction with the
existing reseed cron (documented as design.md D1/D2).

## Section 1 — `shadow_gl_seed_service.py`

New file, TDD: 3 tests (`test_shadow_gl_seed_service.py`) red first (`ModuleNotFoundError`), then
`seed_freemium_opening_balance()` implemented mirroring migration 0028's exact SQL shape via the
Supabase client (idempotency guard on `external_reference_id = SYNTH-{nit}-OPEN` scoped to
`tenant_id`, single entry + 2 lines). 3/3 green.

## Section 2 — wired into `create_b2b_client`

3 new tests in `test_crm_service_b2b_writes.py` (freemium+amount seeds; freemium+no-amount does
not seed; non-freemium tier ignores the field) — red first (`AttributeError` on the patched
`services.crm_service.seed_freemium_opening_balance`), then wired: after the `b2b_clients` insert,
call the seed function when `plan_tier == "freemium" and opening_balance_cents` (truthy — covers
both `None` and `0`). Uses `client_tenant_id`/`nit` already in scope from the tenant creation
earlier in the same function — no extra lookup.

## Section 3 — endpoint

Added `opening_balance_cents: Optional[int] = Field(default=None, ge=0)` to
`CreateB2bClientRequest`, passed through only when non-None (same pattern as `plan_tier`).

## Section 4 — frontend

Added `opening_balance_cents?: number` to `CreateB2bClientInput`. Added a conditional numeric
input ("Saldo de apertura (COP)") to the alta form, rendered only when `altaPlanTier === "freemium"`
— submits `Math.round(Number(altaOpeningBalanceCop) * 100)` when both the tier is freemium and a
value was entered, `undefined` otherwise (so non-freemium submissions never send the field).
Clears on successful alta, same as the other fields.

## Section 5 — Testing

- Backend: 44/44 directly-related tests green (`test_shadow_gl_seed_service.py`,
  `test_crm_service_b2b_writes.py`, `test_crm_endpoints.py`, `test_plan_features.py`). Broader
  sweep `-k "crm or shadow_gl"` (excluding the 3 pre-existing `ModuleNotFoundError: No module
  named 'apps'` collection errors, same as Subdomains 3/4): 125 passed, 50 skipped, 13 failed —
  verified via `git stash` that all 13 failures pre-exist on `main` unmodified
  (`test_shadow_gl_stage1_migration.py`/`stage4_uploader`/`stage5_error_handling`/`stage8_e2e`,
  a historical Shadow GL "Phase 8" migration-file/acceptance suite unrelated to this change and
  to this session's other subdomains).
- Frontend: `tsc --noEmit` — zero errors.
- Dev-server visual check: not performed — same pre-existing local `SUPABASE_URL` gap documented
  in Subdomains 3/4 makes a real end-to-end alta unobservable locally without a founder session
  token.

## Files touched

- New: `apps/backend/services/shadow_gl_seed_service.py`,
  `apps/backend/tests/test_shadow_gl_seed_service.py`,
  `openspec/changes/freemium-tenant-minimum-seed/` (proposal, design, specs, tasks).
- Modified: `apps/backend/services/crm_service.py`, `apps/backend/presentation/crm_endpoints.py`,
  `apps/backend/tests/test_crm_service_b2b_writes.py` (3 new tests),
  `contexia-app/lib/crm-api.ts`, `contexia-app/components/bunker/crm/B2bRetainersTab.tsx`.

## Next step

Awaiting reviewer pass before Stage 11 (deploy + report) and archive.
