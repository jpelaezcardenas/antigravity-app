# Deployment report — taty-document-collection-wiring (2026-09-10)

## Summary

All 5 build tasks (1–5) implemented via the leader/implementer/reviewer harness, running in
parallel with `b2c-social-lead-capture` by explicit founder decision. Deployed to production
and verified live.

## What shipped

- `channels/whatsapp.py::download_chatwoot_attachment(data_url)` — plain, unauthenticated HTTP
  GET against Chatwoot's own hosted copy of an attachment (no `WHATSAPP_TOKEN`), mirroring
  `download_whatsapp_media`'s never-throw contract.
- `services/taty_lead_router.py::route_lead_document()` extended to branch on a `data_url`
  source instead of hardcoding a Graph API `media_id` — the original Graph path is fully
  untouched and still covered by its existing tests.
- `POST /internal/whatsapp/document` (`presentation/whatsapp_document_endpoints.py`) —
  `INTERNAL_API_KEY` fail-closed, same module family as the Siigo/Gmail/voice-note
  `/internal/*` endpoints.
- New branch in `apps/chatwoot-bridge/main.py::process_incoming_message`: an image/file
  attachment with a resolved `lead_id` calls the new backend endpoint; a private ack is sent on
  `processed: true`, and any other outcome (`processed: false` or a failed call) falls through
  to Taty's normal reply — never silence.

## Root cause this closes

`route_lead_document()` had real gating, storage, and tests but zero production callers — its
hardcoded `download_whatsapp_media(media_id)` assumed a Graph API `media_id` that Chatwoot's
webhook payload never exposes (`ChatwootAttachment` only carries `file_type`/`data_url`). A
RUT/extractos document sent by a real client to Taty on WhatsApp was silently never processed.

## Deploy steps taken

1. Tasks 1–4 each implemented and independently reviewer-approved via the harness.
2. Task 5 (regression sweep) independently re-verified after the original implementer died to a
   session rate-limit mid-run: backend **35 failed, 1255 passed, 120 skipped** (3 known
   pre-existing collection errors excluded — same baseline `MEMORY.md` already documents),
   bridge **2 failed, 106 passed**. All failures pre-existing and unrelated to this change's
   files (`test_shadow_gl_stage4/5/8_*.py`, `test_whatsapp_inbox_service.py`,
   `test_wizard_auditoria_sombra.py` on the backend side; `test_chatwoot_client.py`,
   `test_process_message.py::test_reply_comes_from_the_sales_router_not_hermes` on the bridge
   side — none of which this change touches).
3. Commit `2f2fb8d` pushed to `main`. Railway auto-deployed (`f9f84819-...`, `SUCCESS`).

## What was verified live

- `GET /api/v1/health` — 200, `{"status":"healthy",...}`.
- `POST /internal/whatsapp/document` without an `X-Internal-Api-Key` header — **401** `{"detail":
  "Invalid internal API key"}`. This confirms `INTERNAL_API_KEY` is genuinely configured on
  Railway (a 503 would mean the key itself is unset server-side) and the endpoint correctly
  rejects an unauthenticated caller — fail-closed as designed.
- `/internal/whatsapp/document` is present in the live `openapi.json` — the route is genuinely
  mounted, not silently dropped (the exact class of bug Decision #22 in `ARCHITECTURE.md`
  already documented once for this repo's `/internal/*` router registration).

## What was NOT done (deliberately, per Task 6's own wording)

Task 6 — "Controlled verification only — explicitly logged as a test, never a real production
lead, before this is marked done" — is **not executed in this session**. It requires the
founder to name a specific real lead already at `LISTOS_CONTADORA` (or a test lead created for
this purpose) and confirm sending a real WhatsApp document to it. No live-lead exercise was run
here.

## Restrictions respected

- `taty-voice-outbound-calls` Tasks 7–9 untouched.
- No migration involved in this change.
- Ran in parallel with `b2c-social-lead-capture` per the founder's explicit override of the
  harness's one-change-at-a-time invariant; both changes' files were kept cleanly separable
  (verified via `git diff` per-file before each commit) despite a `git stash -u` collision from
  one of the parallel background agents mid-session, which was recovered without losing either
  front's work.
