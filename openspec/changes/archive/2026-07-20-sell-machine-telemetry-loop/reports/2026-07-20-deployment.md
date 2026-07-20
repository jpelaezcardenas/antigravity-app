# Deployment report — sell-machine-telemetry-loop

Date: 2026-07-20

## Summary

Change deployed and verified live in production. `GET /api/v1/sell-machine/telemetry/report` is
reachable and correctly aggregates completed operator-task results plus the `crm_leads` funnel
snapshot; the Copywriter's optional `report` parameter is live with zero impact on existing
callers.

## Commit deployed

- `86c99dd` — feat(sell-machine): add telemetry report + optional Copywriter feedback loop
  (Change G)

## Stage 11 steps executed

1. **7.1-7.2** — Committed on `feature/sell-machine-telemetry-loop`, merged to `main`.
   **Note**: `origin/main` had advanced (a concurrent session completed and archived
   `wompi-payment-integration` — the sandbox Wompi work, verified with 2 real sandbox payments —
   directly on `main` while this change was in progress). Confirmed via `git merge-base` that this
   feature branch's history already contained that state (no actual divergence, so a plain
   fast-forward merge was correct — no rebase needed). Re-ran the full targeted test suite after
   the merge to confirm no interaction with the newly-merged Wompi checkout code in
   `crm_service.py` (both changes touch that file — mine additively via `get_funnel_snapshot()`,
   unrelated to Wompi's checkout/webhook functions). 106/106 still green.
2. **7.3** — Railway auto-deploy of `86c99dd` reached `SUCCESS` and the app came up responding
   normally (no unusual cold-start delay this time, unlike the prior two changes). Confirmed this
   reuses the already-`true` `SELL_MACHINE_CANONICAL` flag (Change F's precedent) — the new
   endpoint was live immediately, no dark-deploy gating needed for a flag flip.
3. **7.4** — No frontend changes (Section 5's optional Búnker panel was skipped) — confirmed no
   sw.js bump/rebuild-sync was needed.
4. **7.5 — Live smoke test.**
   - `GET /api/v1/sell-machine/telemetry/report` → `200`, reflecting the REAL current state:
     `funnel_snapshot: {NUEVOS:1, PROSPECTOS:2, POR_APROBAR:1, LISTOS_CONTADORA:1}` (genuine counts
     from this session's earlier smoke tests across Changes B/D/E), `hook_performance` initially
     zeroed (no completed operator tasks existed yet at that point).
   - Inserted one representative `operator_tasks` row directly via Supabase SQL:
     `task_type="post_content"`, `status="completed"`, `result={"impressions":1200,"clicks":45}` —
     **explicitly labeled as Stage 11 smoke-test data in its own payload note field, not real
     Manus/ad performance** (no Hermes-side consumer exists yet).
   - Re-called `GET /telemetry/report` → correctly reflected it:
     `hook_performance.post_content = {"count":1,"impressions":1200,"clicks":45}`.
   - `POST /api/v1/sell-machine/hooks/generate` (no `report` param, the pre-existing call shape) →
     `200`, valid hooks returned — confirms the additive signature change caused zero regression to
     the existing endpoint.
   - **Decision on the demo row**: leaving `dd173c7f-517f-42e2-89e6-ec157f38530a` in place, matching
     the precedent set in Changes B/E/F — a harmless, clearly-labeled demonstration row.
5. **7.6 — This report.**

## Accepted risks / observations (carried from design.md)

- **Report may be thin/empty in production until real Manus data flows** — confirmed as designed;
  the endpoint correctly returned zeroed `hook_performance` before the smoke-test row existed, no
  error.
- **`result` payload shape varies by `task_type`** — aggregation reads only well-known optional
  numeric fields via `.get()`, confirmed tolerant.
- **No scheduler built** — deliberately absent from this repo; the 3-day cadence remains Hermes'
  responsibility, per the Sell Machine plan.
- **Optional Búnker panel skipped** (Section 5) — no real telemetry exists yet to make it
  meaningful today; the endpoint is directly callable by Hermes or a human in the meantime.

## Verification evidence

- Railway deployment (commit `86c99dd`): `SUCCESS`, confirmed responding without the extended
  cold-start seen on the prior two changes.
- Live `GET /api/v1/sell-machine/telemetry/report`: `200`, correctly aggregates real funnel data
  and the inserted smoke-test operator-task row.
- Live `POST /api/v1/sell-machine/hooks/generate`: `200`, unaffected by the additive signature
  change.
