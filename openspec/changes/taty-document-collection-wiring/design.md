# Design: taty-document-collection-wiring

## Integration point (confirmed by reading both files, 2026-09-09)

`apps/chatwoot-bridge/main.py::process_incoming_message()` (lines ~201-259) already
receives `attachments: list[dict]` per Chatwoot's `ChatwootAttachment` schema
(`file_type`, `data_url`) and already branches on `file_type == "audio"` before the
normal Taty reply path. Document collection is a new branch in the same function,
checked before the generic `taty_reply` call:

```
if attachments and lead_id:
    doc_attachments = [a for a in attachments if a.get("file_type") in ("image", "file")]
    if doc_attachments:
        result = await backend_client.submit_whatsapp_document(
            lead_id, doc_attachments[0]["data_url"], doc_attachments[0]["file_type"]
        )
        # if result["processed"]: send the "thanks, next document" ack (already returned
        # by route_lead_document's own messaging for the RUT->extractos transition);
        # if not processed (wrong stage / already collected): fall through to normal
        # Taty reply so the lead still gets an answer, not silence.
```

Exact fallthrough behavior (silence vs. normal Taty reply when `processed: False`) is
Task 2's decision, made with a test proving the choice, not assumed here.

## Backend: new download path, no `WHATSAPP_TOKEN` needed

`route_lead_document()` (`taty_lead_router.py:513`) currently hardcodes
`download_whatsapp_media(media_id)`. This session confirms `media_id` was never
reachable from Chatwoot's payload — its `data_url` is Chatwoot's own hosted copy, not a
Graph API media id. Fix: `route_lead_document` takes an explicit `source` — either
`media_id` (existing Graph path, untouched) or `data_url` (new). A new
`channels/whatsapp.py::download_chatwoot_attachment(data_url) -> {"content": bytes,
"mime_type": str}` does a plain authenticated-if-needed GET (Chatwoot's `data_url` is
typically already publicly fetchable — verify against a real Chatwoot instance during
implementation, do not assume).

## New endpoint

`POST /internal/whatsapp/document` in the same `/internal/*` presentation module family
as the Siigo/Gmail pollers and the voice-note endpoint (`INTERNAL_API_KEY`, fails
closed with 503 if unset — Decisions #22/#26). Body: `{lead_id: str, data_url: str,
file_type: str}`. Calls `route_lead_document(lead_id, data_url=data_url, mime_type=...)`
and returns its `{"processed": bool}` verbatim.

**SUPERSEDED 2026-09-11 — the risk flagged above (line 36) was real.** Verified against a real
Chatwoot attachment (WhatsApp inbox, "Maria E2E Test" conversation): `data_url` is
`http://localhost:3020/...` — never reachable from Railway. `download_chatwoot_attachment()`
would have failed on every real document, silently degrading to `processed: False` in
production. Fixed by moving the download to the bridge (which IS on Chatwoot's network): the
bridge downloads via `httpx.get(data_url)` itself and posts the bytes as `content_base64`;
`route_lead_document()` gained a `content_bytes` parameter that takes precedence over `data_url`/
`media_id`. The endpoint's body is now `{lead_id, mime_type, content_base64}` (preferred) or
`{lead_id, mime_type, data_url}` (kept for a hypothetical future public-URL deployment, unused by
any current caller). See `tasks.md` task 6a for the full fix and its tests.

## Explicitly out of scope

- No change to the Graph API `media_id` path or `WHATSAPP_TOKEN` usage.
- No change to `CrmService.approve_payment` / the `LISTOS_CONTADORA` gate itself.
- No live-lead exercise. Any test call in this change must target a test lead / staging
  fixture and be logged as such.
