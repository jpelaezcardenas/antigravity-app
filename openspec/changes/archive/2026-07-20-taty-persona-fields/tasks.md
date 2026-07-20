## 1. Setup + verification

- [x] 1.1 Created branch `feature/taty-persona-fields`.
- [x] 1.2 Re-confirmed live `crm_tax_profiles.topes`/`.obligado_declarar` column types (jsonb/
      boolean, via Supabase MCP `information_schema.columns`) and re-read
      `_detect_persona_fields`/`route_lead_message` current bodies — no drift.

## 2. Peso-amount + category extraction — TDD

- [x] 2.1 Wrote failing tests for `_extract_topes_amount(message) -> Optional[Tuple[str, int]]`:
      plain numbers, "millones" suffix, "k" suffix, `patrimonio` keyword, no match when no category
      keyword present, no match when a category keyword has no adjacent amount. Confirmed failing
      (function/import didn't exist).
- [x] 2.2 Implemented `_extract_topes_amount` in `taty_lead_router.py` (category keyword regex +
      amount regex supporting plain/millones/k shapes; amount unit is plain COP pesos, not
      minor-units cents — distinct from `crm_wompi_transactions.amount_cents`'s convention, since
      `topes` isn't a payment amount).
- [x] 2.3 Green (6/6 new tests).

## 3. Merge into topes + compute obligado_declarar — TDD

- [x] 3.1 Wrote failing tests for the extended `_detect_persona_fields(message, existing_topes)`:
      merges a new topes entry with an existing `topes` dict (not overwrite); computes
      `obligado_declarar=True` when `ingresos`/`consignaciones` >= `UMBRAL_RENTA_COP`; computes
      `False` when below; leaves both untouched when no topes keyword+amount detected; confirmed
      `es_asalariado` detection still works unchanged alongside the new logic. Confirmed failing.
- [x] 3.2 Implemented the merge + threshold-compare logic. `route_lead_message` now fetches
      `tax_profile` unconditionally (before persona detection, not only after) to read
      `existing_topes` and pass it into `_detect_persona_fields` — reuses `get_tax_profile`/
      `update_tax_profile`/`_create_empty_tax_profile`, all unmodified.
- [x] 3.3 34/34 green in `test_taty_lead_router.py` (11 new + 23 pre-existing), zero regression.

## 4. Verify + DB state (MANDATORY before Stage 11)

- [x] 4.1 Ran the full targeted suite: 69/69 green across
      `test_taty_lead_router.py`/`test_crm_service_b2c_logic.py`/`test_crm_b2c_endpoints.py`/
      `test_whatsapp_channel.py`/`test_whatsapp_endpoints.py`/`test_document_storage_service.py`,
      zero regression.
- [x] 4.2 Wrote `openspec/changes/taty-persona-fields/reports/2026-07-20-step4-verification.md`.

## 5. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [x] 5.1 Committed (`4ef3df8`), fast-forward merged to `main` (confirmed no divergence via
      `git merge-base`), pushed.
- [x] 5.2 Railway deploy of `4ef3df8` reached `SUCCESS`. No new flag — reuses
      `WHATSAPP_CANONICAL`.
- [x] 5.3 **Live smoke test found a real bug on first attempt**: POSTing a fabricated WhatsApp
      message for a lead with no existing tax profile returned `500`
      (`postgrest.exceptions.APIError: PGRST116` — `CrmService.get_tax_profile`'s `.single()`
      raised on 0 rows, a pre-existing bug only now exposed because this change calls
      `get_tax_profile` unconditionally). Fixed via `.maybe_single()` (commit `2fe9854`),
      redeployed, then confirmed via Supabase SQL: a message mentioning consignaciones of 80M
      correctly set `topes={"consignaciones":80000000}`/`obligado_declarar=true`; a message
      mentioning ingresos of 10M correctly set `topes={"ingresos":10000000}`/
      `obligado_declarar=false`. All test leads/profiles cleaned up.
- [x] 5.4 Created deployment report at
      `openspec/changes/taty-persona-fields/reports/2026-07-20-deployment.md`.

## 6. Archive

- [x] 6.1 Synced the MODIFIED `taty-whatsapp-sales-router` delta into `openspec/specs/` (merged
      into the existing spec file), archived via `git mv` to
      `openspec/changes/archive/2026-07-20-taty-persona-fields/`.
