# Deployment report — taty-whatsapp-sales-router

Date: 2026-07-19

## Summary

Change deployed and verified live in production. The WhatsApp Cloud API channel is reachable at
`https://antigravity-app-production-175a.up.railway.app/api/v1/channels/whatsapp/webhook`, and a
real fabricated inbound message correctly created and advanced a `crm_leads` row end-to-end through
the actual deployed code path (not a DB-layer simulation).

## Commit deployed

- `5652f27` — feat(taty-whatsapp): add WhatsApp sales router (Change D)

## Stage 11 steps executed

1. **6.1-6.2** — Committed on `feature/taty-whatsapp-sales-router`, fast-forward merged to `main`
   (no divergence), pushed.
2. **6.3 — Dark deploy confirmed.** Railway deployment `9d4a5396` (commit `5652f27`) reached
   `SUCCESS`. Confirmed `GET /api/v1/channels/whatsapp/webhook?hub.mode=subscribe&...` returned
   **404** while `WHATSAPP_CANONICAL` was still unset/`false` — the route is correctly gated
   behind the flag, matching `CRM_CANONICAL`/`SELL_MACHINE_CANONICAL`'s precedent.
3. **6.4** — No `contexia-app/` files touched (confirmed via `git status --short` before
   committing) — no sw.js bump, no frontend rebuild/sync, no Vercel deploy for this change.
4. **6.5** — Hub.challenge handshake verified live while dark (404, correctly gated — see 6.3).
5. **6.6 — Flag flip + full live smoke test.**
   - **Deployment instability**: this Stage 11 required **two manual `railway_redeploy` triggers**
     beyond the initial auto-deploy before the service came up reliably. The dark-deploy
     (`9d4a5396`) took an unusually long time to leave `502 Application failed to respond` (~15+
     minutes with no crash signature in logs — same benign pydantic `protected_namespaces`
     warning seen in every prior deploy, then silence). After the first redeploy (`bc563b91`)
     also sat at 502 for an extended period, a second redeploy (`625881a8`, triggered after
     flipping `WHATSAPP_CANONICAL=true`) finally came up and responded correctly. At no point did
     any deployment log show an actual crash/exception — locally, `python -c "import
     presentation.router"` imported cleanly with the new WhatsApp module, confirming this was not
     a code-level import error. This pattern (successful build, long silent gap, eventual
     recovery) matches but is notably worse than what Changes E and F saw (~5-12 min). Flagging
     this as a growing trend worth investigating if it continues on future deploys — possibly
     Railway platform-side cold-start variance, not a bug introduced by this change.
   - Set `WHATSAPP_CANONICAL=true` on Railway; after the redeploy settled, confirmed via `curl`:
     `GET /api/v1/channels/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=contexia-whatsapp-webhook&hub.challenge=12345`
     → `200`, body `12345` (the real default verify token, matching `meta_endpoints.py`'s pattern).
   - `POST /api/v1/channels/whatsapp/webhook` with a fabricated WhatsApp Cloud API payload (one
     text message, `wa_id="573000001111"`, name "Stage 11 Smoke Test Lead", text "Hola, quiero
     saber si me toca declarar renta este ano") → `{"ok": true, "events_processed": 1}`.
   - **Verified directly in Supabase** (`execute_sql` on project `kpynymwghfwshvcvevxq`):
     `SELECT * FROM crm_leads WHERE whatsapp_phone = '573000001111'` returned a real row —
     `full_name="Stage 11 Smoke Test Lead"`, `stage="PROSPECTOS"` (correctly advanced from the
     implicit `NUEVOS` default via the sales-interest keyword match), `source="whatsapp"`. This
     went through the **real deployed webhook → normalizer → lead router → CrmService** path, not
     a DB-layer simulation like Section 5's pre-deploy check.
   - **Important limitation, stated plainly**: this is a simulated/fabricated payload sent via
     curl, not a real inbound message from Meta's WhatsApp infrastructure. True end-to-end
     verification (a real WhatsApp user texting a real Business number) remains impossible until a
     real WhatsApp Business number + token + Meta Business verification exist — an open decision
     tracked in the Sell Machine plan, not resolved by this change.
   - **Decision on the demo row**: leaving it in place, matching the precedent set in Changes B/E/F
     — a harmless, useful production demonstration that the full pipeline works.
6. **6.7 — This report.**

## Accepted risks (carried from design.md)

- **Unverifiable end-to-end without a real WhatsApp number.** Confirmed as designed — see the
  limitation note above. All logic is proven; only the final "real Meta infrastructure calls this
  webhook" link is untested, by necessity.
- **Deterministic keyword classification is coarse**, consistent with Taty's existing
  `taty_intent_router.py` precedent — not a regression, and confirmed working correctly for the
  smoke test's message.
- **Defensive payload parsing** — confirmed via unit tests (Section 2) that malformed/status-only
  payloads return an empty event list rather than crashing; not separately re-tested live since
  the credential-free tests already cover this exhaustively.
- **`generate_wompi_link`/`verify_wompi_transaction` remain `NotImplementedError` stubs** — not
  exercised in this smoke test since the fabricated message used a sales-interest intent, not a
  payment-confirmation one. Confirmed via unit tests instead (Section 3).

## Verification evidence

- Railway deployment `625881a8-2959-4e39-9541-7979018c0834`: `SUCCESS`, confirmed responding.
- Live `GET /api/v1/channels/whatsapp/webhook` (hub.challenge): `200`, `12345`.
- Live `POST /api/v1/channels/whatsapp/webhook` (fabricated inbound message): `200`,
  `{"ok": true, "events_processed": 1}`.
- Supabase `crm_leads` row for `whatsapp_phone='573000001111'`: confirmed via direct SQL,
  `stage="PROSPECTOS"`, `source="whatsapp"`.
