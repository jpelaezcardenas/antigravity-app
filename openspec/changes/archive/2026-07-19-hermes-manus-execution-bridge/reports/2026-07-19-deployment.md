# Deployment report — hermes-manus-execution-bridge

Date: 2026-07-19

## Summary

Change deployed and verified live in production. The generic operator-task bridge is now reachable
at `https://antigravity-app-production-175a.up.railway.app/api/v1/sell-machine/tasks/*` and
`/campaigns/{id}/dispatch`, giving Hermes a pull/push seam to execute approved Sell Machine output
(and other operational asks) via Manus, without any inbound connection into Hermes.

## Commit deployed

- `d7b830a` — feat(hermes-manus): implement operator task bridge (Change F)

## Stage 11 steps executed

1. **6.1-6.2** — Committed on `feature/hermes-manus-execution-bridge`, fast-forward merged to
   `main`, pushed. No conflicts (confirmed via `git fetch` + `git log origin/main` before merging).
2. **6.3 — Railway deploy.** Auto-triggered on push (deployment `ef9dc1d3-b611-4b3d-a048-a90b0e38318e`)
   reached `SUCCESS`. No `contexia-app/` files touched (confirmed via `git status --short` before
   committing) — no sw.js bump, no frontend rebuild/sync, no Vercel deploy needed for this change.
3. **6.4 — Immediate live verification (no dark-deploy step).** Per design.md Decision 3, this
   change reuses the already-`true` `SELL_MACHINE_CANONICAL` flag, so the new routes went live
   immediately on deploy — there was no flag flip to gate. `GET
   /api/v1/sell-machine/tasks/pending` returned `200 []` once the app finished booting (see note
   below on cold-start time), confirming the route is registered and reachable, not a 404.
   - **Cold-start note**: this deploy's boot took noticeably longer than prior observations — the
     app was still returning `502 Application failed to respond` for roughly 10-12 minutes after
     the deployment reached `SUCCESS` (vs. ~80s typical, ~5-6 min for Change E's flag-flip
     redeploy). Runtime logs showed no crash signature throughout — only the same benign pydantic
     `protected_namespaces` warning seen in every prior deploy, followed by silence (no further log
     lines) until the app started responding. No redeploy was triggered this time; it recovered on
     its own. Flagging this pattern in case boot times keep growing as more routes/imports
     accumulate in this backend.
4. **6.5 — Full live smoke test**, exercised via direct `curl` against the production URL:
   1. `POST /api/v1/sell-machine/tasks` with `{"task_type": "research", ...}` → created task
      `c5a69f6b-c6df-4584-b13b-483c98339604`, `status="pending"`.
   2. `GET /api/v1/sell-machine/tasks/pending` → confirmed the task appeared in the list.
   3. `POST /api/v1/sell-machine/tasks/c5a69f6b.../status` `{"status": "dispatched"}` → `200`,
      `status="dispatched"`.
   4. **Re-dispatching the same task** (`pending`→`dispatched` guard) → correctly rejected with
      **409**, `"task ... is 'dispatched', not 'pending' — cannot dispatch"`.
   5. `POST /api/v1/sell-machine/tasks/c5a69f6b.../result` `{"status": "completed", "result": {...}}`
      → `200`, `status="completed"`, `result` stored.
   6. `POST /api/v1/sell-machine/campaigns/7b4439c3-ba70-4490-bd0b-3fcd412aac20/dispatch` (the real
      approved `campaign_package` from Change E's own Stage 11 smoke test) → created task
      `661d395f-d076-41b9-b1cc-7ceeee7e76bc`, `task_type="post_content"`, `status="pending"`,
      `payload.source_decision_id="7b4439c3-..."`.
   7. **Dispatching an unknown decision id** → correctly rejected with **404**,
      `"decision does-not-exist not found"`.
   8. **Creating `post_content` directly via `POST /tasks`** (bypassing the dispatch endpoint) →
      correctly rejected with **400**,
      `"task_type 'post_content' is side-effecting and cannot be created directly..."` — confirms
      the HITL split (design.md Decision 5) is enforced server-side, not just by convention.
   - **Verified directly in Supabase** (`execute_sql` on project `kpynymwghfwshvcvevxq`): both
     `operator_tasks` rows match expectations exactly —
     `c5a69f6b-...` → `task_type=research, status=completed, result={"report_summary":"..."}`;
     `661d395f-...` → `task_type=post_content, status=pending, payload.source_decision_id=7b4439c3-...`.
   - **Decision on the demo rows**: leaving both in place, matching the precedent set in Changes B
     and E — harmless draft/demo records, no real outbound side effect (the `post_content` task
     stays `pending` since no Hermes/Manus consumer exists yet — that integration is explicitly out
     of scope for this change).
5. **6.6 — This report.**

## Accepted risks (carried from design.md)

- **New endpoints reuse the already-`true` `SELL_MACHINE_CANONICAL` flag → live on merge, not
  dark.** Confirmed acceptable: the routes are pull/push-only from Hermes's side and inert until a
  real Hermes/Manus consumer exists (out of scope here); same no-request-auth posture already
  accepted for every other Sell Machine/CRM endpoint (plan's R1, previously accepted in Changes
  A/B/E).
- **No timeout/retry for a task stuck in `dispatched`.** Confirmed as designed — explicitly a
  Non-Goal; a future Hermes-side or Change G concern.
- **No FK from `operator_tasks` to `approval_queue`.** Confirmed working as intended in the live
  smoke test: `payload.source_decision_id` provides traceability without a DB-level FK, keeping the
  operator task self-contained.

## Verification evidence

- Railway deployment `ef9dc1d3-b611-4b3d-a048-a90b0e38318e`: `SUCCESS`.
- Live `GET /api/v1/sell-machine/tasks/pending`: `200`, reflects real-time queue state.
- Supabase `operator_tasks` rows `c5a69f6b-...` (`completed`) and `661d395f-...` (`pending`,
  traceable to the approved campaign package): confirmed via direct SQL.
- All 4 error-path guards (409 re-dispatch, 404 unknown decision, 400 direct side-effecting
  creation) confirmed live, not just in unit tests.
