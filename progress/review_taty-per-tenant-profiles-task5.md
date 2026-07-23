# Review — task taty-per-tenant-profiles-task5

**Verdict:** APPROVED

## Checkpoints
- 5.1 Deprecated `POST /api/v1/agents/taty/ask` route deleted: [x] — confirmed in full read of
  `apps/backend/presentation/agents_endpoints.py`; the `taty_ask` function + `@router.post("/taty/ask")`
  decorator are gone. `grep -n "taty/ask\|taty_ask" apps/backend/presentation/agents_endpoints.py`
  returns zero hits.
- 5.2 `taty_intent_router.py` + its test deleted: [x] — `git status --short` shows exactly
  `D  apps/backend/services/taty_intent_router.py` and `D  apps/backend/tests/test_taty_intent_router.py`,
  matching design.md D4 and spec scenario "No unreferenced intent router remains".
- 5.3 Grep-verify no dangling imports: [x] — `grep -rn "taty_intent_router" apps/backend/ --include="*.py"`
  returns only comment-only hits in `whatsapp_endpoints.py:6`, `taty_lead_router.py:3,69`,
  `test_taty_lead_router.py:4`, exactly as claimed in the report. No import statement anywhere.
- File-set discipline: [x] — `git diff --stat` shows only `agents_endpoints.py` modified
  (34 deletions, 0 insertions — pure removal, no other route touched), plus the two `git rm`
  deletions. Nothing else in the working tree changed except the new progress report.
- `AskRequest` retained, not deleted: [x] — verified directly in `agents_endpoints.py:25-28` (model)
  and line 50 (`async def social_generate_content(request: AskRequest)`). The report's claim is
  accurate, not fabricated — deleting `AskRequest` would have broken a live, unrelated route. This
  is a correct, disciplined deviation from the task's literal wording, consistent with the explicit
  constraint "Do not touch any other route in this file."
- `router.py` stale comment (line 37, still says `/agents/taty/ask`): judged non-blocking. It is a
  comment only — `taty_router` is mounted independently at the same `/agents` prefix and its
  registration is untouched; the comment's factual claim ("do not collide") is unaffected by the
  route's removal, it's just outdated illustrative text. Correctly out of task 5's file scope and
  reasonably deferred to task 10 (doc cleanup) rather than silently expanding scope here.
- Regression suite (tasks 1-4, 23 tests): [x] — reran independently,
  `pytest apps/backend/tests/test_taty_tenant_profiles.py apps/backend/tests/test_taty_ask_tenant_scoping.py apps/backend/tests/test_taty_endpoints_tenant_scoping.py apps/backend/tests/test_telegram_taty_tenant_translation.py -q`
  → 23 passed.
- Agents/taty subset (excluding the 3 pre-existing broken-collection files): [x] — reran
  independently, 89 passed (matches report exactly).
- Import sanity check: [x] — `python -c "from presentation import agents_endpoints, router; print('import OK')"`
  from `apps/backend/` → `import OK`.
- `bash init.sh`: [x] — green (harness structure + canon docs + feature_list.json pointer all OK).
- Pre-existing collection errors not caused by this task: [x] — spot-checked all three.
  `test_profile_support.py:8`, `test_swarm_operators.py:8`, `test_t11_integration.py:20` all use
  `from apps.backend.<module> import ...` (absolute path resolvable only from repo root, not from
  `apps/backend/`). None reference `taty_intent_router` or `taty_ask`. Genuinely pre-existing,
  unrelated to this task's deletions.
- No accidental live duplicate entry point: [x] — the one other `taty/ask`-referencing hit found
  outside test/docs scope, `middleware_config.py:201`, is inside a triple-quoted example-code
  string (`EXAMPLE_MAIN_PY`-style docstring for slowapi rate-limit wiring), not executable code —
  confirmed by reading the surrounding lines. No live duplicate route exists anywhere in the repo.

## Required changes (if any)
None.
