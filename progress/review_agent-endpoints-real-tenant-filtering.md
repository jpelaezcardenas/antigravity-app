# Review - agent-endpoints-real-tenant-filtering

**Original verdict:** CHANGES_REQUESTED (commit d05259c)

**Resolution (commit 4de5c55):** both blocking issues fixed directly (not by a fresh reviewer
pass, given their mechanical nature):
1. ARCHITECTURE.md's duplicate "16." renumbered to "17"; Decision #15's forward-reference
   updated from "ver más abajo" to "ver Decisión #17"; verified via
   `grep -n "^1[4-7]\." ARCHITECTURE.md` showing unique 14/15/16/17.
2. tasks.md's task 11.2 and the Stage 7 report's `init.sh` addendum (both flagged as
   uncommitted) are now committed in 4de5c55; `git status` confirmed clean.

No further code, test, or spec changes were needed — the reviewer's independent re-verification
of the tenant-security implementation itself (6-file migration, helper removal, 403→404,
zero-regression full-suite diff against an isolated `origin/main` worktree) found no issues.

Reviewed commit: d05259c on feature/agent-endpoints-real-tenant-filtering
(worktree: .claude/worktrees/agent-endpoints-real-tenant-filtering).

## Summary of what was independently verified as correct

- apps/backend/presentation/agents_endpoints.py -- all 7 remaining routes now have
  user: dict = Depends(get_current_user), no tenant param threaded through, and
  /orchestrator/full-pipeline (lines 435-454) still returns "mode": "demo" unchanged.
- apps/backend/presentation/pulso_diario_endpoints.py and centinela_agents_endpoints.py
  now require auth and resolve tenant exclusively via resolve_request_tenant_scope; the
  getattr(request.state, "tenant_id", "default-tenant") pattern and the literal string
  "default-tenant" are both gone (confirmed by reading the files and running the tests).
- apps/backend/core/tenant_context.py::resolve_caller_tenant is fully removed. Repo-wide grep
  (grep -rn "resolve_caller_tenant") turns up only comments referencing the removal
  (tenant_context.py:12, test_centinela_endpoint_tenant_scoping.py:11,
  test_tenant_context_helpers.py:8, test_tenant_stamping.py:33) -- no dangling code
  references. Taty's file-local _resolve_cliente_cero_tenant_id / _STAGING_USER import are
  also gone from taty_endpoints.py.
- centinela_endpoints.py (lines 120, 196) and taty_endpoints.py (line 165) both now call
  resolve_request_tenant_scope instead of the removed helpers; observable behavior (empty
  result / source="none" for Centinela, error_code="tenant_not_resolved" for Taty) is
  unchanged per the spec and matching tests.
- approval_queue_endpoints.py -- enqueue_for_approval (line 140), approve_draft (line 193),
  reject_draft (line 232) all raise HTTPException(status_code=404, ...), not 403.
- Test coverage is genuine TDD, not rubber-stamping: test_centinela_endpoint_tenant_scoping.py
  and test_taty_endpoints_tenant_scoping.py both correctly account for
  resolve_request_tenant_scope's real behavior difference from the removed helpers (it always
  calls resolve_cliente_cero_tenant_id first, even off the staging path) via an explicit
  autouse fixture stubbing that lookup to an unrelated id -- this is exactly the subtlety the
  task asked to check for, and it was handled correctly, not copy-pasted.
- No scope creep: git diff origin/main...HEAD --stat touches only the 6 named presentation
  files, core/tenant_context.py, the listed test files, and docs/OpenSpec artifacts.
  sell_machine_endpoints.py and services/operator_task_service.py have zero diff.
- No hardcoded secrets found in the diff; code is English-only; no disabled type-checking, no
  fabricated stubs.
- Independently re-ran the full targeted test list -- 46/46 passed, matching the reports'
  claims exactly.
- Independently re-ran the full backend suite from both apps/backend (my result: 40 failed,
  112 skipped, 13 errors after excluding the 3 pre-existing ModuleNotFoundError collection
  files, matching the reports' failure/error counts exactly; passed-count showed a roughly
  12-test offset from the report's number both on this branch and on my own from-scratch
  origin/main baseline -- a consistent, environment-driven offset, not a regression) and from
  the repo root via RUN_TESTS=1 bash init.sh (my result: 27 failed, 744 passed, 112
  skipped, 13 errors on this branch). A genuinely isolated
  git worktree add --detach origin/main baseline was then built independently, producing 27
  failed, 739 passed, 112 skipped, 13 errors -- an exact match to both this branch's and the
  report's numbers except for the expected +5 net-test-count delta. The zero-regressions claim
  in reports/2026-07-23-step-7-unit-test-and-db-verification.md is independently confirmed,
  not just trusted.
- reports/2026-07-23-step-8-curl-verification.md's reasoning (local Supabase-credential-less
  environment blocks the resolved-tenant/401/404 curl checks; deferred to Stage 10) is plausible
  and consistent with the repo's known local-dev gap and the same precedent set by
  taty-per-tenant-profiles.

## Required changes

1. ARCHITECTURE.md duplicate "16." decision -- real docs defect this change introduced.
   ARCHITECTURE.md:125 (this change's new decision, starting "Un solo contrato de resolucion
   de tenant...") and ARCHITECTURE.md:126 (the pre-existing Taty decision from
   taty-per-tenant-profiles, already numbered 16 on origin/main) are now both numbered
   "16." Verified via git show origin/main:ARCHITECTURE.md -- the Taty decision was already
   16. before this change; this change inserted its own new decision as 16. immediately
   before it instead of renumbering to 17. This is exactly the kind of canon-doc drift
   CLAUDE.md Section 0 and HARNESS.md's docs-sync rule exist to prevent -- a sequential decision
   log with two entries labeled "16" breaks future cross-references (a later doc citing
   "Decision #16" becomes ambiguous). Fix: renumber this change's new decision to 17. (and
   correspondingly any other cross-references that cite "Decision #16" for this specific item).

2. Working tree has uncommitted edits to OpenSpec artifacts that the reviewed commit
   (d05259c) does not contain. git status on the worktree shows unstaged modifications to
   openspec/changes/agent-endpoints-real-tenant-filtering/tasks.md (task 11.2, currently
   unchecked at HEAD, is checked off with a full init.sh / isolated-worktree justification only
   in the working tree) and to
   reports/2026-07-23-step-7-unit-test-and-db-verification.md (the entire "Addendum --
   RUN_TESTS=1 bash init.sh" section, with the isolated-worktree-baseline comparison, exists
   only uncommitted). Per this repo's CLAUDE.md Section 7 ("documentation is the source of
   truth"; artifacts must be updated, not left dangling) and the general hygiene the harness
   enforces (progress/ state must be on disk and versioned, not floating in an uncommitted
   working tree), these edits need to be committed before this change can be considered
   reviewable as a fixed point -- right now the artifact claiming "11.2 done, verified no
   regression" does not actually exist in the commit under review. The content itself is good,
   and its claims were independently re-verified above, so this is a commit-it fix, not a
   redo-it fix.

## Non-blocking observations (do not need to gate approval once the above are fixed)

- No progress/impl_agent-endpoints-real-tenant-filtering*.md file exists -- this change
  appears to have been implemented directly against the OpenSpec tasks.md rather than through
  the leader-implementer-reviewer subagent flow described in HARNESS.md. OpenSpec's own
  tasks.md is authoritative here per HARNESS.md's precedence rules, so this is not a
  correctness problem, just worth noting for consistency with how other changes in this repo
  (taty-per-tenant-profiles, hermes-task-queue-tenant-scoping) left progress/impl_*.md
  trails.
- Stage 10 (Deploy to Production) and Stage 11.1 (reviewer sign-off, this review) are both still
  open -- expected at this point in the workflow; per this repo's mandatory Stage 11/Deploy rule
  the change cannot be archived until deploy plus production smoke test happen, which tasks.md
  already tracks correctly (10.1-10.4 unchecked).
- docs/API_REFERENCE.md's pre-existing drift (route shapes not matching agents_endpoints.py
  reality) is honestly flagged rather than silently left wrong or silently claimed fully fixed --
  appropriate scoping, not a defect of this change.

## Checkpoints (DEPLOYMENT_STAGE/CHECKPOINTS.md, Stages 0-7 applicable pre-deploy)

- Stage 0 Setup: [x] feature branch matches, tracks remote (see Required Change 2 for this
  session's own uncommitted work)
- Stage 1 Proposal: [x] proposal.md clear, concrete Why/What/Impact/Non-Goals
- Stage 2 Design: [x] design.md has a per-endpoint contract table, explicit decisions, risks
- Stage 3 Spec: [x] 4 delta spec files present with scenarios covering every requirement
- Stage 4 Tasks: [x] tasks.md staged, TDD-ordered, deploy stage present (as "Stage 10")
- Stage 5 Implementation:
  - Code compiles / imports clean: [x]
  - Existing + new tests pass: [x] (independently re-run, 46/46 targeted; 0 regressions on
    full suite, independently verified against an isolated baseline)
  - Docs-sync (canon vivo): [ ] -- ARCHITECTURE.md has a duplicate "16." decision number
    (Required Change 1)
- Stage 6 Review: this review (CHANGES_REQUESTED -- see Required Changes above)
- Stage 7 Deploy: not started (correctly left unchecked in tasks.md)

## Hardest adversarial check performed (per the task's own framing)

Specifically hunted for any path where the removed resolve_caller_tenant's behavior was NOT
faithfully replicated by the migration onto resolve_request_tenant_scope, or where an
authenticated caller could see or affect another tenant's data:
- resolve_request_tenant_scope is a strict superset (4 outcomes vs 3), and its 4th outcome
  (operator/all_tenants) is never read by Centinela or Taty (both only read .tenant_id) -- so
  no new privilege leaks through the migration.
- The one real behavioral difference (unconditional resolve_cliente_cero_tenant_id call) is
  explicitly tested against in both migrated test files, with the correct security property
  under test (caller never receives Cliente Cero's tenant_id for an unresolved caller), not a
  weaker "the lookup was never called" assertion that the migration would have broken.
- Approval-queue's all_tenants operator branch and normal-client branch are unchanged by this
  change (only the unresolved-scope status code moved from 403 to 404); both are covered by
  test_approval_queue_endpoint_tenant_scoping.py, all passing.
- No file among the 6 in scope reads request.state.tenant_id or .get("tenant_id") directly
  anymore -- verified by reading each file's imports and body directly.

No cross-tenant leak path found. The two required changes above are documentation/commit-hygiene
issues, not security defects -- but they are concrete, fixable, and block a clean approval per
this reviewer's hard rule against approving with a stale/inconsistent canon doc and against
treating uncommitted work as done.
