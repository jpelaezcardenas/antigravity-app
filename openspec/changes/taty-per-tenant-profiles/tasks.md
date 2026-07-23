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

- [x] 3.1 Write failing tests in `apps/backend/tests/test_taty_endpoints_tenant_scoping.py`
      (mirrors `test_financials_endpoint_tenant_scoping.py` — call handlers directly with
      hand-built user dicts): resolved user → `ask` called with their tenant (scenario
      "Authenticated client is scoped to their own tenant"); staging user → Cliente Cero
      resolver invoked (scenario "Staging identity falls back to Cliente Cero"); authenticated
      unresolved → `error_code="tenant_not_resolved"`, Cliente Cero resolver asserted NEVER
      called (scenario "Unresolved authenticated caller does not leak another tenant"); user A
      + spoofed `company_id` of tenant B → `ask` called with A's tenant (scenario "A supplied
      `company_id` cannot be used to read another tenant's profile") —
      `progress/impl_taty-per-tenant-profiles-task3.md`
- [x] 3.2 Add `Depends(get_current_user)` + canonical resolution block (financials pattern) to
      POST/GET `/api/v1/agents/ask` in `apps/backend/presentation/taty_endpoints.py`; make
      `TatyAskRequest.company_id` `Optional` and ignored for resolution; add optional
      `error_code` to `TatyAskResponse`; add local `_resolve_cliente_cero_tenant_id()`. GET
      delegates to POST's handler (single resolution path). Reviewed APPROVED with adversarial
      bypass trace — no path found where a caller reads another tenant's profile.
      `progress/review_taty-per-tenant-profiles-task3.md`
- [x] 3.3 Tests from 3.1 green (5/5, 18/18 with tasks 1-2)

## 4. Backend: Telegram Tenant Translation (TDD)

- [x] 4.1 Write failing tests: mapped `company_id` resolving to a tenant → `ask(tenant_id=...)`
      called with the translated uuid (scenario "Mapped chat resolves and answers"); unmapped
      `company_id` → existing "no configurado" reply sent, `ask()` never invoked (scenario
      "Unmapped or untranslatable chat is rejected before calling Taty") —
      `progress/impl_taty-per-tenant-profiles-task4.md`
- [x] 4.2 Add `_resolve_tenant_for_company_id(company_id)` helper and use it before the
      `taty.ask(...)` call site in `apps/backend/presentation/telegram_endpoints.py` (Social Ops
      onboarding branch, which reads the same mapping, is untouched — reviewer confirmed). Fixed
      the call site flagged broken by task 2's report. Reviewed APPROVED.
      `progress/review_taty-per-tenant-profiles-task4.md`
- [x] 4.3 Tests from 4.1 green (5/5, 23/23 with tasks 1-3)

## 5. Backend: Retirements

- [x] 5.1 Delete deprecated `POST /api/v1/agents/taty/ask` route (lines only — rest of
      `apps/backend/presentation/agents_endpoints.py` untouched); confirm 404 (scenario
      "Deprecated wrapper route is gone") — `AskRequest` model kept (shared with
      `social_generate_content`, unrelated live route). `progress/impl_taty-per-tenant-profiles-task5.md`
- [x] 5.2 Delete `apps/backend/services/taty_intent_router.py` and
      `apps/backend/tests/test_taty_intent_router.py` (scenario "No unreferenced intent router
      remains") — reviewed APPROVED, `progress/review_taty-per-tenant-profiles-task5.md`
- [x] 5.3 Grep-verify no dangling imports of `taty_intent_router` or the deleted route anywhere
      in `apps/backend` (only comment-only historical mentions remain in whatsapp_endpoints.py /
      taty_lead_router.py, out of scope). Note: `router.py` has one stale comment naming
      `/agents/taty/ask` — non-functional, flagged for task 10 docs cleanup.

## 6. Backend: Review and Update Existing Unit Tests (MANDATORY)

- [x] 6.1 Grep `apps/backend/tests` for `AGENT_PROFILES`, `company_id.*taty`, `taty.*ask`,
      `ctx-001`, `ferez-001`, `martinez-001` and audit every hit — `progress/impl_taty-per-tenant-profiles-task6.md`.
      Result: **negative** — zero pre-existing test files (outside tasks 1-4's own new files)
      call `TatyAgentService.ask()`/`_get_agent_profile`/`AGENT_PROFILES`. All `ctx-001` hits in
      `test_agent_pipeline.py`, `test_centinela_alerts_get.py`, `test_identity_resolver.py`,
      `test_secure_llm.py`, `test_tenant_stamping.py` are unrelated `company_id` values on other
      services (CentinelaService, IdentityResolver, Social Ops, Pulso). Reviewed APPROVED
      (independently re-ran every grep + targeted tests). `progress/review_taty-per-tenant-profiles-task6.md`
- [x] 6.2 No changes needed (valid negative result). Found + flagged for task 7: 2 pre-existing
      TestClient-construction failures (`test_centinela_alerts_get.py`, `test_secure_llm.py`) —
      httpx/starlette version incompatibility, unrelated to this change (neither file touches
      anything tasks 1-5 modified).

## 7. Backend: Run Unit Tests and Verify Database State (MANDATORY)

- [x] 7.1 Capture pre-test baseline: attempted a live `tenants` count query; failed with
      `SupabaseException: supabase_url is required` (no live Supabase credentials configured in
      this local worktree, consistent with task 1's finding) — DB verification deferred to Stage
      11 (production Supabase) per CLAUDE.md's Stage 11 requirement —
      `progress/impl_taty-per-tenant-profiles-task7.md`
- [x] 7.2 Run targeted tests (this change's full new-test surface, all 4 files from tasks 1-4):
      23/23 passed
- [x] 7.3 Run full suite: `RUN_TESTS=1 bash init.sh` hung at the pre-existing
      `test_shadow_gl_stage8_e2e.py` issue (already flagged by task 2's reviewer); fallback
      `pytest apps/backend/tests/ -q --deselect .../test_shadow_gl_stage8_e2e.py` → 648 passed,
      25 failed, 109 skipped, 12 deselected, 13 errors — all 25 failures + 13 errors triaged and
      confirmed unrelated to this change's diff (missing local Supabase creds, pre-existing
      httpx/starlette `TestClient` incompatibility, Windows-encoding bug in unrelated Siigo CSV
      parsing). Zero new failures traceable to tasks 1-5.
- [x] 7.4 No live DB reachable ⇒ no mutation possible; independently confirmed all 4 new test
      files (`test_taty_tenant_profiles.py`, `test_taty_ask_tenant_scoping.py`,
      `test_taty_endpoints_tenant_scoping.py`, `test_telegram_taty_tenant_translation.py`) mock
      `get_supabase`/service internals — no real writes anywhere in this change's suite
- [x] 7.5 Report created:
      `openspec/changes/taty-per-tenant-profiles/reports/2026-07-23-step-7-unit-test-and-db-verification.md`
- [x] 7.6 Step complete — 7.2-7.5 done, PASS

## 8. Backend: Manual Endpoint Testing with curl (MANDATORY - AGENT MUST EXECUTE)

- [x] 8.1 Start local backend server — booted cleanly with zero Supabase credentials, all 60
      routes registered. `progress/impl_taty-per-tenant-profiles-task8.md`
- [x] 8.2 `curl GET /api/v1/agents/ask` unauthenticated (staging path) → routes correctly through
      `_resolve_cliente_cero_tenant_id()` but returns HTTP 500 locally (no reachable Supabase).
      Reviewer independently confirmed this is a byte-for-byte match of
      `financials_endpoints.py`'s identical, already-shipped helper (design D3's explicit
      "copy verbatim in spirit") — not a task-3 regression, just this environment's missing
      Supabase creds. Non-blocking pre-existing-pattern observation, not a code defect in this
      change. `progress/review_taty-per-tenant-profiles-task8.md`
- [x] 8.3 Deferred to Stage 11 (11.6) — requires a real Supabase-issued JWT for a provisioned
      client, unobtainable from this local environment (no Supabase credentials configured, per
      tasks 1/6/7's established finding)
- [x] 8.4 Deferred to Stage 11 — same reason as 8.3 (spoof-proofing already adversarially
      verified at the unit level in task 3's review; this item needs a real second tenant JWT to
      re-verify end-to-end in production)
- [x] 8.5 Deferred to Stage 11 (new item 11.6b added below per reviewer recommendation — Stage
      11 originally had no dedicated check for the authenticated-but-unresolved-tenant case)
- [x] 8.6 `curl POST /api/v1/agents/taty/ask` → confirmed 404 (route removed, task 5)
- [x] 8.7 Documented all commands + real responses in
      `openspec/changes/taty-per-tenant-profiles/reports/2026-07-23-step-8-manual-curl.md`.
      Reviewed APPROVED.

## 9. Frontend: E2E Testing with Playwright MCP

- [x] 9.1 N/A — this change touches backend endpoints only (`/api/v1/agents/ask`,
      Telegram webhook). No frontend workflow or UI changes; the only live in-repo consumer of
      this endpoint before this change was none (verified: Búnker bundle calls
      `/llm/analyze`/`/agents/onboarding/analyze`/`/agents/planner/generate-options`, never
      `/agents/ask`). Skipping per "MANDATORY if applicable."

## 10. Update Technical Documentation (MANDATORY)

- [x] 10.1 Update `apps/backend/presentation/taty_endpoints.py` docstrings/examples to drop
      `ctx-001`-as-request-param examples and reflect auth + `tenant_id` resolution — 2 stale
      spots fixed (query example path, JSON-only example → realistic curl w/ Authorization
      header); task 3 had already done the bulk of this. Also fixed a stale `/agents/taty/ask`
      comment in `router.py` (flagged by task 5). Reviewed APPROVED.
      `progress/impl_taty-per-tenant-profiles-task10.md`, `progress/review_taty-per-tenant-profiles-task10.md`
- [x] 10.2 Update `ARCHITECTURE.md` / `AGENTES.md` — genuine no-op, zero grep hits for
      `taty_intent_router`/`AGENT_PROFILES`/legacy client keys in either file
- [x] 10.3 Confirmed no symlink references broke — this change adds no new `ai-specs`-sourced
      artifacts (diff is entirely `apps/backend/`, `openspec/`, `progress/`)

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
- [ ] 11.6b Production verification: call `/api/v1/agents/ask` with a valid, authenticated
      session that has no active `user_tenants` membership → `error_code="tenant_not_resolved"`,
      never Cliente Cero (added per task 8's reviewer: local curl testing couldn't mint this JWT,
      so this closes that gap against real production auth)
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
