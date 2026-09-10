# Implementer report — taty-document-collection-wiring, Task 2

## Task
Extend `services/taty_lead_router.py::route_lead_document()` to accept a `data_url`-sourced
download (branch instead of always calling `download_whatsapp_media`), keeping the Graph
`media_id` path untouched and covered by its existing tests.

## Files touched

- `apps/backend/services/taty_lead_router.py`
  - Import now pulls in `download_chatwoot_attachment` alongside the existing
    `download_whatsapp_media`/`send_whatsapp_message` from `channels.whatsapp`.
  - `route_lead_document()` signature changed from
    `(lead_id: str, media_id: str, mime_type: str)` to
    `(lead_id: str, media_id: Optional[str] = None, mime_type: str = "application/octet-stream",
    *, data_url: Optional[str] = None)`. `media_id` and `mime_type` stay positional-compatible
    (all four pre-existing call sites in the test suite pass them positionally, unmodified);
    `data_url` is keyword-only and new.
  - New branch right before the download call: `if data_url: downloaded = await
    download_chatwoot_attachment(data_url)` else `downloaded = await
    download_whatsapp_media(media_id)`. Everything downstream of `downloaded` (upload, status
    patch, extractos-request follow-up message, return value) is identical for both sources —
    no duplicated logic.
  - Docstring extended with a short note on the two mutually-exclusive sources, referencing
    design.md's finding that `media_id` was never reachable from Chatwoot's payload.
- `apps/backend/tests/test_taty_lead_router.py`
  - Added two new tests inside `TestRouteLeadDocument`:
    - `test_data_url_source_calls_download_chatwoot_attachment_not_graph_media` — asserts
      `download_chatwoot_attachment` is called with the given URL, `download_whatsapp_media` is
      **not** called, and the rest of the RUT-first-document flow (upload, patch, ack message)
      behaves the same as the existing `media_id` test.
    - `test_data_url_download_failure_does_not_update_any_status` — mirrors the existing
      `test_download_failure_does_not_update_any_status` for the new source.
  - No existing test in this file was modified — the four pre-existing `route_lead_document(...)`
    call sites (positional `lead_id, media_id, mime_type`) are untouched and still pass.

## TDD sequence

1. Wrote the two new tests first (patching `services.taty_lead_router.download_chatwoot_attachment`,
   which did not exist yet on that module).
2. Ran `tests/test_taty_lead_router.py` — confirmed red:
   `AttributeError: <module 'services.taty_lead_router' ...> does not have the attribute
   'download_chatwoot_attachment'` on both new tests; 60 passed (all pre-existing tests still
   green, proving the Graph path test suite was untouched before any code change).
3. Implemented the import + signature + branch described above.
4. Re-ran the full file plus `test_whatsapp_channel.py` (Task 1's suite, to confirm no
   cross-contamination) — green.

## Test output

```
$ py -3.11 -m pytest tests/test_taty_lead_router.py tests/test_whatsapp_channel.py -q
........................................................................ [ 81%]
................                                                         [100%]
88 passed, 3 warnings in 112.74s (0:01:52)
```

88 = 62 (test_taty_lead_router.py, 60 pre-existing + 2 new) + 26 (test_whatsapp_channel.py,
Task 1's suite, run alongside to confirm no regression from the new import).

## Design decisions

- Kept `media_id` as the second **positional** parameter (not renamed/reordered) specifically so
  the four existing test call sites and any other unseen caller using positional args keep
  working without modification — satisfies "keeping the Graph-`media_id` path untouched and
  covered by its existing tests" literally, not just behaviorally.
- Made `data_url` keyword-only (`*, data_url: Optional[str] = None`) rather than a third
  positional slot, to avoid any ambiguity with the existing `(lead_id, media_id, mime_type)`
  call shape and to make the new Task 3 endpoint's call site self-documenting
  (`route_lead_document(lead_id, mime_type=..., data_url=...)`).
- `data_url` takes precedence when both are somehow supplied (`if data_url: ... else:
  download_whatsapp_media(media_id)`) — Task 3's endpoint will only ever pass `data_url`, so this
  branch never has to reject a caller passing both; kept minimal rather than adding validation
  not required by this task's scope.
- No change to `design.md` was needed — its integration-point section already fully specified
  this branch (`route_lead_document takes an explicit source — either media_id ... or data_url`),
  so no spec-before-code gap existed for this task.

## Scope discipline

Only Task 2 was implemented. Task 3 (new `POST /internal/whatsapp/document` endpoint), Task 4
(Chatwoot bridge wiring), and Task 5 (regression sweep) were not touched. `download_whatsapp_media`
itself and its own test suite (`TestDownloadWhatsappMedia` in `test_whatsapp_channel.py`) were not
modified.
