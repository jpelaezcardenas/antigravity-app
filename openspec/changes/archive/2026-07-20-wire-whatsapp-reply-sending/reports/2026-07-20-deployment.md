# Deployment report — wire-whatsapp-reply-sending

Date: 2026-07-20

## Summary

Change deployed and verified live in production. `whatsapp_webhook`'s text-message branch now
sends `route_lead_message`'s computed reply back to the lead via `send_whatsapp_message`, closing
the last of the two follow-up bugs flagged during this session's plan-vs-build gap-closing work.

## Commits deployed

- `7def583` — feat(taty): send route_lead_message's computed reply back over WhatsApp

## Stage 11 steps executed

1. Merged `feature/wire-whatsapp-reply-sending` to `main` (fast-forward), pushed. Railway deploy
   `83489932` reached `SUCCESS`.
2. **Live smoke test**: created a real disposable test lead (`stage=NUEVOS`), POSTed a fabricated
   WhatsApp text-message webhook (`"hola"`) → `200`, `{"ok":true,"events_processed":1}`. Railway
   logs confirm the definitive proof: `channels.whatsapp - WARNING - send_whatsapp_message:
   WHATSAPP_TOKEN/WHATSAPP_PHONE_NUMBER_ID not configured` — this line only appears once
   `send_whatsapp_message` is actually invoked and reaches its credential check, confirming the
   send is genuinely attempted (with the lead's real phone number and the computed reply text) and
   fails gracefully (no crash, `200` still returned), exactly per design.md. Request completed in
   `1.455s`. Test lead cleaned up.
3. No new flag — reuses `WHATSAPP_CANONICAL`.

## Accepted risks / limitations (carried from design.md)

- **No real WhatsApp Business number/token exists yet** — the actual delivery of the reply to a
  real phone can't be verified end-to-end, same limitation as every Taty change this session. The
  send is confirmed attempted and gracefully degraded, which is the maximum verifiable today.

## Verification evidence

- Railway deployment `83489932`: `SUCCESS`, confirmed responding.
- Live webhook smoke test: `200`, `send_whatsapp_message` confirmed invoked via Railway logs,
  graceful no-op confirmed (no crash).
- Full regression suite: 61/61 green, zero regression.

---

## Session wrap-up — 7 OpenSpec changes fully closed

This closes the second and final follow-up bug from this session's plan-vs-build gap-closing work.
Complete tally of this session, each change fully proposed → designed → spec'd → implemented (TDD)
→ Stage 11 live-verified → archived, nothing left open:

1. **`taty-persona-fields`** (gap #8 remainder) — `topes`/`obligado_declarar` detection
2. **`taty-kb-and-react-router`** (gaps #3+#4) — bounded ReAct loop + KB grounding on Taty's fallback
3. **`copywriter-rag`** (gap #5) — Copywriter hooks grounded in retrieved DIAN-pains content
4. **`activate-telemetry-loop`** (gap #6) — `run_creative_loop(use_telemetry=True)` made reachable
5. **`ads-ab-task-dispatch`** (gap #7) — `dispatch_campaign_package` infers `task_type` from budget
6. **`fix-llm-engine-required-keys`** (bug found in #2/#3) — fixed the JSON-mode custom-order crash,
   plus a second bug found mid-fix (list-shaped response crash), both resolved before archiving
7. **`wire-whatsapp-reply-sending`** (bug found in #2) — Taty's replies now actually attempt to
   send over WhatsApp

All six original plan-vs-build gaps (#3 through #8) are closed. Both bugs discovered along the way
during live Stage 11 verification are fixed, not just flagged. No open threads remain from this
session's work.
