# Implementation report — taty-per-tenant-profiles, task 2 (2.1–2.3)

Branch confirmed: `feature/taty-per-tenant-profiles` (`git branch --show-current`).

## Scope

`openspec/changes/taty-per-tenant-profiles/tasks.md` section "## 2. Backend: `ask()` Rename,
KB Keying, Régimen Omission (TDD)" only — items 2.1, 2.2, 2.3. No other section touched. Task
1 (`_get_tenant_profile`, `DEFAULT_PROFILE`, `_error_response(error_code=...)`) was already done
and committed (f72bdc5) — not modified here except deleting the transitional `_get_agent_profile`
delegator as instructed.

## Files touched

- **New**: `apps/backend/tests/test_taty_ask_tenant_scoping.py` (full file, 6 tests across 3
  classes)
- **Modified**: `apps/backend/services/taty_service.py`
  - `ask()` signature: `company_id: str` → `tenant_id: str` (param + docstring), body now calls
    `self._get_tenant_profile(tenant_id)` directly (was `self._get_agent_profile(company_id)`);
    unknown/unresolvable profile now returns `self._error_response("Cliente no configurado",
    start_time, error_code="tenant_not_found")` (previously no `error_code` was passed)
  - `_log_conversation(...)` call site inside `ask()`: `company_id=company_id` → `tenant_id=tenant_id`
  - Deleted `_get_agent_profile` entirely (task 1's transitional delegator to
    `_get_tenant_profile`) — `_get_tenant_profile` is now the sole profile resolver
  - `_retrieve_chunks`: `client_id = profile.get("company_id", "__global__")` →
    `client_id = profile["kb_client_id"]`
  - `_build_prompt`: régimen clause is now conditional — `regimen_clause = f" (Régimen
    {regimen})" if regimen else ""`, interpolated into the greeting line instead of the previous
    unconditional `(Régimen {profile['regimen']})`. Omits cleanly (no dangling "Régimen None" /
    no dangling label) when `profile.get("regimen")` is falsy. Both the `context`-present and
    `context`-empty branches of `_build_prompt` share this — verified only the `context`-present
    branch previously embedded `regimen`; the `context`-empty branch never referenced `regimen` at
    all (unchanged, correct as-is).
  - `_log_conversation(self, tenant_id: str, ...)`: renamed parameter from `company_id`, and the
    log-entry dict key from `"company_id"` to `"tenant_id"`.

Untouched by this task, as instructed: `_extract_citations`, `_check_escalation`,
`_build_system_prompt` (still reads `profile['nombre_empresa']`, unaffected by this task's scope),
`DEFAULT_PROFILE`, `_get_tenant_profile`, `_error_response`. `profile["company_id"]` (the dict
key sourced from `tenants.company_id`, set in `_get_tenant_profile`) was intentionally left
as-is — it is a legitimate DB-field-derived profile field, not a renamed `ask()` param.

## TDD sequence

### Step 1 — new tests written first, confirmed RED

```
FAILED test_taty_ask_tenant_scoping.py::TestBuildPromptRegimenOmission::test_regimen_none_omits_regimen_clause
  AssertionError: assert 'régimen' not in 'eres taty, ... para hermetic test tenant sas (régimen none). ...'
FAILED test_taty_ask_tenant_scoping.py::TestRetrieveChunksKbClientIdKeying::test_retrieve_chunks_passes_through_kb_client_id_to_retrieve_similar
  AssertionError: assert None == '22222222-2222-2222-2222-222222222222'
FAILED test_taty_ask_tenant_scoping.py::TestAskUsesTenantProfileDirectly::test_unknown_tenant_returns_tenant_not_found_error_code
  TypeError: TatyAgentService.ask() got an unexpected keyword argument 'tenant_id'
FAILED test_taty_ask_tenant_scoping.py::TestAskUsesTenantProfileDirectly::test_resolved_tenant_calls_get_tenant_profile_not_get_agent_profile
  AssertionError: _get_agent_profile must be fully removed in task 2 ...
================== 4 failed, 2 passed, 19 warnings in 6.73s ==================
```

(The 2 passes at RED time were `test_regimen_set_includes_regimen_clause` — trivially true since
the old unconditional interpolation always included the régimen text — and
`test_cliente_cero_profile_retrieves_with_ctx_001_client_id`, which passed only by accident
because the old fallback keyed off `profile.get("company_id", "__global__")` and the Cliente Cero
fixture profile happened to also set `company_id="ctx-001"`; the real assertion under test —
"`_retrieve_chunks` reads `kb_client_id` specifically" — was the one that failed, in the sibling
test. Both are genuinely GREEN after the implementation change for the right reason, verified
below.)

### Step 2 — implementation applied, all tests GREEN

```
apps/backend/tests/test_taty_ask_tenant_scoping.py::TestBuildPromptRegimenOmission::test_regimen_none_omits_regimen_clause PASSED
apps/backend/tests/test_taty_ask_tenant_scoping.py::TestBuildPromptRegimenOmission::test_regimen_set_includes_regimen_clause PASSED
apps/backend/tests/test_taty_ask_tenant_scoping.py::TestRetrieveChunksKbClientIdKeying::test_retrieve_chunks_passes_through_kb_client_id_to_retrieve_similar PASSED
apps/backend/tests/test_taty_ask_tenant_scoping.py::TestRetrieveChunksKbClientIdKeying::test_cliente_cero_profile_retrieves_with_ctx_001_client_id PASSED
apps/backend/tests/test_taty_ask_tenant_scoping.py::TestAskUsesTenantProfileDirectly::test_unknown_tenant_returns_tenant_not_found_error_code PASSED
apps/backend/tests/test_taty_ask_tenant_scoping.py::TestAskUsesTenantProfileDirectly::test_resolved_tenant_calls_get_tenant_profile_not_get_agent_profile PASSED
apps/backend/tests/test_taty_tenant_profiles.py::TestGetTenantProfileProvisionedTenant::test_provisioned_tenant_profile_matches_legal_name PASSED
apps/backend/tests/test_taty_tenant_profiles.py::TestGetTenantProfileProvisionedTenant::test_provisioned_tenant_profile_regimen_is_none_by_default PASSED
apps/backend/tests/test_taty_tenant_profiles.py::TestGetTenantProfileProvisionedTenant::test_cliente_cero_tenant_gets_contexia_fiscal_source_without_mutating_default PASSED
apps/backend/tests/test_taty_tenant_profiles.py::TestGetTenantProfileUnknownTenant::test_unknown_tenant_uuid_returns_none PASSED
apps/backend/tests/test_taty_tenant_profiles.py::TestGetTenantProfileLegacyNonUuidKey::test_legacy_non_uuid_key_returns_none_without_exception PASSED
apps/backend/tests/test_taty_tenant_profiles.py::TestErrorResponseErrorCode::test_error_response_includes_error_code_when_provided PASSED
apps/backend/tests/test_taty_tenant_profiles.py::TestErrorResponseErrorCode::test_error_response_omits_error_code_when_not_provided PASSED

======================= 13 passed, 19 warnings in 3.65s =======================
```

`test_taty_tenant_profiles.py` (task 1's suite) re-run in the same invocation with no
modification — still 7/7 green, no regression. It never referenced `_get_agent_profile` (verified
by grep before touching anything — no blocking finding, contrary to the constraint's cautionary
scenario).

### Design-D7 verification against real `kb_seeding_service.py` (not assumed)

Read `retrieve_similar()` in `apps/backend/services/kb_seeding_service.py:254-271`: both the
pgvector and in-memory branches already retry with `client_id="__global__"` internally when the
first lookup returns no results. Design D7's claim ("no change needed in `kb_seeding_service.py`")
is confirmed true. Test 2.1.b was therefore written as "pass-through" (assert `_retrieve_chunks`
calls `retrieve_similar(client_id=profile["kb_client_id"])` verbatim), not as a
special-case-fallback test inside `taty_service.py` — matches reality per the task instructions.

## Collateral regression check

```
pytest apps/backend/tests/test_taty_intent_router.py apps/backend/tests/test_taty_lead_router.py -q
...
47 passed, 19 warnings in 3.12s
```

No regression — neither suite calls `TatyAgentService.ask()` or the removed `_get_agent_profile`.

## Module import check (standalone)

```
$ python -c "import sys; sys.path.insert(0,'.'); import services.taty_service; print('import OK')"
(run from apps/backend/)
import OK
```
(One unrelated dev-only warning printed: "JWT_SECRET not set — using auto-generated secret for
development" — from an unrelated module's import-time side effect, not from `taty_service.py`;
does not affect import success.)

## Broken external callers found (NOT fixed in this task — tasks 3/4 own the fix)

All three still pass `company_id=` as a keyword argument to `ask()`, which now fails with
`TypeError: ask() got an unexpected keyword argument 'company_id'` (positional-if-untyped would
also break since the param itself was renamed):

1. `apps/backend/presentation/agents_endpoints.py:63` — `response = taty.ask(company_id=request.company_id, question=request.question, channel="api")` (the deprecated `POST /api/v1/agents/taty/ask` route — task 5 deletes this route entirely, so it may be moot rather than needing a rename)
2. `apps/backend/presentation/taty_endpoints.py:144` — `response = taty.ask(company_id=request.company_id, question=request.question, channel=request.channel, conversation_id=request.conversation_id, user_id=request.user_id, hermes_profile=x_hermes_profile,)` (also line 138 has a non-functional `logger.info` referencing `request.company_id` — that's a Pydantic request field, not this rename, so it doesn't break, but its log label is now inconsistent with the new `ask()` semantics until task 3 addresses the endpoint)
3. `apps/backend/presentation/telegram_endpoints.py:154` — `response = taty.ask(company_id=company_id, question=user_text, channel="telegram", user_id=user_id,)` (task 4's `_resolve_tenant_for_company_id` translation lands here)

No test file calls `.ask(` other than the new `test_taty_ask_tenant_scoping.py` (grepped
`apps/backend/tests` for `\.ask\(` scoped to taty-related test files — confirmed by name-match
+ content-grep, no other hits).

These three call sites will raise `TypeError` at runtime today if invoked (endpoints not covered
by an automated smoke test in this task's scope) until tasks 3/4/5 land. This is expected per
design D5 ("hard rename, no compat shim... all 3 live callers are updated in this same
[OpenSpec] change") — flagging explicitly per the task's report requirement, not fixing here
(out of this task's scope boundary).

## Deviations

None from the plan. `_get_agent_profile` was deleted cleanly (task 1's report already flagged
this as the expected task-2 action); `_get_tenant_profile` required no changes. Task 1's test
file was confirmed (by grep, before any edit) to never reference `_get_agent_profile` — no
blocking finding.

## Not done in this task (explicitly out of scope, deferred to later tasks.md sections)

- Endpoint auth changes making the 3 callers above pass `tenant_id=` correctly (task 3)
- Telegram `_resolve_tenant_for_company_id` translation helper (task 4)
- Deletion of the deprecated `POST /api/v1/agents/taty/ask` route (task 5)
- `apps/backend/tests` broader audit for other `AGENT_PROFILES`/`ctx-001`/`ferez-001` references
  (task 6)
