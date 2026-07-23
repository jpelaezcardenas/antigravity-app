# Implementation report — taty-lead-router-tenant-scoping — Task Groups 1-2

Branch: `feature/taty-lead-router-tenant-scoping` (base: `feature/chatwoot-hermes-taty-bridge`)

## Files touched

- `apps/backend/services/crm_service.py` — `whatsapp_intake` gains optional `full_name: Optional[str] = None`, used only on the insert path (`full_name or whatsapp_phone`), plus a docstring note explaining the new param and the lookup/insert distinction.
- `apps/backend/services/taty_lead_router.py` — `find_or_create_lead` rewritten to a thin delegating wrapper: `get_crm_service().whatsapp_intake(whatsapp_phone, full_name=full_name)["lead_id"]`. Its own direct `get_service_supabase()` query and inline Cliente Cero tenant-resolution query were removed entirely. Docstring updated to point future readers at `CrmService.whatsapp_intake` instead of re-adding a duplicate lookup.
- `apps/backend/tests/test_crm_whatsapp_intake.py` — added 3 new tests: new phone + `full_name` sets that name on insert; new phone without `full_name` falls back to the phone; known/existing phone lookup ignores any `full_name` argument (never overwrites on find).
- `apps/backend/tests/test_taty_lead_router.py` — rewrote `TestFindOrCreateLead`'s two tests to mock `services.taty_lead_router.get_crm_service` (matching the pattern already used by `TestRouteLeadMessage`) instead of `get_service_supabase`; assert `whatsapp_intake` is called with the phone (and `full_name` when given) and that the returned `lead_id` matches the mock.

No changes to `route_lead_message`, `route_lead_document`, `apps/chatwoot-bridge/`, or `openspec/changes/taty-lead-router-tenant-scoping/tasks.md`.

## Task Group 1 — TDD red → green

1. Added the 3 new tests to `test_crm_whatsapp_intake.py` against the *pre-change* `whatsapp_intake(self, whatsapp_phone: str)` signature.
2. Confirmed red: `pytest tests/test_crm_whatsapp_intake.py -v` → 3 failed (2x `KeyError: 'full_name'` on insert payload, 1x `TypeError: ... unexpected keyword argument 'full_name'`), 5 pre-existing passed.
3. Implemented `full_name: Optional[str] = None` param + `full_name or whatsapp_phone` on the insert dict only.
4. Confirmed green: `pytest tests/test_crm_whatsapp_intake.py -v` → **8 passed** (all 5 pre-existing + 3 new), including the pre-existing tests that call `whatsapp_intake` without `full_name`, unaffected.

## Task Group 2 — TDD red → green

1. Rewrote `TestFindOrCreateLead`'s two tests to mock `services.taty_lead_router.get_crm_service` returning a `MagicMock` whose `.whatsapp_intake(...)` returns `{"lead_id": ..., "is_new": ..., "stage": ...}`.
2. Confirmed red against the pre-delegation implementation: `pytest tests/test_taty_lead_router.py -v -k FindOrCreateLead` → 2 failed with `supabase.client.SupabaseException: supabase_key is required` (proving `find_or_create_lead` was still hitting `get_service_supabase()` directly, not the new mock target).
3. Rewrote `find_or_create_lead` to delegate to `get_crm_service().whatsapp_intake(whatsapp_phone, full_name=full_name)` and return `result["lead_id"]`; removed the direct `crm_leads` query and the inline `tenants`/Cliente Cero resolution query.
4. Confirmed green: `pytest tests/test_taty_lead_router.py -v` → **41 passed** (all tests in the file, including `TestFindOrCreateLead`'s 2 rewritten tests and all pre-existing `route_lead_message`/`route_lead_document`/etc. tests untouched).

## Task Group 3 (per tasks.md — verified as part of this session)

- `apps/backend/tests/test_whatsapp_endpoints.py` mocks `presentation.whatsapp_endpoints.find_or_create_lead` directly (4 occurrences, lines 103/130/163/196) — it patches the function itself at the presentation-layer import site, never reaching into Supabase or `CrmService` internals. This is unaffected by the delegation change; no update needed. Confirmed by running it together with the other two files (see below) — all pass.
- Grepped the full `apps/backend/` tree for `find_or_create_lead`: matches only in `services/taty_lead_router.py` (definition + new docstring reference), `tests/test_taty_lead_router.py`, `presentation/whatsapp_endpoints.py` (the one real caller), and `tests/test_whatsapp_endpoints.py`. No other caller exists.

## Test commands and results

Targeted (Task Group 4.2):
```
cd apps/backend
python -m pytest tests/test_crm_whatsapp_intake.py tests/test_taty_lead_router.py tests/test_whatsapp_endpoints.py -v
```
Result: **58 passed**, 20 warnings (pre-existing pydantic/multipart deprecation warnings, unrelated).

Full suite (Task Group 4.3), from `apps/backend/` as cwd:
```
python -m pytest tests -v --ignore=tests/test_profile_support.py --ignore=tests/test_swarm_operators.py --ignore=tests/test_t11_integration.py
```
Result: **588 passed, 40 failed, 109 skipped** (129.94s).

The 3 ignored files (`test_profile_support.py`, `test_swarm_operators.py`, `test_t11_integration.py`) fail at **collection** with `ModuleNotFoundError: No module named 'apps'` — confirmed pre-existing by stashing this change's diff and re-running them against the unmodified branch tip (same error, same 3 files).

The 40 failures under the ignore-adjusted run are all in modules unrelated to this task's scope: `test_approval_rules_stage3_4.py`, `test_approval_rules_stage8_11.py` (OpenSpec artifact-completeness checks for other, closed changes), `test_centinela_alerts_get.py`, `test_model_selector_cloud_only.py`, `test_secure_llm.py`, `test_shadow_gl_integration.py`, `test_shadow_gl_siigo_csv.py`, `test_shadow_gl_stage1_migration.py`, `test_shadow_gl_stage4_uploader.py`, `test_shadow_gl_stage5_error_handling.py`, `test_shadow_gl_stage8_e2e.py`, `test_wizard_auditoria_sombra.py` — none touch `crm_service.py`, `taty_lead_router.py`, `whatsapp_endpoints.py`, or their test files. A recurring root cause visible in the output is `TypeError: Client.__init__() got an unexpected keyword argument 'app'` — an `httpx`/`starlette.TestClient` version mismatch in the local environment, unrelated to this change. No test touched by Task Groups 1-2 appears in the failure list.

## Scope confirmation

- `route_lead_message`, `route_lead_document`, and `apps/chatwoot-bridge/` were not modified.
- `openspec/changes/taty-lead-router-tenant-scoping/tasks.md` was not modified.
- English-only, full type hints preserved throughout.
