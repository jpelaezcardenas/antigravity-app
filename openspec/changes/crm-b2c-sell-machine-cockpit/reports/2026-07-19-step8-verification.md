# Verification report — crm-b2c-sell-machine-cockpit (Sections 8-9)

Date: 2026-07-19

## 8.1 — Test suites

Backend: `pytest tests/test_crm_service_b2c_logic.py tests/test_crm_b2c_endpoints.py
tests/test_crm_service_grid_logic.py tests/test_crm_endpoints.py` — **26/26 passed**
(credential-free service-logic + mocked endpoint tests for both Change A and B, no regression).

`test_crm_b2c_schema.py` (RUN_CRM_B2B=1-gated, hits the real Supabase project) could not run in
this local shell — same missing `SUPABASE_SERVICE_ROLE_KEY` local-environment gap documented in
Change A's verification report. The underlying data path was independently verified correct via
direct SQL through the Supabase MCP (see 8.2).

Frontend: `npx tsc --noEmit` clean. `npm run build` green, including static export of `/app/bunker`.

## 8.2 — DB state verification

Direct SQL against the live Supabase project (`kpynymwghfwshvcvevxq`):

| Check | Result |
|---|---|
| `crm_leads` stage distribution | 1 lead in each of `NUEVOS`, `PROSPECTOS`, `POR_APROBAR`, `LISTOS_CONTADORA` |
| `crm_tax_profiles` row count | 4 (one per lead, `UNIQUE(lead_id)` holds) |
| `crm_wompi_transactions` rows | 2: `SEED-REF-POR-APROBAR-001` (`PENDING`), `SEED-REF-LISTOS-001` (`APPROVED`) |
| RLS enabled on all 3 new tables | `true` |
| RLS policies present | `crm_leads_admin_only`, `crm_tax_profiles_admin_only`, `crm_wompi_transactions_admin_only` |
| Idempotency | Full seed re-applied twice; counts unchanged both times |

No rows were mutated during this session's verification — final state matches the state
immediately after the seed migration.

## 8.3 — This report

Written per Section 8, task 8.3.

## 9.1 — E2E (browser, local dev server)

Verified against the local `contexia-app` dev server (`/app/bunker`):

- Búnker sidebar unaffected; "CRM / Ventas" nav item works as before.
- The "B2C / Renta Natural" tab now renders the real `B2cKanbanTab` component — the prior
  "Próximamente" placeholder text is completely gone (confirmed via full page-text extraction).
- With the local dev server pointed at the (not-yet-deployed) production backend, the tab
  correctly shows an explicit **"Failed to fetch"** error banner while still rendering the 4-column
  board shell (source defaults to `demo_fallback`, all columns show 0) — matches the established
  error-state pattern (`IdeasTab.tsx`, `B2bRetainersTab.tsx`): never blank, never throws.
- A full live-data walkthrough (real 4 seeded leads across the 4 columns, advance + approve-payment
  actions actually moving cards) requires the new `/crm/b2c/*` endpoints to be deployed — deferred
  to the Stage 11 prod smoke-test, same pattern as Change A's B2B verification.

## Summary

All verifiable-now checks pass: 26/26 tests, clean build, correct idempotent seed data, RLS
confirmed, and the frontend correctly replaces the placeholder and handles the pre-deploy
unreachable-backend case gracefully. The live full-loop walkthrough (advance a lead, approve a
payment, see it move columns in production) is deferred to Stage 11, where the new endpoints
become reachable.
