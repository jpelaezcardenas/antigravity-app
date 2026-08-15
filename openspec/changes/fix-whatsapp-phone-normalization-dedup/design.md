## Context

Two independent bugs, found while investigating one real duplicate lead:

1. **`_normalize_whatsapp_phone`** (`crm_service.py:60-66`) preserves whichever `+`-prefix state the caller passed, so `"+573504187902"` and `"573504187902"` normalize to two different strings and never dedupe against each other, contrary to the function's own docstring claim.
2. **`wizard_service.run_renta_diagnostico`** (`wizard_service.py:243-257`) has its own direct, unrelated `crm_leads` insert with zero normalization and zero dedupe-lookup, using column names (`whatsapp`, `name`, `crm_stage`, `lead_source`, `notes`) that don't exist in the real `crm_leads` schema. Verified live: `SELECT source, count(*) FROM crm_leads GROUP BY source` returns only `whatsapp` (5 rows) — this insert has **never once succeeded** (PostgREST rejects unknown columns; the `except Exception` swallows the error and only logs it). Dead-on-arrival code, not a live risk today, but a landmine if the landing quiz ever gets real traffic.

## Goals / Non-Goals

**Goals:**
- Make `_normalize_whatsapp_phone` actually collapse both formats to one canonical value.
- Make the landing-quiz lead capture actually work, reusing the same correct, deduped, tenant-scoped path the WhatsApp channel already uses.
- Merge the two known-duplicate `crm_leads` rows into one, cleanly, including their HubSpot records.

**Non-Goals:**
- Not changing the `/wizard/renta-diagnostico` endpoint's request/response contract — only what happens to the CRM write internally.
- Not adding new columns to `crm_leads` to store quiz-specific diagnostic detail (income, patrimony, etc.) — that data has never been persisted anywhere real; persisting it is a separate, larger decision (new columns or a `notes`-equivalent) left for a future change if the founder wants it.

## Decisions

**1. `_normalize_whatsapp_phone` always drops the `+`.**
The majority of existing `crm_leads.whatsapp_phone` values have no `+` (digits only, e.g. `"573000001111"`). Standardizing on digits-only (no `+`) matches the existing majority and is simpler than forcing a `+` everywhere (which would require backfilling every existing row). Alternative considered: always add `+`. Rejected — touches more existing data for no functional benefit.

**2. `run_renta_diagnostico` routes through `CrmService.whatsapp_intake` instead of its own broken insert.**
This reuses the now-fixed normalization, the correct column names, the correct Cliente Cero tenant resolution (`_resolve_cliente_cero_tenant_id`, not the hardcoded string `"ctx-000000000"` which isn't even a valid tenant UUID), and — critically — the existing dedupe-by-phone lookup, so a lead who fills the quiz AND later messages WhatsApp with the same number lands in the same `crm_leads` row instead of two. The quiz's diagnostic detail (topes evaluation) is not persisted to `crm_leads` (see Non-Goals) — this fix makes lead *capture* work, not full diagnostic storage.

**3. Duplicate lead merge: keep the older row, migrate related rows, delete the newer duplicate.**
Between `ee0e86d3...` (`+573504187902`, created 2026-07-31) and `8d44107a...` (`573504187902`, created 2026-08-11), keep the older one as the survivor (first real contact with this customer) and re-point any `crm_wompi_transactions`/`crm_tax_profiles` rows from the newer duplicate to the survivor before deleting the duplicate. In HubSpot, delete the duplicate's Contact+Deal (same live-verified delete pattern used for seed/test leads in `hubspot-sync-renta-natural`) — the survivor's HubSpot records stay as-is since they're already correctly synced.

## Risks / Trade-offs

- **[Risk]** Changing `_normalize_whatsapp_phone`'s output format changes the stored value for any *future* insert of a `+`-prefixed phone. → **Mitigation**: existing rows are untouched by the code fix (only new/updated writes are affected); the one known-affected pair is fixed explicitly via the data-merge task below.
- **[Risk]** Routing the wizard through `CrmService.whatsapp_intake` means a wizard-submitted lead is now indistinguishable from a WhatsApp-submitted one via `source` (both land as `source='whatsapp'`, the column default). → **Accepted**: `whatsapp_intake` doesn't currently accept a `source` override, and no live behavior depends on distinguishing them today; a future change can add that if the founder wants to track quiz-origin leads separately.
