# Stage 11 Deployment Report — hermes-bridge-token-production-hardening

**Date:** 2026-08-28
**Status:** ✅ LIVE IN PRODUCTION

## What changed

The 5 operator-task bridge endpoints (`/api/v1/sell-machine/tasks/*`, `/campaigns/{id}/dispatch`,
`/tasks/{id}/status`, `/tasks/{id}/result`) went from unauthenticated in production to requiring a
bearer token. The local Hermes/Manus poller was updated to send that token, replacing a dead
self-signed-JWT path that the backend never verified.

## Deploys

| Component | What | Result |
|---|---|---|
| Railway (env var) | `HERMES_BRIDGE_TOKEN` set via `railway_set_variable`, `skip_deploys=false` | Deployment `d7eeeed3` → SUCCESS |
| Railway (git push) | Commit `891f0bc` pushed to `main`, auto-deploy | Deployment `e621b8e7` → SUCCESS |
| Local poller | Code + `.env` updated in place; no restart needed (one-shot task per tick) | Confirmed via `logs/poller-20260828.log` |

Both Railway deploys hit the documented ~40-80s cold-start window (ARCHITECTURE.md) — confirmed via
`railway_deployment_logs` this was normal startup time, not a crash (`Application startup complete`
logged, followed by successful real requests).

## Live verification (post both deploys)

```
GET /api/v1/health                                          → 200 healthy
GET /api/v1/sell-machine/tasks/pending  (no Authorization)   → 401 "missing or malformed Authorization header"
GET /api/v1/sell-machine/tasks/pending  (wrong token)        → 401 "invalid bridge token"
GET /api/v1/sell-machine/tasks/pending  (correct token)      → 200 []
```

Poller's own scheduled tick (`ContexiaHermesManusPoller`, 1-minute trigger) confirmed sending the
real token and completing successfully in `logs/poller-20260828.log`.

## Tests

- `apps/hermes-manus-poller`: 47/47 passed.
- `apps/backend` (`test_sell_machine_endpoints.py` + `test_operator_task_endpoints.py`): 32/32
  passed (no backend code changed — confirms no regression).
- `./init.sh`: green.

## Review

Leader→implementer→reviewer loop per `HARNESS.md`. First reviewer pass: CHANGES_REQUESTED (a stale
`CONTEXIA_JWT_SECRET` reference survived in `apps/hermes-manus-poller/.env.example`, missed by an
overly-narrow `*.py`-only grep in task 7.1; missing `progress/impl_*.md` paper trail). Both fixed;
second pass: **APPROVED**. Full detail in
`progress/review_hermes-bridge-token-production-hardening.md`.

## Docs updated

- `AGENTES.md` — corrected "fail-open until the env var is set" to reflect the token is now live.
- `docs/runbooks/hermes-bridge-token-rotation.md` — new manual rotation runbook.

## Secrets handling

The token value was generated locally, never written to any repo file, doc, or report (verified by
the reviewer via grep across this entire change directory and the runbook). `bw` CLI was
unreachable from this session's shell (hung on `bw status`) — a pre-existing environment
limitation — so the value was reported directly to the founder in chat instead of stored in
Bitwarden by this session; suggested entry name: `Hermes Bridge Token (production)`.

## Not in scope / not touched

- `apps/chatwoot-bridge/` has its own, unrelated `CONTEXIA_JWT_SECRET`/similar pattern — a
  genuinely different app, out of this change's declared Impact section (confirmed by the
  reviewer).
- `agents_endpoints.py`'s tenant-scoping gap — pre-existing, explicitly deferred elsewhere.
- Files belonging to a concurrent, unrelated session (`ARCHITECTURE.md`'s LLM-cascade edits,
  `apps/backend/config.py`, `apps/backend/agents/llm_engine.py`,
  `apps/backend/tests/test_profile_support.py`, `progress/current.md`, and a second unrelated hunk
  in `AGENTES.md` about WhatsApp inbound-only policy) were left untouched in the working tree —
  this change's commit was staged surgically (including a hand-isolated patch for `AGENTES.md` to
  avoid bundling the other session's in-progress edit).

## Ready to archive

All tasks in `tasks.md` complete (26/26). Ready for `/opsx:archive hermes-bridge-token-production-hardening`.
