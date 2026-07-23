# Review - task taty-lead-router-tenant-scoping (final gate)

**Verdict:** CHANGES_REQUESTED


## Scope of this gate

Code (Task Groups 1-2) was already independently reviewed and APPROVED in
progress/review_taty-lead-router-tenant-scoping-tasks1-2.md. This gate re-verifies that
review's findings still hold against the current code, verifies the leader's post-implementer
work (verification reports, deployment report, task checkboxes), runs the harness's own gate,
and checks CHECKPOINTS.md.

## 1. Spec compliance - re-verified fresh

- apps/backend/services/crm_service.py:387-427 (whatsapp_intake): lookup is keyed on both
  tenant_id (resolved via _resolve_cliente_cero_tenant_id) AND whatsapp_phone
  (.eq("tenant_id", tenant_id).eq("whatsapp_phone", normalized_phone), lines 402-409);
  full_name is applied only on the insert path (line 420), never on the lookup path - matches
  spec.md's MODIFIED requirement and design.md Decision 2.
- apps/backend/services/taty_lead_router.py:246-255 (find_or_create_lead): delegates fully
  to get_crm_service().whatsapp_intake(whatsapp_phone, full_name=full_name)["lead_id"]; no
  independent Supabase query remains in this function. route_lead_message /
  route_lead_document (lines 258-410) are untouched.
- Confirmed via git diff --stat between the parent and this branch: only 4 backend files touched
  (crm_service.py, taty_lead_router.py, test_crm_whatsapp_intake.py,
  test_taty_lead_router.py) plus OpenSpec artifacts - no scope creep into
  apps/chatwoot-bridge/ or unrelated modules.
- No hardcoded secrets found in the touched files (grepped for key/password/token patterns -
  none found).
- All touched artifacts are English-only.

Verdict on item 1: PASS.

## 2. tasks.md vs disk - verified, with a discrepancy

- Task Groups 1-6 checkboxes are [x] and each claim matches disk:
  - reports/2026-07-23-step-4-unit-test-and-db-verification.md exists, claims "58 passed"
    (targeted) and "588 passed, 40 failed, 109 skipped" (full suite) - independently
    reproduced identically (see section 3 below).
  - reports/2026-07-23-step-5-curl-verification.md exists and documents the curl commands and
    responses as claimed.
  - reports/2026-07-23-deployment.md exists.
- Discrepancy from the brief: the brief states the leader marked all tasks.md checkboxes.
  This is not accurate - openspec/changes/taty-lead-router-tenant-scoping/tasks.md
  lines 3-6 (Task 0.1/0.2, branch setup) and lines 90-94 (Task 8.1/8.2, this review gate) are
  still [ ]. Task 8.1/8.2 being unchecked is expected (this review IS 8.1). Task 0.1/0.2
  being unchecked despite the branch clearly existing and being checked out is a minor,
  non-blocking hygiene gap.

Verdict on item 2: PASS (with the above unchecked-0.1/0.2 note, non-blocking).

## 3. RUN_TESTS=1 bash init.sh - ran, but the harness's own pytest gate is not trustworthy as-is

Full output:

```
[OK]    Exists ARCHITECTURE.md
[OK]    Exists HARNESS.md
[OK]    Exists CLAUDE.md
[OK]    Exists AGENTES.md
[OK]    Exists .antigravity/GROUND_TRUTH.md
[OK]    Exists .claude/agents/leader.md
[OK]    Exists .claude/agents/implementer.md
[OK]    Exists .claude/agents/reviewer.md
[OK]    Exists progress/current.md
[OK]    Exists progress/history.md
[OK]    Exists feature_list.json
[OK]    Exists DEPLOYMENT_STAGE/CHECKPOINTS.md
[OK]    feature_list.json valid (active=chatwoot-hermes-taty-bridge, 2 features)
No module named pytest
[OK]    Backend tests passed      <-- FALSE GREEN, see below
[OK]    Harness ready. You can start working.
```

Finding (new, not in CHECKPOINTS.md today): init.sh's backend-test line runs a pytest
invocation piped into tail, then checks the exit status with an if. Because of the pipe,
bash's exit status reflects tail's exit code (always 0), not pytest's. On this machine the
resolved python3 interpreter had no pytest module installed at all - so the gate printed
"Backend tests passed" while zero tests actually ran. This is a latent bug in init.sh itself
(unrelated to this change's code) that silently green-lights a broken test environment.
Recommend adding a new CHECKPOINTS.md rule per the self-improving loop: init.sh's pytest step
must check pytest's actual exit code, not the exit code of a downstream pipe stage, and must
fail loudly if the resolved interpreter has no pytest installed. This is out of scope to fix
in this change, but it means init.sh's own report cannot be trusted as test-gate evidence -
see the manual re-run below, which is what this verdict actually relies on.

Manual re-run (correct interpreter, apps/backend as cwd, matching the Step 4 report's own
methodology):

- Targeted: pytest tests/test_crm_whatsapp_intake.py tests/test_taty_lead_router.py
  tests/test_whatsapp_endpoints.py -q -> 58 passed, 0 failed - matches the report exactly.
- Full suite (excluding the 3 pre-existing collection-error files, same as the report):
  pytest tests -q, ignoring test_profile_support.py, test_swarm_operators.py, and
  test_t11_integration.py -> 588 passed, 40 failed, 109 skipped - matches the report's
  claimed numbers exactly. The 40 failing files (test_approval_rules_stage3_4.py,
  test_approval_rules_stage8_11.py, test_centinela_alerts_get.py,
  test_model_selector_cloud_only.py, test_secure_llm.py, test_shadow_gl_integration.py,
  test_shadow_gl_siigo_csv.py, test_shadow_gl_stage1_migration.py,
  test_shadow_gl_stage4_uploader.py, test_shadow_gl_stage5_error_handling.py,
  test_shadow_gl_stage8_e2e.py, test_wizard_auditoria_sombra.py) touch none of
  crm_service.py, taty_lead_router.py, or whatsapp_endpoints.py - confirms the report's
  "pre-existing, unrelated" claim.

Verdict on item 3: pytest results genuinely green modulo the pre-existing, unrelated 40
failures (independently reproduced). init.sh's own report line is unreliable due to a pipe
exit-code bug - flagging as a harness defect, not a defect in this change.

## 4. CHECKPOINTS.md-relevant items

- No hardcoded secrets: confirmed (section 1).
- English-only artifacts: confirmed.
- No scope creep beyond declared files: confirmed (section 1 diff stat).
- Stage 0 checkpoint "git status limpio", Stage 7 "Report pusheado a rama", and Stage 8
  "Reporte de deployment visible en git" are NOT currently satisfied. git status on
  feature/taty-lead-router-tenant-scoping shows:
  - openspec/changes/taty-lead-router-tenant-scoping/tasks.md - modified, uncommitted
    (this is the file with all the [x] checkboxes verified in section 2 - they only exist in
    the working tree, not in git history yet).
  - openspec/changes/taty-lead-router-tenant-scoping/reports/2026-07-23-deployment.md -
    untracked, not committed.
  - Unrelated uncommitted changes also present in the working tree
    (.claude/settings.local.json, the archived bunker-pwa-auth-enforcement/tasks.md,
    ai-specs/social-content-ops/, openspec/changes/per-tenant-client-access/reports/) - none
    of these belong to this change and should not be swept into its commit.
  - Steps 4/5 reports and the code diff itself ARE already committed on this branch
    (confirmed via git diff --stat against the parent branch).

This is a genuine, concrete gap against the harness's own written checkpoints: the tasks.md
checkbox state and the deployment report this review is supposed to validate are not yet part
of the branch's git history - only working-tree edits. If this worktree were discarded today,
that record of completion would be lost, and git log on this branch would not show it.

## 5. feature_list.json

Read directly: "active" is "chatwoot-hermes-taty-bridge"; two entries listed
(adopt-gbrain-second-brain, status done; chatwoot-hermes-taty-bridge, status in_progress,
summary references Task Groups 5-10 remaining, Task Groups 1-4 already done).

taty-lead-router-tenant-scoping is not listed as its own entry in feature_list.json - it is
tracked only as an OpenSpec sub-change under the parent chatwoot-hermes-taty-bridge, which is
consistent with this change's own tasks.md Task 7.1 (merges into the parent branch, no
independent Stage 11). This does not violate the one-change-at-a-time invariant (active still
correctly points at the parent), so this item is not a blocker - flagging only so it is
recorded as consciously checked, not assumed.

## Checkpoints
- C1 (spec.md compliance, fresh code read): [x]
- C2 (tasks.md claims match disk artifacts): [x] - content matches; not yet committed (see C4)
- C3 (RUN_TESTS=1 bash init.sh plus manual pytest reproduction, green modulo pre-existing
  failures): [x] - see caveat about init.sh's own unreliable report
- C4 (git hygiene - tasks.md and deployment report committed to branch): [ ] - Reason:
  openspec/changes/taty-lead-router-tenant-scoping/tasks.md (modified, uncommitted) and
  openspec/changes/taty-lead-router-tenant-scoping/reports/2026-07-23-deployment.md
  (untracked) are not in git history on this branch - violates CHECKPOINTS.md Stage 7
  "Report pusheado a rama" and Stage 8 "Reporte de deployment visible en git"
- C5 (no hardcoded secrets, English-only, no scope creep): [x]
- C6 (feature_list.json reviewed, one-change-at-a-time invariant intact): [x]

## Required changes

1. Commit openspec/changes/taty-lead-router-tenant-scoping/tasks.md and
   openspec/changes/taty-lead-router-tenant-scoping/reports/2026-07-23-deployment.md to
   feature/taty-lead-router-tenant-scoping - do not sweep in the unrelated uncommitted files
   currently sitting in the working tree (.claude/settings.local.json, the archived
   bunker-pwa-auth-enforcement/tasks.md, ai-specs/social-content-ops/,
   openspec/changes/per-tenant-client-access/reports/) - those belong to other, unrelated work
   and should be committed separately or left alone.
2. (Non-blocking, filed for the self-improving loop) Fix init.sh's backend-test step
   (RUN_TESTS=1 branch) so it checks pytest's actual exit code instead of the exit code of the
   tail pipe stage, and fails/warns loudly if the resolved interpreter has no pytest module -
   currently it silently reports "Backend tests passed" even when pytest never ran.
3. (Non-blocking, cosmetic) Mark tasks.md Task 0.1/0.2 [x] or add a one-line note - the branch
   demonstrably exists and is checked out, so leaving them unchecked is just inaccurate
   bookkeeping.

Once item 1 is committed, this change is otherwise ready for merge into
feature/chatwoot-hermes-taty-bridge - the code (already approved in the tasks1-2 review),
spec compliance, and test evidence all hold up under independent re-verification.
