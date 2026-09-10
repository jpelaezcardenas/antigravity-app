# Review — taty-document-collection-wiring, Task 4

**Verdict:** APPROVED

## What was checked

- `openspec/changes/taty-document-collection-wiring/tasks.md` + `design.md` — Task 4 scope is the
  bridge-side branch in `process_incoming_message` calling the (already-merged, Task 3) backend
  endpoint, with a tested fallthrough decision for `processed: False`. Confirmed the implementer's
  diff matches `design.md`'s integration-point snippet exactly, including the `processed: True` →
  private ack / skip `taty_reply`, `processed: False` (or `None`) → fall through to normal Taty
  reply (never silence) behavior specified in `design.md` lines 18-21 and Task 4's own wording
  ("decide and test the fallthrough behavior").

- `apps/chatwoot-bridge/backend_client.py::submit_whatsapp_document` — new function, posts to
  `{internal_base_url}/internal/whatsapp/document` (not `/api/v1`), `X-Internal-Api-Key` header,
  fail-soft (`None` on missing key / non-200 / network error, never raises) — same contract as the
  sibling `send_voice_note`. Correctly uses the `/internal/*` + `INTERNAL_API_KEY` fail-closed
  convention from ARCHITECTURE.md Decisions #22/#26 (backend fails closed with 503 without the
  key; bridge here fails soft and treats that the same as `processed: False`, which is the correct
  behavior for this caller — a missing key shouldn't silence the lead).

- `apps/chatwoot-bridge/main.py::process_incoming_message` — new branch inserted after `lead_id`
  resolution / before the `taty_reply` call, filtering `attachments` to `file_type in ("image",
  "file")` with a non-empty `data_url`. Matches design exactly.

- Re-ran `cd apps/chatwoot-bridge && python -m pytest tests/ -q` myself:
  `2 failed, 106 passed, 1 warning` — matches the implementer's claimed counts and the two named
  pre-existing failures (`test_chatwoot_client.py::TestCreateIncomingMessage::test_posts_an_incoming_message`,
  `test_process_message.py::TestSingleBrainInvariant::test_reply_comes_from_the_sales_router_not_hermes`).
  Both are `private=True`/missing-attribute issues unrelated to this change, as claimed. Did not
  independently re-run `git stash` baseline (trusted the implementer's shown output), but the
  live full-suite re-run corroborates the failure identity and count.

- `apps/chatwoot-bridge/tests/test_process_message.py::TestDocumentCollection` (7 tests) and the
  new `apps/chatwoot-bridge/tests/test_submit_whatsapp_document.py` (8 tests, respx-mocked HTTP,
  no real network/Chatwoot/WhatsApp calls) — read in full. Tests assert real outcomes (which mock
  was awaited with what args, `taty_reply` NOT called vs called, `send_reply` args/kwargs), not
  just "no exception." Fallthrough test explicitly named
  `test_processed_false_falls_through_to_normal_taty_reply_not_silence` and asserts `taty_reply`
  IS awaited — correctly tests the spec'd behavior, not the inverse.

- No voice/Twilio code touched: `git diff` for the three changed files contains zero references to
  voice/Twilio/outbound-call code, confirmed via grep. `taty-voice-outbound-calls` Tasks 7-9
  remain untouched, as instructed.

- No plaintext secrets: `INTERNAL_API_KEY`/`X-Internal-Api-Key` referenced only as variable names
  and a test fixture value (`"test-internal-key"`), never a real key committed.

- No live-lead testing: all new tests use `respx.mock` / `AsyncMock` against `127.0.0.1:8080`
  fixture URLs and fabricated `lead-1`/`+573001234567` test data — no real Chatwoot conversation ID
  or real WhatsApp number is exercised. Implementer's report explicitly confirms this under "Not
  done."

- `openspec/changes/taty-document-collection-wiring/tasks.md` Task 4 checkbox was `[ ]` (unchecked)
  before this review, as required — implementer did not self-approve. Checked it now per this
  repo's harness rule that reviewers (not implementers) mark done after APPROVED.

## Checkpoints

- Design conformance: [x]
- Tests are real (assert outcomes, not just no-exception): [x]
- Test counts independently reproduced: [x] (106 passed / 2 pre-existing failures, matches claim)
- No scope creep into voice/Twilio code: [x]
- `/internal/*` + `INTERNAL_API_KEY` fail-closed/fail-soft contract respected: [x]
- No secrets committed: [x]
- No live-lead / real API calls in tests: [x]
- Task 4 checkbox was unchecked prior to review (no self-approval): [x]

## Required changes

None. Task 4 is approved as implemented. Tasks 5 (regression sweep vs. isolated main baseline)
and 6 (controlled verification, explicitly logged as a test) remain open per the implementer's own
"Not done" section and are out of scope for this review.
