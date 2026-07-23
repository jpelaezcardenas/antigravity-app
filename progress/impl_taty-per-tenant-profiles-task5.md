# Task 5 — Backend: Retirements

Branch: `feature/taty-per-tenant-profiles` (confirmed via `git branch --show-current`). Not committed (per instructions).

## 5.1 Deleted deprecated `POST /api/v1/agents/taty/ask`

File: `apps/backend/presentation/agents_endpoints.py`

**Deleted** (lines 49-81 in the pre-edit file — the `taty_ask` route + decorator + docstring):

```python
@router.post("/taty/ask")
async def taty_ask(request: AskRequest):
    """
    Taty Contadora: Answer user fiscal questions with RAG, LLM failover, and profile-based routing.

    DEPRECATED: Use POST /api/v1/agents/ask with request body instead.
    This endpoint is kept for backward compatibility and redirects to the new TatyAgentService.
    """
    try:
        from services.taty_service import get_taty_service

        taty = get_taty_service()

        # Call the new profile-aware service (profile defaults to "taty-v1")
        response = taty.ask(
            company_id=request.company_id,
            question=request.question,
            channel="api"  # Legacy endpoint channel identifier
        )

        # Return in the AgentResponse format for backward compatibility
        return AgentResponse(
            result=response.get("answer", response.get("result", "")),
            model_used="glm-5.2",  # Taty profile uses GLM as primary
            task_type="taty_faq",
            tier="tier-1",
            success=True
        )

    except Exception as e:
        logger.error(f"Taty Ask failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

**Deviation from the literal task text (documented, per constraint "verify via grep within the
file before deleting the model"):** the `AskRequest` Pydantic model was **kept**, not deleted.
Grep within `agents_endpoints.py` shows it is also the request model for
`POST /social/generate-content` (`async def social_generate_content(request: AskRequest)`,
line ~84 pre-edit). Deleting it would have broken a live, unrelated route — out of this task's
scope ("Do not touch any other route in this file"). Only the `taty_ask` function + its
`@router.post("/taty/ask")` decorator were removed; `AskRequest`, `social_generate_content`, and
every other route in the file are untouched.

No other route in `agents_endpoints.py` was modified. `presentation/router.py` (the mount point)
was **not touched** — `agents_router` is still included at `/agents` with no code change needed;
it simply now registers one fewer path. (Left one stale comment in `router.py` line 37 that
still names `/agents/taty/ask` as an example non-colliding path — out of this task's file scope,
belongs to task 10 doc cleanup; noting it here so it isn't lost.)

## 5.2 Deleted `taty_intent_router.py` and its test

```
git rm apps/backend/services/taty_intent_router.py apps/backend/tests/test_taty_intent_router.py
```

Both removed via `git rm` (tracked in git status as `D`). Confirmed via design.md D4 and spec
scenario "No unreferenced intent router remains" that this file has zero live callers — only its
own test imported it.

Also removed stale compiled bytecode referencing the deleted module
(`services/__pycache__/taty_intent_router.cpython-311.pyc`,
`tests/__pycache__/test_taty_intent_router.cpython-311-pytest-7.4.3.pyc`) so no artifact of the
deleted module lingers on disk.

## 5.3 Grep verification

```
$ grep -rn "taty_intent_router" apps/backend/
```
Zero import/code hits. Remaining hits are all comparative **comments** in unrelated, still-live
modules explaining they are NOT extensions of the deleted router (kept as-is — historical
context, not a dependency):
- `apps/backend/presentation/whatsapp_endpoints.py:6` — "...a NEW, separate router from
  taty_intent_router.py, since..."
- `apps/backend/services/taty_lead_router.py:3,69` — "A NEW, separate module from
  taty_intent_router.py..." / "...taty_intent_router.py's classify_intent..."
- `apps/backend/tests/test_taty_lead_router.py:4` — "NOT an extension of taty_intent_router.py..."

(Two stale `.pyc` binary matches under `.pytest_cache`/`__pycache__` — deleted, see above. A
`.pytest_cache/v/cache/nodeids` entry listing old collected test ids from the now-deleted test
file — this is pytest's own cache, self-heals on next full collection, not source.)

```
$ grep -rn "from services.taty_intent_router\|import taty_intent_router" apps/backend/
```
Zero hits.

```
$ python -c "import sys; sys.path.insert(0,'.'); from presentation import agents_endpoints, router; print('import OK')"
```
(run from `apps/backend/`) → `import OK` (plus an unrelated dev-mode warning about
auto-generated `JWT_SECRET`, expected in local runs without `.env`).

## Test runs

### `pytest apps/backend/tests/ -k "agents or taty" -v --ignore=tests/test_taty_intent_router.py`

3 pre-existing, unrelated collection errors surfaced first (not caused by this change — all three
import `apps.backend.*` absolute paths that only resolve when pytest is invoked from the repo
root, not from `apps/backend/`; same failure mode existed before this task):
`tests/test_profile_support.py`, `tests/test_swarm_operators.py`, `tests/test_t11_integration.py`
(`ModuleNotFoundError: No module named 'apps'`). Re-ran with those 3 also `--ignore`d:

```
89 passed, 670 deselected, 20 warnings in 8.24s
```

All Taty/agents-related tests pass, including `test_taty_endpoints_tenant_scoping.py` (5/5),
`test_taty_ask_tenant_scoping.py`, `test_taty_tenant_profiles.py`,
`test_telegram_taty_tenant_translation.py`, `test_taty_lead_router.py` (unrelated sibling
module, confirmed untouched and still green), `test_agents_4_7.py`, `test_maestro_*`,
`test_websocket_phase4_regression.py`. No test referenced the deleted `taty_ask` route or
`taty_intent_router`.

### Regression suite (tasks 1-4)

```
pytest apps/backend/tests/test_taty_tenant_profiles.py apps/backend/tests/test_taty_ask_tenant_scoping.py apps/backend/tests/test_taty_endpoints_tenant_scoping.py apps/backend/tests/test_telegram_taty_tenant_translation.py -v
```

```
23 passed, 20 warnings in 4.88s
```

## Files touched

- `apps/backend/presentation/agents_endpoints.py` (modified — route deleted, model kept)
- `apps/backend/services/taty_intent_router.py` (deleted via `git rm`)
- `apps/backend/tests/test_taty_intent_router.py` (deleted via `git rm`)

## Constraints honored

- `taty_service.py`, `taty_endpoints.py`, `telegram_endpoints.py`, `core/deps.py` — untouched.
- No other route in `agents_endpoints.py` touched.
- Nothing committed (per instructions) — branch confirmed `feature/taty-per-tenant-profiles`.

## Next step

Hand off to reviewer for tasks.md items 5.1-5.3.
