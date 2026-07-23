# Stage 7 — Frontend data clients for alerts + liquidity bridge

## Task

`openspec/changes/pwa-tenant-aware-screens/tasks.md` Stage 7: add typed API client
support (`contexia-app/lib/config.ts` + `contexia-app/lib/api-client.ts`) for the two
new backend routes added in Stage 2 (`GET /api/v1/centinela/alerts`) and Stage 3
(`GET /api/v1/financials/liquidity-bridge`), following the existing
`fetchFinancials`/`FinancialsSnapshot`/`ApiError` pattern exactly.

## Files touched

- `contexia-app/lib/config.ts` — added `centinelaAlerts` and `liquidityBridge` to
  `API_ENDPOINTS`.
- `contexia-app/lib/api-client.ts` — added `CentinelaAlert`, `CentinelaAlertsResponse`,
  `LiquidityBridgeSnapshot` interfaces + `fetchCentinelaAlerts()` /
  `fetchLiquidityBridge()`, using the same `authenticatedFetch` + `ApiError` pattern as
  `fetchFinancials`.

## Real backend response shapes (verified against source, not assumed)

Read `apps/backend/presentation/centinela_endpoints.py` (route `GET /alerts`, response
model `CentinelaAlertsScopedResponse`) and `apps/backend/presentation/financials_endpoints.py`
(route `GET /liquidity-bridge`, plain dict returns) directly — my draft in the task
prompt was close but not exact. Differences from the draft:

**Centinela alerts** — backend's `CentinelaAlert` pydantic model has NO `id` or
`created_at` fields (my draft guessed those). Actual fields: `rule_id`, `rule_name`
(missing from my draft), `severity: str` (not a literal union — backend allows
`info`/`warning`/`critical` as plain strings, not type-enforced), `title`,
`description`, `recommendation: Optional[str]` (missing from my draft), `evidence:
Dict[str, Any]` (missing from my draft). Top-level response
(`CentinelaAlertsScopedResponse`) has no `company_id` (unlike the sibling
`/alerts/{company_id}` route) — matches the draft's `alerts`/`alert_count`/
`critical_count`/`warning_count`/`risk_level`/`source` fields exactly.

**Liquidity bridge** — `_empty_liquidity_bridge()` and `compute_liquidity_bridge()`
return exactly `initial_balance`, `inflows`, `outflows`, `final_balance`, `period`
(`"YYYY-MM"`), `status: "ready"|"empty"` — matches the draft exactly, no changes needed.

## Final TypeScript interfaces (contexia-app/lib/api-client.ts)

```ts
export interface CentinelaAlert {
  rule_id: string;
  rule_name: string;
  severity: string; // "info" | "warning" | "critical"
  title: string;
  description: string;
  recommendation?: string | null;
  evidence: Record<string, unknown>;
}

export interface CentinelaAlertsResponse {
  alerts: CentinelaAlert[];
  alert_count: number;
  critical_count: number;
  warning_count: number;
  risk_level: string; // "none" | "low" | "medium" | "high" | "critical"
  source: string; // "supabase" — this route never demo-falls-back
}

export interface LiquidityBridgeSnapshot {
  initial_balance: number; // COP minor units
  inflows: number; // COP minor units
  outflows: number; // COP minor units
  final_balance: number; // COP minor units
  period: string; // "YYYY-MM"
  status: "ready" | "empty";
}

export async function fetchCentinelaAlerts(): Promise<CentinelaAlertsResponse>
export async function fetchLiquidityBridge(): Promise<LiquidityBridgeSnapshot>
```

Both functions call `authenticatedFetch(API_ENDPOINTS.<endpoint>, { method: "GET",
headers: { "Content-Type": "application/json" } })` and throw `ApiError(response.status,
...)` on `!response.ok`, identical to `fetchFinancials`.

## `contexia-app/lib/config.ts` additions

```ts
export const API_ENDPOINTS = {
  financials: `${API_BASE_URL}/api/v1/financials`,
  centinelaAlerts: `${API_BASE_URL}/api/v1/centinela/alerts`,
  liquidityBridge: `${API_BASE_URL}/api/v1/financials/liquidity-bridge`,
};
```

## Verification

`node_modules` was not present in this worktree (only `contexia-app/lib/` is exempted
from `.gitignore` per repo history — see CLAUDE.md §9 incident notes); ran
`npm install --no-audit --no-fund` in `contexia-app/` to install deps locally (not
committed — `node_modules/` stays gitignored), then:

```
$ cd contexia-app && npx tsc --noEmit
(no output — clean, exit 0)
```

No new npm dependencies were added to `package.json`/`package-lock.json` — only
`npm install` to materialize the already-declared devDependency (`typescript`) so
`tsc` could run in this worktree.

## Scope discipline

Only `contexia-app/lib/config.ts` and `contexia-app/lib/api-client.ts` were touched.
`git status --short` before commit showed exactly those 2 files modified, nothing else
(node_modules is gitignored, no other tracked files changed by `npm install`). No
`apps/backend/` file was edited. `tasks.md` was NOT checked off (per instructions —
that's the reviewer's/leader's call).

## Commit

```
db4cdc6 feat(pwa-tenant-aware-screens): frontend data clients for alerts + liquidity bridge
 2 files changed, 62 insertions(+)
```
