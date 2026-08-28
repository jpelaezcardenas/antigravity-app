# Runbook: Rotating `HERMES_BRIDGE_TOKEN`

Static shared secret authenticating the local Hermes/Manus poller to the 5 operator-task bridge
endpoints (`/api/v1/sell-machine/tasks/*`). See
`openspec/changes/hermes-bridge-token-production-hardening/` for why this exists.

## To rotate

1. Generate a new random value (e.g. `python -c "import secrets; print(secrets.token_urlsafe(32))"`).
2. Update the Bitwarden entry `Hermes Bridge Token (production)` with the new value.
3. Set `HERMES_BRIDGE_TOKEN` on the Railway `-175a` service to the new value (this triggers a
   redeploy).
4. Update `HERMES_BRIDGE_TOKEN` in the poller's local `.env`
   (`apps/hermes-manus-poller/.env`) to the same value — no restart needed, the scheduled task
   invokes a fresh process every tick.
5. Verify: an unauthenticated `curl` to `GET .../api/v1/sell-machine/tasks/pending` returns 401;
   the poller's next tick (within ~1 minute) succeeds — check
   `apps/hermes-manus-poller/logs/poller-YYYYMMDD.log` for `HTTP/1.1 200 OK`.

## Rollback if something breaks mid-rotation

Unset `HERMES_BRIDGE_TOKEN` on Railway and let it redeploy — this immediately restores the
no-op/open behavior (no auth required), matching pre-hardening behavior. No code change needed.
