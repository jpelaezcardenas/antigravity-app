# Task 6 (6.1-6.2) — Review and Update Existing Unit Tests (MANDATORY)

**Change:** `taty-per-tenant-profiles`
**Branch:** `feature/taty-per-tenant-profiles`
**Scope:** `apps/backend/tests/` only, test-file audit for breakage caused by tasks 1-5
(rename `company_id` → `tenant_id` in `TatyAgentService.ask()`, deletion of
`AGENT_PROFILES`/`_get_agent_profile`, deletion of `taty_intent_router.py`).

## 1. Scoping greps (run first, from worktree root)

```
$ grep -rln "AGENT_PROFILES\|_get_agent_profile\|taty_intent_router\|ferez-001\|martinez-001" apps/backend/tests/
apps/backend/tests/test_taty_ask_tenant_scoping.py          (new file, task 1-4 — excluded)
apps/backend/tests/test_taty_lead_router.py                 (hit — audited below)
apps/backend/tests/test_taty_tenant_profiles.py              (new file, task 1-4 — excluded)
+ 3 stale __pycache__/*.pyc entries (compiled bytecode, not source; ignored)

$ grep -rln "ctx-001" apps/backend/tests/
apps/backend/tests/test_agent_pipeline.py                    (hit — audited below, unaffected)
apps/backend/tests/test_centinela_alerts_get.py               (hit — audited below, unaffected)
apps/backend/tests/test_identity_resolver.py                  (hit — audited below, unaffected)
apps/backend/tests/test_secure_llm.py                         (hit — audited below, unaffected)
apps/backend/tests/test_taty_ask_tenant_scoping.py            (new file — excluded)
apps/backend/tests/test_taty_tenant_profiles.py                (new file — excluded)
apps/backend/tests/test_tenant_stamping.py                    (hit — audited below, unaffected)
+ matching __pycache__/*.pyc entries (ignored)

$ grep -rln "\.ask(" apps/backend/tests/ | grep -v -E "test_taty_tenant_profiles|test_taty_ask_tenant_scoping|test_taty_endpoints_tenant_scoping|test_telegram_taty_tenant_translation"
(no output — zero hits outside the 4 already-covered new test files)
```

Additional verification greps run to be thorough (not in the mandated list but needed to
independently confirm completeness per the task's "verify against actual current repo state"
instruction):

```
$ grep -rlni "taty" apps/backend/tests/ --include=*.py
test_content_evaluator.py, test_crm_service_b2c_logic.py, test_crm_whatsapp_intake.py,
test_document_storage_service.py, test_llm_engine.py, test_maestro_agent_protocol.py,
test_maestro_load_test.py, test_model_selector_cloud_only.py, test_profile_support.py,
test_social_ops_endpoints.py, test_taty_ask_tenant_scoping.py, test_taty_endpoints_tenant_scoping.py,
test_taty_lead_router.py, test_taty_tenant_profiles.py, test_tax_documents_schema.py,
test_telegram_taty_tenant_translation.py, test_whatsapp_channel.py, test_whatsapp_endpoints.py

$ grep -rln "TatyAgentService\|taty_service\|get_taty_service" apps/backend/tests/ --include=*.py
test_taty_ask_tenant_scoping.py, test_taty_endpoints_tenant_scoping.py,
test_taty_tenant_profiles.py, test_telegram_taty_tenant_translation.py
```

This confirms: **no test file outside the 4 already-covered new files imports or calls
`TatyAgentService` / `taty_service` / `get_taty_service` at all.** The other "taty"-mentioning
files (whatsapp/social-ops/crm/etc.) only reference "Taty" as an agent name string or persona
label, unrelated to the `ask()` API or the deleted profile dict/router.

## 2. Classification of every hit

| File | Pattern matched | Classification | Reason |
|---|---|---|---|
| `test_taty_ask_tenant_scoping.py` | AGENT_PROFILES-family, ctx-001 | **Excluded** (in-scope new file from task 1-4) | Out of scope per instructions |
| `test_taty_tenant_profiles.py` | AGENT_PROFILES-family, ctx-001 | **Excluded** (in-scope new file from task 1-4) | Out of scope per instructions |
| `test_taty_endpoints_tenant_scoping.py` | (imports taty_service) | **Excluded** (in-scope new file from task 1-4) | Out of scope per instructions |
| `test_telegram_taty_tenant_translation.py` | (imports taty_service) | **Excluded** (in-scope new file from task 1-4) | Out of scope per instructions |
| `test_taty_lead_router.py` | `taty_intent_router` (1 hit, line 4) | **Unaffected** | Docstring-only cross-reference: *"This is a NEW, separate lead-scoped router — NOT an extension of taty_intent_router.py, which is tenant-scoped..."*. Confirmed via import list (`from services.taty_lead_router import (...)`) that the file never imports from the deleted `taty_intent_router.py` module. Prose remains historically accurate (explains why this *different* module isn't an extension of the one that existed at the time it was written) — not a functional test of the deleted module, so nothing to change. |
| `test_agent_pipeline.py` | `ctx-001` (×3, lines 122/131/166) | **Unaffected** | `"company_id": "ctx-001"` is passed into `analyst.execute({...})` / `distributor.execute({...})` — Social Content Ops pipeline operators, unrelated to `TatyAgentService.ask()`. No import of `taty_service` in this file. |
| `test_centinela_alerts_get.py` | `ctx-001` (×4) | **Unaffected** | `service.get_alerts_for_company("ctx-001", ...)` — `CentinelaService`, unrelated module. No import of `taty_service`. |
| `test_identity_resolver.py` | `ctx-001` (×2) | **Unaffected** | `IdentityResolver.resolve_tenant_uuid("ctx-001", ...)` / `.resolve(..., "ctx-001")` — tests that `IdentityResolver` correctly maps a `company_id` value to a tenant UUID. This is exactly the mechanism `TatyAgentService.ask()` now relies on (via the identity/tenant resolution layer), but this test exercises `IdentityResolver` directly, not `TatyAgentService.ask()`. No behavior here changed. |
| `test_secure_llm.py` | `ctx-001` (×1, line 91) | **Unaffected** | `"company_id": "ctx-001"` in a POST body to `/api/v1/agents/pulso/analyze` — Pulso endpoint, unrelated to Taty. No import of `taty_service`. |
| `test_tenant_stamping.py` | `ctx-001` (×2) | **Unaffected** | `CentinelaService.save_alerts([{"company_id": "ctx-001", ...}])` — unrelated to Taty. No import of `taty_service`. |

**Result: zero pre-existing test files (outside the 4 already-created new ones) are affected
by the `AGENT_PROFILES`/`_get_agent_profile`/`taty_intent_router` deletions or the
`company_id` → `tenant_id` rename in `TatyAgentService.ask()`.** No caller of
`TatyAgentService.ask()` / `get_taty_service().ask()` exists outside the 4 new test files, and
every `ctx-001` occurrence in a pre-existing file refers to an unrelated `company_id` value on
a different service (`CentinelaService`, `IdentityResolver`, Social Content Ops operators,
Pulso endpoint) — none of which were touched by tasks 1-5.

This is a **valid negative result** per the task's own fallback clause: "If your grep finds
ZERO genuinely-affected pre-existing tests, that's a valid outcome."

## 3. Changes made

**None.** No pre-existing test file required modification. `taty_service.py`,
`taty_endpoints.py`, `telegram_endpoints.py`, `agents_endpoints.py` were not touched (per
constraint). No test file was edited or deleted.

## 4. Test run output

Full collection from repo root (807 tests, 0 collection errors — the earlier 3 collection
errors seen when running pytest from `apps/backend/` as cwd were a `sys.path`/cwd artifact for
files using `from apps.backend...` absolute imports; running from repo root resolves them
cleanly and is unrelated to this change):

```
$ cd <worktree root> && python -m pytest apps/backend/tests/ --collect-only -q
...
807 tests collected in 4.20s
```

Targeted run of every candidate file flagged by the greps:

```
$ python -m pytest apps/backend/tests/test_agent_pipeline.py \
    apps/backend/tests/test_centinela_alerts_get.py \
    apps/backend/tests/test_identity_resolver.py \
    apps/backend/tests/test_secure_llm.py \
    apps/backend/tests/test_tenant_stamping.py \
    apps/backend/tests/test_taty_lead_router.py -q

FAILED apps/backend/tests/test_centinela_alerts_get.py::TestGetAlertsEndpoint::test_endpoint_returns_200_and_shape
FAILED apps/backend/tests/test_secure_llm.py::test_pulso_analyze_endpoint_anonymizes_outbound_prompt
2 failed, 65 passed, 1 skipped, 20 warnings in 5.77s
```

Both failures are **pre-existing environment issues unrelated to this change**: both raise
`TypeError: Client.__init__() got an unexpected keyword argument 'app'` from inside
`starlette/testclient.py` itself (installed versions: `starlette==0.27.0`,
`httpx==0.28.1`, `fastapi==0.104.1` — an incompatible httpx/starlette pairing where
`TestClient(app=...)` construction breaks). This is a `TestClient`-construction-level failure
that occurs for **any** FastAPI endpoint test using `fastapi.testclient.TestClient` in this
environment, not something introduced by tasks 1-5 (neither file imports `taty_service` or
anything touched by this change — confirmed above). Re-run of the remaining, non-TestClient
candidate files to isolate the result:

```
$ python -m pytest apps/backend/tests/test_agent_pipeline.py \
    apps/backend/tests/test_identity_resolver.py \
    apps/backend/tests/test_tenant_stamping.py \
    apps/backend/tests/test_taty_lead_router.py -v
...
59 passed, 1 skipped, 19 warnings in 2.37s
```

All green.

## 5. Constraints followed

- `taty_service.py`, `taty_endpoints.py`, `telegram_endpoints.py`, `agents_endpoints.py` — not touched.
- The 4 new test files from tasks 1-4 — not touched.
- `test_taty_intent_router.py` — already deleted (task 5), not touched.
- English-only.
- No commit made.

`git branch --show-current` → `feature/taty-per-tenant-profiles`
