# Step 4 verification — taty-persona-fields

Date: 2026-07-20

## Test results

Full targeted suite, 69/69 green, zero regression:

```
tests/test_taty_lead_router.py .......................... (34)
tests/test_crm_service_b2c_logic.py ....
tests/test_crm_b2c_endpoints.py ....
tests/test_whatsapp_channel.py ..........
tests/test_whatsapp_endpoints.py ....
tests/test_document_storage_service.py ...
```

## Scope of the change

`services/taty_lead_router.py`:
- `_extract_topes_amount(message) -> Optional[Tuple[str, int]]` (new): detects a
  consignaciones/ingresos/compras/patrimonio category keyword plus an adjacent peso amount
  (plain number, "millones" suffix, or "k" suffix).
- `_detect_persona_fields(message, existing_topes=None)` (extended): now merges a detected topes
  entry into `existing_topes` and computes a preliminary `obligado_declarar` signal (never a legal
  determination — internal/contadora use only, per design.md Non-Goals) against
  `core.constants.UMBRAL_RENTA_COP` (~$69.7M COP for 2026).
- `route_lead_message` (modified call site): now fetches `tax_profile` unconditionally before
  persona detection (previously only inside the `if persona_fields:` branch) so the existing
  `topes` can be read and passed through — no behavior change for messages with no persona
  signal, confirmed by the full pre-existing test suite still passing unmodified.

## No migration

`crm_tax_profiles.topes` (jsonb) and `.obligado_declarar` (boolean) already existed live —
confirmed via `information_schema.columns` during the proposal phase. No DDL in this change.

## Verified no drift

`contexia-app/` untouched (frontend not in scope). No other Change H/I files touched besides
`taty_lead_router.py` and its test file.
