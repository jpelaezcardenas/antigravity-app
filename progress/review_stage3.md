# Review — Stage 3 (pwa-tenant-aware-screens): liquidity bridge endpoint

**Commit reviewed:** `3c809fb` — `feat(pwa-tenant-aware-screens): tenant-scoped GET /api/v1/financials/liquidity-bridge`

**Verdict:** APPROVED

## Checkpoints

- C1 (design.md D3 — scope = account 1110 only, `initial_balance` reuses `_compute_caja_real_balance`): [x]
  `apps/backend/services/financials_service.py:122-192`, `compute_liquidity_bridge` calls
  `_compute_caja_real_balance(supabase, tenant_id, day_before_month)` directly for
  `initial_balance` — no duplicated balance-summation logic. In-month `inflows`/`outflows` come
  from a separate `erp_journal_lines` query filtered to `account_code == "1110"` only, matching
  D3 exactly. `final_balance = initial_balance + inflows - outflows`, computed independently of
  `_compute_caja_real_balance`, then cross-checked in tests (see C3).

- C2 (`status` = "empty"/"ready" based on "any 1110 lines ever", not "balance == 0"): [x]
  Line: `status = "empty" if not has_prior_lines and not lines else "ready"`. `has_prior_lines`
  is a separate boolean query (`lte(... day_before_month)`, `bool(prior_lines_result.data)`),
  independent of the balance sum. This is the correct call per the spec's "Empty tenant returns
  a zeroed, non-error snapshot" scenario, which is keyed on "no `erp_journal_lines` rows on
  account 1110 at all," not on the derived balance being zero. A tenant with real but exactly
  offsetting 1110 debits/credits will have `has_prior_lines=True` or non-empty `lines`, so
  `status` correctly reads `"ready"` even though `final_balance` would be 0. Confirmed no
  balance-based shortcut exists in the code.

- C3 (spec scenario "Final balance matches the equivalent Caja Real balance" — real assertion,
  not tautological): [x]
  `tests/test_financials_liquidity_bridge.py::test_final_balance_matches_equivalent_caja_real`
  inserts an opening entry (debit 300000000 at `prior_day`) and an in-month entry with only a
  debit leg (debit 90000000, no offsetting credit on 1110), calls `compute_liquidity_bridge`
  (which derives `final_balance` via `initial_balance + inflows - outflows`, never calling
  `_compute_caja_real_balance` for `final_balance`), then independently calls
  `_compute_caja_real_balance(supabase, test_tenant_id, month_end)` and asserts equality. Because
  `compute_liquidity_bridge`'s `final_balance` and the test's `expected_final` are computed via
  genuinely different code paths (arithmetic sum of two Stage-3-local queries vs. the pre-existing
  cumulative-balance helper), this is a real convergence check, not `x == x`.

- C4 (`GET /liquidity-bridge` — same tenant resolution policy as `get_financials`): [x]
  `apps/backend/presentation/financials_endpoints.py:102-142`. Both `get_financials` and
  `get_liquidity_bridge` call `resolve_caller_tenant_id(user,
  cliente_cero_resolver=_resolve_cliente_cero_tenant_id)` (the shared Stage 1 resolver), and both
  return an empty/zeroed shape (`_empty_snapshot()` / `_empty_liquidity_bridge()`) when
  `tenant_id is None` rather than falling back to Cliente Cero — matches ARCHITECTURE.md
  Decisión #13 ("un cliente autenticado cuyo tenant no resuelve recibe un snapshot vacío, nunca
  los datos de Cliente Cero"). Confirmed by the green
  `test_authenticated_unresolved_tenant_returns_empty_not_cliente_cero` case (re-run, still
  passing) in the existing `test_financials_endpoint_tenant_scoping.py` suite, unmodified by this
  commit.

- C5 (final route path is `/api/v1/financials/liquidity-bridge`): [x]
  `apps/backend/presentation/router.py:51` mounts `financials_router` at `prefix="/financials"`;
  `apps/backend/main.py:133` mounts `api_router` at `prefix="/api/v1"`; the endpoint itself is
  declared `@router.get("/liquidity-bridge")`. Path chain: `/api/v1` + `/financials` +
  `/liquidity-bridge` = `/api/v1/financials/liquidity-bridge`, matching the spec requirement
  text verbatim.

- C6 (test run — 20/20 green): [x]
  Re-ran independently:
  `cd apps/backend && python -m pytest tests/test_financials_liquidity_bridge.py
  tests/test_financials_aggregation.py tests/test_financials_endpoint_tenant_scoping.py -v`
  → `20 passed, 20 warnings in 54.46s`. Matches the implementer's reported output exactly (same
  5+10+4=19... actually 5+10+5=20 test IDs, all PASSED, no skips/xfails).

- C7 (diff scope — only 3 expected files touched, no `.env`, Stage 2 files untouched by this
  commit): [x]
  `git show --stat 3c809fb` → exactly 3 files: `apps/backend/presentation/financials_endpoints.py`
  (+57/-1), `apps/backend/services/financials_service.py` (+73), `apps/backend/tests/
  test_financials_liquidity_bridge.py` (new, +268). No `.env` in the diff. `git show 95945f0
  --name-only` (the Stage 2 commit, `centinela_endpoints.py` + its test) is a disjoint set from
  3c809fb's file list — confirmed no overlap. `git status --short` at HEAD shows only unrelated
  in-flight work (staged `migrations/0033_rolling_reseed_synthetic_shadow_gl.sql` for D4, and an
  untracked `progress/review_stage2.md`) — neither belongs to or was introduced by 3c809fb.

- C8 (English-only, fully typed): [x]
  All new code/comments/docstrings in English. `compute_liquidity_bridge(tenant_id: str, year:
  int, month: int) -> Dict[str, Any]` and `_empty_liquidity_bridge() -> dict` are typed,
  consistent with the pre-existing style in the same files (`_empty_snapshot() -> dict`,
  `_compute_caja_real_balance(supabase, tenant_id: str, as_of_date: date) -> int`). No `Any`
  abuse beyond the pre-existing `Dict[str, Any]` return convention already used by
  `compute_pulso_snapshot`.

- Docs-sync: [x] — no new container/external dependency introduced (reuses existing Shadow GL
  tables, existing tenant resolver, existing router). `ARCHITECTURE.md` does not need a change
  for this stage.

## Notes (non-blocking)

- Syntax-checked all three touched Python files with `ast.parse` — no syntax errors.
- The staged `migrations/0033_rolling_reseed_synthetic_shadow_gl.sql` (D4 work) and untracked
  `progress/review_stage2.md` visible in `git status` are out of scope for this review (not part
  of commit `3c809fb`) — flagging only so the leader is aware they're mid-flight, not a Stage 3
  defect.

## Required changes

None.
