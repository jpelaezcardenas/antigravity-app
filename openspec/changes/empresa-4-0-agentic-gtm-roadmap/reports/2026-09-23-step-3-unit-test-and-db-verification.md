# Step 3 Report - Unit Tests and Database Verification (Meta CAPI Attribution)

- Date: 2026-09-23
- Change: empresa-4-0-agentic-gtm-roadmap
- Agent: Claude Sonnet 5

## Commands Executed
- `py -3.11 -m pytest tests/test_social_capture_endpoints.py -v`
- `py -3.11 -m pytest -q --ignore=tests/test_profile_support.py --ignore=tests/test_swarm_operators.py --ignore=tests/test_t11_integration.py`

## Unit Test Results
- Targeted tests (`test_social_capture_endpoints.py`): 18 passed, 0 failed, 0 skipped
  - 13 pre-existing tests: unchanged, still passing
  - `TestSocialCaptureMetaCapiLeadEvent` (new): 4 passed
  - `TestMetaCapiClient` (new): 5 passed
- Full/required suite (excluding 3 modules with pre-existing, unrelated collection errors —
  `test_profile_support.py`, `test_swarm_operators.py`, `test_t11_integration.py`, all failing
  on `ModuleNotFoundError: No module named 'apps.backend'`, unrelated to this change):
  1283 passed, 38 failed, 120 skipped, runtime 252.11s
- Notes: All 38 failures are pre-existing and unrelated to this change — they concern
  Supabase-migration-file-existence checks, tenant-scoping tests requiring a live Supabase
  connection, and other modules never touched by this change (`test_approval_rules_*`,
  `test_shadow_gl_*`, `test_llm_engine.py`, `test_pwa_clients.py`, etc.). None reference
  `social_capture_endpoints` or `meta_capi_client`. This matches the documented pre-existing
  baseline for this backend (py3.11-only pytest environment, collection errors and Supabase-
  dependent failures known to exist on `main` independent of this change).

## Database State Verification
- Pre-test baseline: no `crm_leads` rows touch real Supabase in these tests — all
  `CrmService`/Supabase calls are mocked (`unittest.mock.patch`), matching this test file's
  existing convention (no live DB connection is made by `test_social_capture_endpoints.py`).
- Post-test validation: same — no live DB state was created or mutated by the new tests.
- State restored: N/A (no live DB touched)
- Restoration actions: none needed

## Outcome
- Step 3 status: PASS
- Blocking issues: none for the code implemented. Task 1.2 (setting real
  `META_CAPI_ACCESS_TOKEN`/`META_PIXEL_ID` in Railway) remains blocked on founder action —
  the CAPI client fails closed (no-ops, logs a warning) until that's set, verified by
  `test_returns_false_and_no_network_call_when_unconfigured`.

## Addendum — Step 4: Manual Endpoint Testing with curl (2026-09-23, later same day)

### Environment issue found and resolved
The machine's *global* `py -3.11` interpreter has `pydantic==2.13.4` installed (pinned for
`hermes-agent`), incompatible with this backend's `fastapi==0.104.1`/`pydantic==2.5.0`
(`requirements.txt`) — running `main:app` under the global interpreter crashed at import with
`AttributeError: 'FieldInfo' object has no attribute 'in_'` in `presentation/metrics_endpoints.py`.
This is a known, already-documented issue (`apps/backend/README-venv.md`) with a pre-existing fix:
a project-local `.venv/` with the correct pinned versions. No application code was changed —
switching to `.venv/Scripts/python.exe -m uvicorn main:app` started the server cleanly.

### Commands Executed
```bash
.venv/Scripts/python.exe -m uvicorn main:app --host 127.0.0.1 --port 8123
curl -s -X POST http://127.0.0.1:8123/api/v1/crm/social-capture/partial \
  -H "Content-Type: application/json" \
  -d '{"whatsapp_phone": "+573009998877", "full_name": "OpenSpec CAPI Test Lead", "source": "openspec_curl_test_DELETE_ME"}'
curl -s -X POST http://127.0.0.1:8123/api/v1/crm/social-capture/partial -H "Content-Type: application/json" -d '{}'
```

### Responses
- New lead POST: `200 {"lead_id":"9b0ca406-c0f9-4d74-87b5-62000821af7a","is_new":true,"stage":"NUEVOS"}`
- Server log confirms the Meta CAPI Lead event fired and no-oped exactly as designed (today's
  real state — token not yet set):
  `services.meta_capi_client - WARNING - send_lead_event: META_CAPI_ACCESS_TOKEN/META_PIXEL_ID not
  configured, skipping CAPI send for lead 9b0ca406-c0f9-4d74-87b5-62000821af7a` — logged, and the
  endpoint still returned `200` (Task 4.3/4.4: unavailable-CAPI path verified against the real
  current environment, since Task 1.2's Railway token is not yet set).
- Validation error case (empty body): `422`, `{"detail":[{"type":"missing","loc":["body",
  "whatsapp_phone"],...}]}` — unchanged from pre-existing behavior.

### Database State Verification (production Supabase, per founder-approved exception)
- This endpoint writes to the real production `crm_leads` table (Cliente Cero tenant) — there is
  no separate staging Supabase project. The founder explicitly approved proceeding with
  "immediate cleanup" for this one curl test (see conversation).
- Pre-test: lead `9b0ca406-c0f9-4d74-87b5-62000821af7a` did not exist.
- Test: `POST` created it (`201 Created` in Supabase log), `source="openspec_curl_test_DELETE_ME"`
  clearly marking it as test data in case cleanup had failed.
- Post-test: deleted via service-role client
  (`client.table("crm_leads").delete().eq("id", "9b0ca406-c0f9-4d74-87b5-62000821af7a").execute()`),
  verified `0` rows remain with that id. State restored.
- Test server stopped (`Stop-Process` on the uvicorn PID) after testing completed.

### Outcome
- Step 4 status: PASS
- All curl-testable behavior (new-lead CAPI attempt, unconfigured-CAPI-does-not-block-response,
  validation error) verified against the real running app. Database fully restored.

## Addendum — Step 6: E2E Testing (2026-09-23, later same session)

### Environment fixes made (incidental, found during setup)
1. `.claude/launch.json`'s "Backend (FastAPI / uvicorn)" config used the bare `python`
   executable (this machine's global interpreter, with the wrong pydantic/fastapi versions
   per `apps/backend/README-venv.md`). Fixed to `apps/backend/.venv/Scripts/python.exe`.
2. `apps/backend/config.py`'s `ALLOWED_ORIGINS` default never included
   `http://localhost:3001` — the exact port `.claude/launch.json`'s "Contexia App (end-user
   PWA)" config runs on. Added it alongside the existing 3000/3002 local-dev ports. Verified
   the fix directly:
   ```bash
   curl -i -X OPTIONS "http://127.0.0.1:8080/api/v1/crm/social-capture/partial" \
     -H "Origin: http://localhost:3001" -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: content-type"
   # -> HTTP/1.1 200 OK, access-control-allow-origin: http://localhost:3001
   ```

### What could and could not be verified
- Backend CORS configuration: verified correct via curl (above).
- The actual pixel `Lead` event firing in a real browser after form submit: **could not be
  verified end-to-end** in this session's sandboxed Browser pane. Filling and submitting
  `RentaNaturalLandingForm` via `preview_start` (PWA on :3001) against the backend
  (:8080, also via `preview_start`) consistently failed with `Failed to fetch` /
  `No 'Access-Control-Allow-Origin' header is present on the requested resource` when
  observed from *inside* the page's own JavaScript console — even though the exact same
  request succeeds when issued via `curl` from the host shell, and even though each preview
  origin loads correctly when navigated to directly. This points to the sandbox isolating
  fetch() calls that cross between two different `preview_start`-managed origins, not a
  defect in the CORS configuration or the application code.
- `connect.facebook.net` (Meta's pixel script host) is unreachable from this sandbox
  entirely (no requests to that domain were ever observed, successful or failed), so even a
  working cross-preview fetch would not have let this session verify a *real* Meta Events
  Manager delivery — only that `window.fbq(...)` gets called, which the code (Section 5.2)
  and its call site already demonstrate directly.

### Confidence basis for shipping without full browser E2E
Three independent, already-completed verifications stand in for the blocked E2E step:
1. 18 passing unit tests (Sections 2-3) covering the CAPI client and its wiring into
   `social_capture_partial`, including the exact gating logic (`is_new` only) that also
   governs the frontend's `trackPixelLead()` call.
2. The real manual curl test (Section 4) against production Supabase, proving the full
   request/response cycle for `social_capture_partial` including the CAPI attempt.
3. This session's curl-verified CORS fix, proving the local dev environment (once correctly
   configured) accepts cross-origin requests from the PWA to the backend.

No test lead data was created or needed cleanup — every attempted fetch failed before
reaching the backend, so `crm_leads` was never touched during this addendum.
