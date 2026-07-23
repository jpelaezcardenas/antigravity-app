# Implementer report — Section 7 (Manual Endpoint Testing with curl)

**Change:** `approval-queue-tenant-scoping`
**Task:** Section 7, tasks 7.1-7.7 ("Manual Endpoint Testing with curl (MANDATORY — AGENT MUST
EXECUTE)")
**Date:** 2026-07-23

## Constraint (confirmed, not assumed)

No `.env` file exists in `apps/backend/`, and no `SUPABASE_URL`/`SUPABASE_SERVICE_ROLE_KEY` are
set in this session's environment (confirmed via `python -c "from config import settings;
print(settings.SUPABASE_URL)"` → `''`). This is a local-only worktree with no live Supabase
connection. This was known going in (per the task prompt) and is documented, not hidden.

## What was actually executed

All of the following were run against a genuinely live local `uvicorn` process (started/stopped
twice, once per `AUTH_ENFORCED` value), not simulated:

1. **7.1** — started `apps/backend` with `python -m uvicorn main:app --port 8000`,
   `AUTH_ENFORCED=false`. Confirmed clean startup (all routers, incl. approval-queue,
   registered) via the real stdout log.
2. **7.2** — `curl GET /api/v1/approval-queue`, no token → `500`, traced to
   `resolve_request_tenant_scope` → `resolve_cliente_cero_tenant_id` → `create_client('', ...)`
   raising `SupabaseException: supabase_url is required`. Confirmed via the real server
   traceback in the uvicorn log, not inferred.
3. **7.3** — `curl POST /enqueue`, no token → same `500`/same boundary, before
   `ApprovalQueueService.enqueue_draft` is called. No row created (Supabase client never
   initialized) — no cleanup needed.
4. **7.4** — minted a locally-signed backend JWT (`core.security.create_access_token`) with an
   explicit `JWT_SECRET` shared between a one-off token-mint script and a restarted server
   process (env vars aren't shared across separate `python -c` invocations, so this had to be
   done deliberately to get a token the running server would actually verify). Confirmed via
   server log that `identity_resolver` genuinely attempted its Supabase calls, caught the
   exception itself (fail-closed, per `core/identity_resolver.py`'s own try/except), and let
   the request continue to `get_current_user`'s return — a materially deeper code path than
   7.2/7.3. The eventual 500 comes from the endpoint's own (unguarded)
   `resolve_request_tenant_scope` call.
5. **7.5** — `curl POST /approve` and `POST /reject`, no token → same DB boundary, before the
   service layer. The actual scoped-select/cross-tenant-not-found logic this task cares about
   is proven by Section 2/4's mocked unit tests (already green); documented that explicitly
   rather than re-claiming curl proved something it couldn't in this environment.
6. **7.6** — restarted the server with `AUTH_ENFORCED=true`. All 4 routes with no token, plus a
   malformed-token variant, returned **401** with zero Supabase calls (confirmed: no traceback
   in the log for any of these 5 requests) — a fully DB-independent, completely verified check.
   Malformed `decision_id` isn't independently reachable here; verified by inspection instead
   (Section 2's diff didn't touch the existing error path).
7. **7.7** — full report written to
   `openspec/changes/approval-queue-tenant-scoping/reports/2026-07-23-step-7-curl-endpoint-tests.md`
   with every command and its real response/traceback, plus an explicit summary table of what
   was proven locally vs. what's deferred to Stage 11 / task 10.5.

## Cleanup

- Both uvicorn processes (PID 24768 for the `AUTH_ENFORCED=false` run, PID 22840 for
  `AUTH_ENFORCED=true`) were killed with `taskkill /F` after their respective test batches.
- Confirmed no orphaned listener on port 8000 afterward (`curl` to `127.0.0.1:8000` returns no
  response / connection refused).
- No database state was created or changed (every write attempt failed before reaching
  Supabase), so no restore step was needed.

## Files touched

- `openspec/changes/approval-queue-tenant-scoping/tasks.md` — checked off 7.1-7.7 with notes
  on what was verified vs. deferred.
- `openspec/changes/approval-queue-tenant-scoping/reports/2026-07-23-step-7-curl-endpoint-tests.md`
  — new, full command/response log.
- `progress/impl_section7.md` — this report.

No production code was modified. No migration was created (Section 8 explicitly out of scope
for this task — requires founder confirmation before touching the live DB). No push to `main`
or deploy attempted (Section 10 out of scope).

## Scope discipline confirmed

- Did not touch `apps/backend/migrations/0033_*` (Section 8) — not created.
- Did not push to `main` or attempt any Stage 10/11 deploy step.
- Did not modify any file under `presentation/`, `services/`, or `core/` — this section is
  test-execution + documentation only, no code changes.

## Next step

Hand to reviewer for Section 7 verdict before marking the section `done` in any tracker.
