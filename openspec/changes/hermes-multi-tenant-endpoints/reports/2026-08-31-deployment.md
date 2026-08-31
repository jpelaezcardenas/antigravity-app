# Deployment Report — hermes-multi-tenant-endpoints
**Date:** 2026-08-31  
**Environment:** Production (`antigravity-app-production-175a.up.railway.app`)  
**Final commit:** `a00089c`

## What was deployed

5 new internal aggregator endpoints behind `HERMES_BRIDGE_TOKEN` auth:
- `GET /internal/health`
- `GET /internal/pulso/all-active`
- `GET /internal/centinela/all-active`
- `GET /internal/radar/all-active`
- `POST /internal/auditoria-sombra/all-active`
- `GET /internal/social-ops/all-active`

New modules: `core/hermes_auth.py`, `core/pwa_clients.py`, `routers/internal.py`  
Modified: `main.py` (conditional router registration)

## Deployment timeline

| Time (UTC) | Event |
|---|---|
| 00:05 | Commit `4ec10ab` pushed, Railway deploy SUCCESS |
| 00:13 | `/internal/health` → 200 ✅ |
| 00:13 | `/internal/pulso/all-active` → 500 ❌ |
| 00:19 | Fix 1 committed (`c087f7c`): inject `get_service_supabase()` into per-client helpers; replace `.single()` with `.limit(1)` on tenants table |
| 00:21 | Still 500 — new traceback: `column b2b_clients.nombre does not exist` (42703) |
| 00:22 | Fix 2 committed (`a00089c`): `pwa_clients.py` — select `name` not `nombre` |
| 00:23 | `/internal/pulso/all-active` → **200 ✅**, 11 active clients returned |

## Smoke test results

| Endpoint | Status | Notes |
|---|---|---|
| `GET /internal/health` | ✅ 200 | `{"status":"ok"}` |
| `GET /internal/pulso/all-active` | ✅ 200 | 11 clients, all with Pulso payload |
| `GET /internal/centinela/all-active` | ✅ 200 | 11 clients, commit `0b38927` fixed `resolved` column bug |
| `GET /internal/radar/all-active` | ✅ 200 | 11 clients, risk_score and cashflow_forecast_30d |
| `POST /internal/auditoria-sombra/all-active` | ✅ 200 | 11 clients, report_id + download_url per client |
| `GET /internal/social-ops/all-active` | ✅ 200 | 11 clients, full pipeline data with leads |

## Bugs found and fixed during deployment

### Bug 1 — anon Supabase client bypassed by RLS
- **Root cause:** `get_daily_summary` and `calculate_risk_score`/`calculate_cashflow_forecast` called `get_supabase()` (anon client). Without a user JWT, RLS blocks `tenants` table queries. `.single()` on 0 rows throws `PGRST116` → 500.
- **Fix:** Added optional `supabase_client` param to those functions; internal router injects `get_service_supabase()`. Replaced `.single()` → `.limit(1)` (defensive).

### Bug 2 — wrong column name in b2b_clients query
- **Root cause:** `pwa_clients.py` selected `nombre` but the actual column is `name` (from migration `0020_crm_b2b_retainers.sql`).
- **Fix:** Updated select to `id, tenant_id, name` and row mapping to `row.get("name")`.

### Bug 3 — `resolved` filter on centinela_alerts (column does not exist)
- **Root cause:** `get_centinela_alerts` in `routers/internal.py` called `.eq("resolved", False)`. The `centinela_alerts` table has no `resolved` boolean column (the production endpoint `centinela_endpoints.py` never used such a filter).
- **Fix:** Removed the `.eq("resolved", False)` filter; added `.order("created_at", desc=True)` to match the pattern from `centinela_endpoints.py`. Commit `0b38927`, Railway deploy `51792ff5` SUCCESS.

## CHECKPOINTS self-improving loop additions

New rules to add to `DEPLOYMENT_STAGE/CHECKPOINTS.md`:
1. When querying any Supabase table from a system/internal endpoint (no user JWT), always use `get_service_supabase()` — never `get_supabase()`.
2. Before writing `SELECT` queries against a new table, verify column names against the migration SQL in `apps/backend/migrations/`.

## Hermes scripts generated

5 bash scripts ready to install at `~/.hermes/profiles/contexia/scripts/`:
- `pulso.sh`, `centinela.sh`, `radar.sh`, `auditoria-sombra.sh`, `social-ops.sh`

Each calls a single `/internal/*/all-active` endpoint and iterates `clientes[]` via `jq`.  
Auth: `$HERMES_BRIDGE_TOKEN` env var. Backend URL: `$CONTEXIA_BACKEND_URL` (overridable).
