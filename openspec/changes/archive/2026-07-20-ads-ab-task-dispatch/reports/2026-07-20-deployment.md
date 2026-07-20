# Deployment report — ads-ab-task-dispatch

Date: 2026-07-20

## Summary

Change deployed and verified live in production. `dispatch_campaign_package` now infers
`task_type` from an approved campaign package's own `budget_cents` field — `run_ads_ab` for a
budgeted package, `post_content` for an organic one — closing gap #7, the last of the six gaps
tackled this session.

## Commits deployed

- `c9841a6` — feat(sell-machine): infer run_ads_ab task_type from campaign package budget

## Stage 11 steps executed

1. Merged `feature/ads-ab-task-dispatch` to `main` (fast-forward, confirmed via
   `git merge-base`), pushed. Railway deploy `a8d0a193` reached `SUCCESS`.
2. **Live smoke test**: created two real `approval_queue` rows directly via Supabase SQL
   (`draft_type='campaign_package'`, `status='approved'` — one with `budget_cents: 500000`, one
   with `budget_cents: null`). Called the real
   `POST /sell-machine/campaigns/{decision_id}/dispatch` for each:
   - Budgeted package → `200`, `task_type: "run_ads_ab"`.
   - Organic package → `200`, `task_type: "post_content"`.
   Confirmed both directly via Supabase SQL against the resulting `operator_tasks` rows (not just
   the HTTP response). All test data (both `operator_tasks` rows and both `approval_queue` rows)
   cleaned up afterward.
3. No new flag — reuses `SELL_MACHINE_CANONICAL`.

## Accepted risks / limitations (carried from design.md)

- **No new explicit field** — task_type is inferred from `budget_cents`, not a separate founder
  choice; a token/trivial budget (e.g. `budget_cents=1`) would also dispatch as `run_ads_ab`,
  accepted since the founder controls this field when creating the package.
- **No Hermes/Manus-side execution change** — out of this repo's scope.

## Verification evidence

- Railway deployment `a8d0a193`: `SUCCESS`, confirmed responding.
- Live dispatch of two real approved campaign packages: correct `task_type` in both the HTTP
  response and the underlying `operator_tasks` row, confirmed via direct SQL.
- Full regression suite: 31/31 green, zero regression.

---

## Session summary — all six plan-vs-build gaps closed

This closes the last of six gaps tackled sequentially in this session, each as its own complete
OpenSpec change (propose → design → spec → tasks → apply/TDD → Stage 11 live verify → archive):

| Gap | Change | What closed it |
|---|---|---|
| #8 (persona fields, remainder) | `taty-persona-fields` | `topes`/`obligado_declarar` detection + persistence |
| #3 + #4 (ReAct, KB) | `taty-kb-and-react-router` | Bounded Reason→Act→Reason loop on Taty's unknown-intent fallback, KB-grounded |
| #5 (Copywriter RAG) | `copywriter-rag` | Hook generation grounded in retrieved DIAN-pains KB content |
| #6 (dormant telemetry loop) | `activate-telemetry-loop` | `POST /sell-machine/creative-loop/run` makes `use_telemetry=True` reachable |
| #7 (run_ads_ab never dispatched) | `ads-ab-task-dispatch` | `dispatch_campaign_package` infers `task_type` from budget |

### Two new bugs found and flagged along the way (not fixed — separate scope)

1. **`route_lead_message`'s replies are never sent over WhatsApp** — `whatsapp_endpoints.py`'s
   webhook handler discards the return value for text messages. This affects every intent branch
   (sales_interest, payment_confirmation, and the new KB-grounded fallback) across every archived
   Taty change to date. Found during `taty-kb-and-react-router`'s Stage 11.
2. **`agents/llm_engine.py`'s `_parse_llm_response` doesn't accept `required_keys`**, but
   `_get_json_with_retry_custom_order` calls it with that argument anyway — breaks every real
   JSON-mode LLM call routed through a custom provider order. Confirmed affecting both
   `copywriter_service` (hook generation) and `agents/content_evaluator.py` (hook evaluation).
   Found during `copywriter-rag`'s Stage 11, reconfirmed during `activate-telemetry-loop`'s.

Both are genuine, live production bugs discovered through this session's discipline of always
exercising the real endpoint/integration during Stage 11 rather than trusting mocked unit tests
alone. Recommend prioritizing the `llm_engine.py` fix first given its reach (breaks the actual LLM
generation path for both Copywriter and Content Critic, silently falling back to
deterministic/hard-ban-only behavior every time).
