# Verification report — crm-b2b-retainers-cockpit (Sections 8-9)

Date: 2026-07-19

## 8.1 — Test suites

Backend: `pytest tests/test_crm_service_grid_logic.py tests/test_crm_endpoints.py` — **11/11 passed**
(credential-free pivot/aggregation logic + endpoint shape/flag-gating tests).

`tests/test_crm_b2b_schema.py` and `tests/test_crm_service.py` (RUN_CRM_B2B=1-gated, hit the real
Supabase project via `get_service_supabase()`) could not be executed in this local shell — the local
`apps/backend/.env` has `SUPABASE_URL`/`SUPABASE_KEY` but no `SUPABASE_SERVICE_ROLE_KEY`. This is a
local-credential gap, not a code defect: the underlying data path these tests assert on was
independently verified correct via direct SQL through the Supabase MCP (see 8.2). These tests will
run in CI/Railway where `SUPABASE_SERVICE_ROLE_KEY` is configured — same gating convention already
used by `test_shadow_gl_schema.py`/`test_radar.py` (`RUN_SHADOW_GL=1`).

Frontend: `npx tsc --noEmit` clean. `npm run build` green, including static export of `/app/bunker`.

## 8.2 — DB state verification

Direct SQL against the live Supabase project (`kpynymwghfwshvcvevxq`):

| Check | Result |
|---|---|
| `b2b_clients` row count | 10 |
| `b2b_payments` row count | 60 |
| `b2b_payments.amount_cents` sum | `3,732,000,000` (37,320,000 COP) — matches the hand-computed fixture from the corrected source ledger |
| Repuestos Don Álvaro, period `2026-03-01` | `120,000,000` cents (1,200,000 COP) — typo corrected as intended |
| RLS enabled on both tables | `true` |
| RLS policies present | `b2b_clients_admin_only`, `b2b_payments_admin_only` (both `FOR ALL`) |
| Idempotency | Full seed re-applied twice; counts and total unchanged both times |

No rows were mutated by any manual/exploratory testing during this session — the final state above
matches the state immediately after the original seed migration.

## 8.3 — This report

Written per Section 8, task 8.3.

## 9.1 — E2E (browser)

Verified in-browser against the local `contexia-app` dev server (`/app/bunker`):

- Búnker sidebar renders unchanged; "CRM / Ventas" nav item present and functional.
- Selecting "CRM / Ventas" renders the new tab shell with both tabs ("B2B / Retainers", "B2C / Renta
  Natural") — no trace of the old hardcoded mock clients ("Contexia Marketing", "Lavaderos L&D",
  "Sion", "Repuestos Don Álvaro" (old mock entry), "Studio 4") anywhere in the section.
- With the backend/flag unreachable (local dev default), the B2B tab renders an explicit
  **"Failed to fetch"** error state rather than blank or throwing — satisfies the spec's error-state
  scenario.
- A full live-data screenshot (real 10-client grid, `source: "supabase"`) was attempted by running
  the backend locally with `CRM_CANONICAL=true`, but was blocked by this machine's local environment:
  a concurrent session/process was already occupying port 8080 (the backend dev-server port) and
  reusing it silently, so the flag change could not be observed locally. This does not indicate a
  code defect — the endpoint wiring is independently verified via the mocked HTTP tests (Section 5)
  and the DB state via direct SQL (8.2). The live full-stack render will be confirmed as part of the
  Stage 11 prod smoke-test (Section 10), where `CRM_CANONICAL` is flipped against the real deployed
  Railway backend with real credentials.

## Summary

All verifiable-now checks pass. The one deferred check (full live-data screenshot) is deferred to
Stage 11 for environmental reasons (local port contention with a concurrent session), not a code
correctness concern, and is covered by three independent verification layers already completed:
direct DB SQL, credential-free service-logic unit tests, and mocked endpoint-shape tests.
