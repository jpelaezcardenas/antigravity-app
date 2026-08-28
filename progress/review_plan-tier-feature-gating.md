# Review — task plan-tier-feature-gating

**Verdict:** APPROVED

## Independent verification performed

- Read migration `apps/backend/migrations/0043_add_plan_tier.sql`: `text` + `CHECK
  (plan_tier IN ('freemium','starter','growth','enterprise'))`, `DEFAULT 'starter'`, idempotent
  (`ADD COLUMN IF NOT EXISTS`, `pg_constraint` existence guard). Matches design.md D1 exactly —
  not the dead `plan_type` enum, default `'starter'` not `'freemium'` or `NULL`.
- Read `apps/backend/core/plan_features.py`: plain dict `PLAN_FEATURES` + `has_feature()`,
  fail-open on unrecognized/missing tier (line 34-36). Matches D2.
- `apps/backend/presentation/financials_endpoints.py`: gate correctly inserted in both
  `get_financials` (lines 161-172) and `get_liquidity_bridge` (lines 204-215) — in each case
  *after* `_resolve_caller_tenant_id`/the `tenant_id is None` empty-response guard, *before* the
  `compute_*` call. Confirmed by direct read, not summary.
- `apps/backend/presentation/centinela_endpoints.py`: `get_my_alerts` (lines 337-382) gate at
  lines 344-346, after `resolve_request_tenant_scope`'s `tenant_id is None` guard, before the
  `centinela_alerts` query. The legacy `GET /centinela/alerts/{company_id}`
  (`get_company_alerts`, lines 178-251) has zero references to `plan_features`/`has_feature` —
  confirmed untouched, as proposal.md and the spec's "legacy route is unaffected" scenario
  require.
- `apps/backend/presentation/tenant_endpoints.py` + `router.py`: new `GET /api/v1/tenant/me`
  wired at `prefix="/tenant"` (router.py:54), uses canonical `resolve_request_tenant_scope`
  per D5, not a new local resolver.
- Ran the 9 named test files directly: `54 passed` (`test_plan_features.py`,
  `test_financials_endpoint_plan_tier_gating.py`, `test_financials_endpoint_tenant_scoping.py`,
  `test_financials_aggregation.py`, `test_financials_liquidity_bridge.py`,
  `test_centinela_alerts_plan_tier_gating.py`, `test_centinela_alerts_tenant_scoping.py`,
  `test_centinela_endpoint_tenant_scoping.py`, `test_tenant_me_endpoint.py`). All green.
- Ran the full backend suite myself (excluding 3 files that fail to *collect* on this machine
  due to a pre-existing `ModuleNotFoundError: No module named 'apps'` import-path issue, verified
  via grep to have zero references to any file this change touches): **863 passed, 120 skipped,
  29 failed**. Spot-checked the failure list — none reference `financials_endpoints`,
  `centinela_endpoints`, `plan_features`, `tenant_endpoints`, or `0043`. Directly re-ran
  `test_centinela_alerts_get.py::test_endpoint_returns_200_and_shape` (one of the 29) in
  isolation and confirmed the implementer's claimed root cause: `TypeError: Client.__init__()
  got an unexpected keyword argument 'app'` — a `starlette`/`httpx` `TestClient` version
  mismatch, not a regression from this change. My raw numbers (863/29) differ slightly from the
  implementer's reported 847/28 (different environment snapshot / whether the 3
  collection-error files were counted), but the substantive claim — zero failures traceable to
  this change's touched files — holds under my own independent run.
- Frontend: read `CashTodayCard.tsx`, `ActiveAlerts.tsx`, `MonthlyLiquidityBridgeCard.tsx`,
  `TenantInfoCard.tsx`, `UpgradePlanBanner.tsx`, `api-client.ts`, `config.ts`, and all 4 page
  files (`config/page.tsx`, `fiscal/page.tsx`, `radar/page.tsx`, `patrimonio/page.tsx`). Each
  matches design.md D3/D4/D5 precisely: `CashTodayCard` has no new branch (comment explains
  why, `pulso_diario` unreachable as `not_in_plan`); `MonthlyLiquidityBridgeCard` gets a distinct
  `"not_in_plan"` state separate from `"unavailable"`; `ActiveAlerts` gets one new muted-line
  branch instead of its usual render-nothing; the 3 mock pages (`fiscal`, `radar`, `patrimonio`)
  each got exactly one import + one `<UpgradePlanBanner />` JSX line, no other changes.
  `contexia-app/CLAUDE.md`'s "Pantallas data-bound" section documents this as the 8th exception
  (living-doc rule respected).
- Ran `npx tsc --noEmit` in `contexia-app/` myself: zero errors, zero output.
- Confirmed `specs/pulso-financials-api/spec.md` and `specs/centinela-alerts/spec.md` exist as
  delta specs alongside the new `specs/plan-tier-feature-gating/` capability directory.

## Not independently re-verified (documented as gaps, not blockers)

- Live Supabase `information_schema.columns` state was not queried directly by me (no Supabase
  MCP tool available in this session) — relying on the implementer's reported verification
  (13/13 tenants, 10/10 b2b_clients at `'starter'`, zero NULL) and the migration file's own
  logic, which is unambiguous and idempotent.
- Stage 11 (deploy to production) tasks in `tasks.md` are still `[ ]` — this change has not yet
  been deployed/archived. That is expected at this review checkpoint (pre-deploy code review),
  not a defect in the implementation itself, but the change is NOT done per ARCHITECTURE.md
  Decision #2 / CLAUDE.md §8 until Stage 11 completes.
- `progress/current.md` is stale (dated 2026-08-17, predates this change, does not mention
  `plan-tier-feature-gating`) — a harness bookkeeping gap, not a code defect. Should be updated
  before/during Stage 11.

## Checkpoints

- Migration additive, idempotent, correct default: [x]
- `plan_features.py` fail-open, matches D2: [x]
- All 3 endpoints gated at the correct insertion point: [x]
- Legacy `get_company_alerts` route untouched: [x]
- New `GET /api/v1/tenant/me` uses canonical resolver: [x]
- Targeted test files pass (54/54): [x]
- Full suite has no new failures attributable to this change: [x]
- Frontend changes match design.md D3/D4/D5, minimal diff to mock screens: [x]
- `contexia-app/CLAUDE.md` living-doc updated (8th exception): [x]
- `tsc --noEmit` clean: [x]
- Stage 11 (deploy to production): [ ] — not yet done, required before archive per
  ARCHITECTURE.md Decision #2.
- `progress/current.md` sync: [ ] — stale, should be updated alongside Stage 11.

## Required changes (if any)

None blocking code approval. Before archiving this OpenSpec change:
1. Complete Stage 11 (commit + push + Vercel/Railway deploy + verify `GET /api/v1/tenant/me` in
   production + deployment report), per `tasks.md`'s own unchecked section 11.
2. Update `progress/current.md` to reflect this change's status (currently stale/silent on it).
