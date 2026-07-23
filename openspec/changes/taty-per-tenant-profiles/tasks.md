## 0. Setup: Create Feature Branch (MANDATORY - FIRST STEP)

- [x] 0.1 Create feature branch `feature/taty-per-tenant-profiles` from updated `main`
      (via isolated worktree `.claude/worktrees/taty-per-tenant-profiles`, rebased onto local
      `main` @ c3efe41)
- [x] 0.2 Verify branch creation and current branch status (`git branch --show-current` →
      `feature/taty-per-tenant-profiles`)
- [x] 0.3 Flip `feature_list.json` pointer: mark `chatwoot-hermes-taty-bridge` `done` (Stage 11
      already committed at c3efe41, owning session will formally archive), add
      `taty-per-tenant-profiles` `in_progress`, `active` = `taty-per-tenant-profiles`
- [x] 0.4 `bash init.sh` green with the flipped pointer

## 1. Backend: Service Profile Resolver (TDD)

- [x] 1.1 Write failing tests in `apps/backend/tests/test_taty_tenant_profiles.py`:
      provisioned tenant → scoped profile (spec scenario 1); unknown tenant uuid →
      `error_code="tenant_not_found"` (scenario 2); legacy key `"ferez-001"` → graceful
      `tenant_not_found`, no exception (scenario 3) — `progress/impl_taty-per-tenant-profiles-task1.md`
- [x] 1.2 Implement `DEFAULT_PROFILE`, `_get_tenant_profile(tenant_id)`, delete
      `AGENT_PROFILES`, extend `_error_response(error_code=...)` in
      `apps/backend/services/taty_service.py` — reviewed APPROVED,
      `progress/review_taty-per-tenant-profiles-task1.md`. Note: `_get_agent_profile` kept as a
      transitional delegator to `_get_tenant_profile` (not yet deleted) — task 2 rewires `ask()`
      to call `_get_tenant_profile` directly and removes `_get_agent_profile`.
- [x] 1.3 Tests from 1.1 green (7 passed)

## 2. Backend: `ask()` Rename, KB Keying, Régimen Omission (TDD)

- [x] 2.1 Write failing tests: `regimen=None` omits régimen clause from built prompt (scenario
      "Taty never asserts an unverified tax regime"); tenant with no chunks retrieves
      `__global__` DIAN corpus (design D7); Cliente Cero tenant → `retrieve_similar` called with
      `client_id="ctx-001"` (design D7) — `test_taty_ask_tenant_scoping.py`,
      `progress/impl_taty-per-tenant-profiles-task2.md`
- [x] 2.2 Rename `ask(company_id, ...)` → `ask(tenant_id, ...)`; `_retrieve_chunks` uses
      `profile["kb_client_id"]`; `_build_prompt` omits régimen clause when `None`;
      `_get_agent_profile` deleted (task 1's transitional delegator, no longer needed) —
      reviewed APPROVED, `progress/review_taty-per-tenant-profiles-task2.md`
- [x] 2.3 Tests from 2.1 green (13/13, incl. task 1's 7). ⚠️ 3 live callers now raise TypeError
      until tasks 3/4/5 land (expected per design D5, all fixed within this same OpenSpec
      change): `agents_endpoints.py:63` (task 5 deletes this route), `taty_endpoints.py:144`
      (task 3), `telegram_endpoints.py:154` (task 4). Reviewer also flagged: full
      `RUN_TESTS=1 init.sh` suite is red due to a pre-existing, unrelated issue in
      `test_shadow_gl_stage8_e2e.py` (predates this branch) — tracked for task 7 DB-verification
      step, not caused by this change.

## 3. Backend: Endpoint Auth + Tenant Resolution (TDD)

- [ ] 3.1 Write failing tests in `apps/backend/tests/test_taty_endpoints_tenant_scoping.py`
      (mirrors `test_financials_endpoint_tenant_scoping.py` — call handlers directly with
      hand-built user dicts): resolved user → `ask` called with their tenant (scenario
      "Authenticated client is scoped to their own tenant"); staging user → Cliente Cero
      resolver invoked (scenario "Staging identity falls back to Cliente Cero"); authenticated
      unresolved → `error_code="tenant_not_resolved"`, Cliente Cero resolver asserted NEVER
      called (scenario "Unresolved authenticated caller does not leak another tenant"); user A
      + spoofed `company_id` of tenant B → `ask` called with A's tenant (scenario "A supplied
      `company_id` cannot be used to read another tenant's profile")
- [ ] 3.2 Add `Depends(get_current_user)` + canonical resolution block (financials pattern) to
      POST/GET `/api/v1/agents/ask` in `apps/backend/presentation/taty_endpoints.py`; make
      `TatyAskRequest.company_id` `Optional` and ignored for resolution; add optional
      `error_code` to `TatyAskResponse`; add local `_resolve_cliente_cero_tenant_id()`
- [ ] 3.3 Tests from 3.1 green

## 4. Backend: Telegram Tenant Translation (TDD)

- [ ] 4.1 Write failing tests: mapped `company_id` resolving to a tenant → `ask(tenant_id=...)`
      called with the translated uuid (scenario "Mapped chat resolves and answers"); unmapped
      `company_id` → existing "no configurado" reply sent, `ask()` never invoked (scenario
      "Unmapped or untranslatable chat is rejected before calling Taty")
- [ ] 4.2 Add `_resolve_tenant_for_company_id(company_id)` helper and use it before the
      `taty.ask(...)` call site in `apps/backend/presentation/telegram_endpoints.py` (Social Ops
      onboarding branch, which reads the same mapping, is untouched)
- [ ] 4.3 Tests from 4.1 green

## 5. Backend: Retirements

- [ ] 5.1 Delete deprecated `POST /api/v1/agents/taty/ask` route (lines only — rest of
      `apps/backend/presentation/agents_endpoints.py` untouched); confirm 404 (scenario
      "Deprecated wrapper route is gone")
- [ ] 5.2 Delete `apps/backend/services/taty_intent_router.py` and
      `apps/backend/tests/test_taty_intent_router.py` (scenario "No unreferenced intent router
      remains")
- [ ] 5.3 Grep-verify no dangling imports of `taty_intent_router` or the deleted route anywhere
      in `apps/backend`

## 6. Backend: Review and Update Existing Unit Tests (MANDATORY)

- [ ] 6.1 Grep `apps/backend/tests` for `AGENT_PROFILES`, `company_id.*taty`, `taty.*ask`,
      `ctx-001`, `ferez-001`, `martinez-001` and audit every hit (expected candidates:
      `test_agent_pipeline.py`, `test_secure_llm.py`, `test_tenant_stamping.py`,
      `test_centinela_alerts_get.py` — confirm actual scope during execution)
- [ ] 6.2 Update each affected test to the new `tenant_id` signature / mocks; do not weaken
      assertions to force a pass

## 7. Backend: Run Unit Tests and Verify Database State (MANDATORY)

- [ ] 7.1 Capture pre-test baseline: `tenants` roster count, `telegram_chat_mappings` rows
      (confirm none reference `ferez-001`/`martinez-001`), `knowledge_chunks` `client_id`
      distribution
- [ ] 7.2 Run targeted tests: `pytest apps/backend/tests/test_taty_tenant_profiles.py
      apps/backend/tests/test_taty_endpoints_tenant_scoping.py -q`
- [ ] 7.3 Run full suite: `RUN_TESTS=1 bash init.sh` (wraps `pytest apps/backend -q`)
- [ ] 7.4 Re-check the same DB indicators from 7.1; confirm no unintended mutation (this change
      is read-only against `tenants`/`telegram_chat_mappings` — no restoration should be needed)
- [ ] 7.5 Create report
      `openspec/changes/taty-per-tenant-profiles/reports/YYYY-MM-DD-step-7-unit-test-and-db-verification.md`
- [ ] 7.6 Mark this step complete only after 7.2–7.5 are done and green

## 8. Backend: Manual Endpoint Testing with curl (MANDATORY - AGENT MUST EXECUTE)

- [ ] 8.1 Start local backend server
- [ ] 8.2 `curl GET /api/v1/agents/ask` unauthenticated (staging path) → Cliente Cero-scoped
      answer, 200
- [ ] 8.3 `curl POST /api/v1/agents/ask` with a provisioned client's JWT → answer reflects that
      tenant's `legal_name`, 200, no `error_code`
- [ ] 8.4 `curl POST /api/v1/agents/ask` with a provisioned client's JWT but a `company_id` in
      the body belonging to a different tenant → answer still reflects the caller's own tenant
      (spoof-proof), 200
- [ ] 8.5 `curl POST /api/v1/agents/ask` with a JWT for a user with no tenant membership →
      `error_code="tenant_not_resolved"`, 200
- [ ] 8.6 `curl POST /api/v1/agents/taty/ask` → 404 (route removed)
- [ ] 8.7 Document all commands + responses in
      `openspec/changes/taty-per-tenant-profiles/reports/YYYY-MM-DD-step-8-manual-curl.md`

## 9. Frontend: E2E Testing with Playwright MCP

- [x] 9.1 N/A — this change touches backend endpoints only (`/api/v1/agents/ask`,
      Telegram webhook). No frontend workflow or UI changes; the only live in-repo consumer of
      this endpoint before this change was none (verified: Búnker bundle calls
      `/llm/analyze`/`/agents/onboarding/analyze`/`/agents/planner/generate-options`, never
      `/agents/ask`). Skipping per "MANDATORY if applicable."

## 10. Update Technical Documentation (MANDATORY)

- [ ] 10.1 Update `apps/backend/presentation/taty_endpoints.py` docstrings/examples to drop
      `ctx-001`-as-request-param examples and reflect auth + `tenant_id` resolution
- [ ] 10.2 Update `ARCHITECTURE.md` / `AGENTES.md` only if either names `taty_intent_router` or
      the old hardcoded-profile mechanism (check during execution; do not touch bilingual
      founder summary carve-out unnecessarily)
- [ ] 10.3 Confirm no symlink references broke (per CLAUDE.md §6) — this change adds no new
      `ai-specs`-sourced artifacts

## 11. Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: main
- Backend URL: https://antigravity-app-production-175a.up.railway.app

Tasks:
- [ ] 11.1 `git branch --show-current` (confirm on `feature/taty-per-tenant-profiles`); commit +
      push branch; open PR against `main` (classifier may block a direct push to main — hand off
      to founder if so)
- [ ] 11.2 Rebase-check `taty_service.py` / `telegram_endpoints.py` against latest `main`
      before merge (parallel sibling sessions may have landed commits)
- [ ] 11.3 Merge to `main`
- [ ] 11.4 Railway deploy active (backend change)
- [ ] 11.5 Check Railway access logs for any pre-deploy `/agents/ask` traffic from an unknown
      consumer (risk #2 in design.md) before considering the auth flip safe
- [ ] 11.6 Production verification: log in as a provisioned B2B client (founder supplies
      Bitwarden credentials) and call `/api/v1/agents/ask` with their session → answer scoped to
      their own `legal_name`, no "Cliente no configurado"
- [ ] 11.7 Production verification: unauthenticated call to `/api/v1/agents/ask` under
      `AUTH_ENFORCED=true` on Railway → 401
- [ ] 11.8 Production verification: Cliente Cero's existing Telegram chat still answers normally
- [ ] 11.9 Create report:
      `openspec/changes/taty-per-tenant-profiles/reports/YYYY-MM-DD-deployment.md`

## 12. Sync Specs and Archive

- [ ] 12.1 `openspec-sync-specs` — sync `taty-fiscal-assistant` delta spec into main
      `openspec/specs/`
- [ ] 12.2 Reviewer gate: `APPROVED` verdict in `progress/review_<id>.md` against
      `ARCHITECTURE.md`, `docs/backend-standards.md`, `DEPLOYMENT_STAGE/CHECKPOINTS.md`, and
      `.antigravity/GROUND_TRUTH.md` (régimen-omission wording)
- [ ] 12.3 Archive change to `openspec/changes/archive/YYYY-MM-DD-taty-per-tenant-profiles/`
- [ ] 12.4 `feature_list.json`: mark `taty-per-tenant-profiles` `done`
