# Review — task 10 (taty-per-tenant-profiles): Update Technical Documentation

**Verdict:** APPROVED

## Checkpoints

- C1 (10.1 — `taty_endpoints.py` docstring accuracy): [x]
  - Stale `GET /api/v1/agents/taty/ask` example fixed → `GET /api/v1/agents/ask`, matching
    the live route (`router.py:40` mounts `taty_router` at `/agents`, `taty_endpoints.py:121`
    registers `POST /ask`; `main.py:133` mounts `api_router` at `/api/v1`). Full path
    `/api/v1/agents/ask` confirmed correct.
  - New `Authorization: Bearer <token>` header line added — accurate, matches
    `Depends(get_current_user)` on `ask_taty` (`taty_endpoints.py:130`) and the "Auth / tenant
    resolution" section already present from task 3.
  - New curl example: `POST https://antigravity-app-production-175a.up.railway.app/api/v1/agents/ask`
    with `Authorization: Bearer <token>`, `Content-Type: application/json`, and body
    `{"question": ..., "channel": "dashboard"}` — correct HTTP method, correct full URL (matches
    `ARCHITECTURE.md`'s canonical backend URL), correct header, and body matches
    `TatyAskRequest` schema (`question` required min_length=5, `channel` optional default
    `"dashboard"`). No stale `company_id=ctx-001` in the example. Independently re-verified via
    `grep -n "taty/ask\|ctx-001\|ferez-001\|martinez-001" apps/backend/presentation/taty_endpoints.py`
    → zero hits.

- C2 (10.2 — ARCHITECTURE.md / AGENTES.md no-op): [x]
  - `grep -n "taty_intent_router\|AGENT_PROFILES\|ferez-001\|martinez-001\|ctx-001"
    ARCHITECTURE.md AGENTES.md` independently re-run → zero hits, confirming the claimed no-op
    is genuine. Correctly skipped per the task 10.2 instruction ("only if either names..."). No
    docs-sync fail — no container/dependency changed by this documentation-only task, so
    ARCHITECTURE.md staying untouched is correct, not stale.

- C3 (10.3 — `router.py` stale comment): [x]
  - Comment at `router.py:36-39` fixed: dropped the reference to the deleted
    `/agents/taty/ask` wrapper route from the "does not collide with" list, added a note
    dating the deletion to task 5. Read against the live `include_router` calls
    (`router.py:35,40`) — accurate.

- C4 (Scope / diff isolation): [x]
  - `git status --short` shows only `apps/backend/presentation/router.py` (M),
    `apps/backend/presentation/taty_endpoints.py` (M), and the untracked
    `progress/impl_taty-per-tenant-profiles-task10.md`. `git diff` confirms both modified files
    contain only comment/docstring edits — no route logic, no model fields, no imports, no
    control flow changed. Zero scope creep.

- C5 (Tests): [x]
  - `python -m pytest apps/backend/tests/test_taty_tenant_profiles.py
    apps/backend/tests/test_taty_ask_tenant_scoping.py
    apps/backend/tests/test_taty_endpoints_tenant_scoping.py
    apps/backend/tests/test_telegram_taty_tenant_translation.py -q` → 23 passed, 0 failed
    (independently re-run, matches implementer's report).

- C6 (`bash init.sh`): [x]
  - Green — living canon present, harness structure present, `feature_list.json` valid with
    single active change (`taty-per-tenant-profiles`), backend tests skipped as designed
    (`RUN_TESTS=1` opt-in, already covered directly above).

## Required changes

None.
