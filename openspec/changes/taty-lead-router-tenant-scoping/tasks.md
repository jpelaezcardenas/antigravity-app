## 0. Setup: Create Feature Branch (MANDATORY - FIRST STEP)

- [ ] 0.1 Create feature branch `feature/taty-lead-router-tenant-scoping` from
      `feature/chatwoot-hermes-taty-bridge` (**not** `main` — `CrmService.whatsapp_intake` only
      exists on that branch today; see design.md's Hard dependency note)
- [ ] 0.2 Verify branch creation and current branch status (`git status`, `git branch --show-current`)

## 1. Backend: Extend `whatsapp_intake` with optional `full_name` (TDD)

- [ ] 1.1 Write a failing test in `apps/backend/tests/test_crm_whatsapp_intake.py`: a new phone with
      `full_name="Some Name"` creates a lead with that `full_name`; a new phone with no `full_name`
      creates a lead with `full_name` falling back to the phone number (matching
      `find_or_create_lead`'s existing behavior); an existing/known phone's lookup path ignores any
      `full_name` argument (never overwrites on find)
- [ ] 1.2 Add `full_name: Optional[str] = None` to `CrmService.whatsapp_intake`'s signature; use
      `full_name or whatsapp_phone` only on the insert path, never touch the lookup path
- [ ] 1.3 Run `pytest apps/backend/tests/test_crm_whatsapp_intake.py -v` and confirm all pass
      (including the pre-existing tests from Task Group 1 of `chatwoot-hermes-taty-bridge`, which
      call `whatsapp_intake` without `full_name` and must be unaffected)

## 2. Backend: `find_or_create_lead` delegates to `CrmService.whatsapp_intake` (TDD)

- [ ] 2.1 Rewrite the two `find_or_create_lead` tests in `apps/backend/tests/test_taty_lead_router.py`
      to mock `services.taty_lead_router.get_crm_service` (matching the pattern already used by
      `route_lead_message`'s tests in the same file) instead of `get_service_supabase` — assert
      `CrmService.whatsapp_intake` is called with the given phone (and `full_name` when provided),
      and that `find_or_create_lead`'s return value is the mocked `lead_id`. Confirm these rewritten
      tests fail against the *current* (pre-delegation) implementation.
- [ ] 2.2 Rewrite `find_or_create_lead` in `apps/backend/services/taty_lead_router.py` to call
      `get_crm_service().whatsapp_intake(whatsapp_phone, full_name=full_name)` and return
      `result["lead_id"]`, removing its own direct `get_service_supabase()` query and its own inline
      Cliente Cero tenant-resolution query entirely
- [ ] 2.3 Run `pytest apps/backend/tests/test_taty_lead_router.py -v` and confirm all pass

## 3. Backend: Review and Update Existing Unit Tests (MANDATORY)

- [ ] 3.1 Review `apps/backend/tests/test_whatsapp_endpoints.py` (the caller of `find_or_create_lead`
      via `whatsapp_endpoints.py`) for any assumption about its internals (e.g. mocking
      `get_service_supabase` transitively) that the delegation changes; update if needed — it should
      only need to mock `find_or_create_lead` itself or `get_crm_service`, not raw Supabase calls
- [ ] 3.2 Confirm no other caller of `find_or_create_lead` exists beyond `whatsapp_endpoints.py`
      (grep the full `apps/backend/` tree) — none expected, but verify

## 4. Backend: Run Unit Tests and Verify Database State (MANDATORY)

- [ ] 4.1 Capture pre-test database baseline — N/A, all tests use a mocked Supabase/CrmService
- [ ] 4.2 Run targeted tests: `pytest apps/backend/tests/test_crm_whatsapp_intake.py
      apps/backend/tests/test_taty_lead_router.py apps/backend/tests/test_whatsapp_endpoints.py -v`
- [ ] 4.3 Run the full backend suite (from `apps/backend/` as cwd, per the cwd-relative test
      discovered in `chatwoot-hermes-taty-bridge`'s Step 3 report): `pytest tests -v`
- [ ] 4.4 Verify post-test database state — N/A, mocked
- [ ] 4.5 Create report
      `openspec/changes/taty-lead-router-tenant-scoping/reports/YYYY-MM-DD-step-4-unit-test-and-db-verification.md`
- [ ] 4.6 Mark this step complete only after tests pass and the report exists

## 5. Backend: Manual Endpoint Testing with curl (MANDATORY - AGENT MUST EXECUTE)

- [ ] 5.1 Start the backend server locally with `CRM_CANONICAL=true WHATSAPP_CANONICAL=true` (both
      routers must be mounted to exercise this end-to-end)
- [ ] 5.2 `curl -X POST http://127.0.0.1:8080/api/v1/channels/whatsapp/webhook` with a simulated
      Meta WhatsApp payload for a fresh phone number → verify the response and check server logs
      confirm `find_or_create_lead` delegated through `CrmService.whatsapp_intake` (tenant-scoped
      query in the logs/traceback path, not the old direct query) — if this 500s on a missing
      `SUPABASE_SERVICE_ROLE_KEY` (the same pre-existing local env gap documented in
      `chatwoot-hermes-taty-bridge`'s Step 4 report), document that explicitly rather than treating
      it as a new regression, same as that report did
- [ ] 5.3 Document all curl commands and responses in
      `openspec/changes/taty-lead-router-tenant-scoping/reports/YYYY-MM-DD-step-5-curl-verification.md`

## 6. Documentation

- [ ] 6.1 No `ARCHITECTURE.md` change needed — no new container, no new external dependency
- [ ] 6.2 Note in `apps/backend/services/taty_lead_router.py`'s module docstring or
      `find_or_create_lead`'s own docstring that it now delegates to `CrmService.whatsapp_intake`
      rather than querying Supabase directly (so a future reader doesn't reintroduce the duplicate)

## 7. Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [ ] 7.1 This change's branch merges into `feature/chatwoot-hermes-taty-bridge` (its base), not
      directly into `main` — it ships to production only when that branch's own Stage 11 (backend
      endpoint → Railway `-175a`) runs, since neither `CRM_CANONICAL` nor `WHATSAPP_CANONICAL` is
      live in production yet regardless
- [ ] 7.2 Create report:
      `openspec/changes/taty-lead-router-tenant-scoping/reports/YYYY-MM-DD-deployment.md`, noting
      the merge target and that production deploy is deferred to the parent branch's own Stage 11

## 8. Review Gate

- [ ] 8.1 `reviewer` agent validates against `specs/taty-whatsapp-sales-router/spec.md`'s modified
      requirement, `design.md`'s decisions, no hardcoded secrets, English-only, no scope creep into
      `route_lead_message`/`route_lead_document`
- [ ] 8.2 `RUN_TESTS=1 bash init.sh` green before marking ready to archive (only after merging into
      `feature/chatwoot-hermes-taty-bridge`)
