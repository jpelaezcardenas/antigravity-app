## Context

Hermes runs 7 cron jobs as shell scripts. Each script calls a backend endpoint with a hardcoded `COMPANY_ID` (the founder's). This works for a single-client setup but fails as soon as additional B2B clients are onboarded — those clients receive no automated Pulso/Centinela/Radar/Auditoría/Social Ops delivery.

The backend already has per-tenant RLS, a tenant resolver (`core/tenant_context.py`), and a `b2b_clients` table with `status` and `provision_status` fields. The missing piece is a `/internal/` route group that:
1. authenticates Hermes via `HERMES_BRIDGE_TOKEN` (not Supabase JWT — Hermes has no user session)
2. resolves all active PWA clients in one query
3. fans out the per-client computation and returns an aggregated response

**Active PWA client definition** (confirmed from schema):
- `b2b_clients.status = 'activo'` AND `b2b_clients.provision_status = 'provisioned'`
- The founder can manually enable/disable any client from the Búnker CRM by toggling `status`; no separate `founder_override` field needed.

## Goals / Non-Goals

**Goals:**
- Add `/internal/` router authenticated by `HERMES_BRIDGE_TOKEN` (Bearer token, env var)
- Add `core/pwa_clients.py`: `get_active_pwa_clients(supabase_client)` → `list[ActiveClient]`
- Add 5 aggregator endpoints (one per Hermes agent) returning `{clientes: [...], total: N, timestamp: ISO}`
- Per-client queries inside each endpoint MUST respect per-tenant RLS (use service role, filter by `tenant_id`)
- Update Hermes scripts from `?company_id=<hardcoded>` to `/internal/*/all-active`

**Non-Goals:**
- Changing existing `/api/v1/*` endpoints (zero breakage)
- Adding write operations to `/internal/` (read/aggregate only)
- Building a generic multi-tenant fan-out framework — 5 specific endpoints is enough
- Adding `founder_override` as a separate DB field (not needed; `status = 'activo'` is the manual override)
- Frontend changes (Búnker or PWA)

## Decisions

### D1: HERMES_BRIDGE_TOKEN as auth, not Supabase JWT
Hermes runs as a system process (WSL cron), not as an authenticated user. Using Supabase JWT would require Hermes to manage a login session and refresh tokens. `HERMES_BRIDGE_TOKEN` (already in Railway env vars) is simpler, already used on existing Hermes endpoints, and appropriate for internal machine-to-machine calls.

Alternatives considered:
- **Service role key**: too powerful (unrestricted DB access); `HERMES_BRIDGE_TOKEN` is scoped to the `/internal/` prefix only
- **Per-client JWT loop**: Hermes would need one JWT per client, requiring a new token management system

### D2: Aggregator pattern (backend fans out, not Hermes)
The backend queries all active clients and returns one consolidated JSON. Hermes receives `{clientes: [...]}` and iterates locally.

Alternatives considered:
- **Hermes fans out**: Hermes calls `/api/v1/pulso?company_id=X` N times. Rejected: N+1 network calls, each needing a per-tenant JWT, no benefit over current state.
- **Streaming / SSE**: overkill for ≤10 clients; simple JSON is sufficient.

### D3: Per-client data fetched inside the aggregator using service-role Supabase client
Each endpoint's per-client loop uses the service-role Supabase client (already available in backend via `get_supabase_service_client()`) filtered by `tenant_id`. This avoids the need to instantiate a per-tenant JWT session inside the aggregator and maintains the RLS contract (explicit `eq("tenant_id", ...)` filter in every query — defense in depth even if RLS is bypassed at the service-role level).

### D4: One endpoint per agent, not a single generic `/internal/all-active`
Each agent endpoint (Pulso, Radar, Centinela, Auditoría Sombra, Social Ops) calls a different service and returns a different payload shape. A single generic endpoint would require complex dispatch logic. Five dedicated endpoints are explicit, testable, and match the existing agent architecture.

## Risks / Trade-offs

- **New attack surface** → `/internal/*` must return 403 for any request without a valid `HERMES_BRIDGE_TOKEN`. Add a FastAPI dependency `verify_hermes_token` that reads `HERMES_BRIDGE_TOKEN` from env and compares with `secrets.compare_digest`. Never fall back to "open if env var missing" — fail closed.
- **Service-role queries bypass RLS** → explicit `eq("tenant_id", client.tenant_id)` in every Supabase query inside the aggregator; no cross-tenant data leakage even if RLS rules change.
- **Client list could be empty** → normal; return `{clientes: [], total: 0, timestamp: ...}` — Hermes script handles empty list gracefully.
- **Slow aggregation for many clients** → sequential per-client calls are fine for ≤10 clients. If the client base grows to 50+, add `asyncio.gather` fan-out at that time.
- **`HERMES_BRIDGE_TOKEN` rotation** → token is in Railway env vars; rotation requires updating Railway + Hermes config in sync. Documented in runbook.

## Migration Plan

1. Add `HERMES_BRIDGE_TOKEN` to Railway env vars (already exists; confirm value matches Hermes config)
2. Deploy `apps/backend/core/pwa_clients.py` + `apps/backend/routers/internal.py` to Railway
3. Smoke-test: `curl /internal/pulso/all-active -H "Authorization: Bearer <token>"` → 200 with founder's company in `clientes`
4. Update Hermes scripts (WSL) to new URLs
5. Verify cron jobs produce multi-client output

Rollback: `/internal/` router can be disabled by removing it from `main.py` router registration without touching any existing code.

## Open Questions

- **Social Ops endpoint**: `GET /social-ops/briefing` currently delegates to `SocialOpsService`. Need to confirm the service returns data per `tenant_id`; if not, social ops aggregator may return empty payload per client until that service is made tenant-aware.
- **Auditoría Sombra nightly mode**: `POST /wizard/auditoria-sombra` takes `{"company_id": ..., "mode": "nightly"}`. The aggregator will call the underlying service directly rather than the HTTP endpoint (avoids self-referential HTTP call inside the backend).
