# Verification report — taty-wompi-tools-integration (Section 6)

Date: 2026-07-20

## 6.1 — Test suites

Backend: `pytest tests/test_taty_lead_router.py tests/test_whatsapp_endpoints.py
tests/test_whatsapp_channel.py tests/test_crm_service_grid_logic.py
tests/test_crm_service_b2c_logic.py tests/test_crm_endpoints.py tests/test_crm_b2c_endpoints.py` —
**56/56 passed** (18 in `test_taty_lead_router.py`, including 9 new/rewritten tests for the real
Wompi tools + independiente detection; 38 pre-existing tests re-run alongside, zero regression).

Confirmed via `git status --short` no `contexia-app/` files touched — backend-only change.

## 6.2 — DB state (direct Supabase verification, pre-deploy)

Created a disposable `crm_leads` row, then inserted two `crm_wompi_transactions` rows for it out
of chronological order (an older `APPROVED` row, then a newer `PENDING` row) to confirm
`_get_latest_transaction`'s query (`ORDER BY created_at DESC LIMIT 1`) correctly returns the
**newest** row regardless of status — returned `PENDING`/`new-ref-pending` as expected, not the
older `APPROVED` row. This is the exact query shape `generate_wompi_link`'s reuse-vs-create-new
logic depends on. Both rows and the lead cleaned up afterward.

## 6.3 — This report

Written per Section 6, task 6.3.

## Summary

All verifiable-now checks pass: 56/56 tests, and the live "latest transaction" query behaves
correctly under a real ordering scenario. The live full-loop walkthrough (calling
`generate_wompi_link`/`verify_wompi_transaction` against the real, production-credentialed
`checkout_lead_payment`) is deferred to Stage 11, where these functions are reachable via the
already-deployed WhatsApp webhook.
