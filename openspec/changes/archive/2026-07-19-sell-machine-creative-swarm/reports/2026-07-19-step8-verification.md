# Verification report — sell-machine-creative-swarm (Sections 8-9)

Date: 2026-07-19

## 8.1 — Test suites

Backend: `pytest tests/test_content_evaluator.py tests/test_copywriter_service.py
tests/test_sell_machine_service.py tests/test_sell_machine_endpoints.py
tests/test_crm_service_grid_logic.py tests/test_crm_endpoints.py tests/test_crm_service_b2c_logic.py
tests/test_crm_b2c_endpoints.py` — **50/50 passed** (33 new Sell Machine tests + 17 pre-existing
CRM tests re-run alongside, zero regression despite touching shared `router.py`/`config.py`).

Three unrelated test files (`test_profile_support.py`, `test_swarm_operators.py`,
`test_t11_integration.py`) fail to *collect* due to a pre-existing `ModuleNotFoundError: No module
named 'apps'` import-path issue — confirmed pre-existing and unrelated to this change (these files
import via an `apps.backend.*` absolute path that doesn't resolve from this test-runner's cwd;
untouched by any file in this change).

Frontend: `npx tsc --noEmit` clean. `npm run build` green, including static export of
`/app/bunker`.

## 8.2 — DB state

This change introduces **no new tables and no migration** — it writes only to the existing
`approval_queue` table via the existing `ApprovalQueueService.enqueue_draft()` function (confirmed
unmodified; see design.md Context). Live verification that a real `campaign_package` row lands
correctly is deferred to the Stage 11 production smoke-test (Section 10.6), since there is nothing
new to verify locally beyond what the credential-free unit tests in Section 4 already prove
(the mocked call reaches `enqueue_draft` with the correct `draft_type`/payload shape).

## 8.3 — This report

Written per Section 8, task 8.3.

## 9.1 — E2E (browser, local dev server)

Verified against the local `contexia-app` dev server (`/app/bunker`):

- Búnker sidebar shows the new "Sell Machine" item; existing sections (Dashboard, CRM/Ventas,
  Onboarding, Social Content Ops) unaffected.
- Selecting "Sell Machine" renders the section: header, "Generar Hooks" button, and "Campaign
  Packages Pendientes" panel showing the correct empty state ("Sin campaign packages pendientes").
- With the backend/flag unreachable (local dev default), the section shows an explicit
  **"Failed to fetch"** error banner rather than blank/crashing — matches the established
  error-state pattern from every prior data-bound screen.
- A full live-data walkthrough (generate hooks → evaluate → create a package → approve it,
  observing a real row appear/disappear from the pending list) requires the new
  `/sell-machine/*` endpoints and flag to be deployed — deferred to the Stage 11 prod smoke-test,
  same pattern as Changes A and B.

## Summary

All verifiable-now checks pass: 50/50 tests, clean build/typecheck, and the frontend correctly
handles the pre-deploy unreachable-backend case. The live full-loop walkthrough (generate → evaluate
→ package → approve, observed via the UI and confirmed via direct SQL on the `approval_queue`
table) is deferred to Stage 11, where the new endpoints and flag become reachable.
