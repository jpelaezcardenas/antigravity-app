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

- [ ] 3.1 Write failing unit tests for `copywriter_service.py`: `generate_hooks(count)` returns the
      requested count with the correct shape; falls back to a deterministic hook set when all LLM
      providers fail; `rewrite_hook(hook, rejection_reason)` returns a single rewritten hook.
- [ ] 3.2 Author `apps/backend/services/copywriter_service.py`: `generate_hooks(count=5)` and
      `rewrite_hook(hook, reason)`, same LLM-call idiom as Change 2's Critic (shared
      `social-ops-v1` profile per design.md Decision 3), deterministic fallback hook set.
- [ ] 3.3 Run tests green.

## 4. Sell Machine orchestration service + Approval Queue integration — TDD

- [ ] 4.1 Write failing unit tests for `sell_machine_service.py`: `run_creative_loop(count, target)`
      orchestrates generate → evaluate (with the one-rewrite-pass rule) → returns survivors;
      `create_campaign_package(hooks, brief, segment, budget)` calls
      `ApprovalQueueService.enqueue_draft(draft_id=<uuid4>, draft_type="campaign_package",
      journal_entry=<package dict>, memo=...)` directly (per design.md Decision 1 — not the
      generic REST endpoint) and returns the created draft; `list_campaigns(status)` reads
      `campaign_package` drafts back out.
- [ ] 4.2 Author `apps/backend/services/sell_machine_service.py` implementing the above, importing
      `ApprovalQueueService` directly (matching the `taty_escalation`/`social_reply` precedent).
- [ ] 4.3 Run tests green; confirm (via test, not just reading code) that a `campaign_package`
      draft's `enqueue_draft` call does NOT trigger the accounting Critic's balance validation
      (since `campaign_package` is not in `JOURNAL_ENTRY_DRAFT_TYPES`) — this is the load-bearing
      assumption design.md Decision 2 rests on.

## 5. Backend endpoints + flag — TDD

- [ ] 5.1 Write failing endpoint tests (isolated FastAPI app + `httpx.AsyncClient` +
      `ASGITransport` + `pytest.mark.asyncio`, per the established pattern — the sync `TestClient`
      remains broken in this environment) for all 4 routes: `POST /sell-machine/hooks/generate`,
      `POST /sell-machine/hooks/evaluate`, `POST /sell-machine/campaigns`,
      `GET /sell-machine/campaigns`.
- [ ] 5.2 Add `SELL_MACHINE_CANONICAL: bool = False` to `apps/backend/config.py`. Create
      `apps/backend/presentation/sell_machine_endpoints.py` (`APIRouter(tags=["sell-machine"])`)
      with the 4 routes, delegating to `sell_machine_service`/`copywriter_service`/
      `content_evaluator`. Register in `apps/backend/presentation/router.py` behind
      `if settings.SELL_MACHINE_CANONICAL: api_router.include_router(sell_machine_router,
      prefix="/sell-machine", ...)`.
- [ ] 5.3 Run tests green; confirm no regression in the existing `test_crm_*` suites (shared
      `router.py`/`config.py` files are touched).

## 6. Frontend client + Búnker section

- [ ] 6.1 Create `contexia-app/lib/sell-machine-api.ts`: private `api<T>(path, init?)` wrapper
      cloned from `crm-api.ts`'s idiom; exports `generateHooks(count)`, `evaluateHooks(hooks)`,
      `createCampaignPackage(payload)`, `listCampaigns(status?)`, and — reusing the existing
      generic Approval Queue endpoints directly (no Sell-Machine-specific approve/reject route
      needed per design.md) — `approveCampaignPackage(decisionId, approvedBy)` and
      `rejectCampaignPackage(decisionId, reason)` calling `/api/v1/approval-queue/approve` and
      `/reject`. Plus the TypeScript types (`Hook`, `CampaignPackage`, `EvaluationResult`).
- [ ] 6.2 Add `"sell-machine"` to `BunkerSidebar.tsx`'s `BunkerSection` union + `NAV_ITEMS` (per
      design.md Decision 6 — a new top-level item, not a CRM/Ventas sub-tab).
- [ ] 6.3 Create `contexia-app/components/bunker/sell-machine/SellMachineSection.tsx` (+ any
      sub-components needed, e.g. a hooks-generation panel and a pending-campaigns list):
      `useEffect`/`useState` with `loading`/`error`/`empty` states, generate → evaluate → create
      package flow, and an approve/reject action per pending package. `@theme` tokens only, no new
      libraries, no drag-and-drop.
- [ ] 6.4 Wire the new section into `contexia-app/app/app/bunker/page.tsx`'s section-switch.

## 7. Docs

- [ ] 7.1 Add a fifth data-bound screen entry ("Búnker → Sell Machine") to `contexia-app/CLAUDE.md`'s
      *Pantallas data-bound* section (reads + writes: generate/evaluate hooks, create + approve/
      reject campaign packages), and update the top-level "Reglas duras" bullet accordingly.
- [ ] 7.2 Confirm the `sell-machine-creative-swarm` delta spec is in place at
      `specs/sell-machine-creative-swarm/spec.md`, ready for archive-time sync.

## 8. Verify + DB state (MANDATORY before Stage 11)

- [ ] 8.1 Run the full targeted backend + frontend test suites; confirm green (`tsc --noEmit`,
      `npm run build`); confirm no regression in existing CRM/Social-Ops suites.
- [ ] 8.2 Verify live via Supabase MCP: after exercising the loop once locally/in a test call,
      confirm a `campaign_package` row lands in `approval_queue` with the expected `payload` shape,
      and that approving it via the existing `/approve` endpoint flips its status correctly with no
      unintended side effects (no `executor_outbox` row, since that's `tax_correction`-only).
- [ ] 8.3 Write `openspec/changes/sell-machine-creative-swarm/reports/YYYY-MM-DD-step8-verification.md`.

## 9. E2E (browser)

- [ ] 9.1 Open the Búnker, navigate to the new "Sell Machine" section, generate hooks, run
      evaluation, create a campaign package, confirm it appears as pending, approve it, and confirm
      it disappears from the pending list / shows as approved.

## 10. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [ ] 10.1 Commit the backend and frontend changes in scoped commits, referencing this change id.
- [ ] 10.2 Merge to `main` (check for conflicts against any concurrent work) and push.
- [ ] 10.3 Confirm Railway backend deploy completes green with `SELL_MACHINE_CANONICAL=false` (dark
      deploy — this DOES need the dark-deploy step, unlike Change B, since this is a new flag).
- [ ] 10.4 **Bump `contexia-app/public/sw.js` `CACHE_VERSION`** (commit and push immediately,
      learned from prior collisions), rebuild, and sync `contexia-app/out/` → `app/` additively
      using the Python-based all-characters chunk verifier established after Change A's incident.
      Confirm Vercel deploy green.
- [ ] 10.5 Verify live at `https://contexia.online/app/bunker`: sidebar shows the new "Sell
      Machine" item; existing sections (CRM/Ventas B2B+B2C, Social Content Ops, Onboarding)
      unaffected.
- [ ] 10.6 Flip `SELL_MACHINE_CANONICAL=true` on Railway; in production, exercise the full loop
      once: generate hooks → evaluate → create a campaign package → approve it via the UI. Confirm
      via direct SQL that the `approval_queue` row's status is `approved`. Note in the deployment
      report that this creates a real (if harmless) `campaign_package` row in production — decide
      whether to leave it (as a demonstration) or clean it up, matching the precedent set in
      Change B's report.
- [ ] 10.7 Create deployment report at
      `openspec/changes/sell-machine-creative-swarm/reports/YYYY-MM-DD-deployment.md`, including
      the accepted-risk notes from design.md (non-deterministic Critic backed by a hard
      deterministic gate; `tenant_id` not persisted on Approval Queue rows, pre-existing).

## 11. Archive

- [ ] 11.1 Sync the `sell-machine-creative-swarm` capability into `openspec/specs/` (using `git mv`
      for the archive move, per the process fix established after Change A's tree-drift incident)
      and archive this change once Stage 11 is confirmed complete and verified live.
