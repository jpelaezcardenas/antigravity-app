## 1. Setup + verification (no code — confirm this stays true)

- [x] 1.1 Re-confirmed live Railway env vars: still all sandbox (`WOMPI_ENV=sandbox`,
      `WOMPI_PUBLIC_KEY=pub_test_...`, `WOMPI_PRIVATE_KEY=prv_test_...`,
      `WOMPI_INTEGRITY_SECRET=test_integrity_...`, `WOMPI_EVENTS_SECRET=test_events_...`) — no
      drift since the change was proposed.
- [x] 1.2 Re-confirmed `validate_wompi_config()`, `checkout_lead_payment`, `handle_wompi_webhook`,
      and the checkout/webhook endpoints require zero code changes (unchanged since design.md).
- [x] 1.3 Re-confirmed `WOMPI_BASE_URL` is genuinely unreferenced anywhere in
      `apps/backend/**/*.py` outside its own declaration.

## 2. FOUNDER ACTION — obtain production credentials (manual, outside any tool's reach)

- [x] 2.1 **Juan David**: logged into the Wompi merchant dashboard in production mode (Desarrollo:
      Programadores > Llaves del API / Secretos).
- [x] 2.2 **Juan David**: copied the 4 production credentials (`pub_prod_...`, `prv_prod_...`,
      integrity secret, events secret).
- [x] 2.3 **Juan David**: shared them via screenshot; agent read the 4 values directly from the
      image and set them via `railway_set_variable` (not retyped as chat narrative).

## 3. FOUNDER ACTION — register the production webhook (manual, outside any tool's reach)

- [x] 3.1 **Juan David**: registered the webhook URL in Wompi's production "URL de Eventos" field:
      `https://antigravity-app-production-175a.up.railway.app/api/v1/crm/wompi/webhook` (was
      initially empty in the dashboard screenshot — agent caught this and asked Juan David to fill
      it in and save BEFORE proceeding to Section 4, per design.md's risk-ordering).
- [x] 3.2 **Juan David**: confirmed the registration was saved ("ya") before Section 4 proceeded.

## 4. Config flip — Railway env vars

- [x] 4.1 Set `WOMPI_ENV=production` and the 4 production credentials via `railway_set_variable`.
      Did NOT touch `WOMPI_BASE_URL` (confirmed dead config, design.md Decision 1 — still reads
      the old sandbox URL value, harmless since nothing references it).
- [x] 4.2 Confirmed the resulting Railway deployment reached `SUCCESS` and the app responded
      (`GET /api/v1/sell-machine/tasks/pending` → 200) — this proves `validate_wompi_config()`
      passed with the new production values. Required 2 manual `railway_redeploy` triggers after
      an unusually long silent gap (~15+ min total, no crash signature in logs) — the same Railway
      platform slow-boot pattern observed on the last several changes this session, not a
      config/code issue (confirmed no `ValueError` traceback from `validate_wompi_config` in any
      deployment's logs).
- [x] 4.3 Sanity-checked via `railway_list_variables`: all 5 Wompi vars read as expected
      (`WOMPI_ENV=production`, `pub_prod_.../prv_prod_...`, `prod_integrity_.../prod_events_...`,
      `WOMPI_BASE_URL` unchanged from its sandbox value, confirmed harmless/dead).

## 5. STOP — real-money verification (FOUNDER ACTION, never agent-executed)

- [ ] 5.1 **STOP.** The agent does not execute, simulate, or fabricate this step. Ask Juan David to
      complete ONE real Renta Natural checkout (real card, real money) through the live product
      flow, using the now-production-configured checkout.
- [ ] 5.2 **Juan David**: report back the resulting Wompi transaction reference (or the
      `crm_leads`/lead identifier used) once the payment completes.

## 6. Verify + deployment report

- [ ] 6.1 Once Juan David reports the transaction, confirm via direct Supabase SQL that the
      corresponding `crm_wompi_transactions` row is `status="APPROVED"` with a genuine
      (non-`test_`-prefixed) `wompi_transaction_id`.
- [ ] 6.2 Create deployment report at
      `openspec/changes/wompi-production-go-live/reports/YYYY-MM-DD-deployment.md`, including: the
      confirmed real transaction's reference/id (status only, no card data), the `WOMPI_BASE_URL`
      dead-config observation, and the rollback plan (revert 4 env vars to sandbox values).

## 7. Archive

- [ ] 7.1 Sync the `wompi-production-go-live` capability into `openspec/specs/` (using `git mv` for
      the archive move, per the process fix established after Change A's tree-drift incident) and
      archive this change once the real-payment verification is confirmed complete.
