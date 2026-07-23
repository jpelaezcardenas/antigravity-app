# Review — Stage 7 (pwa-tenant-aware-screens)

**Verdict:** APPROVED

Commit reviewed: `db4cdc6` — `contexia-app/lib/config.ts` + `contexia-app/lib/api-client.ts` only
(confirmed via `git show --stat db4cdc6`; matches Stage 7 scope in
`openspec/changes/pwa-tenant-aware-screens/tasks.md` 7.1/7.2 exactly — Stage 7 is deliberately
just the typed clients, wiring into `ActiveAlerts`/`MonthlyLiquidityBridgeCard` is Stage 8/9, not
yet done and not claimed to be done).

## Checkpoints

- **Backend field-for-field match — Centinela** (`apps/backend/presentation/centinela_endpoints.py:60-68,212-234`):
  `CentinelaAlert` pydantic model = `rule_id`, `rule_name`, `severity: str`, `title`,
  `description`, `recommendation: Optional[str]`, `evidence: Dict[str, Any]`; response wrapper
  `CentinelaAlertsScopedResponse` = `alerts`, `alert_count`, `critical_count`, `warning_count`,
  `risk_level`, `source` (no `company_id`, confirmed at line 213-220). This matches
  `CentinelaAlert`/`CentinelaAlertsResponse` in `contexia-app/lib/api-client.ts:42-59`
  field-for-field, including nullability (`recommendation?: string | null`). [x]
- **Backend field-for-field match — Liquidity bridge** (`apps/backend/presentation/financials_endpoints.py:43-54,104-142`,
  `apps/backend/services/financials_service.py:122-144`): `_empty_liquidity_bridge()` and
  `compute_liquidity_bridge()` both return `initial_balance`, `inflows`, `outflows`,
  `final_balance`, `period` ("YYYY-MM"), `status` ("empty"/"ready"). Matches
  `LiquidityBridgeSnapshot` in `api-client.ts:61-68` exactly. [x]
- **Endpoint URLs resolve correctly**: `router.py:32` mounts `centinela_router` at
  `/centinela`, `router.py:51` mounts `financials_router` at `/financials`, `main.py:133` mounts
  `api_router` at `/api/v1`. Route decorators are `@router.get("/alerts")`
  (`centinela_endpoints.py:237`) and `@router.get("/liquidity-bridge")`
  (`financials_endpoints.py:104`), giving final paths `/api/v1/centinela/alerts` and
  `/api/v1/financials/liquidity-bridge` — exactly what `contexia-app/lib/config.ts:12-14` builds. [x]
- **Pattern consistency**: `fetchCentinelaAlerts`/`fetchLiquidityBridge`
  (`api-client.ts:70-100`) both call `authenticatedFetch(..., { method: "GET", headers: {
  "Content-Type": "application/json" } })` and throw `new ApiError(response.status, ...)` on
  `!response.ok`, identical shape to the pre-existing `fetchFinancials` (`api-client.ts:26-40`).
  No divergent error handling introduced. [x]
- **`npx tsc --noEmit`**: ran it myself in this worktree (`node_modules` already present) — clean,
  exit 0. [x]
- **No new npm dependency**: `git diff db4cdc6~1 db4cdc6 -- contexia-app/package.json
  contexia-app/package-lock.json` — empty diff. [x]
- **Scope discipline**: `git show --stat db4cdc6` shows exactly 2 files, 62 insertions, 0
  deletions. No `apps/backend/` file touched, `tasks.md` correctly left unchecked (reviewer's
  call to check off, not implementer's). [x]
- **`contexia-app/CLAUDE.md` data-bound pattern**: Stage 7 only adds the client-side plumbing;
  it does not yet wire any screen to `fetchCentinelaAlerts`/`fetchLiquidityBridge` (that's Stage
  8/9), so there's no new "data-bound screen" claim to reconcile against the CLAUDE.md exception
  list yet — correctly deferred, not skipped. Flagging as a forward note (not a blocker for
  Stage 7): whichever of Stage 8/9 lands first must add its screen to the "Pantallas data-bound"
  section of `contexia-app/CLAUDE.md` per the doc's own convention (5 prior exceptions listed
  there) — reviewer for that stage should check for it. [x] (informational, not required for this
  stage's approval)

## Required changes (if any)

None.
