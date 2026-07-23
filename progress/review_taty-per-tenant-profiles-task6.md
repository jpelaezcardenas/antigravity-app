# Review — task 6 (taty-per-tenant-profiles)

**Verdict:** APPROVED

## Independent verification performed

1. Re-ran all 5 mandated/supplementary greps from the worktree root; output byte-for-byte
   matches the implementer's report (same file hits, same `__pycache__` noise).
2. Independently re-opened and re-classified every hit file:
   - `test_taty_lead_router.py` — `taty_intent_router` occurs only in a docstring comment (line 4);
     no import from the deleted module. Confirmed via `grep -n "^from\|^import"`.
   - `test_agent_pipeline.py` — `ctx-001` used as `company_id` payload for Social Content Ops
     agents (`PlannerAgent`/`GeneratorAgent`/etc.), no `taty_service` import.
   - `test_centinela_alerts_get.py` — `ctx-001` used against `CentinelaService`, no `taty_service`
     import.
   - `test_identity_resolver.py` — `ctx-001` exercises `IdentityResolver` directly, not
     `TatyAgentService.ask()`. No `taty_service` import.
   - `test_secure_llm.py` — `ctx-001` posted to `/api/v1/agents/pulso/analyze` (Pulso, not Taty).
     Confirmed `agents_endpoints.py`'s only diff vs base (`git diff c3efe41`) is the deletion of
     the deprecated `POST /taty/ask` route — unrelated to `/agents/pulso/analyze`.
   - `test_tenant_stamping.py` — `ctx-001` used against `CentinelaService`/`ApprovalQueueService`,
     no `taty_service` import.
   - The 13 other "taty"-matching files (whatsapp, crm, maestro, model_selector, profile_support,
     social_ops, etc.) checked individually with `grep -ni taty` — all are persona-string mentions
     (`"taty-v1"` profile name, mock agent named `"taty"`, changelog references), none import
     `TatyAgentService`/`taty_service`/`AGENT_PROFILES`.
   All classifications in the report's table match my independent read.

3. Ran the targeted test files myself:
   `test_agent_pipeline.py test_identity_resolver.py test_tenant_stamping.py test_taty_lead_router.py`
   → 59 passed, 1 skipped — matches the report exactly.

4. Ran `test_centinela_alerts_get.py` + `test_secure_llm.py` myself → same 2 failures, same error:
   `TypeError: Client.__init__() got an unexpected keyword argument 'app'`, raised from inside
   `starlette/testclient.py:399` (before any application code executes). Confirmed installed
   versions: `httpx==0.28.1`, `starlette==0.27.0`, `fastapi==0.104.1` — a known-incompatible
   pairing. `git diff c3efe41 -- apps/backend/tests/test_centinela_alerts_get.py
   apps/backend/tests/test_secure_llm.py` is empty — these two files are byte-identical to the
   base commit, so the failure predates this change and cannot be a masked regression from
   tasks 1-5.

5. `python -m pytest apps/backend/tests/ --collect-only -q` → `807 tests collected in 5.89s`,
   0 collection errors, from repo root — matches the report.

6. `git diff c3efe41 --stat -- apps/backend/` confirms the actual touched surface: only
   `agents_endpoints.py`, `taty_endpoints.py`, `telegram_endpoints.py`, `taty_service.py`,
   `taty_intent_router.py` (deleted), `test_taty_intent_router.py` (deleted), and the 4 new task
   1-4 test files. No file the report classified "unaffected" appears in this diff.

7. `bash init.sh` → green (`[OK] Harness ready. You can start working.`).

## Checkpoints
- C1 (greps independently reproduced, exact match): [x]
- C2 (every classified file independently re-audited, correct): [x]
- C3 (targeted pre-existing tests green, matches reported 59 passed/1 skipped): [x]
- C4 (2 TestClient failures confirmed pre-existing/environmental, not a masked regression): [x]
- C5 (807 tests collected, 0 errors, consistent): [x]
- C6 (init.sh green): [x]
- C7 (docs-sync: no container/dependency change in task 6 itself — audit-only, no ARCHITECTURE.md update required): [x]

## Required changes

None. The negative result is genuine — independently re-derived from scratch, not just
re-trusted.
