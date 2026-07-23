# Task 8 — Manual Endpoint Testing with curl (implementer report)

Date: 2026-07-23
Branch: `feature/taty-per-tenant-profiles` (confirmed via `git branch --show-current`)

## Scope

`openspec/changes/taty-per-tenant-profiles/tasks.md` Section 8 only (items 8.1-8.7). No source
files modified — this was a testing-only task.

## What was done

1. Confirmed `AUTH_ENFORCED` defaults to `False` in `apps/backend/config.py:31`.
2. Started the real FastAPI backend locally with uvicorn
   (`python -m uvicorn main:app --host 127.0.0.1 --port 8000`) from `apps/backend/`, backgrounded,
   polled `/api/v1/health` until 200.
3. Confirmed the app boots cleanly with zero Supabase credentials configured — all 60 routes
   registered, no startup crash.
4. Ran every curl scenario that is actually reachable in this environment:
   - 8.2 (unauthenticated GET, staging→Cliente-Cero path): routed correctly through
     `_resolve_cliente_cero_tenant_id()`, but returns `HTTP 500` because that specific helper
     (unlike `TatyAgentService.ask()`/`_get_tenant_profile()`) has no graceful-degradation
     contract and raises `SupabaseException("supabase_url is required")` with no live Supabase —
     documented as a finding, not silently swept under "PASS."
   - 8.6 (deleted `/agents/taty/ask` route): confirmed 404.
   - 8.7 (malformed body): confirmed 422 for both under-length and missing `question`.
5. Documented 8.3-8.5 (provisioned-client JWT scenarios) as **not executable locally** —
   no Supabase credentials means no way to mint a real ES256/JWKS-signed session JWT — and
   deferred them explicitly to Stage 11 (tasks.md 11.6/11.7), matching task 7's precedent for
   the same environment constraint. No curl output was fabricated for these.
6. Stopped the background uvicorn process cleanly (`taskkill /F /PID 15344`).

## Mandatory curl report

`openspec/changes/taty-per-tenant-profiles/reports/2026-07-23-step-8-manual-curl.md` — every
command actually run, with real pasted output (HTTP status + body + server-side traceback where
relevant), a summary table of PASS/deferred status per item, and one open gap flagged for the
leader's attention: Stage 11 (section 11) has no dedicated item covering the "authenticated but
tenant-unresolved" scenario (8.5's production equivalent) — only 11.6 (provisioned client) and
11.7 (unauthenticated 401) exist. Worth a Stage 11 task addition or a manual spot-check if a
tenant-less test user exists in production.

## Constraints honored

- No source files modified.
- No curl output fabricated — every reported response was actually observed and pasted verbatim.
- Environment limitation (no local Supabase) documented precisely rather than worked around or
  hidden.
- Did not commit.
