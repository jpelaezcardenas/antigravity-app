## 1. Setup + verification

- [x] 1.1 Created branch `feature/taty-wompi-tools-integration`.
- [x] 1.2 Re-confirmed `checkout_lead_payment`/`handle_wompi_webhook`/`crm_wompi_transactions`
      columns by reading the live source + Supabase directly — no drift.
- [x] 1.3 Confirmed Wompi's Web Checkout URL format via `docs.wompi.co`: base
      `https://checkout.wompi.co/p/`, required params `public-key`, `currency`,
      `amount-in-cents`, `reference`, `signature:integrity` — matches design.md exactly.

## 2. `generate_wompi_link` — TDD

- [x] 2.1 Wrote tests: no existing transaction → calls `checkout_lead_payment`, builds a URL
      containing all 5 expected query params with the correct values; existing `PENDING`
      transaction → does NOT call `checkout_lead_payment` again, reuses the existing
      reference/amount/currency and recomputes the signature; existing `APPROVED` transaction →
      creates a fresh new transaction (decided: only `PENDING` is reused, any other status —
      `APPROVED`/`DECLINED`/`VOIDED`/none — creates a new one). Confirmed failing.
- [x] 2.2 Authored `_get_latest_transaction(lead_id)` + `_build_web_checkout_url(...)` +
      the real `generate_wompi_link` implementation in `taty_lead_router.py`.
- [x] 2.3 3/3 tests green.

## 3. `verify_wompi_transaction` — TDD

- [x] 3.1 Wrote tests: `APPROVED` transaction → returns `{"status": "APPROVED", ...}`; `PENDING` →
      returns `{"status": "PENDING", ...}`; no transaction → returns `{"status": None, ...}`.
      Confirmed failing.
- [x] 3.2 Authored the real `verify_wompi_transaction` implementation (reuses
      `_get_latest_transaction`).
- [x] 3.3 3/3 tests green.

## 4. Wire into `route_lead_message` — TDD

- [x] 4.1 Wrote tests: `sales_interest` reply now includes a checkout link (mocking
      `generate_wompi_link`); `payment_confirmation` with `APPROVED` advances to `POR_APROBAR` and
      confirms; `payment_confirmation` with `PENDING` asks to wait, no stage change;
      `payment_confirmation` with no transaction says so, no stage change. Confirmed failing (old
      hardcoded behavior).
- [x] 4.2 Updated `route_lead_message` to call the now-real tools instead of the old fixed replies.
- [x] 4.3 4/4 new tests green; no regression in existing `sales_interest`/persona-persistence
      tests from Change D.

## 5. Persona-state: independiente detection — TDD

- [x] 5.1 Wrote a test: a message containing an "independiente" signal sets `es_asalariado=False`
      via `_detect_persona_fields`. Confirmed failing.
- [x] 5.2 Added the `_INDEPENDIENTE_KEYWORDS` set and the symmetric `elif` detection branch.
- [x] 5.3 Test green. Full targeted suite (56 tests: `test_taty_lead_router.py` (18) +
      `test_whatsapp_endpoints.py` + `test_whatsapp_channel.py` + CRM suites) green, zero
      regression.

## 6. Verify + DB state (MANDATORY before Stage 11)

- [x] 6.1 Ran the full targeted suite: 56/56 green (18 in `test_taty_lead_router.py` + 38
      pre-existing, zero regression). Confirmed no `contexia-app/` files touched.
- [x] 6.2 Confirmed live in Supabase (via MCP): inserted an older `APPROVED` row then a newer
      `PENDING` row out of order for a disposable lead, confirmed the `ORDER BY created_at DESC
      LIMIT 1` query correctly returns the newest (`PENDING`) row — the exact logic
      `generate_wompi_link`'s reuse-vs-create-new decision depends on. Cleaned up.
- [x] 6.3 Wrote `openspec/changes/taty-wompi-tools-integration/reports/2026-07-20-step6-verification.md`.

## 7. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [ ] 7.1 Commit backend changes in scoped commits referencing this change id.
- [ ] 7.2 Merge to `main` (check for conflicts) and push.
- [ ] 7.3 Confirm Railway backend deploy completes green. No new flag — reuses
      `WHATSAPP_CANONICAL` (already live), so this change is live immediately on deploy.
- [ ] 7.4 Live smoke test: create/find a real test lead via direct Supabase SQL; call
      `generate_wompi_link(lead_id)` for real (this hits the live, production-credentialed
      `checkout_lead_payment` — creates one real `PENDING` `crm_wompi_transactions` row, no money
      moves since only a signed URL is generated, not a completed payment); confirm the URL's
      query params and that the signature recomputes identically from the same inputs; call
      `verify_wompi_transaction(lead_id)` and confirm it correctly reports `PENDING`; call
      `generate_wompi_link` again for the same lead and confirm via Supabase SQL that no duplicate
      row was created (reuse path).
- [ ] 7.5 Create deployment report at
      `openspec/changes/taty-wompi-tools-integration/reports/YYYY-MM-DD-deployment.md`, noting the
      real `PENDING` transaction row created during verification (harmless, no money moved) and the
      accepted risk of no TTL/staleness handling for abandoned `PENDING` rows.

## 8. Archive

- [ ] 8.1 Sync the `taty-whatsapp-sales-router` capability's updated spec into `openspec/specs/`
      (this is a MODIFIED delta, not a new capability — merge into the existing spec file) using
      `git mv` for the archive move, and archive this change once Stage 11 is confirmed complete
      and verified live.
