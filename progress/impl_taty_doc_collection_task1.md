# Implementer report — taty-document-collection-wiring, Task 1

## Task
`channels/whatsapp.py::download_chatwoot_attachment(data_url)` — new, plain HTTP GET
against Chatwoot's own hosted `data_url`, returns `{"content": bytes, "mime_type": str}`
or `None` on failure. Mirrors `download_whatsapp_media`'s never-throw pattern.

## Files touched

- `apps/backend/channels/whatsapp.py` — added `download_chatwoot_attachment(data_url)`
  (new function, appended after `download_whatsapp_media`). No changes to any existing
  function; the Graph API `media_id` path (`download_whatsapp_media`) is untouched.
- `apps/backend/tests/test_whatsapp_channel.py` — added `TestDownloadChatwootAttachment`
  (5 tests) + import of `download_chatwoot_attachment` and `httpx`.

## Implementation notes

- Plain `httpx.AsyncClient().get(data_url)` — no `WHATSAPP_TOKEN`/auth header, since
  Chatwoot's `data_url` is its own hosted, directly-fetchable copy (confirmed against
  `design.md`'s framing of this task).
- Never raises: wrapped in `try/except Exception`, logs a warning/error and returns
  `None` on any failure (non-200 status or network/timeout exception) — same contract as
  `download_whatsapp_media`.
- `mime_type` is read from the response's `Content-Type` header; falls back to
  `"application/octet-stream"` when the header is missing or present-but-empty/blank
  (covered by two separate tests: missing header, and header present as an empty string).

## Test output

```
$ py -3.11 -m pytest tests/test_whatsapp_channel.py -v
...
tests/test_whatsapp_channel.py::TestDownloadChatwootAttachment::test_success_returns_content_and_mime_type PASSED
tests/test_whatsapp_channel.py::TestDownloadChatwootAttachment::test_http_error_status_returns_none PASSED
tests/test_whatsapp_channel.py::TestDownloadChatwootAttachment::test_network_exception_returns_none PASSED
tests/test_whatsapp_channel.py::TestDownloadChatwootAttachment::test_missing_content_type_header_falls_back_to_default PASSED
tests/test_whatsapp_channel.py::TestDownloadChatwootAttachment::test_malformed_content_type_header_falls_back_to_default PASSED
...
============================= 26 passed in 0.67s ==============================
```

All 26 tests in the module pass (21 pre-existing + 5 new), including the pre-existing
`TestDownloadWhatsappMedia` suite, confirming the Graph API `media_id` path is untouched.

## Scope discipline

Only Task 1 was implemented. Task 2 (`route_lead_document` branching on `data_url` vs
`media_id`), Task 3 (new `/internal/whatsapp/document` endpoint), and Task 4 (Chatwoot
bridge wiring) were not touched.
