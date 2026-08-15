## 1. Fix phone normalization

- [x] 1.1 Write failing test: `_normalize_whatsapp_phone("+573001234567") == _normalize_whatsapp_phone("573001234567")`
- [x] 1.2 Fix `_normalize_whatsapp_phone` to always strip the `+` (digits-only canonical form)
- [x] 1.3 Write failing test: `whatsapp_intake` called with the no-`+` form finds a lead created via the `+` form (existing-lead path)
- [x] 1.4 Confirm 1.3 passes with the fix (no separate implementation needed — same fix covers it) — 12/12 tests passing

## 2. Fix wizard quiz lead capture

- [x] 2.1 Write failing test: `run_renta_diagnostico` with a phone matching an existing `crm_leads` row does not create a duplicate
- [x] 2.2 Write failing test: `run_renta_diagnostico` with a new phone creates a `crm_leads` row via `CrmService.whatsapp_intake` (correct columns, real tenant)
- [x] 2.3 Replace the broken direct `.insert()` in `run_renta_diagnostico` with a call to `CrmService().whatsapp_intake(whatsapp, full_name=nombre)` — 15/15 new tests passing; full backend suite run (816 passed, 39 pre-existing failures unrelated to this change — verified `test_wizard_auditoria_sombra.py` failures are a pre-existing httpx/starlette TestClient version mismatch, not caused by this edit)

## 3. One-time data merge (the known duplicate)

- [x] 3.1 Confirm which of the two duplicate leads (`ee0e86d3...` / `+573504187902`, `8d44107a...` / `573504187902`) has related `crm_wompi_transactions`/`crm_tax_profiles` rows — survivor had 1 Wompi transaction, duplicate had 1 tax profile
- [x] 3.2 Re-point any related rows from the duplicate to the survivor (older row, `ee0e86d3...`) — `crm_tax_profiles` row re-pointed via UPDATE
- [x] 3.3 Delete the duplicate `crm_leads` row — `8d44107a-293d-485d-b9aa-32246fac1f47` deleted
- [x] 3.4 Delete the duplicate's HubSpot Contact + Deal (Private App token, same pattern as the seed/test cleanup) — Deal `63963052401` + Contact `242195353915`, both `204`
- [x] 3.5 Confirm the survivor's Chatwoot cross-reference attributes are still correct (both duplicates already pointed at the same Chatwoot contact — no Chatwoot change expected) — unchanged, no action needed

## 4. Verification

- [x] 4.1 Run full backend test suite for the touched files — 15/15 new tests passing, no regressions from this change (39 pre-existing unrelated failures confirmed via a clean-file check)
- [x] 4.2 Live confirm: only 4 real leads remain in `crm_leads`, HubSpot has no orphaned duplicate Deal/Contact — confirmed via `SELECT count(*)` and the HubSpot delete 204s
- [x] 4.3 Next poller tick still succeeds (5-min scheduled run) with the reduced lead count — `leads_synced: 4, b2b_clients_synced: 10`, zero failures

## 5. Stage 11 — Deploy to Production (MANDATORY)

Tasks:
- [ ] 5.1 git commit + push to main (backend code change; no schema migration)
- [ ] 5.2 Verify Railway backend redeploys successfully
- [ ] 5.3 Create report: `openspec/changes/fix-whatsapp-phone-normalization-dedup/reports/YYYY-MM-DD-deployment.md`

## 6. Archive

- [ ] 6.1 Confirm all tasks above checked and Stage 11 report exists
- [ ] 6.2 Run `openspec archive` to close and archive this change
