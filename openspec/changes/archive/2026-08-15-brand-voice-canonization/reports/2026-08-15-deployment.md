# Stage 11 Deployment Report — brand-voice-canonization

- Date: 2026-08-15
- Change: brand-voice-canonization
- Agent: Claude Code (Sonnet)
- Deploy branch: `main`
- Backend URL: https://antigravity-app-production-175a.up.railway.app

## 9.1 — Commit + Merge + Push

- Committed on `feature/brand-voice-canonization` (`867b144`)
- Fast-forward merged into `main` (`b231de9..867b144`)
- Pushed to `origin/main`: `2cd52a9..867b144 main -> main`
- The 3 pre-existing uncommitted modifications from another session
  (`apps/chatwoot-bridge/run_bridge.ps1`, `apps/hermes-manus-poller/run_poller.ps1`,
  `openspec/FOUNDER_ACTIONS_2026-08-13.md`) were deliberately left untouched — not staged, not
  committed, not part of this push.

## 9.2 — Railway Deploy

- Project: `elegant-success` (the sole canonical backend, per `ARCHITECTURE.md` Decision #9)
- Service: `antigravity-app` · Environment: `production`
- Deployment `21b80fdb-f1d2-4e14-8600-d5cc11c57187`, triggered by the push, went
  `BUILDING` → **`SUCCESS`**
- Confirmed via Railway MCP (`railway_get_deployment`)

## 9.3 — Production Verification

`POST /api/v1/sell-machine/hooks/evaluate` (like all sell-machine endpoints except the
Hermes-bridge task-dispatch routes) requires `Depends(get_current_user)` — a real authenticated
Supabase session. Per this session's safety rules, the agent must never obtain, hold, or submit
a production auth credential — so a full end-to-end curl proving a specific hook gets rejected
was **not attempted**, and is a deliberate scope boundary, not an oversight.

**What was verified instead, as substitute evidence the deploy is healthy and correct:**

1. **The endpoint is live and reachable post-deploy.** `curl -X POST .../hooks/evaluate` (no
   auth header) returned `401 {"detail":"Invalid or missing authentication token"}` — not a
   connection failure, not a 500, not an import error. A broken `brand_rubric.py` import (e.g. a
   typo, a missing `core.constants` symbol) would have crashed the app at startup or on first
   request; instead the auth layer evaluated cleanly, which only happens after the module import
   graph resolves successfully.
2. **Railway runtime logs confirm the request landed correctly and the app is otherwise serving
   traffic normally** — `POST /api/v1/sell-machine/hooks/evaluate - 401 - 0.003s` appears in the
   deployment's live logs alongside healthy 200s on unrelated endpoints
   (`/channels/whatsapp/inbox/pending`, `/sell-machine/tasks/pending`) in the same time window,
   i.e. the deploy did not degrade the service.
3. **The actual Claim Ledger logic is exhaustively covered by the 30 unit tests** run in Step 6
   (`2026-08-14-step-6-unit-test-verification.md`), including the exact regression case this
   change exists to prevent: a hook containing `$471.000` is deterministically rejected, and the
   correct `$523.740` figure is not. Those tests run against the same `brand_rubric.py` module
   now live in this deployment — there is no code-path divergence between what was tested and
   what was deployed (no environment-specific branching in `check_claims`).

**Recommended follow-up (not blocking, not part of this change's scope):** a founder or
authenticated admin can optionally repeat the `$471.000` curl call with a real bearer token to
see the live 200 response with `"approved": false` — this is a nice-to-have confirmation, not a
gap in coverage.

## 9.4 — This Report

Created at `openspec/changes/brand-voice-canonization/reports/2026-08-15-deployment.md`.

## Outcome

Stage 11 status: **PASS**, with the auth-boundary substitution documented above in place of a
full authenticated curl round-trip.
