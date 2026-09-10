# Implementation report — taty-document-collection-wiring, Task 4

## Scope

Bridge (`apps/chatwoot-bridge/main.py`): new branch in `process_incoming_message` — image/file
attachment + resolved `lead_id` → call the backend's `POST /internal/whatsapp/document` endpoint
(Task 3, already merged); decide and test the fallthrough behavior when `processed: False`.

## Files touched

- `apps/chatwoot-bridge/backend_client.py` — new `submit_whatsapp_document(lead_id, data_url,
  mime_type) -> Optional[dict]` (added after `send_voice_note`, before `pull_pending_events`).
  Posts to `{internal_base_url}/internal/whatsapp/document` with `X-Internal-Api-Key`, same
  fail-soft contract as `send_voice_note` (never raises; returns `None` on missing key, non-200,
  or network error).
- `apps/chatwoot-bridge/main.py`:
  - new module-level constant `DOCUMENT_ACK_REPLY` (next to `AUDIO_FALLBACK_REPLY` /
    `HANDOVER_FALLBACK_REPLY`).
  - new branch in `process_incoming_message`, inserted right after `lead_id` is resolved (and the
    existing "no lead_id → handover" early return), before the `taty_reply` call. Filters
    `attachments` to `file_type in ("image", "file")` AND a non-empty `data_url`; if any match,
    calls `backend_client.submit_whatsapp_document(lead_id, data_url, file_type)` with the first
    one.
- `apps/chatwoot-bridge/tests/test_process_message.py` — added `submit_whatsapp_document` to the
  `mocked_clients` fixture (default `AsyncMock(return_value=None)`, exposed as
  `mocks["submit_doc"]`), and a new `TestDocumentCollection` class (7 tests, see below). Also
  fixed two pre-existing assertions in the new tests to include `private=True` — the final Taty
  reply (`main.py:248`, unchanged by this task) has always sent `private=True`; unrelated baseline
  tests that assert without it (`TestSingleBrainInvariant::test_reply_comes_from_the_sales_router_not_hermes`)
  were already failing before this change (confirmed via `git stash` — see Test results below) and
  were left untouched, since fixing them is out of this task's scope.
- `apps/chatwoot-bridge/tests/test_submit_whatsapp_document.py` — new file, 8 tests for
  `backend_client.submit_whatsapp_document` mirroring `test_send_voice_note.py`'s pattern
  (`/internal` not `/api/v1`, payload shape, auth header, 200/401/503/network-error/no-key paths).

## Exact branch added (`main.py`, inside `process_incoming_message`)

```python
    # taty-document-collection-wiring: an image/file attachment with a resolved lead is a
    # candidate RUT/extractos document (sequential collection owned by route_lead_document on the
    # backend, gated on LISTOS_CONTADORA). `processed: True` means the backend already stored it,
    # so we ack privately here and skip the normal Taty text reply below. `processed: False` (or a
    # failed call, treated the same — see backend_client.submit_whatsapp_document) is deliberately
    # NOT silence: it falls through to the normal Taty reply so the lead still gets a helpful
    # answer instead of nothing when the document arrives at the wrong stage, both documents are
    # already collected, or the download itself failed.
    doc_attachments = [
        a for a in attachments if a.get("file_type") in ("image", "file") and a.get("data_url")
    ]
    if doc_attachments:
        doc_result = await backend_client.submit_whatsapp_document(
            lead_id, doc_attachments[0]["data_url"], doc_attachments[0]["file_type"]
        )
        if doc_result and doc_result.get("processed"):
            await chatwoot_client.send_reply(conversation_id, DOCUMENT_ACK_REPLY, private=True)
            return
```

## Fallthrough decision (`processed: False`)

**Decision: fall through to the normal Taty text reply, not silence.** This was already specified
in `design.md`'s integration-point snippet ("if not processed ... fall through to normal Taty
reply so the lead still gets an answer, not silence"), and this task implements + tests that exact
choice rather than re-deciding it. Reasoning, restated: `route_lead_document`'s `processed: False`
covers three normal, expected outcomes — wrong stage (before `LISTOS_CONTADORA`), both documents
already collected, or the Chatwoot download itself failing — none of which are the lead's fault,
and none of which should leave them without any reply. `submit_whatsapp_document`'s `None` return
(missing `INTERNAL_API_KEY`, non-200, or a network error talking to the backend) is treated
identically to `{"processed": False}` for the same reason: from the lead's point of view a backend
outage and a legitimate "not now" are indistinguishable, and both should degrade to "answer
normally" rather than "say nothing."

For `processed: True` I made one explicit choice not spelled out verbatim in `design.md`'s
snippet: send a fixed **private** ack (`DOCUMENT_ACK_REPLY`, mirrored into Chatwoot for operator
visibility, not delivered a second time to the customer) and return, skipping `taty_reply`
entirely — rather than also invoking Taty's LLM reply on top. Rationale: for the RUT→extractos
transition, `route_lead_document` already sends `EXTRACTOS_REQUEST_MESSAGE` directly to the
customer's phone via Graph API server-side (`taty_lead_router.py:583-586`) — an LLM-generated reply
on top would risk a redundant/contradictory message. For the final "extractos collected" case, no
backend-side customer message exists today, so the private ack is at minimum an operator-visible
confirmation; a customer-facing ack for that specific transition is a known, documented gap left
for a future change (not introduced or silently patched over here — see "Deviations" below).

## Test results

Full `apps/chatwoot-bridge` suite:

```
$ cd apps/chatwoot-bridge && python -m pytest tests/ -q
...
FAILED tests/test_chatwoot_client.py::TestCreateIncomingMessage::test_posts_an_incoming_message
FAILED tests/test_process_message.py::TestSingleBrainInvariant::test_reply_comes_from_the_sales_router_not_hermes
2 failed, 106 passed, 1 warning in 79.70s (0:01:19)
```

Confirmed both failures are pre-existing baseline failures, unrelated to this change, by running
the same two tests against `git stash` (working tree reverted to `main`):

```
$ git stash && cd apps/chatwoot-bridge && python -m pytest tests/test_process_message.py::TestSingleBrainInvariant tests/test_chatwoot_client.py::TestCreateIncomingMessage -q
FAILED tests/test_process_message.py::TestSingleBrainInvariant::test_reply_comes_from_the_sales_router_not_hermes
FAILED tests/test_chatwoot_client.py::TestCreateIncomingMessage::test_posts_an_incoming_message
2 failed, 1 warning in 5.92s
$ git stash pop
```

`test_chatwoot_client.py::TestCreateIncomingMessage` fails because `chatwoot_client` has no
`create_incoming_message` attribute (unrelated feature never landed / different in-progress work).
`test_process_message.py::TestSingleBrainInvariant::test_reply_comes_from_the_sales_router_not_hermes`
fails because it asserts `send_reply(42, "Respuesta de Taty")` without `private=True`, which has
been the actual call shape since `taty-whatsapp-renta-sales-capability`/`voicebox-local-voice-
adoption` landed (main.py:248) — pre-dates this task, not touched here.

New/modified tests, isolated:

```
$ python -m pytest tests/test_process_message.py::TestDocumentCollection tests/test_submit_whatsapp_document.py -v
```

All 7 `TestDocumentCollection` tests and all 8 `test_submit_whatsapp_document.py` tests pass
(included in the "106 passed" full-suite run above; also verified individually with `-v`).

Backend sanity check (Task 3's endpoint, not touched by this task):

```
$ cd apps/backend && python -m pytest tests/test_whatsapp_document_endpoint.py -q
7 passed, 3 warnings in 84.12s
```

## Deviations / known gaps (documented, not silently patched)

1. `DOCUMENT_ACK_REPLY` text is a fixed string, not sourced from any existing constant — there was
   no pre-existing customer-facing ack copy for this transition to reuse.
2. As noted above: the final "extractos collected" transition (`processed: True`, but
   `document_type == "extractos"`, so `route_lead_document` sends no Graph API message itself)
   only gets the bridge's private-note ack today, not a customer-facing WhatsApp message. This
   matches `route_lead_document`'s existing behavior (it doesn't message the customer for that
   case either) and is out of this task's stated scope (Task 4 is the bridge wiring, not backend
   messaging policy) — flagging it explicitly rather than silently leaving the gap undocumented.
3. `tasks.md` checkbox for Task 4 left **unchecked** per the implementer protocol — it is only
   checked after reviewer APPROVED, not by this session.

## Not done (explicitly out of scope for this task)

- Task 5 (regression sweep against an isolated `main` baseline) and Task 6 (controlled live
  verification) — next tasks in the sequence, not this one.
- No live lead was exercised; all verification is via mocked unit tests (respx for HTTP,
  `AsyncMock` for the bridge's internal collaborators).
