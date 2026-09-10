# Review — taty-document-collection-wiring, Task 1

**Verdict:** APPROVED

## Checkpoints
- Function contract matches spec: `download_chatwoot_attachment(data_url)` added in
  `apps/backend/channels/whatsapp.py:285-303`, plain unauthenticated `httpx.AsyncClient().get()`,
  no `WHATSAPP_TOKEN`/Graph API involvement. [x]
- Never-throw / never-raise contract: wrapped in `try/except Exception`, returns `None` on
  non-200 status and on network exception — mirrors `download_whatsapp_media` (lines 243-279)
  pattern exactly. [x]
- `download_whatsapp_media` and all Graph API / `WHATSAPP_TOKEN` logic untouched — confirmed via
  `git diff`: the diff is a pure append (new function + `_DEFAULT_MIME_TYPE` constant) after the
  existing function, zero lines changed inside it. [x]
- Return shape `{"content": bytes, "mime_type": str}` or `None` — correct. `mime_type` falls
  back to `application/octet-stream` on missing/blank `Content-Type`, matches spec's implicit
  robustness requirement. [x]
- TDD / real tests: 5 new tests in `TestDownloadChatwootAttachment`
  (`apps/backend/tests/test_whatsapp_channel.py:295-386`) cover success, HTTP error status,
  network exception (`httpx.ConnectTimeout`), missing header, and empty-string header. Each
  asserts the actual returned dict/`None`, not just "no exception" — real outcome assertions. [x]
- Boundary mocked is the real external boundary (`channels.whatsapp.httpx.AsyncClient`), not the
  function under test itself — avoids the exact anti-pattern Decision #22 documented
  (ARCHITECTURE.md #22: "a test must not mock the boundary it claims to verify"). [x]
- Test run independently verified (not trusting the implementer's report blindly): ran
  `py -3.11 -m pytest tests/test_whatsapp_channel.py -v` myself from
  `apps/backend`. Real output: **26 passed in 0.85s**, including the 5 new
  `TestDownloadChatwootAttachment` tests and all 21 pre-existing tests (including
  `TestDownloadWhatsappMedia`'s 3 tests, confirming the Graph API path still passes unmodified).
  Matches the implementer's claim exactly. [x]
- Scope discipline: `git status`/`git diff` for `apps/backend` + `apps/chatwoot-bridge` shows only
  `channels/whatsapp.py` and `tests/test_whatsapp_channel.py` touched by this work. Task 2
  (`route_lead_document` branching), Task 3 (`/internal/whatsapp/document` endpoint), and Task 4
  (Chatwoot bridge wiring) are untouched — no branch logic added to `route_lead_document`, no new
  `/internal/*` route, no changes under `apps/chatwoot-bridge/`. `apps/backend/core/plan_features.py`
  (modified) and `apps/backend/migrations/0052_crm_leads_source.sql` (untracked) are pre-existing,
  unrelated changes from a different in-flight branch (visible in the session's git status
  snapshot before this task started) — not introduced by this implementer. [x]
- No fabricated stubs, no disabled type-checking, no hand-edited `app/`. [x]
- Docs-sync: no container/dependency change in `ARCHITECTURE.md`'s sense — this is an internal
  function addition inside an existing container (Backend API), no new external dependency, no
  new data flow across a tenant/RLS boundary. No `ARCHITECTURE.md` update required for this task
  alone. [x]

## Required changes
None.
