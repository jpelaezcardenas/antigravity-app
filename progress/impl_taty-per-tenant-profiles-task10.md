# Task 10 — Update Technical Documentation (MANDATORY)

Branch: `feature/taty-per-tenant-profiles` (confirmed via `git branch --show-current`)

## 10.1 `apps/backend/presentation/taty_endpoints.py`

Read the full file first. Task 3's implementer had already done the bulk of the work
(dropped the `company_id=ctx-001` JSON/query examples, added the "Auth / tenant
resolution" docstring section, added `Optional`/deprecated field descriptions on both
`TatyAskRequest.company_id` and the GET handler's `company_id` query param — those were
already accurate, no changes needed there).

Two remaining stale spots found and fixed in `ask_taty`'s docstring:

**Before:**
```
    **Query Alternative** (for dashboard GET):
    ```
    GET /api/v1/agents/taty/ask?question=¿Cuál es el UVT?
    ```

    **Headers:**
    - X-Hermes-Profile: Profile name (e.g., "taty-v1") for Hermes-based LLM routing
```
(stale path — `/agents/taty/ask` was deleted in task 5; the live GET route is
`/agents/ask`. Also no mention of the Authorization header despite auth now being
required.)

**After:**
```
    **Query Alternative** (for dashboard GET):
    ```
    GET /api/v1/agents/ask?question=¿Cuál es el UVT?
    ```

    **Headers:**
    - Authorization: Bearer <token> — required in production (AUTH_ENFORCED=True);
      identifies the caller so their tenant can be resolved (see "Auth / tenant
      resolution" below)
    - X-Hermes-Profile: Profile name (e.g., "taty-v1") for Hermes-based LLM routing
```

**Before (Example section — JSON body only, no auth, no curl):**
```
    **Example:**
    ```json
    {
      "question": "¿Cuál es el UVT para 2026?",
      "channel": "dashboard"
    }
    ```
```

**After (realistic curl example showing the actual auth mechanism):**
```
    **Example:**
    ```bash
    curl -H "Authorization: Bearer <token>" \
      -X POST https://antigravity-app-production-175a.up.railway.app/api/v1/agents/ask \
      -H "Content-Type: application/json" \
      -d '{"question": "¿Cuál es el UVT para 2026?", "channel": "dashboard"}'
    ```
```

## 10.2 `ARCHITECTURE.md` / `AGENTES.md`

```
grep -n "taty_intent_router\|AGENT_PROFILES\|ferez-001\|martinez-001\|ctx-001" ARCHITECTURE.md AGENTES.md
```
→ zero hits. Neither file names `taty_intent_router` or the hardcoded `AGENT_PROFILES`
mechanism, nor any of the old client-key examples (`ctx-001`/`ferez-001`/`martinez-001`).
**No-op** — no changes made to either file, per the grep evidence above. Bilingual
founder-summary carve-out untouched (nothing to touch).

## 10.3 `apps/backend/presentation/router.py` — stale comment (~line 36-38)

**Before:**
```python
# taty_router intentionally shares the /agents prefix. Its paths (/agents/ask,
# /agents/health) do not collide with agents_router's paths (/agents/taty/ask,
# /agents/social/..., etc.), so both can be mounted at the same prefix.
```
(`/agents/taty/ask` no longer exists — deleted in task 5.)

**After:**
```python
# taty_router intentionally shares the /agents prefix. Its paths (/agents/ask,
# /agents/health) do not collide with agents_router's paths (/agents/social/...,
# etc.), so both can be mounted at the same prefix. (The deprecated
# /agents/taty/ask wrapper route was deleted — taty-per-tenant-profiles, task 5.)
```

## 10.4 Symlink / ai-specs check

`git diff --stat main...HEAD` (34 files changed) — none under `ai-specs/` or
`.claude/skills/`; the diff is entirely `apps/backend/`, `openspec/`, and `progress/`.
This change added no new `ai-specs`-sourced artifacts, so no symlinks needed. No action
required — confirmed via the stat output already captured in task 7's summary and
re-verified here.

## Test confirmation

No code logic was touched (docstrings/comments only). Ran the full targeted suite for
this change:

```
$ python -m pytest apps/backend/tests/test_taty_tenant_profiles.py apps/backend/tests/test_taty_ask_tenant_scoping.py apps/backend/tests/test_taty_endpoints_tenant_scoping.py apps/backend/tests/test_telegram_taty_tenant_translation.py -q
.......................                                                  [100%]
23 passed, 20 warnings in 2.22s
```

## Files touched

- `apps/backend/presentation/taty_endpoints.py` — docstring fixes (2 spots)
- `apps/backend/presentation/router.py` — stale comment fix (1 spot)
- `ARCHITECTURE.md`, `AGENTES.md` — no changes (verified no-op via grep)

Tasks 10.1-10.3 in `openspec/changes/taty-per-tenant-profiles/tasks.md` are ready to be
marked done pending reviewer approval.
