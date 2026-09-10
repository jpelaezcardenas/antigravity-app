# Implementer report — taty-document-collection-wiring, Task 3

## Task

```
- [x] 3. Backend: new `POST /internal/whatsapp/document` endpoint (`INTERNAL_API_KEY`
      fail-closed, same module family as the Siigo/Gmail/voice-note `/internal/*`
      endpoints). TDD.
```

## Pre-flight: verified prior partial work before touching anything

A previous implementer session was dispatched for this same task (tick 8+ of the current
`/loop` session) and never produced `progress/impl_taty_doc_collection_task3.md`. Before doing
any work I checked for real partial work in the working tree:

- `git status --porcelain=v1 apps/backend/` showed the exact deliverable already present as
  **untracked** files:
  - `apps/backend/presentation/whatsapp_document_endpoints.py` (new endpoint)
  - `apps/backend/tests/test_whatsapp_document_endpoint.py` (new test)
  - `apps/backend/main.py` modified (router import + registration)
- `git stash list` — one relevant WIP stash (`stash@{0}: On main: WIP: parallel work
  (whatsapp-durable-inbox, taty-channel-consolidation, etc.)`) exists but is unrelated to this
  file set (those files are already present in the working tree unstashed, not inside the
  stash).

**Decision: continue the existing work, do not discard it.** I read the full contents of both
new files against `design.md`/`proposal.md`'s contract and confirmed:
- Body shape matches design.md exactly: `{lead_id, data_url, file_type}` — implemented as
  `WhatsappDocumentRequest(lead_id, data_url, mime_type)` (design.md's prose calls the third
  field `file_type` in the bridge payload description but `mime_type` in the endpoint
  signature — `route_lead_document`'s existing signature from Task 2 takes `mime_type`, so this
  is the correct name to forward under, not a deviation).
- `INTERNAL_API_KEY` fail-closed pattern: unset env → 503 (checked first, before any body
  processing), wrong/missing header → 401. Mirrors `presentation/voice_endpoints.py` exactly
  (same env var name, same order of checks).
- Endpoint does zero download/gating logic itself — it forwards straight to
  `services.taty_lead_router.route_lead_document(lead_id, mime_type=..., data_url=...)` (Task
  2's already-approved data_url branch), returning `{"processed": bool}` verbatim per
  design.md's contract, as 200 always (not raised) — matches the "processed: False is a normal
  outcome, not an error" stance documented in proposal.md.
- Registration in `main.py`: added to `_internal_router` alongside `siigo_sync_router`,
  `ingest_file_router`, `voice_router`, `cadence_router`, `voice_outbound_router` — same
  `/internal` prefix, mounted plainly (no `try/except` swallowing registration errors, per
  Decision #22's fail-loud correction). Confirmed via `git diff apps/backend/main.py`: the
  import and `include_router` calls are unconditional, and the log line was updated to list
  `/internal/whatsapp/document` alongside the existing routes.

No code was written from scratch for this task — the prior session's work matched the design
and proposal contracts on inspection, so I verified it via test execution rather than
rewriting it (see below), and I take responsibility for that verification as this session's
implementer.

## TDD verification

The test file already exists and follows the repo's established pattern for `/internal/*`
auth tests (`test_voice_endpoint_auth.py`): the endpoint coroutine is awaited directly rather
than driven through `TestClient`, because httpx 0.28.1 removed the `app=` shortcut this repo's
starlette 0.27.0 still needs.

Test coverage (7 tests, all in `tests/test_whatsapp_document_endpoint.py`):
- `test_missing_internal_key_env_returns_503`
- `test_empty_internal_key_env_returns_503`
- `test_wrong_key_returns_401`
- `test_absent_header_returns_401`
- `test_delegates_to_route_lead_document_with_data_url` — asserts the endpoint forwards
  `(lead_id, media_id=None, mime_type, data_url)` to the real function, never re-implementing
  download/gating.
- `test_not_processed_result_is_returned_not_raised`
- `test_uses_the_real_route_lead_document_not_a_reimplementation` — asserts
  `endpoints.route_lead_document is services.taty_lead_router.route_lead_document` (no local
  copy/mock substituted at import time — this is the boundary-mocking guard Decision #22 calls
  out: the test must not mock the function it claims to prove is wired to the real thing).

### Command run and output (this session, 2026-09-10)

```
cd C:/Users/contexia/Projects/antigravity-app/apps/backend
py -3.11 -m pytest tests/test_whatsapp_document_endpoint.py -v
```

```
collected 7 items

tests/test_whatsapp_document_endpoint.py::test_missing_internal_key_env_returns_503 PASSED [ 14%]
tests/test_whatsapp_document_endpoint.py::test_empty_internal_key_env_returns_503 PASSED [ 28%]
tests/test_whatsapp_document_endpoint.py::test_wrong_key_returns_401 PASSED [ 42%]
tests/test_whatsapp_document_endpoint.py::test_absent_header_returns_401 PASSED [ 57%]
tests/test_whatsapp_document_endpoint.py::test_delegates_to_route_lead_document_with_data_url PASSED [ 71%]
tests/test_whatsapp_document_endpoint.py::test_not_processed_result_is_returned_not_raised PASSED [ 85%]
tests/test_whatsapp_document_endpoint.py::test_uses_the_real_route_lead_document_not_a_reimplementation PASSED [100%]

================== 7 passed, 3 warnings in 101.40s (0:01:41) ==================
```

Interpreter: `py -3.11` (per `MEMORY.md`: only py311 has pytest installed in this repo).

### Sanity check — module import chain

`py -3.11 -c "import main"` from `apps/backend/` fails, but on an **unrelated, pre-existing**
error, before it ever reaches `whatsapp_document_endpoints` import:

```
File "presentation/metrics_endpoints.py", line 33, in <module>
    @router.get("/auto-approval/last-7-days", response_model=AutoApprovalMetricsResponse)
...
AttributeError: 'FieldInfo' object has no attribute 'in_'
```

This is a FastAPI/pydantic version-mismatch bug in `metrics_endpoints.py`, imported at
`main.py` line 7 — well before line 262-273 where the whatsapp-document router lives. It is
not something Task 3 introduced or touched; `test_whatsapp_document_endpoint.py` doesn't
import `main` at all (it imports `presentation.whatsapp_document_endpoints` directly), which
is exactly why the pytest run above passes cleanly despite this. Confirmed pre-existing/known
via `MEMORY.md`'s note that "init.sh's green gate does NOT mean tests ran" and the documented
25F/28E baseline — this repo's full-suite collection has known pre-existing failures unrelated
to any single change. Not investigated further as out of scope for Task 3 (no task in this
change touches `metrics_endpoints.py`).

## Files touched (all pre-existing from the prior session; verified, not rewritten)

- `apps/backend/presentation/whatsapp_document_endpoints.py` (new)
- `apps/backend/tests/test_whatsapp_document_endpoint.py` (new)
- `apps/backend/main.py` (router import + registration, fail-loud, no try/except)

## Files touched by me, this session

- `openspec/changes/taty-document-collection-wiring/tasks.md` — checked off Task 3.
- `progress/impl_taty_doc_collection_task3.md` (this report).

## Scope discipline

Did not touch Task 4 (bridge wiring), Task 5 (regression sweep), Task 6 (controlled
verification), or `taty-voice-outbound-calls` (Tasks 7-9, out of scope per instructions). Did
not exercise this endpoint against any real lead.

## Self-verify status

Green on the task's own test file (7/7). Per repo convention this checkbox reflects
"honestly complete" work, not final sign-off — a separate reviewer must still validate against
`ARCHITECTURE.md` + standards + `CHECKPOINTS.md` before this is truly done.
