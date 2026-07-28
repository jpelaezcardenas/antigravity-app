## 0. Setup: Create Feature Branch (MANDATORY - FIRST STEP)

- [x] 0.1 Create feature branch `feature/taty-lead-router-tenant-scoping` from
      `feature/chatwoot-hermes-taty-bridge` (**not** `main` — `CrmService.whatsapp_intake` only
      exists on that branch today; see design.md's Hard dependency note)
- [x] 0.2 Verify branch creation and current branch status (`git status`, `git branch --show-current`)

## 1. Backend: Extend `whatsapp_intake` with optional `full_name` (TDD)

- [x] 1.1 Write a failing test in `apps/backend/tests/test_crm_whatsapp_intake.py`: a new phone with
      `full_name="Some Name"` creates a lead with that `full_name`; a new phone with no `full_name`
      creates a lead with `full_name` falling back to the phone number (matching
      `find_or_create_lead`'s existing behavior); an existing/known phone's lookup path ignores any
      `full_name` argument (never overwrites on find)
- [x] 1.2 Add `full_name: Optional[str] = None` to `CrmService.whatsapp_intake`'s signature; use
      `full_name or whatsapp_phone` only on the insert path, never touch the lookup path
- [x] 1.3 Run `pytest apps/backend/tests/test_crm_whatsapp_intake.py -v` and confirm all pass
      (including the pre-existing tests from Task Group 1 of `chatwoot-hermes-taty-bridge`, which
      call `whatsapp_intake` without `full_name` and must be unaffected) — 8 passed

## 2. Backend: `find_or_create_lead` delegates to `CrmService.whatsapp_intake` (TDD)

- [x] 2.1 Rewrite the two `find_or_create_lead` tests in `apps/backend/tests/test_taty_lead_router.py`
      to mock `services.taty_lead_router.get_crm_service` (matching the pattern already used by
      `route_lead_message`'s tests in the same file) instead of `get_service_supabase` — assert
      `CrmService.whatsapp_intake` is called with the given phone (and `full_name` when provided),
      and that `find_or_create_lead`'s return value is the mocked `lead_id`. Confirm these rewritten
      tests fail against the *current* (pre-delegation) implementation.
- [x] 2.2 Rewrite `find_or_create_lead` in `apps/backend/services/taty_lead_router.py` to call
      `get_crm_service().whatsapp_intake(whatsapp_phone, full_name=full_name)` and return
      `result["lead_id"]`, removing its own direct `get_service_supabase()` query and its own inline
      Cliente Cero tenant-resolution query entirely
- [x] 2.3 Run `pytest apps/backend/tests/test_taty_lead_router.py -v` and confirm all pass — 41 passed

## 3. Backend: Review and Update Existing Unit Tests (MANDATORY)

- [x] 3.1 Review `apps/backend/tests/test_whatsapp_endpoints.py` (the caller of `find_or_create_lead`
      via `whatsapp_endpoints.py`) for any assumption about its internals (e.g. mocking
      `get_service_supabase` transitively) that the delegation changes; update if needed — it should
      only need to mock `find_or_create_lead` itself or `get_crm_service`, not raw Supabase calls —
      confirmed it mocks `find_or_create_lead` directly at the presentation-layer import site, no
      update needed
- [x] 3.2 Confirm no other caller of `find_or_create_lead` exists beyond `whatsapp_endpoints.py`
      (grep the full `apps/backend/` tree) — confirmed, no other caller

## 4. Backend: Run Unit Tests and Verify Database State (MANDATORY)

- [x] 4.1 Capture pre-test database baseline — N/A, all tests use a mocked Supabase/CrmService
- [x] 4.2 Run targeted tests — 58 passed
- [x] 4.3 Run the full backend suite (from `apps/backend/` as cwd) — 588 passed, 40 pre-existing
      failures independently confirmed identical before/after this change (see report)
- [x] 4.4 Verify post-test database state — N/A, mocked
- [x] 4.5 Create report
      `openspec/changes/taty-lead-router-tenant-scoping/reports/2026-07-23-step-4-unit-test-and-db-verification.md`
- [x] 4.6 Mark this step complete only after tests pass and the report exists

## 5. Backend: Manual Endpoint Testing with curl (MANDATORY - AGENT MUST EXECUTE)

- [x] 5.1 Start the backend server locally with `CRM_CANONICAL=true WHATSAPP_CANONICAL=true` — done,
      cleanly stopped afterward (port 8080 confirmed free)
- [x] 5.2 `curl -X POST .../webhook` with a simulated Meta WhatsApp payload — hit the same known
      `SUPABASE_SERVICE_ROLE_KEY` gap, but the traceback confirms `find_or_create_lead` delegates
      through `whatsapp_intake` -> `_resolve_cliente_cero_tenant_id` (the corrected, tenant-scoped
      path), not the old direct query. Also verified `GET /webhook` hub.challenge verification
      (200 correct token, 403 wrong token).
- [x] 5.3 Document all curl commands and responses in
      `openspec/changes/taty-lead-router-tenant-scoping/reports/2026-07-23-step-5-curl-verification.md`

## 6. Documentation

- [x] 6.1 No `ARCHITECTURE.md` change needed — no new container, no new external dependency
- [x] 6.2 `find_or_create_lead`'s docstring already updated (done as part of Task Group 2's
      implementation) to point future readers at `CrmService.whatsapp_intake` and explicitly warn
      against reintroducing a duplicate, tenant-less lookup

## 7. Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [x] 7.1 This change's branch merges into `feature/chatwoot-hermes-taty-bridge` (its base), not
      directly into `main` — it ships to production only when that branch's own Stage 11 (backend
      endpoint → Railway `-175a`) runs, since neither `CRM_CANONICAL` nor `WHATSAPP_CANONICAL` is
      live in production yet regardless
- [x] 7.2 Create report:
      `openspec/changes/taty-lead-router-tenant-scoping/reports/2026-07-23-deployment.md`, noting
      the merge target and that production deploy is deferred to the parent branch's own Stage 11

## 8. Review Gate

- [x] 8.1 `reviewer` agent validated (`progress/review_taty-lead-router-tenant-scoping-final.md`):
      initial verdict CHANGES_REQUESTED on one item — `tasks.md`/deployment report were uncommitted
      at review time — resolved by commit `e82b37f`. Spec compliance, no hardcoded secrets,
      English-only, no scope creep into `route_lead_message`/`route_lead_document` all confirmed
      PASS on fresh code re-read, independent of the report's claims.
- [x] 8.2 `RUN_TESTS=1 bash init.sh` — the review that surfaced this task also discovered init.sh's
      own pytest-gate had a false-green bug (piped exit code swallowed by `tail`), fixed separately
      this session (see `chatwoot-hermes-taty-bridge` tasks.md). Re-verified in that change's final
      review gate: `init.sh` now correctly reports `[FAIL]` due to ~40 pre-existing, unrelated
      backend failures (none touching `crm_service.py`/`taty_lead_router.py`/
      `whatsapp_endpoints.py`), not a false `[OK]`.
