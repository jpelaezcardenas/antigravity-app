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
- [~] 6. Controlled verification only — explicitly logged as a test, never a real
      production lead, before this is marked done. **Partially verified 2026-09-11, NOT fully
      closed**: confirmed live in production that `POST /internal/whatsapp/document` is mounted
      (present in `openapi.json`) and fails closed correctly (401 without a valid
      `X-Internal-Api-Key`; an initial 502 on the very first request was a transient blip —
      `/api/v1/health` was 200 throughout and an immediate retry returned the correct 401, so this
      was not a repeat of the traffic-cutover incident in `renta-natural-first-sale`). **Could not
      verify the actual download+processing leg**: this needs a real Chatwoot-hosted `data_url`
      from an actual test conversation attachment, and the Chatwoot MCP for this session was
      `CONNECTION_CLOSED` — fabricating a fake `data_url` would only prove the auth gate (already
      shown above), not the real behavior, so no synthetic call was made. To finish this task:
      re-run with the Chatwoot MCP connected (or from a session with direct Chatwoot access),
      upload a test PDF/image to one of the existing test conversations (e.g. "Maria E2E Test"),
      and post its real `data_url` against a `crm_leads` test row in the `LISTOS_CONTADORA` stage.

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
