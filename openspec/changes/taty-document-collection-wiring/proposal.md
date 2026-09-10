# Proposal: taty-document-collection-wiring

## Why

`apps/backend/services/taty_lead_router.py::route_lead_document()` was built during
`taty-whatsapp-renta-sales-capability` (archived) to collect a lead's RUT + extractos
bancarios once they reach `LISTOS_CONTADORA`. It has real gating logic, storage upload,
and tests — but **zero production callers**. Neither `apps/backend/presentation/*` nor
`apps/chatwoot-bridge/main.py` invokes it. A lead sending their RUT by WhatsApp today gets
no document collection at all. Confirmed via full grep of `apps/` (2026-09-09, this
session): the only reference outside its own definition is
`apps/backend/tests/test_taty_lead_router.py`.

Founder decision (2026-09-09): close this wiring gap now, priority 1 for the current
sales season.

## What changes

Wire `route_lead_document()` into the real WhatsApp inbound path, with one necessary
correction to its original design surfaced by this investigation:

- `route_lead_document(lead_id, media_id, mime_type)` assumes a **WhatsApp Graph API
  `media_id`**, downloaded via `channels/whatsapp.py::download_whatsapp_media()`
  (2-step Graph flow, needs `WHATSAPP_TOKEN`).
- But the actual caller is `apps/chatwoot-bridge/main.py::process_incoming_message()`,
  which only ever sees Chatwoot's own webhook payload
  (`schemas.py::ChatwootAttachment`: `file_type` + `data_url`, Chatwoot's *own* hosted
  copy of the media — no raw WhatsApp `media_id` is exposed in that payload). Calling
  `download_whatsapp_media` with anything derived from Chatwoot's `data_url` would be
  building against the wrong API entirely.
- **Chosen fix**: add a second, real download path —
  `channels/whatsapp.py::download_chatwoot_attachment(data_url)` (plain HTTP GET, no
  `WHATSAPP_TOKEN`) — and make `route_lead_document` accept already-downloaded bytes
  (or branch on which source is available) instead of hard-requiring a Graph
  `media_id`. `download_whatsapp_media` stays as-is for a possible future direct-Meta-
  webhook path; it is not deleted, just no longer the only path in.
- New internal endpoint `POST /internal/whatsapp/document` (same `INTERNAL_API_KEY`
  fail-closed pattern as the Siigo/Gmail pollers and the voice-note endpoint, Decisions
  #22/#26), called by the bridge with `{lead_id, data_url, file_type}`.
- Bridge change: `process_incoming_message` gains a branch — when an attachment has
  `file_type` in `{"image", "file"}` (Chatwoot's vocabulary; audio already branches
  earlier) AND the lead's current CRM stage is `LISTOS_CONTADORA`, call the new
  endpoint instead of (or in addition to) the normal Taty text reply.
- Explicitly NOT touched: `download_whatsapp_media`/Graph media_id path, Wompi HITL
  gate, any lead outside `LISTOS_CONTADORA` (acknowledged only, per existing gate logic).

## Non-goals

- No test-run against a real production lead. Any verification of this flow must be
  explicitly logged as a controlled test, never silently run against live leads.
- No change to `classify_lead_intent()` stages or the Wompi approval gate.
