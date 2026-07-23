# Task Group 1 — Backend: CRM WhatsApp Intake Endpoint (TDD)

Change: `openspec/changes/chatwoot-hermes-taty-bridge`
Tasks covered: 1.1, 1.2, 1.3, 1.4 (from `tasks.md`)

## Files touched

- `apps/backend/tests/test_crm_whatsapp_intake.py` (new) — failing tests written first:
  - `TestWhatsappIntakeService`: new phone creates a `crm_leads` row (`stage: "NUEVOS"`,
    `is_new: True`) and asserts the normalized phone + tenant_id in the insert payload; known
    phone is found (`is_new: False`, existing stage returned) and no insert is attempted.
  - `TestWhatsappIntakeEndpoint`: `POST /crm/leads/whatsapp-intake` returns 200 with the
    service's result for both new/known phones; an unauthenticated call with
    `settings.AUTH_ENFORCED = True` returns a 4xx and never touches the service layer
    (`mock_get_service.return_value.whatsapp_intake.assert_not_called()`).
- `apps/backend/services/crm_service.py`:
  - Added `_normalize_whatsapp_phone(whatsapp_phone: str) -> str` module-level helper — strips
    everything but digits, keeps a leading `+` if the input had one. No existing normalization
    helper in the codebase to reuse, so this is a new, simple, deterministic rule (documented
    inline).
  - Added `CrmService.whatsapp_intake(whatsapp_phone: str) -> Dict[str, Any]`: resolves the
    Cliente Cero tenant via the existing `_resolve_cliente_cero_tenant_id` (same pattern as
    `b2c_pipeline`/`advance_lead`), looks up `crm_leads` by normalized phone + tenant via
    `.maybe_single()` (matches the existing `get_tax_profile` 0-row-safe pattern), returns
    `{lead_id, is_new: False, stage}` if found, else inserts a new row with `stage: "NUEVOS"`
    and returns `{lead_id, is_new: True, stage: "NUEVOS"}`.
- `apps/backend/presentation/crm_endpoints.py`:
  - Added `WhatsappIntakeRequest(BaseModel)` with `whatsapp_phone: str`.
  - Added `POST /leads/whatsapp-intake` → `get_crm_service().whatsapp_intake(payload.whatsapp_phone)`.
    Uses the router-level `Depends(get_current_user)` already applied to the whole router — no
    second auth dependency added. Full endpoint path once mounted per `router.py`:
    `POST /api/v1/crm/leads/whatsapp-intake`.

## Test commands run

```
python -m pytest apps/backend/tests/test_crm_whatsapp_intake.py -v
```
Result (after implementation): **5 passed** (0 failed).

Before implementing, the same file was run against the pre-implementation state to confirm
TDD red: 4 failed (404 on the endpoint tests, `AttributeError`/`Mock` mismatch on the service
tests), 1 passed (the auth-rejection test — router-level auth is enforced regardless of route
existence, which is itself a useful confirmation that the router-level `Depends` protects
the new route too).

Regression run:
```
python -m pytest apps/backend/tests/test_crm_service.py apps/backend/tests/test_crm_service_b2b_writes.py \
  apps/backend/tests/test_crm_endpoints.py apps/backend/tests/test_crm_b2c_endpoints.py \
  apps/backend/tests/test_crm_whatsapp_intake.py -v
```
Result: **26 passed, 4 skipped** (the 4 skips are pre-existing in `test_crm_service.py`, unrelated
to this change — no regressions).

## Deviations from the task instructions

None. Implementation matches the spec scenarios in
`openspec/changes/chatwoot-hermes-taty-bridge/specs/crm-b2c-sell-machine/spec.md` exactly:
new phone → new row + `is_new: true`; known phone → existing `lead_id`/`stage` + `is_new: false`;
unauthenticated → 4xx, no row read or written (verified via mock `assert_not_called`).

Task group 2 (review/update existing unit test assumptions), group 3 (DB-state verification +
report), and group 4 (manual curl testing) are out of scope for this session per the leader's
delegation and are left for follow-up tasks.
