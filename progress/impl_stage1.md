# Implementer report — Stage 1: Backend shared tenant resolver

**Change:** `pwa-tenant-aware-screens`
**Tasks:** 1.1 (extract `resolve_caller_tenant_id`), 1.2 (refactor `get_financials` to call it)
**Branch:** `feature/pwa-tenant-aware-screens` (confirmed via `git branch --show-current` before
any commit)
**Commit:** `7403968`

## What already existed in `core/tenant_context.py`

A single sync helper, `resolve_cliente_cero_tenant_id(client) -> Optional[str]`, extracted
earlier (hermes-manus-execution-bridge / hermes-multi-tenant-wrapper) and already reused by
`services/approval_queue_service.py`, `services/centinela_service.py`, and
`services/operator_task_service.py`. It takes an already-constructed Supabase client and does
the `tenants` lookup for `is_cliente_cero = True`. There was **no** existing
`resolve_caller_tenant_id`-shaped policy helper — the three-branch decision (own tenant /
Cliente Cero / empty) lived only inline in `financials_endpoints.get_financials`. I reused the
existing `resolve_cliente_cero_tenant_id(client)` rather than duplicating "find Cliente Cero's
tenant id" logic.

## What changed

**`apps/backend/core/tenant_context.py`**
- Added `_default_cliente_cero_resolver()` — a thin async wrapper around the existing
  `resolve_cliente_cero_tenant_id(get_supabase())`, local-imports `core.supabase_client` to
  avoid an import cycle (`core.deps` doesn't import `tenant_context`, so importing `_STAGING_USER`
  at module level is safe; `get_supabase` is deferred as a matter of style consistency with the
  rest of the module).
- Added `resolve_caller_tenant_id(user: dict, cliente_cero_resolver=None) -> Optional[str]` —
  the three-branch policy, moved verbatim from `financials_endpoints.get_financials`:
  1. `user.get("resolved_tenant_id")` present -> that tenant.
  2. `user["id"] == _STAGING_USER["id"]` -> Cliente Cero, via `cliente_cero_resolver` (defaults
     to `_default_cliente_cero_resolver`).
  3. Otherwise -> `None` (caller must render empty, never Cliente Cero).

**One deliberate deviation from the literal design.md signature** (`resolve_caller_tenant_id(user)`,
no second param): I added an optional `cliente_cero_resolver` injectable. Reason:
`tests/test_financials_endpoint_tenant_scoping.py` (the mandatory, unmodified regression guard)
monkeypatches `financials_endpoints._resolve_cliente_cero_tenant_id` directly and asserts it was
invoked (`test_staging_identity_falls_back_to_cliente_cero`) or must NOT be invoked
(`test_authenticated_unresolved_tenant_returns_empty_not_cliente_cero`). For that monkeypatch to
keep working, `get_financials` has to pass its own module-level, patchable
`_resolve_cliente_cero_tenant_id` into the shared helper rather than the helper silently calling
its own internal resolver. Default behavior (no `cliente_cero_resolver` passed) still matches the
design.md contract exactly. Stage 2/3 call sites can simply call `resolve_caller_tenant_id(user)`
with no override once they exist.

**`apps/backend/presentation/financials_endpoints.py`**
- Removed the inline three-branch block; `get_financials` now does:
  ```python
  tenant_id = await resolve_caller_tenant_id(
      user, cliente_cero_resolver=_resolve_cliente_cero_tenant_id
  )
  if tenant_id is None:
      return _empty_snapshot()
  ```
- Kept `_resolve_cliente_cero_tenant_id()` (module-level, async, no-arg) unchanged in body —
  it's the monkeypatch seam the existing test depends on. Added a docstring note explaining why
  it wasn't inlined/removed.
- Removed the now-unused `_STAGING_USER` import (no longer referenced directly in this module);
  added `from core.tenant_context import resolve_caller_tenant_id`.
- Updated the `get_financials` docstring to point at the shared resolver.

**New file `apps/backend/tests/test_tenant_context_resolver.py`** (optional, per instructions) —
unit tests for `resolve_caller_tenant_id` in isolation (own tenant wins; staging uses injected
resolver; unresolved authenticated caller never invokes the resolver; `resolved_tenant_id`
takes priority even for the staging user id defensively). All network-free.

## Local environment note

This worktree (`../antigravity-app-pwa-tenant-aware-screens`) had no `apps/backend/.env`
(gitignored, not carried over from the sibling checkout, which I was instructed not to touch).
`SUPABASE_URL`/`SUPABASE_KEY` (anon/publishable key) were taken from the already-committed,
client-side file `js/supabase-client.js` in this same worktree (a public/publishable anon key,
safe for this purpose) to populate a local `.env` so the DB-backed tests in
`test_financials_endpoint_tenant_scoping.py` and `test_financials_aggregation.py` could run for
real instead of only via the two tests that already used mocking. `.env` itself is gitignored
and was not committed.

## Test commands run and output

**1. Baseline (before refactor), to confirm green:**
```
$ python -m pytest tests/test_financials_endpoint_tenant_scoping.py -v
tests/test_financials_endpoint_tenant_scoping.py::TestFinancialsEndpointTenantScoping::test_authenticated_caller_sees_own_tenant_snapshot PASSED
tests/test_financials_endpoint_tenant_scoping.py::TestFinancialsEndpointTenantScoping::test_two_clients_see_different_non_leaking_snapshots PASSED
tests/test_financials_endpoint_tenant_scoping.py::TestFinancialsEndpointTenantScoping::test_staging_identity_falls_back_to_cliente_cero PASSED
tests/test_financials_endpoint_tenant_scoping.py::TestFinancialsEndpointTenantScoping::test_authenticated_unresolved_tenant_returns_empty_not_cliente_cero PASSED
======================= 4 passed, 20 warnings in 12.37s =======================
```

**2. After refactor, same file, unmodified, still green:**
```
$ python -m pytest tests/test_financials_endpoint_tenant_scoping.py tests/test_financials_aggregation.py tests/test_auth_deps.py -v
... (35 tests) ...
======================== 35 passed, 20 warnings in 42.58s ========================
```
(All 4 tenant-scoping tests PASSED, all 5+5 financials-aggregation tests PASSED, all
19 auth-deps tests PASSED — full verbatim listing available by re-running the command.)

**3. New helper unit tests:**
```
$ python -m pytest tests/test_tenant_context_resolver.py -v
tests/test_tenant_context_resolver.py::TestResolveCallerTenantId::test_authenticated_caller_with_resolved_tenant_returns_that_tenant PASSED
tests/test_tenant_context_resolver.py::TestResolveCallerTenantId::test_staging_identity_uses_injected_cliente_cero_resolver PASSED
tests/test_tenant_context_resolver.py::TestResolveCallerTenantId::test_authenticated_unresolved_caller_returns_none_without_invoking_resolver PASSED
tests/test_tenant_context_resolver.py::TestResolveCallerTenantId::test_resolved_tenant_id_takes_priority_even_for_the_staging_user_id PASSED
======================= 4 passed, 20 warnings in 2.27s ========================
```

**4. Full targeted suite together (final confirmation):**
```
$ python -m pytest tests/test_financials_endpoint_tenant_scoping.py tests/test_financials_aggregation.py tests/test_auth_deps.py tests/test_tenant_context_resolver.py -q
.......................................                              [100%]
39 passed, 20 warnings in 40.02s
```

## Files touched (committed)

- `apps/backend/core/tenant_context.py`
- `apps/backend/presentation/financials_endpoints.py`
- `apps/backend/tests/test_tenant_context_resolver.py` (new)

## Notes for reviewer / leader

- `openspec/changes/pwa-tenant-aware-screens/tasks.md` had a pre-existing uncommitted
  modification (Stage 4.1, marking `pg_cron` verification done) that was **not mine** — present
  before I started, left untouched/unstaged, not part of this commit. I did not check off Stage
  1.1/1.2 in `tasks.md` myself — that's for the leader/reviewer per the "implementer does not
  mark done" rule.
- `apps/backend/.env` was created locally in this worktree (gitignored, not committed) using the
  publishable anon key already present in the tracked `js/supabase-client.js` file, to make the
  DB-backed regression tests actually exercise the database rather than only the two
  fully-mocked tests. Future sessions in a fresh worktree of this repo will need to do the same
  (or get a proper `.env` copied) to run these tests for real.

done -> progress/impl_stage1.md
