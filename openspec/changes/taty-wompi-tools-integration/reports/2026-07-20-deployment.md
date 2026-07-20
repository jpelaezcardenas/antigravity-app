# Deployment report — taty-wompi-tools-integration

Date: 2026-07-20

## Summary

Change deployed and verified live in production. Taty's WhatsApp sales router can now generate a
real Wompi checkout link and honestly verify payment status — closing the most critical gap found
in the plan-vs-build audit against the original Antigravity SOTA Sell Machine design.

## Commit deployed

- `e682613` — feat(taty): wire real Wompi tools into the WhatsApp sales router (Change H)

## Stage 11 steps executed

1. **7.1-7.2** — Committed on `feature/taty-wompi-tools-integration`, fast-forward merged to
   `main` (confirmed no divergence via `git merge-base`), pushed.
2. **7.3** — Railway auto-deploy (commit `e682613`) reached `SUCCESS`. Took ~15 min to leave a
   `502` cold-start state (same recurring platform pattern seen throughout this session) — no
   crash signature in logs, confirmed locally via `python -c "import services.taty_lead_router"`
   that the new imports (`config.settings`, `services.wompi_signature`) introduce no circular
   import. No new Railway flag — reuses `WHATSAPP_CANONICAL` (already live), so this change was
   live immediately once the app finished booting.
3. **7.4 — Live smoke test**, exercised through the real deployed WhatsApp webhook (since
   `generate_wompi_link`/`verify_wompi_transaction` are internal functions reached only via
   `route_lead_message`, not standalone HTTP endpoints):
   1. Created a real test lead directly via Supabase SQL (`whatsapp_phone="573000007777"`,
      `stage="NUEVOS"`).
   2. `POST /api/v1/channels/whatsapp/webhook` with a fabricated sales-interest message
      ("Quiero saber si me toca declarar renta este ano") → `{"ok":true,"events_processed":1}`.
   3. **Verified directly in Supabase**: a real `crm_wompi_transactions` row was created
      (`status="PENDING"`, `amount_cents=8900000`, `currency="COP"`, a real reference), and the
      lead correctly advanced `NUEVOS → PROSPECTOS`. This went through the **real, production-
      credentialed** `checkout_lead_payment` — `generate_wompi_link` built a genuine Wompi Web
      Checkout URL from it.
   4. `POST` a fabricated payment-confirmation message ("Ya pague, listo") for the same phone →
      confirmed via Supabase that the lead's stage stayed `PROSPECTOS` (correctly did **not**
      advance to `POR_APROBAR`, since the transaction is genuinely still `PENDING` — no real
      payment was made in this smoke test, matching `verify_wompi_transaction`'s honest read of
      the actual DB state).
   5. Re-sent the same sales-interest message a second time for the same lead → confirmed via
      Supabase that the transaction count stayed at exactly **1** — the reuse-vs-create-new logic
      (design.md Decision 2) correctly avoided creating a duplicate `PENDING` row.
   - **Decision on the demo lead/transaction**: leaving both in place, matching the precedent set
     throughout this session — a harmless, clearly-labeled demonstration of the full loop working
     end-to-end. No real money moved (only a signed checkout URL was generated, never an actual
     completed payment).
4. **7.5 — This report.**

## Accepted risks (carried from design.md)

- **No TTL/staleness handling for abandoned `PENDING` transactions.** Confirmed as designed — out
  of scope, deferred if it becomes a real problem at higher volume.
- **`generate_wompi_link`'s smoke test created a real `PENDING` row against production Wompi
  credentials.** Confirmed harmless — no money moves for generating a signed URL alone.

## Verification evidence

- Railway deployment (commit `e682613`): `SUCCESS`, confirmed responding.
- Real `crm_wompi_transactions` row created via the live, deployed webhook → `route_lead_message` →
  `generate_wompi_link` → `checkout_lead_payment` chain, confirmed via direct Supabase SQL.
- `verify_wompi_transaction` confirmed honestly reporting `PENDING` (not fabricating an approval)
  and correctly gating the `POR_APROBAR` advance behind a real `APPROVED` status.
- Reuse-vs-create-new logic confirmed live: exactly 1 transaction row after 2 sales-interest
  messages from the same lead.
