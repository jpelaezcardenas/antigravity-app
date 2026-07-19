# Verification report — taty-whatsapp-sales-router (Section 5)

Date: 2026-07-19

## 5.1 — Test suites

Backend: `pytest tests/test_whatsapp_endpoints.py tests/test_taty_lead_router.py
tests/test_whatsapp_channel.py tests/test_operator_task_service.py
tests/test_operator_task_endpoints.py tests/test_sell_machine_service.py
tests/test_sell_machine_endpoints.py tests/test_content_evaluator.py
tests/test_copywriter_service.py tests/test_crm_service_grid_logic.py tests/test_crm_endpoints.py
tests/test_crm_service_b2c_logic.py tests/test_crm_b2c_endpoints.py` — **95/95 passed** (23 new
this-change tests + 72 pre-existing tests re-run alongside, zero regression).

Confirmed via `git status --short` that no `contexia-app/` files were touched — no
`tsc`/build/sw.js-bump step applies to Stage 11 for this change.

## 5.2 — DB state (direct Supabase verification, pre-deploy)

Simulated the full lead-scoped flow directly via SQL (the same pre-deploy pattern used in Change
F's Section 5.2), since the code isn't deployed yet:

- Created a disposable `crm_leads` row (`whatsapp_phone='573000000999'`, `stage='NUEVOS'`) —
  landed correctly.
- Simulated the sales-intent advance: `stage` updated to `PROSPECTOS` — correct.
- Simulated persona-field persistence: inserted a `crm_tax_profiles` row for that lead with
  `es_asalariado=true` — correct.
- Both rows deleted afterward — direct-SQL simulations of what the service will do, not artifacts
  of the real code path (which isn't deployed yet).

## 5.3 — This report

Written per Section 5, task 5.3.

## Summary

All verifiable-now checks pass: 95/95 tests, and the `crm_leads`/`crm_tax_profiles` write paths
this change will drive behave correctly under direct SQL simulation. The live full-loop walkthrough
via the actual deployed webhook (a fabricated inbound WhatsApp payload via curl) is deferred to
Stage 11, where the new routes become reachable. True end-to-end verification with a real inbound
WhatsApp message remains gated on a real WhatsApp Business number/token that does not exist yet
(documented as an accepted limitation, not glossed over).
