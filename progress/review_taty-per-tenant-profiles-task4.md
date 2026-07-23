# Review — task 4 (taty-per-tenant-profiles)

**Verdict:** APPROVED

## Scope check
- tasks.md §4 items 4.1–4.3 only. `git diff c9aecb5 -- apps/backend/presentation/telegram_endpoints.py` shows exactly: new `_resolve_tenant_for_company_id` helper (lines 59-74), a new "PASO 4" translation block before the `taty.ask()` call (lines 167-173), the `company_id=` → `tenant_id=` swap at the call site, and comment-only renumbering of the two trailing PASO comments. No other hunks. Matches design.md D6 verbatim (same helper name, same query shape `tenants.select("id").eq("company_id", ...)`, same untouched Social Ops branch rationale).
- `apps/backend/presentation/telegram_endpoints.py:127-165` (Social Ops command branch + onboarding `if active_ws:` branch) is byte-for-byte unchanged per the diff — provably untouched, not just claimed.
- No scope creep: `taty_service.py`, `taty_endpoints.py`, `agents_endpoints.py`, `taty_intent_router.py`, `core/deps.py` untouched (confirmed via `git status --short`, only `telegram_endpoints.py` modified + new test file).

## Code correctness
- `_resolve_tenant_for_company_id` (telegram_endpoints.py:59-74): correctly typed `(company_id: str) -> Optional[str]`, queries `tenants` filtered by `.eq("company_id", company_id)` (not `.eq("id", ...)` — correct per D6), selects `"id"` as the returned tenant uuid. Wrapped in broad `try/except Exception`, logs, returns `None` on any failure (bad connection, malformed response, etc.) — never propagates. Fail-safe confirmed both by code inspection and by `test_returns_none_on_lookup_error_without_raising`, which injects a `RuntimeError` at `.table()` and asserts a clean `None` return.
- Call site (lines 167-185): translation happens strictly before `get_taty_service()`/`ask()` is invoked. On `not tenant_id`, sends the pre-existing "❌ Este chat no está configurado.\nContacta a soporte." string and `return`s — the `ask()` call is textually unreachable on that path, not just conditionally skipped. Confirmed by `test_untranslatable_company_id_sends_no_configurado_and_never_calls_ask`, which wires a `_ForbiddenTatyService.ask()` that raises `AssertionError` if ever called; test passes, meaning `ask()` is genuinely never reached.
- `taty.ask(...)` now passes `tenant_id=tenant_id` exclusively; no remaining `company_id=` kwarg into `ask()` (grep of `company_id` in the file classified — all other hits are the `telegram_chat_mappings` lookup, the Social Ops/onboarding branch, and the translation input variable, none feed `ask()` directly).
- PASO comment renumbering (4→5→6→7) is purely cosmetic per the diff — no code reordering or logic hidden inside it.

## Tests
- `test_telegram_taty_tenant_translation.py`: 5 tests, all assert real outcomes (tenant_id value equality, absence of `company_id` key in the ask() kwargs, exact "no configurado" substring, forbidden-mock hard-fail for the negative path, `None` return on both empty-result and exception paths for the helper). Not weakened/soft assertions.
- `pytest apps/backend/tests/test_telegram_taty_tenant_translation.py -v` → 5/5 passed.
- `pytest .../test_telegram_taty_tenant_translation.py .../test_taty_endpoints_tenant_scoping.py .../test_taty_ask_tenant_scoping.py .../test_taty_tenant_profiles.py -q` → 23/23 passed (no regression in tasks 1-3 suites).
- `bash init.sh` → green (harness gate, canon/structure/feature_list checks all OK).

## Checkpoints
- C1 (scope contract matches tasks.md §4): [x]
- C2 (design.md D6 respected): [x]
- C3 (TDD: tests written first, assert real behavior): [x]
- C4 (Social Ops branch untouched): [x]
- C5 (fail-safe helper, no stub/placeholder, no disabled type-checking): [x]
- C6 (init.sh green): [x]
- C7 (docs-sync: no architecture container/dependency change in this task, no ARCHITECTURE.md update required): [x]

## Required changes
None.
