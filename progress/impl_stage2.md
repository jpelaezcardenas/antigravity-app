# Stage 2 — Backend: tenant-scoped alerts route (TDD)

## What I found

- `apps/backend/presentation/centinela_endpoints.py` had one existing route,
  `GET /alerts/{company_id}` (`get_company_alerts`), consumed by Hermes's
  `CentinelaAlertsTool`, with a demo fallback when Supabase has no rows for the
  given `company_id`. Not touched.
- `apps/backend/core/tenant_context.py` already had `resolve_caller_tenant_id(user,
  cliente_cero_resolver=None)` from Stage 1 (commit `7403968`) — read-only, not
  modified. Its default `cliente_cero_resolver` is `_default_cliente_cero_resolver`
  (module-level function), which I used directly (no override) per task instructions.
- `centinela_alerts.company_id` FKs to `agent_profiles.company_id` — the only
  existing row observed via the anon client is `"ctx-001"`, so hermetic test rows
  reuse that literal `company_id` while isolation is asserted purely on `tenant_id`
  (which is what the new route filters by, and what the test tenants/cleanup are
  scoped to).
- `.env` already existed in this worktree (created by the Stage 1 implementer);
  no new `.env` needed.

## What I changed

`apps/backend/presentation/centinela_endpoints.py`:
- Added imports: `Depends` from fastapi, `get_current_user` from `core.deps`,
  `resolve_caller_tenant_id` from `core.tenant_context`.
- Added `CentinelaAlertsScopedResponse` (no `company_id` field — the caller's
  tenant is resolved server-side, not passed as a free-text path param) and
  `_empty_alerts_scoped_response()` (hardcodes `risk_level: "none"` per spec).
- Added `GET /alerts` (`get_my_alerts`): `Depends(get_current_user)`, calls
  `resolve_caller_tenant_id(user)` plainly (no injected resolver — this route has
  no prior monkeypatch seam to preserve, unlike `financials_endpoints.py`); on
  `None` tenant returns the empty response; otherwise queries `centinela_alerts`
  filtered by `tenant_id`, ordered `created_at desc`, `limit=20` default, via
  `get_supabase()` (anon client — same as the rest of this file; RLS on
  `centinela_alerts` currently has a coexisting allow-all policy, same as the
  legacy route's `get_service_supabase()` usage). No demo fallback — Supabase
  errors bubble to the existing `except Exception` → 500 pattern.
- Route ordering: `/alerts` (literal) and `/alerts/{company_id}` (path param)
  don't collide — Starlette matches by segment count, order in the file doesn't
  matter here.

`apps/backend/tests/test_centinela_alerts_tenant_scoping.py` (new, 5 tests):
1. `test_authenticated_caller_sees_own_tenant_alerts_only`
2. `test_two_tenants_never_see_each_others_alerts`
3. `test_resolved_tenant_with_no_rows_returns_honest_empty_list`
4. `test_staging_identity_falls_back_to_cliente_cero` (monkeypatches
   `core.tenant_context._default_cliente_cero_resolver`, mirrors the assertion
   pattern in `test_financials_endpoint_tenant_scoping.py`, adapted since this
   route has no module-level monkeypatchable resolver of its own)
5. `test_authenticated_unresolved_tenant_returns_empty_never_cliente_cero`
   (asserts the Cliente Cero resolver is never invoked, `risk_level == "none"`)

Uses hermetic throwaway tenants (`tenants` table insert/delete) and
`centinela_alerts` rows created/deleted in fixture teardown — no production data
touched.

## TDD sequence

1. Wrote the 5 tests first against a not-yet-existing `get_my_alerts` — collection
   would fail (import error) until the route existed.
2. Implemented the route.
3. Iterated on two hermetic-data snags surfaced by real Supabase constraints (not
   mocked): (a) my first staging-identity test's fake Cliente Cero tenant id
   wasn't a valid UUID (Postgres `22P02`) — fixed by returning a real UUID; (b) my
   first inserts used synthetic `company_id`s that don't exist in `agent_profiles`
   (FK violation `23503`) — fixed by reusing the existing `"ctx-001"` row's id and
   asserting isolation on `tenant_id` only.

## Test output

```
cd apps/backend && python -m pytest tests/test_centinela_alerts_tenant_scoping.py tests/test_centinela_alerts_get.py -v
```

```
tests/test_centinela_alerts_tenant_scoping.py::TestCentinelaAlertsEndpointTenantScoping::test_authenticated_caller_sees_own_tenant_alerts_only PASSED
tests/test_centinela_alerts_tenant_scoping.py::TestCentinelaAlertsEndpointTenantScoping::test_two_tenants_never_see_each_others_alerts PASSED
tests/test_centinela_alerts_tenant_scoping.py::TestCentinelaAlertsEndpointTenantScoping::test_resolved_tenant_with_no_rows_returns_honest_empty_list PASSED
tests/test_centinela_alerts_tenant_scoping.py::TestCentinelaAlertsEndpointTenantScoping::test_staging_identity_falls_back_to_cliente_cero PASSED
tests/test_centinela_alerts_tenant_scoping.py::TestCentinelaAlertsEndpointTenantScoping::test_authenticated_unresolved_tenant_returns_empty_never_cliente_cero PASSED
tests/test_centinela_alerts_get.py::TestGetAlertsForCompany::test_falls_back_to_demo_when_supabase_unavailable PASSED
tests/test_centinela_alerts_get.py::TestGetAlertsForCompany::test_severity_filter_demo_fallback PASSED
tests/test_centinela_alerts_get.py::TestGetAlertsForCompany::test_returns_supabase_data_when_available PASSED
tests/test_centinela_alerts_get.py::TestGetAlertsEndpoint::test_endpoint_returns_200_and_shape FAILED

1 failed, 8 passed, 20 warnings in 23.56s
```

The single failure (`TestGetAlertsEndpoint::test_endpoint_returns_200_and_shape`)
is a pre-existing `TypeError: Client.__init__() got an unexpected keyword
argument 'app'` from a `starlette`/`httpx` version mismatch in this environment's
`TestClient` — **verified pre-existing** by `git stash`-ing my changes and
re-running just that file: same single failure, 3/4 passing, before any of my
edits. Not caused by, and not fixable within, this task's scope (it's an
environment/dependency-pinning issue unrelated to `centinela_endpoints.py`
route logic). The other 3 tests in that legacy-route file, and all 5 of my new
tests, are green.

## Constraints honored

- Did not touch `financials_endpoints.py`, `financials_service.py`, or
  `core/tenant_context.py` (read-only).
- Did not stage/commit `progress/impl_stage3.md` or `progress/review_stage1.md`
  (untracked files belonging to the concurrent Stage 3 agent) — verified with
  `git status --short` before `git add`.
- Did not check off `tasks.md`.

## Commit

`95945f0` — `feat(pwa-tenant-aware-screens): tenant-scoped GET /api/v1/centinela/alerts`
(branch `feature/pwa-tenant-aware-screens`, worktree
`antigravity-app-pwa-tenant-aware-screens`).

Files touched:
- `apps/backend/presentation/centinela_endpoints.py`
- `apps/backend/tests/test_centinela_alerts_tenant_scoping.py` (new)
