# Hermes Integration — Contexia

Hermes is the agentic OS that orchestrates all automated operations for Contexia.
It runs as a systemd daemon in WSL/Ubuntu and connects to this backend via `HERMES_BRIDGE_TOKEN`.

## Architecture

```
WSL Ubuntu (local)
  └── hermes gateway (systemd: hermes-gateway-contexia.service)
        └── 7 cron jobs (script mode, no LLM, no tokens)
              └── curl → Railway 175a (antigravity-app-production)
                    └── FastAPI backend → Supabase (RLS multi-tenant)
```

## Gateway

- **Config path:** `~/.hermes/profiles/contexia/`
- **Dashboard:** `http://127.0.0.1:9119/cron?profile=contexia`
- **Ports:** 8642 (loopback), 8644 (public), 9119 (dashboard)
- **Auth to backend:** `HERMES_BRIDGE_TOKEN` (stored in `.env`, sourced from Railway project `elegant-success` / service `175a`)

## Cron Jobs (7 active)

All jobs use script mode (`no_agent: true`) — deterministic bash, zero tokens, zero LLM cost.
Watchdog pattern: **silent on clean state, output only when action is needed.**

| ID | Name | Schedule (COT) | Script | Delivery |
|----|------|----------------|--------|----------|
| `766179c9c73a` | Pulso Diario | 8:00 AM Mon-Fri | `pulso-diario.sh` | bot-chat → Taty |
| `00d1f51e3e65` | Conciliacion Shadow GL | 3:00 AM daily | `conciliacion-shadow-gl.sh` | local |
| `f33d5bf666a7` | Insight Bridge | 9:00 AM Mon-Fri | `pulso-diario-insight-bridge.sh` | bot-chat → Taty |
| `4b62dc638909` | Radar Predictivo | 6:00 AM Mon-Fri | `radar-predictivo.sh` | bot-chat |
| `e1d727ec5f45` | Centinela Fiscal | 12:00 PM Mon-Fri | `centinela-fiscal.sh` | bot-chat |
| `d02cede71b87` | Auditoria Sombra | 2:00 AM daily | `auditoria-sombra.sh` | local |
| `5ee336482311` | Social Ops | 8:00 AM Mon-Fri | `social-ops-briefing.sh` | bot-chat |

Scripts live in WSL at: `~/.hermes/profiles/contexia/scripts/`
Backup copies are in this repo at: `docs/hermes/scripts/`

## Backend Endpoints Called

| Script | Primary endpoint | Fallback |
|--------|-----------------|---------|
| pulso-diario | `POST /api/v1/agents/pulso-diario/summary` | `GET /api/v1/financials` |
| conciliacion-shadow-gl | `GET /api/v1/agents/centinela-fiscal/alerts` | `GET /api/v1/centinela/alerts` |
| radar-predictivo | `GET /api/v1/radar?company_id=...` | `GET /api/v1/agents/radar/predictions` |
| centinela-fiscal | `GET /api/v1/centinela/alerts?company_id=...` | `GET /api/v1/agents/centinela-fiscal/alerts` |
| auditoria-sombra | `POST /api/v1/wizard/auditoria-sombra` | `GET /api/v1/agents/auditoria-sombra/run` |
| social-ops-briefing | `GET /api/v1/social-ops/briefing?company_id=...` | `GET /api/v1/channels/social-ops/pipeline` |

## Current Limitation — Single Tenant

All scripts are hardcoded to `company_id=ff1a8b7c-b0a1-422e-bc48-fac6242be027` (Contexia founder).

**Pending:** Implement `/internal/*` aggregator endpoints that return data for ALL active PWA clients
in a single authenticated call. See OpenSpec proposal for multi-tenant aggregator.

Access criteria for a client to appear in aggregated results:
1. Active B2B client with Contexia
2. Client in trial/onboarding with PWA access
3. Manually enabled by founder (founder override flag)

## HITL Rules (Non-Negotiable)

Hermes NEVER auto-approves:
- Tax declarations or financial statements
- Paid advertising on Meta/FB/IG
- Bank transfers
- Commits to this repo

All financial actions require: `Hermes produces → approval_queue → founder click → execution`

## Restore Procedure (if WSL resets)

1. Install Hermes in WSL: `curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash`
2. Copy scripts from `docs/hermes/scripts/` to `~/.hermes/profiles/contexia/scripts/`
3. Re-add env vars to `~/.hermes/profiles/contexia/.env`:
   - `HERMES_BRIDGE_TOKEN` — get from Railway project `elegant-success` → service `175a` → variables
   - `HERMES_API_BASE=https://antigravity-app-production-175a.up.railway.app`
   - `OMNI_API_KEY` — get from OmniRoute dashboard at `localhost:20128`
4. Re-register the 7 cron jobs:
   ```bash
   hermes cron create "0 13 * * 1-5" "Pulso Diario — 8:00 AM COT" --script pulso-diario.sh --deliver bot-chat
   hermes cron create "0 8 * * *"    "Conciliacion Shadow GL — 3:00 AM COT" --script conciliacion-shadow-gl.sh --deliver local
   hermes cron create "0 14 * * 1-5" "Insight Bridge — 9:00 AM COT" --script pulso-diario-insight-bridge.sh --deliver bot-chat
   hermes cron create "0 11 * * 1-5" "Radar Predictivo — 6:00 AM COT" --script radar-predictivo.sh --deliver bot-chat
   hermes cron create "0 17 * * 1-5" "Centinela Fiscal — 12:00 PM COT" --script centinela-fiscal.sh --deliver bot-chat
   hermes cron create "0 7 * * *"    "Auditoria Sombra — 2:00 AM COT" --script auditoria-sombra.sh --deliver local
   hermes cron create "0 13 * * 1-5" "Social Ops — 8:00 AM COT" --script social-ops-briefing.sh --deliver bot-chat
   ```
5. Verify: `hermes cron list` — should show 7 jobs with `[active]` status
6. Verify dashboard: `http://127.0.0.1:9119/cron?profile=contexia`

## Admin Commands

```bash
# List all jobs
hermes cron list

# Run a job manually
hermes cron run <job-id>

# View logs of last run
hermes cron logs <job-id> --tail 20

# Check gateway status
hermes gateway status
```
