# Review — task pwa-tenant-aware-screens Stage 1

**Verdict:** APPROVED

## Scope reviewed

Commits `7403968` (refactor: extract shared tenant resolver) and `6bd77de` (docs: check off
Stage 1 + Stage 4.1 + implementer report), against `design.md` §D1, `tasks.md` Stage 1,
`ARCHITECTURE.md` Decisión #13, and `DEPLOYMENT_STAGE/CHECKPOINTS.md` Stage 5/6.

## Findings

1. **`core/tenant_context.py::resolve_caller_tenant_id`** — correctly implements the
   3-branch policy from design.md D1 and ARCHITECTURE.md Decisión #13:
   `resolved_tenant_id` wins → staging identity (`_STAGING_USER["id"]`) falls back to Cliente
   Cero via an injectable resolver → any other authenticated caller gets `None` (never Cliente
   Cero). Verified line-by-line against the diff (`apps/backend/core/tenant_context.py:31-64`).
   - **`cliente_cero_resolver` deviation from the literal design.md signature is justified.**
     `tests/test_financials_endpoint_tenant_scoping.py::test_staging_identity_falls_back_to_cliente_cero`
     and `::test_authenticated_unresolved_tenant_returns_empty_not_cliente_cero` both
     `monkeypatch.setattr(endpoints_module, "_resolve_cliente_cero_tenant_id", ...)` and assert
     it was/was-not called (lines 128-158 of the test file). That module-level attribute has to
     stay the thing actually invoked for the monkeypatch to have any effect; a helper that calls
     its own hardcoded internal resolver would silently defeat both tests' assertions (they'd
     still pass by accident on the first, but the "must never be called" assertion in the second
     would no longer be exercising real code). The injectable is optional and defaults to
     `_default_cliente_cero_resolver`, so default behavior matches the design.md contract for any
     future non-`/financials` call site — confirmed by design.md's own stated purpose ("Stage 2/3
     call sites can simply call `resolve_caller_tenant_id(user)` with no override").
   - **Import-cycle claim verified false-negative-checked**: `core/deps.py` does not import
     `core.tenant_context` anywhere (`grep` confirms zero references), so the new top-level
     `from core.deps import _STAGING_USER` in `tenant_context.py` is safe. The `get_supabase`
     local import inside `_default_cliente_cero_resolver` is stylistic, not required for cycle
     safety — correctly described as such in the report, not overclaimed.

2. **`presentation/financials_endpoints.py::get_financials`** — pure behavior-preserving
   refactor. The three inline branches are gone, replaced by a single call to
   `resolve_caller_tenant_id(user, cliente_cero_resolver=_resolve_cliente_cero_tenant_id)` +
   `if tenant_id is None: return _empty_snapshot()`. `_resolve_cliente_cero_tenant_id()` is
   unchanged in body and still present as the monkeypatch seam, with a docstring explaining why
   it wasn't inlined. No new logic, no removed branch, no changed early-return shape.

3. **Test verification (independent run, not just trusting the report):**
   ```
   cd apps/backend && python -m pytest tests/test_financials_endpoint_tenant_scoping.py \
     tests/test_financials_aggregation.py tests/test_auth_deps.py \
     tests/test_tenant_context_resolver.py -q
   → 39 passed, 20 warnings in 41.76s
   ```
   Matches the implementer's reported output exactly. All 4 tenant-scoping regression tests
   (own-tenant, two-tenant isolation, staging→Cliente Cero, authenticated-unresolved→empty) pass
   unmodified — the file was not touched by commit `7403968` (confirmed via `git show --stat`).

4. **`git status` / `git log --stat`** — working tree clean (`nothing to commit`). Commit
   `7403968` touches exactly 3 files: `core/tenant_context.py`,
   `presentation/financials_endpoints.py`, and the new `tests/test_tenant_context_resolver.py`
   (72 lines, network-free, all 4 new unit tests independently verified green). Commit `6bd77de`
   touches only `tasks.md` (checking off 1.1/1.2 and, separately, the pre-existing Stage 4.1
   pg_cron-verification WIP the implementer explicitly flagged as "not mine" in the report) and
   the new `progress/impl_stage1.md`. No unrelated files, no `app/` hand-edits, no `.env`
   committed — `apps/backend/.env` exists locally (created per the implementer's documented
   local-environment note, using the public/publishable anon key already tracked in
   `js/supabase-client.js`) but has zero git history (`git log --all -- apps/backend/.env` is
   empty) and is gitignored.

5. **English-only / typed** — all new/changed code and comments are English. New function
   signature is fully typed (`Optional[Callable[[], Awaitable[Optional[str]]]]`); no `Any`
   smuggled in. Docstrings are substantive (explain the injectable's purpose and cite
   design.md D1), not filler.

## Checkpoints (Stage 5/6 of CHECKPOINTS.md, applicable subset for a backend refactor task)

- Código compilable / sin syntax errors: [x]
- Tests existentes pasan (unmodified regression suite): [x]
- Tests nuevos pasan: [x]
- Type checking (Python type hints): [x]
- Docs-sync (canon vivo): [x] N/A — no container/dependency change; this is an internal
  refactor of existing, already-documented policy (ARCHITECTURE.md Decisión #13 already
  describes the 3-branch policy this formalizes; no new architectural decision introduced).
- No hardcoded secrets: [x] — `.env` is local-only, gitignored, uses a publishable anon key.
- No "FIXME"/"HACK" without an issue: [x] — none present.

## Required changes

None. Stage 1 is correctly scoped, TDD-verified, and does not overreach into Stage 2/3.
