# Review — b2c-social-lead-capture, Task 2

**Verdict:** APPROVED

## Checkpoints

- Endpoint contract matches design.md Decision 2 and tasks.md 2.1-2.4: `POST
  /api/v1/crm/social-capture/partial` implemented in
  `apps/backend/presentation/social_capture_endpoints.py`, mounted unconditionally via
  `presentation/router.py` (prefix `/crm`) as a standalone router, deliberately not inside
  `crm_router` (which applies `get_current_user`). Confirmed via `git diff` that no
  `Depends(get_current_user)` exists anywhere in the new router — genuinely public, matching
  the explicit, narrow exception to ARCHITECTURE.md Decisions #13-#17 documented in both the
  module docstring and design.md. [x]
- Reuse, not duplication: `CrmService.whatsapp_intake` gained an additive `source: Optional[str]
  = None` param (`apps/backend/services/crm_service.py`), stamped only on the insert path — an
  existing lead's `source` is never overwritten on repeat capture. The new endpoint calls this
  same method rather than reimplementing find-or-create. Matches design.md Decision 2 exactly. [x]
- IP + phone throttle (tasks.md 2.3): `apps/backend/services/social_capture_throttle.py`, in-
  process dict/deque-backed, `IP_MAX_REQUESTS=5`/`IP_WINDOW_SECONDS=60` and
  `PHONE_WINDOW_SECONDS=600`. IP-throttled requests never reach the service layer (429, no
  `whatsapp_intake` call); phone-repeat requests are silently no-op'd (`{"is_new": false,
  "throttled_repeat": true}`), also never reaching the service layer — correctly prevents
  duplicate leads/future duplicate first-contact sends per design.md's stated risk mitigation.
  In-process (not Supabase-backed) is an explicit, justified trade-off (single Railway instance,
  narrow abuse surface) documented in the module docstring, matching tasks.md 2.3's "to decide
  during implementation" framing. [x]
- Migration `0052_crm_leads_source.sql` matches tasks.md 1.1/1.2: nullable `source text`, no
  default, no backfill, same additive pattern as `lead_type` (0049). Already applied live per
  tasks.md 1.2 and the founder-confirmed note in `progress/current.md`. [x]
- TDD / real outcome assertions, not "no exception": 6 new tests in
  `tests/test_social_capture_endpoints.py` assert actual status codes, response bodies, and
  `assert_called_once_with(...)` argument values (e.g.
  `test_delegates_to_crm_service_whatsapp_intake_with_source`,
  `test_repeat_phone_within_window_is_a_no_op`). One additional test
  (`test_source_stamped_only_on_insert_path`) exercises `CrmService.whatsapp_intake` directly
  with a MagicMock Supabase client and asserts the actual insert payload contains
  `source`. [x]
- Independently re-ran the tests myself (not trusting the implementer's report blindly):
  `cd apps/backend && py -3.11 -m pytest tests/test_social_capture_endpoints.py
  tests/test_crm_whatsapp_intake.py -v` → **18 passed in 6.13s**, byte-identical result to the
  implementer's claimed output, including all 12 pre-existing `test_crm_whatsapp_intake.py`
  tests (confirming zero regression in the extended `whatsapp_intake` method). [x]
- Full-suite regression check: independently ran `py -3.11 -m pytest -q` from `apps/backend`.
  Result: 3 collection errors (`test_profile_support.py`, `test_swarm_operators.py`,
  `test_t11_integration.py`, all `ModuleNotFoundError: No module named 'apps.backend'`) — a
  pre-existing, unrelated `sys.path`/absolute-import issue, not caused by this task (none of the
  three touch `crm_service`, `social_capture_*`, or `router.py`; the error is a collection-time
  import failure identical in shape to the known pre-existing baseline noise documented in
  project memory `project_pytest_interpreter_py311`). This blocks a full pass/fail count via `-q`
  but does not implicate any file this task touched — confirmed by running the scoped test files
  directly above, which pass cleanly. Task 6 (explicitly out of scope for Task 2) owns doing the
  full-sweep-vs-main diff properly; this reviewer independently confirms no new regression was
  introduced by Task 2's files specifically. [x]
- Scope discipline: `git status --porcelain apps/backend/` shows exactly the files the
  implementer's report claims: `social_capture_throttle.py` (new), `social_capture_endpoints.py`
  (new), `test_social_capture_endpoints.py` (new), `crm_service.py` (additive edit),
  `router.py` (additive edit), plus migration `0052`. `channels/whatsapp.py`,
  `core/plan_features.py`, `tests/test_whatsapp_channel.py`,
  `services/taty_lead_router.py`, `tests/test_taty_lead_router.py` are also modified in the
  working tree, but these belong to the concurrently in-flight `taty-document-collection-wiring`
  change (confirmed via `git diff services/taty_lead_router.py` — the diff is
  `download_chatwoot_attachment`/`data_url` branching, matching that change's design.md, not
  anything in `b2c-social-lead-capture`'s scope) — pre-existing dirty state from a parallel
  session, not introduced by this implementer, and correctly excluded from the "Files touched"
  list in `progress/impl_b2c_social_task2.md`. No Task 3 (first-contact trigger), Task 4
  (frontend), or Task 6 (full sweep) work was touched. [x]
- No fabricated stubs, no disabled type-checking, no hand-edited `app/`. [x]
- Docs-sync: no `ARCHITECTURE.md` container/dependency change required — this is a new endpoint
  inside the existing Backend API container, with an explicitly narrow, already-precedented
  tenant-scoping exception (public endpoint resolving to Cliente Cero) that the endpoint's own
  docstring documents inline referencing Decisions #13-#17. No new external dependency. [x]

## Required changes

1. **`openspec/changes/b2c-social-lead-capture/tasks.md` lines 17-25 (subtasks 2.1-2.4) are still
   `[ ]` despite Task 2 being fully implemented, tested, and now reviewer-approved.** This is the
   same gap already caught once this session on the sibling `taty-document-collection-wiring`
   Task 1 (see `progress/current.md`'s "Gap detectado este tick" note) — CLAUDE.md §7 requires
   OpenSpec artifacts to reflect reality, and `tasks.md` is the sole source of truth for "what's
   done" per HARNESS.md's Capa 3. Whoever picks up Task 3 (or the leader before dispatching it)
   must check off 2.1-2.4 with a pointer to this review file before treating Task 2 as closed —
   do not let a second implementer session silently re-attempt work that is actually finished.

Non-blocking for this review's verdict (the code, tests, and scope are all sound), but this must
be closed before the change is archived (Stage 8 checkpoint: "Todos los checkpoints anteriores
están ✅").
