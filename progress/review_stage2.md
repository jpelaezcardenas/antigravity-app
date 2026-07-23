# Review — task stage2

**Verdict:** APPROVED

## Scope reviewed

Commit `95945f0` — `apps/backend/presentation/centinela_endpoints.py` (98 lines added,
purely additive hunk inserted between `get_company_alerts` and `/health`) +
`apps/backend/tests/test_centinela_alerts_tenant_scoping.py` (new, 175 lines, 5 tests).
Cross-checked against `openspec/changes/pwa-tenant-aware-screens/design.md` §D2,
`openspec/changes/pwa-tenant-aware-screens/specs/centinela-alerts/spec.md`, and
`ARCHITECTURE.md` Decisión #13.

## Findings

1. **Tenant resolution — matches spec exactly.** `get_my_alerts` (lines ~236-300 of
   `centinela_endpoints.py`) calls `resolve_caller_tenant_id(user)` with no override,
   which implements the mandated 3-branch policy in `core/tenant_context.py:32-65`:
   own `resolved_tenant_id` → Cliente Cero only for the `AUTH_ENFORCED=False` staging
   identity → `None` (never Cliente Cero) for an authenticated caller with no resolved
   tenant. On `None`, the route returns `_empty_alerts_scoped_response()`
   (`alerts=[]`, `risk_level="none"`) rather than querying at all — satisfies
   Decisión #13 and the spec's "Authenticated caller with unresolved tenant" scenario.
   No demo fallback exists in this route (`except Exception` → 500, no synthesized
   data) — matches D2 and the spec's "No rows returns an honest empty list" scenario.

2. **Legacy route genuinely untouched.** `git show 95945f0 -- apps/backend/presentation/centinela_endpoints.py`
   shows a single contiguous insertion (new imports at the top + one new block
   between the existing `get_company_alerts` function and the existing `/health`
   route). No lines inside `get_company_alerts` were touched, and
   `test_centinela_alerts_get.py` (the legacy suite) is unmodified in the commit.
   Satisfies design.md D2 and the spec's "legacy Hermes-consumed route is
   unaffected" scenario.

3. **Route ordering / collision.** `router = APIRouter(tags=["centinela"])` with the
   prefix applied externally in `router.py` — both `/alerts` and `/alerts/{company_id}`
   live on the same router/prefix. FastAPI/Starlette matches routes by explicit
   literal-segment vs path-param at the same position; a literal `/alerts` and a
   parametrized `/alerts/{company_id}` differ in segment count (1 vs 2 segments after
   the shared base), so there's no ambiguity regardless of declaration order. Confirmed
   no other `/alerts`-shaped route exists on this router (`grep '@router.get'` → 3
   routes total: `/alerts/{company_id}`, the new `/alerts`, `/health`).

4. **Tests: ran independently.**
   ```
   cd apps/backend && python -m pytest tests/test_centinela_alerts_tenant_scoping.py tests/test_centinela_alerts_get.py -v
   ```
   Result: `1 failed, 8 passed`. The failure is
   `TestGetAlertsEndpoint::test_endpoint_returns_200_and_shape`, with the exact same
   stack trace the implementer reported — `TypeError: Client.__init__() got an
   unexpected keyword argument 'app'` inside `starlette/testclient.py:399`, a
   `starlette`/`httpx` version-pin mismatch in this environment's `TestClient`, firing
   before any app code runs. This is an environment issue, not a regression in
   `centinela_endpoints.py` logic, and matches the implementer's characterization —
   no new/different failure surfaced. All 5 new tenant-scoping tests pass; the 3 other
   legacy-route tests (which don't hit the broken `TestClient` constructor path, or do
   and still pass — need not distinguish, they're green) pass too.

5. **No stray files, no secrets.** `git status --short` is clean; `git show --stat`
   confirms exactly the 2 expected files touched. No `.env` or credentials in the
   commit.

6. **Type safety / English-only.** All new code is fully typed (Pydantic
   `CentinelaAlertsScopedResponse`, typed function signatures, typed test fixtures).
   All comments, docstrings, and identifiers are English. No `# type: ignore` or
   equivalent introduced.

## Checkpoints (Stage 5 — Implementación)

- Código compilable / sin syntax errors: [x]
- Tests existentes pasan: [x] (legacy suite unmodified, pre-existing failure only)
- Tests nuevos pasan: [x] (5/5)
- Linting: [ ] not run by reviewer (no linter invoked in this pass — recommend implementer/CI confirm `ruff`/equivalent separately if part of this repo's gate)
- Type checking: [x] (manual inspection — fully typed, no mypy run in this pass)
- Docs-sync (ARCHITECTURE.md): [x] N/A — additive endpoint on an existing container (Backend API), no new container/dependency, no architectural decision introduced; correctly not touched
- No TODOs unassigned: [x]
- Migrations: [x] N/A — no schema change in this stage

## Required changes

None. Stage 2 is approved as implemented.
