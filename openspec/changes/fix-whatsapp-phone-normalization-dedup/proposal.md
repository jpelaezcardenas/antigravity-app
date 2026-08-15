## Why

`_normalize_whatsapp_phone` (`apps/backend/services/crm_service.py:60`) was introduced to make `"+57 300 123 4567"` and `"573001234567"` resolve to the same lead — but its own logic preserves whichever `+`-prefix state the caller passed in (`has_plus` branch), so the two forms never actually normalize to the same string. Found live 2026-08-15 while verifying the `hubspot-sync-renta-natural`/`chatwoot-hubspot-supabase-cross-ids` pollers: two `crm_leads` rows (`+573504187902` and `573504187902`) turned out to be the same real WhatsApp customer, confirmed by both mapping to the same Chatwoot contact. No existing test exercises the mixed-`+`-format case, which is why this shipped unnoticed.

## What Changes

- Fix `_normalize_whatsapp_phone` so both forms collapse to one canonical representation (digits only, no `+`) — matches how `crm_leads.whatsapp_phone` values are already stored elsewhere in the table (the working majority of rows have no `+`).
- Add test coverage for the exact gap that let this ship: mixed `+`/no-`+` input for both the new-lead and existing-lead paths of `whatsapp_intake`.
- One-time data fix: merge the two known-duplicate `crm_leads` rows (`ee0e86d3-725e-405a-b61c-fec58297630b` / `+573504187902` and `8d44107a-293d-485d-b9aa-32246fac1f47` / `573504187902`) into a single row, carrying over any related `crm_wompi_transactions`/`crm_tax_profiles` rows, and clean up the now-duplicate HubSpot Contact/Deal.

## Capabilities

### New Capabilities
- `crm-lead-phone-dedup`: documents the correct phone-normalization contract for `crm_leads` intake (both the WhatsApp and landing-quiz paths) so this class of bug is testable and can't silently regress.

### Modified Capabilities
(none — `hubspot-lead-sync`'s sync behavior is unaffected; it just receives correctly-deduplicated `crm_leads` rows going forward.)

## Impact

- `apps/backend/services/crm_service.py`: `_normalize_whatsapp_phone` logic fix.
- `apps/backend/tests/test_crm_whatsapp_intake.py`: new regression tests for mixed-format phone matching.
- One-time Supabase data fix on `crm_leads`/`crm_wompi_transactions`/`crm_tax_profiles` (no schema/migration — a data DELETE/UPDATE, not DDL).
- One-time HubSpot cleanup: delete the duplicate Contact+Deal via the Private App token, same pattern used to clean up seed/test leads in `hubspot-sync-renta-natural`.
- No Chatwoot change needed — both duplicate leads already resolved to the same Chatwoot contact (id 2), confirmed live.
