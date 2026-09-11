# Tasks: taty-document-collection-wiring

- [x] 1. Backend: `channels/whatsapp.py::download_chatwoot_attachment(data_url)` (new,
      plain HTTP GET, returns `{"content": bytes, "mime_type": str}` or `None` on
      failure — mirrors `download_whatsapp_media`'s never-throw pattern). TDD.
- [x] 2. Backend: extend `route_lead_document()` to accept a `data_url`-sourced download
      (branch instead of always calling `download_whatsapp_media`), keeping the
      Graph-`media_id` path untouched and covered by its existing tests. TDD.
- [x] 3. Backend: new `POST /internal/whatsapp/document` endpoint (`INTERNAL_API_KEY`
      fail-closed, same module family as the Siigo/Gmail/voice-note `/internal/*`
      endpoints). TDD.
- [x] 4. Bridge (`apps/chatwoot-bridge/main.py`): new branch in
      `process_incoming_message` — image/file attachment + resolved `lead_id` → call
      the new backend endpoint; decide and test the fallthrough behavior when
      `processed: False` (silence vs. normal Taty reply).
- [x] 5. Regression sweep: run the full backend + bridge test suites, confirm zero new
      failures vs. an isolated `main` baseline (byte-identical failure list). Independently
      verified — see `progress/impl_taty_doc_collection_task5.md`: backend 35 failed/1255
      passed/120 skipped (3 known pre-existing collection errors excluded), bridge 2 failed/106
      passed, all failures pre-existing and unrelated to this change's files.
- [x] 6a. **Real bug found and fixed 2026-09-11**, before verification could even proceed: with
      the Chatwoot MCP reconnected, inspected a real attachment on a real WhatsApp-channel
      conversation ("Maria E2E Test", inbox 1, message 107). Its `data_url` was
      `http://localhost:3020/rails/active_storage/blobs/...` — Chatwoot's own local address. The
      backend's `download_chatwoot_attachment()` runs on Railway and does a plain `httpx.get()` on
      whatever `data_url` it's given — meaning **every real document collection would have failed
      in production**, silently returning `processed: False` and falling through to a generic Taty
      reply, never actually storing the RUT/extractos. `design.md` (line 36) had explicitly
      flagged this exact risk ("verify against a real Chatwoot instance during implementation, do
      not assume") but that verification was never actually done until now.

      Fix: flipped who downloads. The bridge (same network as Chatwoot, can reach `localhost:3020`)
      now downloads the attachment itself and posts the raw bytes as `content_base64` to
      `POST /internal/whatsapp/document`, instead of forwarding a URL for Railway to re-fetch.
      `route_lead_document()` gained a `content_bytes` parameter (takes precedence over `data_url`/
      `media_id` when given); the endpoint decodes `content_base64` and passes it through;
      `backend_client.submit_whatsapp_document()` downloads via `httpx.get(data_url)` (bridge-side,
      where it's reachable) then POSTs base64. `data_url`/`media_id` paths are kept, unused by any
      current caller, for a future deployment where the URL is genuinely public. TDD throughout:
      1 new backend test (`taty_lead_router`), 1 new + 1 updated backend test
      (`whatsapp_document_endpoint`), rewrote all 9 bridge tests
      (`test_submit_whatsapp_document.py`) to mock both the download and the forward legs
      separately. Full suites green: backend 71/71 (taty_lead_router + whatsapp_document_endpoint),
      bridge 107 passed / 2 pre-existing failures (confirmed via `git stash`, unrelated to this
      change — `test_chatwoot_client.py`/`test_process_message.py`, both pre-date this session).
- [ ] 6b. Controlled verification — explicitly logged as a test, never a real production lead,
      before this whole task is marked fully done. Still not run end-to-end: needs a `crm_leads`
      test row in the `LISTOS_CONTADORA` stage and a live call to
      `apps/chatwoot-bridge/main.py::process_incoming_message` (or `submit_whatsapp_document`
      directly) against the real "Maria E2E Test" attachment, from a session with the bridge
      actually running (this session has no way to execute the bridge process itself, only to
      read/edit its code and call Chatwoot's API directly).

## Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [x] 11.1 git commit + push to main (`2f2fb8d`).
- [x] 11.2 Not applicable — no frontend touched.
- [x] 11.3 Railway deploy active — `f9f84819-...`, `SUCCESS`.
- [x] 11.4 Production URL: `/internal/whatsapp/document` present in live `openapi.json`,
      returns **401** (not 503 — that would mean `INTERNAL_API_KEY` itself is unconfigured,
      which it correctly is not) without the header, confirming fail-closed rejection of an
      unauthenticated caller. No live lead exercised.
- [x] 11.5 Create report: `openspec/changes/taty-document-collection-wiring/reports/2026-09-10-deployment.md`.
