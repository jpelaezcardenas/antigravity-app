# Deployment report — activate-telemetry-loop

Date: 2026-07-20

## Summary

Change deployed and verified live in production. `run_creative_loop(use_telemetry=True)` — fully
built and tested since Change G but never reachable — is now exposed via
`POST /api/v1/sell-machine/creative-loop/run`, closing gap #6.

## Commits deployed

- `afd0bd2` — feat(sell-machine): expose the telemetry-aware creative loop via an endpoint

## Stage 11 steps executed

1. Merged `feature/activate-telemetry-loop` to `main` (fast-forward, confirmed via
   `git merge-base`), pushed. Railway deploy `26464f67` reached `SUCCESS`.
2. **Live smoke test**: called the real `POST /sell-machine/creative-loop/run` with `{"count": 3}`
   → `200`, `5.470s`, non-empty `survivors` list with correct `{headline, body, cta, pain_tag}`
   shape. Railway logs confirm the telemetry branch executed for real:
   `GET operator_tasks?...task_type=eq.post_content`, `GET operator_tasks?...task_type=eq.run_ads_ab`
   (both `list_completed_tasks` calls), and `GET crm_leads?select=stage` (`get_funnel_snapshot`) —
   exactly `get_telemetry_report`'s three underlying queries, confirming `use_telemetry=True` took
   the telemetry-aware path, not the generic one.
3. **Further confirmation of the `llm_engine.py` bug flagged in `copywriter-rag`'s deployment
   report**: the same `_parse_llm_response() takes from 2 to 4 positional arguments but 5 were
   given` error appeared again — this time in **both** `copywriter_service` (hook generation) and
   `agents/content_evaluator.py` (hook tone-check evaluation), confirming the bug affects every
   consumer of `get_ai_response_with_profile`'s JSON-mode path, not just the Copywriter. Both
   correctly fell back to their documented graceful-degradation behavior (deterministic hooks;
   hard-ban-only evaluation) — no crash, `200` returned. Still not fixed here (unrelated file, out
   of this change's scope — reinforces that the follow-up fix is worth prioritizing given its
   reach).
4. No new flag — reuses `SELL_MACHINE_CANONICAL`.

## Accepted risks / limitations (carried from design.md)

- **No in-backend scheduler** — this endpoint makes the loop reachable; actually calling it on a
  3-day cadence is Hermes's responsibility (local, out of this repo's scope), not yet configured.
- **No new Búnker UI** — not requested; mirrors the existing `/tasks/pending` precedent.
- **Doesn't auto-create a campaign package** — stops at `survivors`, consistent with the existing
  three-step HITL flow.

## Verification evidence

- Railway deployment `26464f67`: `SUCCESS`, confirmed responding.
- Live `POST /sell-machine/creative-loop/run`: `200`, correct shape, telemetry branch confirmed
  executing via Railway logs.
- Full regression suite: 48/48 green, zero regression.
