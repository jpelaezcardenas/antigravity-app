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

- [ ] 4.1 Commit + merge to `main` (check for divergence) + push.
- [ ] 4.2 Confirm Railway deploy green. No new flag — reuses `WHATSAPP_CANONICAL`.
- [ ] 4.3 Live smoke test (logic-only, no real WhatsApp number — same accepted limitation as
      every Taty change this session): create a real disposable test lead, POST a fabricated
      WhatsApp text-message webhook, confirm `200` and (via Railway logs) that
      `send_whatsapp_message` was actually invoked with the lead's phone and a non-empty reply,
      confirming it fails gracefully (no crash) since `WHATSAPP_TOKEN` is unset. Clean up test
      data.
- [ ] 4.4 Create deployment report at
      `openspec/changes/wire-whatsapp-reply-sending/reports/YYYY-MM-DD-deployment.md`.

## 5. Archive

- [ ] 5.1 Sync the ADDED `taty-whatsapp-sales-router` requirement into `openspec/specs/` (append
      to the existing spec file), archive via `git mv` once Stage 11 is confirmed complete.
