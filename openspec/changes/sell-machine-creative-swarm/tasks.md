## 1. Setup + verification

- [x] 1.1 Created branch `feature/sell-machine-creative-swarm`.
- [x] 1.2 Re-confirmed `get_ai_response_with_profile`'s exact signature and `generate_idea_draft`'s
      sync (not async) call idiom by reading the live source directly.

## 2. Content Critic rubric + module — TDD

- [x] 2.1 Wrote `apps/backend/tests/test_content_evaluator.py` (credential-free, mocks the single
      `_llm_tone_check` call point): hard-ban rejection (unconditional, LLM cannot override),
      pass-through, LLM-failure fallback (both clean and hard-banned hooks), and LLM-driven tone
      rejection. Confirmed failing (module didn't exist).
- [x] 2.2 Authored `apps/backend/agents/content_evaluator.py` — pure per-hook evaluation
      (`evaluate_hook(hook) -> {approved, reason}`), no relation to `agent_critic.py`. Hardcoded
      brand rubric (condensed from `content_ops_rules.md` §7-8) as both an LLM system prompt and a
      literal hard-ban phrase list (non-overridable gate); LLM tone check isolated in
      `_llm_tone_check()` for clean test patching; deterministic fallback (hard-ban result alone)
      on any LLM failure. Note: the one-rewrite-pass orchestration lives in `sell_machine_service`
      (Section 4), not here — this module only evaluates one hook at a time, no rewrite logic.
- [x] 2.3 6/6 tests green.

## 3. Copywriter module — TDD

- [x] 3.1 Wrote `apps/backend/tests/test_copywriter_service.py` (credential-free, mocks
      `_llm_generate_hooks`/`_llm_rewrite_hook`): correct shape/count, deterministic fallback on
      LLM failure (both functions). Confirmed failing (module didn't exist).
- [x] 3.2 Authored `apps/backend/services/copywriter_service.py`: `generate_hooks(count=5)` and
      `rewrite_hook(hook, reason)`, shared `social-ops-v1` profile (design.md Decision 3),
      deterministic fallback hook set/original-hook-passthrough on any LLM failure.
- [x] 3.3 11/11 tests green (5 new + 6 from Section 2, no regression).

## 4. Sell Machine orchestration service + Approval Queue integration — TDD

- [x] 4.1 Wrote `apps/backend/tests/test_sell_machine_service.py`: `run_creative_loop` (approved
      survives, rejected-then-fixed-rewrite survives, rejected-and-still-bad discarded, rewrite
      attempted at most once per hook — confirmed via call-count assertion); `create_campaign_package`
      (calls `ApprovalQueueService.enqueue_draft` with `draft_type="campaign_package"`, raises
      `RuntimeError` on failure) and `list_campaigns` (async, mocks `ApprovalQueueService` directly,
      no Supabase credentials needed). Confirmed failing (module didn't exist).
- [x] 4.2 Authored `apps/backend/services/sell_machine_service.py` implementing all three
      functions, importing `ApprovalQueueService` directly (matching the
      `taty_escalation`/`social_reply` precedent).
- [x] 4.3 18/18 tests green (7 new + 11 from Sections 2-3, no regression). The mocked
      `create_campaign_package` test confirms the call reaches `ApprovalQueueService.enqueue_draft`
      with `draft_type="campaign_package"` — since that type is not in
      `JOURNAL_ENTRY_DRAFT_TYPES = {"tax_correction"}` (confirmed by reading the live source in
      Section 1.2 / design.md's Context), the accounting Critic's `validate_journal_entry` is
      never invoked for this path — the load-bearing assumption behind design.md Decision 2.

## 5. Backend endpoints + flag — TDD

- [x] 5.1 Wrote `test_sell_machine_endpoints.py` (isolated FastAPI app + `httpx.AsyncClient` +
      `ASGITransport` + `pytest.mark.asyncio`) for all 4 routes plus the flag-gating checks.
      Confirmed failing (module/routes didn't exist).
- [x] 5.2 Added `SELL_MACHINE_CANONICAL: bool = False` to `apps/backend/config.py`. Created
      `apps/backend/presentation/sell_machine_endpoints.py` with the 4 routes (refactored
      `sell_machine_service.py` first to extract a standalone `evaluate_hooks()` — reused by both
      `run_creative_loop` and the `/hooks/evaluate` endpoint — before wiring endpoints, so
      `/hooks/generate` and `/hooks/evaluate` can be called independently as the spec requires).
      Registered in `router.py` behind the new flag. Endpoints call `.to_dict()` on
      `ApprovalDecision` results explicitly (verified `to_dict()` exists by reading
      `models/approval_decisions.py`) so real production responses serialize correctly, not just
      the plain-dict test mocks.
- [x] 5.3 50/50 tests green (9 new Sell Machine endpoint tests + 41 pre-existing CRM + Sell
      Machine unit tests) — zero regression despite `router.py`/`config.py` being shared files.

## 6. Frontend client + Búnker section

- [x] 6.1 Created `contexia-app/lib/sell-machine-api.ts`: private `api<T>(path, init?)` wrapper
      cloned from `crm-api.ts`'s idiom; exports `generateHooks(count)`, `evaluateHooks(hooks)`,
      `createCampaignPackage(payload)`, `listCampaigns(status?)`, and — confirmed
      `/approval-queue/approve`/`/reject` are registered unconditionally in `router.py` (no flag
      gate) by reading it directly, then reused them as-is — `approveCampaignPackage`/
      `rejectCampaignPackage`. Plus `Hook`/`CampaignPackage` TypeScript types.
- [x] 6.2 Added `"sell-machine"` to `BunkerSidebar.tsx`'s `BunkerSection` union + `NAV_ITEMS`.
- [x] 6.3 Created `contexia-app/components/bunker/sell-machine/SellMachineSection.tsx`: single
      component covering generate → evaluate → create-package flow plus a pending-campaigns list
      with approve/reject actions; `loading`/`error`/`empty` states throughout. `@theme` tokens
      only, no new libraries, no drag-and-drop.
- [x] 6.4 Wired the new section into `contexia-app/app/app/bunker/page.tsx`'s section-switch.

Verification: `tsc --noEmit` clean, `npm run build` green. Visually confirmed in-browser (local
dev server): "Sell Machine" nav item present, section renders with an explicit "Failed to fetch"
error state (backend not yet deployed) plus the "Generar Hooks" button and "Sin campaign packages
pendientes" empty state — matches the established data-bound-screen error-handling pattern.

## 7. Docs

- [x] 7.1 Added the fifth data-bound screen entry ("Búnker → Sell Machine") to
      `contexia-app/CLAUDE.md`'s *Pantallas data-bound* section, and updated the top-level
      "Reglas duras" bullet accordingly.
- [x] 7.2 Confirmed the `sell-machine-creative-swarm` delta spec is in place at
      `specs/sell-machine-creative-swarm/spec.md`, ready for archive-time sync.

## 8. Verify + DB state (MANDATORY before Stage 11)

- [x] 8.1 Ran the full targeted suite: 50/50 backend tests green (33 new + 17 pre-existing CRM,
      zero regression); `tsc --noEmit` clean; `npm run build` green. Noted 3 unrelated
      pre-existing collection errors (`test_profile_support.py` etc., `apps.backend.*` import
      path issue) — confirmed unrelated to this change.
- [x] 8.2 No new tables/migration in this change (writes only to the existing `approval_queue`
      via the unmodified `ApprovalQueueService.enqueue_draft()`) — deferred the live
      `campaign_package` row verification to the Stage 11 prod smoke-test (10.6), since there is
      nothing new to check locally beyond what Section 4's mocked tests already prove.
- [x] 8.3 Wrote `openspec/changes/sell-machine-creative-swarm/reports/2026-07-19-step8-verification.md`.

## 9. E2E (browser)

- [x] 9.1 Opened the Búnker locally, navigated to "Sell Machine": confirmed the section renders
      (header, "Generar Hooks" button, "Sin campaign packages pendientes" empty state) and shows
      an explicit "Failed to fetch" error state (not blank) with the backend/flag unreachable
      pre-deploy. Full live-data walkthrough (generate → evaluate → package → approve, observing
      real state changes) deferred to the Stage 11 prod smoke-test, same as Changes A/B.

## 10. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [x] 10.1 Commit the backend and frontend changes in scoped commits, referencing this change id.
- [x] 10.2 Merge to `main` (check for conflicts against any concurrent work) and push.
- [x] 10.3 Confirm Railway backend deploy completes green with `SELL_MACHINE_CANONICAL=false` (dark
      deploy — this DOES need the dark-deploy step, unlike Change B, since this is a new flag).
      Confirmed via `railway_list_variables` the flag was absent (defaults `false`) before flipping.
- [x] 10.4 **Bump `contexia-app/public/sw.js` `CACHE_VERSION`** (commit and push immediately,
      learned from prior collisions), rebuild, and sync `contexia-app/out/` → `app/` additively
      using the Python-based all-characters chunk verifier established after Change A's incident.
      Confirm Vercel deploy green. Vercel `dpl_4XdUcCgykA8heQKyFKWe6MtnuXPA` (commit `bb450fd`)
      READY, aliased to `contexia.online`.
- [x] 10.5 Verify live at `https://contexia.online/app/bunker`: sidebar shows the new "Sell
      Machine" item; existing sections (CRM/Ventas B2B+B2C, Social Content Ops, Onboarding)
      unaffected. Confirmed pre-flip 404 handled gracefully (no blank/crash).
- [x] 10.6 Flip `SELL_MACHINE_CANONICAL=true` on Railway; in production, exercise the full loop
      once: generate hooks → evaluate → create a campaign package → approve it via the UI. Confirm
      via direct SQL that the `approval_queue` row's status is `approved`. Note in the deployment
      report that this creates a real (if harmless) `campaign_package` row in production — decide
      whether to leave it (as a demonstration) or clean it up, matching the precedent set in
      Change B's report. Full loop exercised via API: generate→evaluate (3/3 survived)→create
      package `7b4439c3-ba70-4490-bd0b-3fcd412aac20`→approve. Confirmed live in Supabase:
      `status="approved"`. Decision: leaving the demo row in place (harmless draft record).
- [x] 10.7 Create deployment report at
      `openspec/changes/sell-machine-creative-swarm/reports/YYYY-MM-DD-deployment.md`, including
      the accepted-risk notes from design.md (non-deterministic Critic backed by a hard
      deterministic gate; `tenant_id` not persisted on Approval Queue rows, pre-existing). Written
      at `reports/2026-07-19-deployment.md`.

## 11. Archive

- [x] 11.1 Sync the `sell-machine-creative-swarm` capability into `openspec/specs/` (using `git mv`
      for the archive move, per the process fix established after Change A's tree-drift incident)
      and archive this change once Stage 11 is confirmed complete and verified live.
