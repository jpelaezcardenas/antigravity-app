# Stage 11 Deployment Report — renta-natural-first-sale

**Date**: 2026-09-10/11
**Commit**: `992d357` (pushed to `main`)
**Railway deployments**: `7ffee9c9` (SUCCESS build, stuck traffic cutover) → `811aac26` (SUCCESS,
forced redeploy, live)

## What was deployed

- Fix in `apps/backend/services/whatsapp_inbox_service.py::pull_pending`: the OR-filter query
  builder call used `query.params.add(...)`, but the installed `postgrest-py` (0.13.2) exposes
  query params on the builder's wrapped `.request.params`, not `.params` directly. This was
  silently broken (`AttributeError`), failing 2 tests. Fixed in both the source and the test's own
  assertion (same wrong attribute path).
- New migration `apps/backend/migrations/0053_crm_wompi_transactions_remittance_tracking.sql` —
  generic `remittance_status`/`remittance_error`/`remitted_at` tracking columns on
  `crm_wompi_transactions`. **Written, not applied** — Wompi remittance is deferred (see below),
  so this migration is inert and harmless to leave unapplied indefinitely.
- OpenSpec artifacts for `renta-natural-first-sale` (proposal/design/specs/tasks) and
  `feature_list.json` pointer update.
- No frontend change.

## Scope note: what this change does NOT include

Per the founder's explicit decision (2026-09-10 evening), the Wompi/Entidad A remittance rail
(originally absorbed from `taty-wompi-entidad-a-remittance`) is **deferred, out of scope**. The
first Renta Natural sale closes on cash or a direct transfer (key/QR) Tatiana receives in person,
not through Wompi. See `design.md` Decision 3b for the full rationale. No payout service, CRM
trigger, or retry endpoint was written.

## Deployment incident: stuck traffic cutover (found and resolved this session)

The first deploy (`7ffee9c9`) reported `status: SUCCESS` from Railway's build system, but the
production URL returned `502` on both `GET /api/v1/health` and the WhatsApp webhook for several
minutes after boot, with logs stuck after a single benign pydantic startup warning (no crash
traceback, no "Uvicorn running" line). This matches a previously documented anomaly in this repo
(`pulso-diario-agent-insight-bridge`, 2026-08-29: "Railway never completed the traffic cutover
after ~30 minutes... a manual `railway_redeploy` resolved it in ~2 minutes"). Applied the same
fix: `railway_redeploy` on the stuck deployment produced a new deployment (`811aac26`), which came
up healthy within the wait window.

**Recurrence note**: this is now the second time this exact anomaly has been observed on this
Railway project/service. If it recurs a third time, it likely warrants a founder-level check of
the Railway dashboard's auto-deploy/health-check configuration rather than treating each
occurrence as an independent one-off.

## Verification (production, this session)

| Check | Result |
|---|---|
| `GET /api/v1/health` | `200` |
| `POST /api/v1/channels/whatsapp/webhook` with unsigned body | `403` (rejects, as required) |
| `whatsapp_inbound_events` backlog (Supabase MCP) | `0` unprocessed, `64` total, newest event 2026-09-10 21:59:26 UTC — poller draining real production traffic with no backlog before and after this deploy |
| Full backend test suite (direct `pytest`, py311) | 33 failed / 1257 passed / 120 skipped — all 33 failures confirmed pre-existing on `main` via `git stash` comparison, none touching whatsapp/wompi/crm_service/inbox |
| `RUN_TESTS=1 bash init.sh` | Reports the repo's own documented pre-existing baseline (different Python interpreter than the direct run above; direct run is the trustworthy signal per project memory) |

## Section 5 (Stage 11) task status

- [x] 5.1 git commit + push to main — `992d357`.
- [x] 5.2 Vercel — not applicable, no frontend change in this deploy.
- [x] 5.3 Railway deploy active and healthy — `811aac26`, `GET /api/v1/health` → 200.
- [x] 5.4 Production verification — webhook rejects unsigned payloads (403); inbox durability
      confirmed via live traffic evidence (0 backlog across the deploy), not a synthetic drill
      (see `tasks.md` 2.11-2.13 for why the drills were not run against the live channel).
- [x] 5.5 This report.

## Is this change complete?

**No — explicitly not yet**, per `design.md` Decision 4 (revised). All deployable code for
Sections 1-2 (channel consolidation + durable inbox) is live and verified in production. What
remains before this change can be archived:

1. **Founder action 1.3b**: update the Verify Token in Meta Dashboard → WhatsApp → Configuration →
   Webhooks to `contexia-whatsapp-2026-prod`.
2. **Founder action 2.7**: create a dedicated "Taty Bot" Chatwoot user for the poller's injection
   identity (currently shares the single `CHATWOOT_API_TOKEN`).
3. **Section 4 — the actual closing criterion**: one real Renta Natural lead closed end to end,
   with Tatiana receiving cash or a direct transfer in person, recorded per the
   `renta-natural-sale-verification` spec. This is a sales/operational event, not a code task —
   nothing further to deploy blocks it.

Do not archive this change or its three source changes (`taty-channel-consolidation`,
`whatsapp-durable-inbox` — actively absorbed; `taty-wompi-entidad-a-remittance` — deferred, frozen)
until item 3 above has actually happened.
