# Implementation report — taty-per-tenant-profiles, task 4 (4.1–4.3)

Branch confirmed: `feature/taty-per-tenant-profiles` (`git branch --show-current`).

## Scope

`openspec/changes/taty-per-tenant-profiles/tasks.md` section "## 4. Backend: Telegram Tenant
Translation (TDD)" only — items 4.1, 4.2, 4.3. No other file touched. The Social Ops onboarding
branch (`if active_ws:`, lines ~137-147 pre-change) was left untouched, as instructed.

## Files touched

- **New**: `apps/backend/tests/test_telegram_taty_tenant_translation.py` (full file, 8 tests
  across 3 classes)
- **Modified**: `apps/backend/presentation/telegram_endpoints.py`
  - Added `_resolve_tenant_for_company_id(company_id: str) -> Optional[str]` (new function,
    inserted before `verify_telegram_signature`, ~lines 59-74): sync (matches the file's existing
    convention — the `telegram_chat_mappings` query a few lines below is also a sync
    `.execute()` call inside the async `telegram_webhook` handler, not awaited). Does
    `get_supabase().table("tenants").select("id").eq("company_id", company_id).execute()`,
    returns `result.data[0]["id"]` or `None` if no row matched or on any exception (mirrors the
    existing try/except-and-log pattern used around the `telegram_chat_mappings` lookup).
  - At the `taty.ask(...)` call site (~lines 167-185): inserted a new "PASO 4" step that calls
    `_resolve_tenant_for_company_id(company_id)` before calling Taty. If it returns falsy, sends
    the exact existing "❌ Este chat no está configurado.\nContacta a soporte." message (same
    string already used for the "no hay empresa mapeada" case a few lines above) and returns
    `{"ok": True}` early — `taty.ask()` is never reached. If it returns a tenant_id, calls
    `taty.ask(tenant_id=tenant_id, question=user_text, channel="telegram", user_id=user_id)`
    (previously `taty.ask(company_id=company_id, ...)`).
  - Renumbered the trailing `# PASO 5` / `# PASO 6` comments to `# PASO 6` / `# PASO 7` to keep
    the existing step-numbering scheme consistent after inserting the new PASO 4/5 (tenant
    resolution + Taty call) — comment-only, no behavior change.

Untouched, as instructed: the Social Ops onboarding branch (`if active_ws:`, still reads the raw
`company_id` from the mapping unrelated to Taty), `taty_service.py`, `taty_endpoints.py`,
`agents_endpoints.py`, `taty_intent_router.py`, `core/deps.py`.

## Existing test file check

No `test_telegram_endpoints*.py` (or any `test_telegram*.py`) file existed in
`apps/backend/tests/` before this task (confirmed via `ls apps/backend/tests | grep -i
telegram` — no output). Created `test_telegram_taty_tenant_translation.py` as a new file, per
the fallback instruction. Its mocking convention mirrors `test_taty_endpoints_tenant_scoping.py`
(direct-function-call pattern, `monkeypatch.setattr` on module-level globals,
`_FakeTatyService`/forbidden-fake pattern for the "must never be called" assertion) for
consistency with the rest of this OpenSpec change's test suite, plus a minimal `_FakeRequest`
(async `.body()` only) since `telegram_webhook` takes a raw `fastapi.Request`, and a chainable
`_FakeSupabase`/`_FakeTable` that routes `.table("telegram_chat_mappings")` vs `.table("tenants")`
to distinct fixture rows (both real queries the webhook makes).

## TDD sequence

### Step 1 — new tests written first, confirmed RED

```
tests/test_telegram_taty_tenant_translation.py::TestTelegramCompanyIdToTenantTranslation::test_mapped_company_id_resolves_and_calls_ask_with_tenant_id FAILED
  KeyError: 'tenant_id'   (ask() was still being called with company_id=, matching pre-task-4 state)
tests/test_telegram_taty_tenant_translation.py::TestTelegramCompanyIdToTenantTranslation::test_untranslatable_company_id_sends_no_configurado_and_never_calls_ask FAILED
  AssertionError: taty.ask() must NOT be called for an untranslatable company_id
    (raised by the forbidden-fake ask(), proving ask() was called before any translation existed)
tests/test_telegram_taty_tenant_translation.py::TestResolveTenantForCompanyIdHelper::test_returns_tenant_id_when_matching_row_exists FAILED
  AttributeError: module 'presentation.telegram_endpoints' has no attribute '_resolve_tenant_for_company_id'
tests/test_telegram_taty_tenant_translation.py::TestResolveTenantForCompanyIdHelper::test_returns_none_when_no_matching_row FAILED
  AttributeError: module 'presentation.telegram_endpoints' has no attribute '_resolve_tenant_for_company_id'
tests/test_telegram_taty_tenant_translation.py::TestResolveTenantForCompanyIdHelper::test_returns_none_on_lookup_error_without_raising FAILED
  AttributeError: module 'presentation.telegram_endpoints' has no attribute '_resolve_tenant_for_company_id'

======================= 5 failed, 20 warnings in 7.47s =======================
```
(3 tests in `TestResolveTenantForCompanyIdHelper` failed pre-implementation, matching the
"missing helper" state; 5 tests total failed, all for expected reasons tied to the not-yet-built
translation step.)

### Step 2 — implementation applied, all tests GREEN

```
tests/test_telegram_taty_tenant_translation.py::TestTelegramCompanyIdToTenantTranslation::test_mapped_company_id_resolves_and_calls_ask_with_tenant_id PASSED
tests/test_telegram_taty_tenant_translation.py::TestTelegramCompanyIdToTenantTranslation::test_untranslatable_company_id_sends_no_configurado_and_never_calls_ask PASSED
tests/test_telegram_taty_tenant_translation.py::TestResolveTenantForCompanyIdHelper::test_returns_tenant_id_when_matching_row_exists PASSED
tests/test_telegram_taty_tenant_translation.py::TestResolveTenantForCompanyIdHelper::test_returns_none_when_no_matching_row PASSED
tests/test_telegram_taty_tenant_translation.py::TestResolveTenantForCompanyIdHelper::test_returns_none_on_lookup_error_without_raising PASSED

======================= 5 passed, 20 warnings in 5.90s =======================
```

## Regression check (tasks 1-3's suites)

```
$ pytest tests/test_taty_endpoints_tenant_scoping.py tests/test_taty_ask_tenant_scoping.py tests/test_taty_tenant_profiles.py -v
...
tests/test_taty_endpoints_tenant_scoping.py  5 passed
tests/test_taty_ask_tenant_scoping.py        6 passed
tests/test_taty_tenant_profiles.py           7 passed
======================= 18 passed, 20 warnings in 3.82s =======================
```

## Module import check

```
$ python -c "import sys; sys.path.insert(0,'.'); from presentation import telegram_endpoints; print('import OK')"
(run from apps/backend/)
import OK
```
(Same unrelated dev-only warning as in task 2's report: "JWT_SECRET not set — using
auto-generated secret for development" — import-time side effect of an unrelated module, not
`telegram_endpoints.py`; does not affect import success.)

## Deviations

None from the plan. `_resolve_tenant_for_company_id` was implemented as a plain sync function
(not `async def`) — the surrounding `telegram_webhook` handler is `async`, but its own Supabase
calls (e.g. the `telegram_chat_mappings` lookup just above) are sync `.execute()` calls, so this
matches the file's existing convention rather than introducing a mixed style. Also renumbered two
downstream `# PASO N` comments (comment-only) to keep the step sequence internally consistent
after inserting the new tenant-resolution step — not part of the original task wording but a
trivial consistency fix within the same edited block, flagged here for visibility.

## Not done in this task (explicitly out of scope, deferred to later tasks.md sections)

- Deletion of `POST /api/v1/agents/taty/ask` and `taty_intent_router.py` (task 5)
- Broader audit of `apps/backend/tests` for other `AGENT_PROFILES`/`ctx-001`/legacy references
  (task 6)
- Full `RUN_TESTS=1 init.sh` suite / DB-state verification (task 7)
