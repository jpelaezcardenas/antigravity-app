## Context

The consumer GPS Financiero app (`contexia-app`, Next.js `output:export`) is a mock-only demo: every screen renders from `lib/mock/*`, and its charter explicitly forbids backend/fetch/DB. The Overview/Pulso screen shows a hardcoded Caja Real of `$42.850.000` via `pulsoMock.cash`.

In parallel, the Shadow GL ingestion pipeline is live in production: manual CSV Siigo + DIAN XML uploads persist to `erp_journal_entries`, `erp_journal_lines`, and `dian_xml_documents` (Supabase project `kpynymwghfwshvcvevxq`), keyed by the Cliente Cero tenant `e2d30d09-6b96-4ebe-a79a-c6aff7a5df34`. There is an orphaned `GET /api/v1/financials` endpoint that reads a non-existent `company_financials` table with an unrelated id — nothing calls it and it would 500.

This design is the first vertical slice of converting the demo into a real data app: bind exactly one number (Caja Real) to live Shadow GL data, end-to-end, including deploy.

## Goals / Non-Goals

**Goals:**
- Compute the Pulso cash snapshot deterministically from `erp_journal_lines` for the Cliente Cero tenant and expose it via `GET /api/v1/financials`.
- Render the live Caja Real in the Overview `CashTodayCard` via client-side fetch, with loading / error / empty states (graceful fallback, never a blank screen).
- Deploy and verify the live value on `contexia.online/app/overview` (Stage 11).
- Establish the minimal, reusable frontend data-fetch pattern (API base URL config + typed client) for future slices.

**Non-Goals:**
- Fiscal / Radar / Patrimonio screens (stay on mocks — future slices).
- Any write path, auth, roles, or HITL (read-only snapshot).
- DB migrations or new tables (reads existing Shadow GL tables).
- Multi-tenant routing (Cliente Cero only, same constraint as existing agent endpoints).
- Precise accounting semantics beyond the agreed account-code rules (good-enough, plausible, deterministic).

## Decisions

**D1. Aggregate from `erp_journal_lines`, not a snapshot table.**
Caja Real = balance of bank account `1110` = `sum(debit_minor) - sum(credit_minor)` over all lines with `account_code = '1110'` for the tenant. Income (`ventas`) and outflow (`salidas`) sum credits/debits over income (`4100`,`4105`) and expense (`5xxx`,`6xxx`) accounts within a period.
- *Why over re-introducing `company_financials`:* avoids a denormalized snapshot that drifts from the ledger and needs a refresh job. The ledger is the single source of truth; aggregation is cheap at Cliente Cero volume.
- *Alternative considered:* a materialized view / nightly snapshot — deferred until volume justifies it (consistent with the deliberately-deferred sharding decision).

**D2. Account-code rules live in the backend, not the frontend.**
The frontend receives final COP minor-unit integers and a `status`. Classification (which accounts are bank/income/expense) is backend-owned so the rule has one home and the UI stays dumb.

**D3. Keep the endpoint path `GET /api/v1/financials` and its response shape additive.**
Preserve existing keys (`caja_real`, `dinero_disponible`, `status`) so any cached/embedded consumer still parses; add `ventas_periodo` / `salidas_periodo`. Tenant resolved server-side via `is_cliente_cero = true` (reuse the `_resolve_tenant_id` pattern from `shadow_gl_service`) — the client sends no id.

**D4. Client-side fetch in a `"use client"` card; static export stays.**
`output:export` produces a browser bundle; `fetch` runs client-side at runtime against the Railway backend. No SSR/server runtime is introduced. API base URL comes from a build-time `NEXT_PUBLIC_API_BASE_URL` (defaulting to the Railway prod URL) so local/prod differ cleanly.
- *Why over server components / ISR:* incompatible with `output:export`; client fetch is the minimal change.

**D5. Charter amendment is explicit and scoped.**
Update `contexia-app/CLAUDE.md`: data-bound screens MAY fetch read-only snapshots from the Contexia backend; mock-only remains the default for un-wired screens. This is a deliberate supersede, recorded so future agents don't "fix" the fetch back into a mock.

**D6. Resolve the source-of-truth branch before deploy.**
`contexia-app` lives only on worktree branch `temp-layout-fix`. The change must land that source on the canonical branch (merge/rebase into `main`) and document the build→`app/` sync step, so the deployed export is reproducible from `main`.

## Risks / Trade-offs

- **[Source on a non-canonical branch]** → Merge `temp-layout-fix` (contexia-app) into `main` as part of this change; treat the committed `app/` export as build output regenerated from `main`. Block Stage 11 until source-of-truth is on `main`.
- **[Static export caches stale bundle on `contexia.online/app`]** → Hard-refresh + verify the network call to `/api/v1/financials` fires and Caja Real ≠ the `$42.85M` mock; bust cache via the existing PWA bundle-versioning pattern.
- **[Backend returns 0 / empty for the tenant]** → Card shows an explicit empty state ("sin datos aún"), never a misleading mock. Treated as a real, valid state.
- **[CORS / mixed content]** → `ALLOWED_ORIGINS` already includes `contexia.online`; backend is HTTPS (Railway). Verify preflight in Stage 11.
- **[Account-code rules too simplistic]** → Accepted: this is a plausible MVP snapshot, not audited accounting. Documented in the spec so expectations are explicit; refine in later slices if needed.
- **[Anon key + own JWT, `auth.uid()` NULL]** → Read aggregation runs against existing Shadow GL tables the backend already reads; no new RLS surface. No service-role escalation introduced.

## Migration Plan

1. Backend (TDD): write failing tests for the aggregation → implement service + rewrite endpoint → green.
2. Frontend: add API client + base-URL config → wire `CashTodayCard` with loading/error/empty → keep other cards on mocks.
3. Land `contexia-app` source on `main` (D6); rebuild static export; sync `out/` → `app/`.
4. Deploy (Stage 11): push `main` → Railway redeploy backend; publish static export; verify live Caja Real; write deployment report.
5. Rollback: revert the `app/` export commit (restores mock card) and the endpoint commit independently — frontend and backend are decoupled.

## Open Questions

- Exact `dinero_disponible` definition vs `caja_real` (e.g., minus committed/withheld) — default to equal for the MVP unless a simple rule is provided.
- Period window for `ventas`/`salidas` (current month vs trailing 30 days) — default to current calendar month.
- Who/what runs the `contexia-app` build → `app/` sync today (manual vs script) — confirm during Stage 11 so it's reproducible.
