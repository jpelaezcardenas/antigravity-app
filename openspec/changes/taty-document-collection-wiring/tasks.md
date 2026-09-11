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
- [x] 6b1. **Second real bug found and fixed 2026-09-11**, while designing the controlled
      verification for 6b: the durable-inbox poller (`apps/chatwoot-bridge/inbox_poller.py`) — the
      ONLY path live in production since `taty-channel-consolidation` moved Meta's webhook to
      Railway — hardcoded `attachments=[]` on every call to `process_incoming_message`, regardless
      of whether the event carried a real `media_id` (migration `0036` captures it;
      `channels/whatsapp.py::normalize_whatsapp_webhook` sets it on the event). This meant **every
      real inbound RUT/extractos document was silently dropped** before it could ever reach the
      document-collection branch fixed in 6a — that fix was correct but structurally unreachable
      from the live production path.

      Fix: `inbox_poller.py` now builds `attachments=[{"file_type": "file", "media_id": ...}]`
      when the event has a `media_id`. `main.py`'s document branch now recognizes attachments
      keyed by `media_id` as well as `data_url`. `backend_client.submit_whatsapp_document()`
      gained a `media_id` parameter — when given, it skips the bridge-side download entirely
      (Graph API is reachable from Railway, unlike Chatwoot's localhost `data_url`) and forwards
      the id directly; the backend's original, untouched `download_whatsapp_media(media_id)` path
      (Task 1, unchanged since before this session) handles the actual Graph download.
      `whatsapp_document_endpoints.py` accepts `media_id` as a third valid source alongside
      `data_url`/`content_base64`. TDD throughout: 2 new poller tests, 1 new `main.py` test,
      rewrote `submit_whatsapp_document`'s docstring/signature — bridge suite 40/41 (1
      pre-existing unrelated failure, confirmed via earlier `git stash` comparison), backend
      71/71 green.
- [x] 6b2. Controlled verification — **CONFIRMED end to end 2026-09-11**, via the founder's own
      real WhatsApp phone against the production number, targeting a controlled test lead
      (`crm_leads.id=6e717c21-c2df-4761-a030-78cf69496977`, temporarily moved to
      `LISTOS_CONTADORA` with the founder's explicit authorization; a real B2B lead, not a
      synthetic fixture — restored after this verification, see note below). Confirmed via
      Supabase: `crm_tax_profiles` row `3663bea3-be68-413a-b698-58eb87830ca0` has
      `rut_status="collected"`, `rut_storage_path="6e717c21.../rut.pdf"` (the actual uploaded
      file), `extractos_status="requested"` (correctly sequenced to ask for the next document).
      This is the real, live production path — not a mock.

      **This single verification attempt surfaced and fixed 8 real, independent production bugs**,
      none of which were caught by unit tests before this session because none of this repo's
      tests modeled the actual dev/prod topology gap (Vercel vs. Railway) or the actual pinned
      dependency versions (this repo's local dev venv runs materially newer `postgrest`/`supabase`/
      `storage3` than what `requirements.txt` pins and Railway installs):
      1. `download_chatwoot_attachment` given a `localhost` Chatwoot URL, unreachable from Railway
         (6a — fixed by having the bridge download and forward bytes instead of a URL).
      2. The live durable-inbox poller hardcoded `attachments=[]`, never forwarding Meta's
         `media_id` (6b1).
      3. `whatsapp_inbox_service.pull_pending` manipulated `postgrest`'s private internal
         attributes for its OR filter — broke differently in prod vs. local dev venv twice in a
         row before being rewritten to filter client-side in plain Python.
      4. The bridge derived `/internal/*`'s URL from `CONTEXIA_API_URL`'s origin (Vercel), which
         never exposes `/internal/*` by design — fixed with an explicit `INTERNAL_API_BASE_URL`.
      5. `CrmService.update_tax_profile` silently no-op'd on an UPDATE against a non-existent row
         — fixed with an insert-if-missing fallback.
      6-7. `document_storage_service.upload_tax_document`'s `upsert` option wasn't honored by the
         actually-pinned `storage3` version; two fix attempts before landing on the version's real
         primitives (`remove()` + `upload()`, verified directly against the pinned wheel, not the
         local venv).
      8. The insert-if-missing fallback from fix 5 omitted `tenant_id` (NOT NULL), caught on the
         very next live attempt.

      **Founder action after this session**: restore `crm_leads.id=6e717c21-...` to its original
      `stage="PROSPECTOS"` / `lead_type="business_interest"` (it was authorized as a temporary
      change for this test only) — not done automatically here since it's the founder's own real
      lead and the change should be visible/confirmed by him first.

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
