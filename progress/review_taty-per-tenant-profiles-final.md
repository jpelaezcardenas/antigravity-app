# Review — taty-per-tenant-profiles (FINAL, whole-change gate)

**Verdict:** APPROVED (recommend archive now, with explicit follow-up conditions — see below)

## Summary of independent verification

- pytest apps/backend/tests/test_taty_tenant_profiles.py apps/backend/tests/test_taty_ask_tenant_scoping.py apps/backend/tests/test_taty_endpoints_tenant_scoping.py apps/backend/tests/test_telegram_taty_tenant_translation.py -v -> 23/23 passed, matches every prior task report.
- grep -rn "AGENT_PROFILES|taty_intent_router" apps/backend/ -> zero functional references anywhere in the whole apps/backend tree. Remaining hits are documentation comments (taty_lead_router.py, whatsapp_endpoints.py, and this changes own test docstring) explicitly distinguishing the new lead-scoped router from the deleted intent router; no dead import, no live call.
- curl -X POST .../api/v1/agents/taty/ask -> 404 (deleted route stays gone in prod, right now).
- curl .../api/v1/agents/ask?question=test1234 -> 401 (auth flip is live and enforced in prod, right now).
- Read full current-state files: apps/backend/services/taty_service.py, apps/backend/presentation/taty_endpoints.py, apps/backend/presentation/telegram_endpoints.py, apps/backend/presentation/agents_endpoints.py (grepped for taty/company_id remnants; only unrelated social_generate_content fields remain). End-to-end result is coherent: _get_tenant_profile -> ask(tenant_id=...) -> 3 call sites (taty_endpoints.py, telegram_endpoints.py) all pass tenant_id, no caller still passes company_id for resolution. DEFAULT_PROFILE[regimen] = None, _build_prompt() omits the regimen clause when unset, matching .antigravity/GROUND_TRUTH.md (nunca inventar claims regulatorios). Taty is never described as a regulated accounting firm anywhere in these files.
- bash init.sh -> FAILS on 2 features in_progress (max 1) in this local worktrees feature_list.json. Investigated: this is stale local worktree state, not a defect of this change. origin/mains current feature_list.json (fetched and diffed) shows taty-per-tenant-profiles as the sole in_progress entry; approval-queue-tenant-scoping (the other in_progress feature in this stale worktree copy) has since been archived on origin/main, and a new centinela-tenant-scoped-alerts entry explicitly notes it is pending because taty-per-tenant-profiles currently holds the in_progress slot. This is a real, live signal that archiving this change is what unblocks the next queued change; leaving it un-archived has a genuine downstream cost, not just a cosmetic one.
- openspec/specs/taty-fiscal-assistant/spec.md (main) exists on disk and its body is byte-identical to the delta spec (only the header line differs, which openspec-sync-specs is expected to normalize). However this file is untracked (git status shows the path as untracked); it is not committed anywhere, not even to origin/main. This confirms tasks.md 12.1 (openspec-sync-specs) is honestly unchecked; it genuinely has not happened yet, it is not a false negative.

## Design/spec/compliance review

- proposal.md/design.md/spec.md are internally consistent with the shipped code. D3s authenticated-but-unresolved handling (in-band error_code=tenant_not_resolved, never Cliente Cero) is exactly what taty_endpoints.py lines 176-190 implement, and is exercised by test_authenticated_unresolved_caller_gets_error_and_never_calls_cliente_cero (passing).
- D4 (delete taty_intent_router.py, do not revive) confirmed deleted, zero functional references.
- D6 (Telegram company_id to tenant_id translation) confirmed in telegram_endpoints.py lines 59-74 and 167-173, matches the unmapped-chat scenario (existing no-configurado reply sent, ask never invoked).
- Regimen-omission compliance (.antigravity/GROUND_TRUTH.md, nunca inventar claims regulatorios) verified directly in taty_service.py lines 306-317 and covered by test_regimen_none_omits_regimen_clause.
- ARCHITECTURE.md Decision #13 (per-tenant-client-access) is not contradicted by this change; it extends the same resolution pattern (resolved_tenant_id maps to own tenant; staging identity maps to Cliente Cero; unresolved authenticated caller gets an explicit error, never Cliente Cero) to a second endpoint family. Minor, non-blocking doc gap: Decision #13s prose currently only names GET /api/v1/financials; it does not yet mention /api/v1/agents/ask now following the identical pattern. This is a legitimate docs-sync candidate per HARNESS.md Section 7 and CHECKPOINTS.md Stage 5, but it is describing an application of an already-settled decision, not a new architectural decision or a new container/dependency, so it does not rise to a blocking gap. Recommend a one-line addendum to Decision #13 in a follow-up, not a reason to withhold approval.

## Checkpoints (DEPLOYMENT_STAGE/CHECKPOINTS.md)

- Stage 0 (Setup): pass. branch created, merged, git status clean except the not-yet-committed synced spec file (expected pre-Stage-12).
- Stage 1-4 (Proposal/Design/Spec/Tasks): pass. all present, Stage 11 listed as mandatory final task in tasks.md.
- Stage 5 (Implementacion): pass on code (23/23 targeted, 648 passed and 25 pre-existing-unrelated-failures on full suite per the Stage-5 CHECKPOINTS.md baseline exception added 2026-07-23); docs updated (taty_endpoints.py docstrings, router.py stale comment fixed in task 10); partial on docs-sync, see minor ARCHITECTURE.md gap above, non-blocking.
- Stage 6 (Review): pass. every task 1-10 has its own progress review file with an APPROVED verdict; task 3s review includes an explicit adversarial tenant-bypass trace.
- Stage 7 (Deploy): pass. pushed to main, Railway deployment SUCCESS, health endpoint 200, deployment report exists with commit hash and before/after checks documented.
- Stage 8 (Cierre): partial. all checkpoints green except three explicitly-flagged founder-only production spot-checks (11.6, 11.6b, 11.8). See judgment call below.

## The archive-timing judgment call

Recommendation: archive now, not hold.

Reasoning:
1. 11.6, 11.6b and 11.8 are not testability gaps in the code or in this agents diligence. They require a real Supabase-issued session JWT for a provisioned B2B client (founders Bitwarden credentials) and access to a live Telegram bot account. I, the reviewer, independently confirm I have the same limitation; I cannot execute these three checks either. This is a genuine external dependency, not a shortcut.
2. docs/openspec-tasks-mandatory-steps.md requires the agent to execute tests itself before marking a task complete, and explicitly forbids fabricating results. The implementer complied with this rule correctly by leaving 11.6, 11.6b and 11.8 unchecked rather than fabricating a pass; this is the rule working as intended, not a violation of it. The rules purpose, integrity of checkmarks, is preserved regardless of archive state.
3. The security-critical surface of Stage 11 is done and independently reverified live in production right now (401 unauthenticated, 404 deleted route, adversarial spoofed-company_id bypass trace at the unit level in task 3, tenant_not_resolved never-Cliente-Cero path unit-tested). The three deferred items are UAT-style spot-checks on top of an already-verified security boundary, not the boundary itself.
4. Leaving the change un-archived does not make the three founder-only checks more likely to happen. Nothing about the openspec/changes directory visibility pages the founder; it is not a task queue with reminders. What it does do is keep occupying the single in_progress slot in feature_list.jsons one-change-at-a-time invariant, and this has a real, currently-observed cost: centinela-tenant-scoped-alerts (already implemented, merged via PR 6, tested) is explicitly blocked from starting because this change holds that slot. Holding the change un-archived actively delays unrelated, already-completed work for no compensating benefit.
5. Precedent in this repo (ARCHITECTURE.md Decision #12, task_d1ec7639) is to track a founder-dependent follow-up as its own durable, named item rather than stall the OpenSpec lifecycle indefinitely.

Conditions attached to the archive (must be satisfied by whoever performs Stage 12, not by this review):
1. Do not check off 11.6, 11.6b and 11.8 to force a clean archive; the archived tasks.md must preserve them as unchecked, exactly as they are now. Archiving is not claiming 100 percent done.
2. Commit the currently-untracked openspec/specs/taty-fiscal-assistant/spec.md sync (task 12.1) as part of the archive commit; right now it exists only in this local worktrees working tree and is not on origin/main.
3. Create an explicit, durable, separately-trackable founder-follow-up record for 11.6, 11.6b and 11.8 before or in the same commit as the archive; e.g. a feature_list.json entry analogous to task_d1ec7639, or an equivalently visible note in progress/history.md under a clearly flagged FOUNDER ACTION REQUIRED heading. A bare unchecked checkbox buried in an archived tasks.md is not sufficiently visible on its own.
4. Optionally, non-blocking but recommended: add the one-line ARCHITECTURE.md Decision #13 addendum noting /api/v1/agents/ask now follows the same per-tenant resolution pattern as /api/v1/financials.

## Required changes (if any)

None blocking. The three conditions above gate the archive mechanics, not the code or test quality; no code defect was found in taty_service.py, taty_endpoints.py, telegram_endpoints.py, or agents_endpoints.py.
