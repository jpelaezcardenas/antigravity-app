## Why

Hermes has 7 active cron jobs that call backend endpoints with a single hardcoded `company_id` (the founder's). This means all automated agent jobs — Pulso, Centinela, Radar, Auditoría Sombra, Social Ops — only run for one client. As Contexia onboards additional B2B clients, those clients receive no automated monitoring or reporting.

## What Changes

- Add a `/internal/` route group on the FastAPI backend, authenticated exclusively via `HERMES_BRIDGE_TOKEN` (not Supabase JWT)
- Introduce a `get_active_pwa_clients()` helper that queries all tenants with active PWA access (B2B contract, trial onboarding, or founder manual override)
- Create 5 aggregator endpoints — one per Hermes agent — that iterate all active clients and return a consolidated response
- Update Hermes scripts from `company_id`-per-call pattern to single `/internal/*/all-active` call + client iteration

## Capabilities

### New Capabilities
- `internal-multi-tenant-api`: Authenticated `/internal/` route group that returns aggregated per-client data for all active PWA clients; consumed exclusively by Hermes bridge token

### Modified Capabilities
- `hermes-scripts`: Hermes cron scripts change their call pattern from single `?company_id=` to `/internal/*/all-active`; no new spec file needed (implementation-only change, no spec-level behavior change to existing endpoints)

## Impact

- **New code**: `apps/backend/routers/internal.py` (new router), `apps/backend/core/pwa_clients.py` (active client resolver)
- **Existing code**: `apps/backend/main.py` (register new router), Supabase query against `b2b_clients` or equivalent table
- **No existing endpoints changed** — `/api/v1/*` endpoints are untouched
- **Hermes scripts** (`~/.hermes/profiles/contexia/scripts/*.sh`): URL change only, no logic change
- **Security**: `/internal/` must be unreachable without `HERMES_BRIDGE_TOKEN`; RLS per-client must be maintained inside each aggregated query
- **HITL unchanged**: Hermes continues to produce reports; founder approves actions via Approval Queue
