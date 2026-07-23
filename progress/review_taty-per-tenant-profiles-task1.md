# Review — task taty-per-tenant-profiles-task1

**Verdict:** APPROVED

## Scope verification

`git diff --stat HEAD` shows exactly one modified file
(`apps/backend/services/taty_service.py`, +91/-50) plus one new file
(`apps/backend/tests/test_taty_tenant_profiles.py`). No other file touched.
Matches tasks.md items 1.1–1.3 exactly. No scope creep.

## Checkpoints (Stage 5 — Implementación)

- Código compilable / sin syntax errors: [x] — module imports cleanly, pytest collects.
- Tests existentes pasan: [x] — collateral run of `test_taty_intent_router.py` +
  `test_taty_lead_router.py` (47 tests) reported unaffected; independently re-verified
  `bash init.sh` green (structure gate; RUN_TESTS not required for this scoped review since
  task's own suite was run directly).
- Tests nuevos pasan: [x] — independently re-ran `pytest apps/backend/tests/test_taty_tenant_profiles.py -v`:
  7 passed, 19 warnings, 3.60s.
- Linting/type checking: [x] — new/changed signatures fully typed
  (`_get_tenant_profile(self, tenant_id: str) -> Optional[Dict]`, `_error_response(self, error: str,
  start_time: float, error_code: Optional[str] = None) -> Dict`), consistent with existing file's
  loose-`Dict` convention (no regression).
- Docs-sync (canon vivo): [N/A] — no container/dependency change; `ARCHITECTURE.md` untouched
  correctly (decision #13 already documents per-tenant resolution direction; this task is
  internal to `taty_service.py`).

## Specific findings

1. **Shared-mutable-default-list bug avoided.** `apps/backend/services/taty_service.py:257`
   (`fuentes_habilitadas = list(DEFAULT_PROFILE["fuentes_habilitadas"])`) copies before
   conditionally appending `"contexia_fiscal"` for `is_cliente_cero` tenants
   (lines 258-259), and the merged profile dict overrides the key with the copy
   (lines 261-263). `test_cliente_cero_tenant_gets_contexia_fiscal_source_without_mutating_default`
   (test file lines 73-89) explicitly asserts `DEFAULT_PROFILE["fuentes_habilitadas"]` is
   untouched after the call — a real regression test, not tautological (it would fail if
   `.append()` were used directly on the module dict).

2. **`regimen: None` confirmed as the only default, no code path in this diff asserts a regime.**
   `DEFAULT_PROFILE["regimen"] = None` (taty_service.py:51), preserved through the merge
   (`**DEFAULT_PROFILE` spread, line 262, nothing overrides `regimen`).
   `test_provisioned_tenant_profile_regimen_is_none_by_default` asserts this directly.
   Matches design.md D1's compliance constraint and GROUND_TRUTH's "never atribuir firma
   profesional / never invent regulatory claims" rule. `_build_prompt` (task 2's job) still
   unconditionally interpolates `profile['regimen']` into the prompt string when `context` is
   non-empty (line 320) — this is the known, explicitly-flagged carry-over for task 2, not a
   task-1 defect, since `_build_prompt` was correctly left untouched per the task boundary.

3. **`_get_agent_profile` → `_get_tenant_profile` delegation deviation is reasonable and clearly
   flagged.** Both the progress report ("Deviation from the plan" section) and the code docstring
   itself (taty_service.py:216-222) state plainly that this is transitional, that task 2 must
   rewire `ask()` to call `_get_tenant_profile` directly, and that `_get_agent_profile` should
   then be deleted rather than left as a dead pass-through. This satisfies the instruction to
   "note this deviation clearly" — a task-2 implementer reading either artifact will not be
   confused about the delegator being permanent.

4. **Type annotations present and correct** on all new/changed signatura: `_get_tenant_profile`,
   `_error_response`'s new `error_code: Optional[str] = None` parameter, `DEFAULT_PROFILE: Dict`
   module constant.

5. **Test suite is hermetic.** `services.taty_service.get_supabase` is patched with a `MagicMock`
   (test file lines 21-34); no live Supabase URL/credentials required. Verified independently —
   `pytest apps/backend/tests/test_taty_tenant_profiles.py -v` passes standalone with no network
   dependency, consistent with the report's stated reason for deviating from the
   `test_financials_endpoint_tenant_scoping.py` hermetic-real-DB pattern (that pattern fails 2/4
   in this worktree due to missing live Supabase creds — a pre-existing environment limitation,
   not something this task introduced or is responsible for fixing).

6. **Read 3 tests closely for assertion quality, not just "no exception":**
   - `test_provisioned_tenant_profile_matches_legal_name` — asserts `profile["nombre_empresa"]`
     equals the mocked `legal_name`, `tenant_id` equals the mocked id, `nit` equals the mocked
     nit. Real field-mapping assertions, not just `is not None`.
   - `test_unknown_tenant_uuid_returns_none` — asserts `profile is None` when the mocked table
     returns an empty row set. Meaningful (would fail if the method incorrectly fell back to
     `DEFAULT_PROFILE` on empty results).
   - `test_legacy_non_uuid_key_returns_none_without_exception` — asserts `profile is None` for
     `"ferez-001"` with the Supabase mock never even being queried in a way that matters (the uuid
     validation short-circuits before the DB call at taty_service.py:233-237). Correctly exercises
     scenario 3 from the spec (legacy key degrades gracefully, no exception).
   None of the 7 tests are tautological or merely check that a mock was called with whatever it
   was configured to return.

7. **`AGENT_PROFILES` fully removed, not renamed.** `grep -n "AGENT_PROFILES" -r apps/backend`
   returns only two doc-comment mentions (the new test file's module docstring, and
   `_get_agent_profile`'s docstring explaining the dict was deleted) plus a stale `.pyc` binary
   match — no executable reference to the dict remains.

8. **GROUND_TRUTH compliance** — nothing in this diff asserts an unverified tax regime or
   misrepresents Contexia's corporate identity. `DEFAULT_PROFILE["regimen"] = None` is the sole
   regime-related addition, correctly deferring assertion to task 2's `_build_prompt` change.

## Independent verification run

- `pytest apps/backend/tests/test_taty_tenant_profiles.py -v` → 7 passed, 3.60s.
- `grep -n "AGENT_PROFILES" apps/backend/services/taty_service.py` → only the docstring mention
  at line 218 describing its removal; no live dict.
- `bash init.sh` → green (canon + harness structure + `feature_list.json` single-active-change
  invariant all OK).
- `git diff --stat HEAD` → confirms scope is exactly `taty_service.py` + new test file.

## Required changes (if any)

None. Task 1 is correctly scoped, TDD sequence is real (RED shown in the report via an
`ImportError`, then GREEN), the shared-mutable-list bug is genuinely avoided (not just claimed),
`regimen: None` is the true default with no assertion path in this diff, and the
`_get_agent_profile` deviation is transitional and clearly documented for the next implementer.
