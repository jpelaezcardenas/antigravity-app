# Tasks: whatsapp-b2b-lead-bridge

**Change:** whatsapp-b2b-lead-bridge
**Status:** apply

---

## 1. Classifier: add `business_interest` category

- [x] 1.1 Write failing tests in `taty_lead_router` test suite: business-shaped messages classify
      as `business_interest`; every existing `sales_interest`/`payment_confirmation`/`unknown`
      fixture still classifies unchanged; a message matching both payment and business keywords
      classifies as `payment_confirmation`.
- [x] 1.2 Add `BUSINESS_INTEREST_KEYWORDS` and the 4th branch to `classify_lead_intent()`
      (`apps/backend/services/taty_lead_router.py:91-106`), checked after payment-confirmation and
      before sales-interest.
- [x] 1.3 Tests green.

## 2. `crm_leads.lead_type` column

- [x] 2.1 Create migration `00XX_crm_leads_lead_type.sql` — nullable `lead_type text` column, no
      default change to existing rows, numbered following the current highest migration in
      `apps/backend/migrations/`.
- [x] 2.2 Do not apply yet — apply only with explicit founder confirmation, same as every other
      migration in this repo.

## 3. Wire `lead_type` write into `route_lead_message`

- [x] 3.1 Write failing tests: a new lead classified `business_interest` gets `lead_type` set on
      creation; an existing lead re-classified `business_interest` gets `lead_type` set on update,
      no duplicate row; `lead_type` is not cleared by a later non-business message; `stage` is
      never advanced/regressed by a `business_interest` classification.
- [x] 3.2 Implement the write in `route_lead_message()` (`taty_lead_router.py:317-413`), reusing
      `CrmService.whatsapp_intake`/`advance_lead` — no independent Supabase query.
- [x] 3.3 Tests green.

## 4. Chatwoot auto-tagging: extend `_auto_tag_chatwoot()`

- [x] 4.1 **Before writing code**: confirm the exact live Chatwoot dropdown option strings for the
      business-signal `servicio_interes` and `tipo_contribuyente` values (admin UI or API) — do
      not hardcode a guessed string from the archived investigation's paraphrase.
- [x] 4.2 Write failing tests: `business_interest` sets the confirmed business-signal attribute
      values; a Chatwoot API failure during business tagging doesn't raise/block the reply (same
      fire-and-forget contract as the existing branches).
- [x] 4.3 Add `"business_interest"` to `_INTENT_TO_SERVICIO_INTERES` and the `tipo_contribuyente`
      branch in `apps/chatwoot-bridge/main.py:86-119`, using the confirmed values from 4.1.
- [x] 4.4 Tests green.

## 5. Non-goal guards (verify, don't build)

- [x] 5.1 Confirm by reading the code touched above that no path in this change creates a
      `tenants`/`b2b_clients` row, and that `hermes-hubspot-poller`'s Company/Deal sync rule is
      untouched.

## 6. Testing sweep

- [x] 6.1 Full backend test sweep for touched files green; no regression in the existing
      `taty-whatsapp-sales-router` spec's other requirements (sales/payment/unknown/reply-delivery/
      Wompi scenarios all still pass).

## Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: main
- Backend URL: https://antigravity-app-production-175a.up.railway.app

Tasks:
- [x] 11.1 Applied migration `0049_crm_leads_lead_type.sql` in Supabase, with explicit founder
      confirmation. Verified live: `lead_type text`, nullable, no default; 0/5 existing rows
      backfilled.
- [x] 11.2 git commit (`75ae6e0`) + merge `origin/main` (`73f781e`, resolving a real
      `ARCHITECTURE.md` decision-numbering collision) + push to main.
- [x] 11.3 Railway deploy active — deployment `79eb9162` SUCCESS, `/api/v1/health` returns 200.
- [x] 11.4 **Verified with a real WhatsApp conversation**, sent by the founder after the bridge
      restart. Confirmed live in Supabase: `crm_leads` row for phone `573504187902` has
      `lead_type="business_interest"`, `stage="PROSPECTOS"` (untouched by this classification, as
      designed), `updated_at=2026-09-09 23:43:41 UTC` — matches the founder's real WhatsApp
      message timestamp (18:43 America/Bogota) that said *"tengo empresa ya constituida...
      necesito... contadora interna"*. A companion normal Renta Natural message
      ("como me toca pagar impuestos") in the same conversation did not set `lead_type`, and
      Taty's reply used real prices from `pricing_catalog.py` (Decisión #25) without inventing a
      final number — confirms this change did not regress the existing Renta Natural funnel.
- [x] 11.5 Report created: `openspec/changes/whatsapp-b2b-lead-bridge/reports/2026-09-09-deployment.md`.
