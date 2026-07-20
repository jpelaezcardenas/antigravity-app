## 1. Setup + verification

- [x] 1.1 Created branch `feature/wire-whatsapp-reply-sending`.
- [x] 1.2 Re-confirmed `whatsapp_webhook`'s current body, `route_lead_message`'s return shape, and
      `send_whatsapp_message`'s signature/graceful-degradation pattern — no drift.

## 2. Wire the send — TDD

- [x] 2.1 Wrote failing tests: a text message event routes to `route_lead_message`, and
      `send_whatsapp_message` is called with `event["account_id"]` and the computed `reply`;
      `send_whatsapp_message` returning `False` still yields a `200` response; a document/media
      event does NOT additionally call `send_whatsapp_message` from the handler (unaffected —
      `route_lead_document` sends internally). Confirmed failing.
- [x] 2.2 Implemented the wiring in `whatsapp_endpoints.py`'s `whatsapp_webhook` handler.
- [x] 2.3 9/9 green in `test_whatsapp_endpoints.py` (3 new + 6 pre-existing), zero regression.

## 3. Verify + DB state (MANDATORY before Stage 11)

- [x] 3.1 Ran the full targeted suite: 61/61 green across
      `test_whatsapp_endpoints.py`/`test_whatsapp_channel.py`/`test_taty_lead_router.py`, zero
      regression.
- [x] 3.2 Wrote `openspec/changes/wire-whatsapp-reply-sending/reports/2026-07-20-step3-verification.md`.

## 4. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [x] 4.1 Committed (`7def583`), fast-forward merged to `main`, pushed.
- [x] 4.2 Railway deploy `83489932` reached `SUCCESS`. No new flag — reuses
      `WHATSAPP_CANONICAL`.
- [x] 4.3 **Live smoke test**: created a real disposable test lead, POSTed a fabricated WhatsApp
      text-message webhook (`"hola"`) → `200`, `events_processed:1`. Railway logs confirm
      `send_whatsapp_message: WHATSAPP_TOKEN/WHATSAPP_PHONE_NUMBER_ID not configured` — proves the
      send was actually attempted (reaching the credential check) and degraded gracefully, no
      crash. Test lead cleaned up.
- [x] 4.4 Created deployment report at
      `openspec/changes/wire-whatsapp-reply-sending/reports/2026-07-20-deployment.md`, including
      the full session wrap-up (7 changes closed).

## 5. Archive

- [x] 5.1 Synced the ADDED `taty-whatsapp-sales-router` requirement into `openspec/specs/`
      (appended to the existing spec file), archived via `git mv` to
      `openspec/changes/archive/2026-07-20-wire-whatsapp-reply-sending/`.
