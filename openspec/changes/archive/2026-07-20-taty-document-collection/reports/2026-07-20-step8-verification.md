# Verification report — taty-document-collection (Section 8)

Date: 2026-07-20

## 8.1 — Test suites

Backend: full targeted suite across `test_taty_lead_router.py`, `test_whatsapp_channel.py`,
`test_whatsapp_endpoints.py`, `test_document_storage_service.py`, `test_crm_service_b2c_logic.py`,
`test_crm_b2c_endpoints.py`, `test_crm_service_grid_logic.py`, `test_crm_endpoints.py`,
`test_operator_task_service.py`, `test_operator_task_endpoints.py`, `test_sell_machine_service.py`,
`test_sell_machine_endpoints.py`, `test_telemetry_service.py`, `test_telemetry_endpoint.py` —
**111/111 passed** (30 new/rewritten this-change tests + 81 pre-existing tests re-run alongside,
zero regression).

Confirmed via `git status --short` no `contexia-app/` files touched — backend-only change.

## 8.2 — DB state and Storage verification (direct, pre-deploy)

**Critical finding during this step**: the live `crm_tax_profiles.rut_status`/`extractos_status`
columns already had CHECK constraints restricting values to `('pending', 'collected')` only — not
visible from `information_schema.columns`, discovered only when a test insert with `'requested'`
failed with a constraint violation. One existing seeded row already used `collected`. The
migration (`0026_crm_tax_documents.sql`) was amended to `ALTER` both constraints, adding
`'requested'` and reusing `'collected'` as the terminal value — the design's original word choice
of `'received'` was replaced throughout the codebase and OpenSpec artifacts to match.

With the corrected vocabulary, verified live:
- Created a disposable `crm_leads` row directly at `stage='LISTOS_CONTADORA'` (simulating an
  already-approved payment) and a `crm_tax_profiles` row with `rut_status='requested'` — both
  landed correctly.
- **Storage bucket verified via real HTTP calls to the Supabase Storage REST API** (using the
  service-role key, not just SQL introspection): uploaded a real test file to
  `crm-tax-documents/test-verification/rut.txt` (`201`-equivalent success), generated a signed URL
  and confirmed it returns the real file content (`200`), confirmed the bucket is genuinely
  private — the public object path returns `{"error":"Bucket not found"}` (Supabase's storage API
  reports private buckets as not-found on the public route, correctly refusing unauthenticated
  access). Test file and disposable rows all cleaned up afterward.

## 8.3 — This report

Written per Section 8, task 8.3.

## Summary

All verifiable-now checks pass: 111/111 tests, and the Storage bucket's privacy was proven with a
real upload + signed URL + blocked-public-access round trip (not merely a mocked test). The
critical vocabulary correction (`collected` instead of `received`, discovered via a live CHECK
constraint) is now consistent across code, tests, and OpenSpec artifacts. The live full-loop
WhatsApp document flow (a fabricated inbound document message triggering `route_lead_document`
through the real deployed webhook) is deferred to Stage 11 — logic-only, since no real WhatsApp
Business number exists yet (same accepted limitation as Change D).
