## Why

The 5 operator-task bridge endpoints Hermes/Manus use to claim and report on Sell Machine work
(`/api/v1/sell-machine/tasks/*`) are unauthenticated in production today: `HERMES_BRIDGE_TOKEN`
was never set on the canonical Railway backend (`-175a`), so `require_hermes_bridge_token` no-ops
exactly per its documented "optional" contract. Setting the token naively would not fix this
safely — the local poller (`apps/hermes-manus-poller/backend_client.py`) doesn't send a matching
credential at all; it signs a JWT keyed by a separate, also-unset variable (`CONTEXIA_JWT_SECRET`).
Turning the guard on without touching the poller would silently 401 every request and stall the
task queue the Sell Machine content pipeline depends on. This needs fixing now because it is a live
unauthenticated write surface, and because a planned freemium-onboarding effort intends to extend
this same bridge for a "Pulso Diario agent insight" pipeline — that work should not inherit an
unauthenticated foundation.

## What Changes

- Generate and set `HERMES_BRIDGE_TOKEN` on the canonical Railway backend (`-175a`) via Bitwarden —
  the value is never written to any repo file, doc, or report (per ARCHITECTURE.md Decision #12).
- Update `apps/hermes-manus-poller` to send a credential the backend guard actually accepts,
  reconciling the bearer-token (`require_hermes_bridge_token`) vs. JWT (`sign_tenant_jwt` /
  `CONTEXIA_JWT_SECRET`) mismatch. Which mechanism becomes canonical is a design.md decision, not
  decided here.
- Upgrade the `hermes-manus-execution-bridge` capability's authentication requirement from
  documenting today's "optional, no-op when unset" behavior to describing the production-hardened
  posture: token configured, poller compatible with it.
- **BREAKING (operational, not code)**: once the token is live, any other caller of these 5
  endpoints without a valid credential starts receiving 401s instead of succeeding silently.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `hermes-manus-execution-bridge`: the existing requirement "Operator-task bridge endpoints support
  optional machine bearer authentication" changes from describing open-by-default behavior to
  describing the production-hardened behavior — token configured in Railway, and the Hermes poller
  sending a credential that satisfies it.

## Impact

- `apps/backend/config.py` (`HERMES_BRIDGE_TOKEN` setting), `apps/backend/presentation/sell_machine_endpoints.py`
  (`require_hermes_bridge_token`).
- `apps/hermes-manus-poller/backend_client.py` and `apps/hermes-manus-poller/config.py` (credential
  sending).
- Railway production environment (`-175a`) and the Bitwarden vault (new secret entry, name only —
  never the value — recorded in design.md).
- No frontend/PWA impact. No tenant-scoping changes — the 5 endpoints already resolve `tenant_id`
  correctly per the existing spec; only the authentication layer in front of them changes.
