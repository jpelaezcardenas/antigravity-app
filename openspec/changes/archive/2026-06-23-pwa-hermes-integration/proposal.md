# OpenSpec Change: pwa-hermes-integration

> **Backfilled retroactively (2026-06-24).** This change was implemented and deployed
> 2026-06-22/23 without proposal/design/tasks artifacts, in violation of `CLAUDE.md` §7
> ("documentation is the source of truth" — artifacts must exist, not just code + a
> deployment report). Written after the fact from the existing `reports/2026-06-23-deployment.md`
> and direct verification against the current codebase. Verified live in this session
> (2026-06-24): `apps/backend/api/websocket_handler.py` and `apps/backend/services/agent_context.py`
> exist; `main.py` registers `websocket_router` at `/api/v1/ws`; `websockets>=12.0` is in
> `requirements.txt`; frontend `useAgentWebSocket.ts` hook and `PulsaCard`/`CentinelaAlerts`/
> `ApprovalQueue` components exist; all 9 commits listed in the deployment report
> (`1c218de` through `d87a902`) exist in git history; backend health endpoint returns 200.

## Executive Summary

**What:** Real-time WebSocket channel connecting the Contexia PWA frontend to the Hermes
agent backend, replacing one-off REST polling with a persistent, authenticated connection.

**Why:** The PWA needs live updates from Hermes agents (Pulso Diario, Centinela Fiscal,
Radar Predictivo, etc.) — alerts, financial pulses, approval requests — without polling.
This is the production-grade successor to the broken/never-deployed REST approach attempted
in `contexia-pwa-data-layer-mvp` (closed as superseded the same day this was backfilled).

**Impact:** PWA can subscribe to agent-level channels and receive push updates; HITL
approval workflow (approve/reject) is exposed in the UI; offline message queueing and
reconnect-with-backoff are implemented client-side.

## What Changed

### Backend (Railway — production-175a)
- `apps/backend/api/websocket_handler.py` — WebSocket endpoint (`/api/v1/ws`) + connection
  manager with per-workspace isolation, 30s heartbeat
- `apps/backend/services/agent_context.py` — session/permission context propagation
- `apps/backend/main.py` — registers `websocket_router`
- `apps/backend/requirements.txt` — added `websockets>=12.0`

### Frontend (Vercel — contexia.online)
- `frontend/dashboard/src/hooks/useAgentWebSocket.ts` — connection hook (auto-connect,
  reconnect with exponential backoff, offline queueing)
- `frontend/dashboard/src/components/PulsaCard.tsx` — financial pulse dashboard
- `frontend/dashboard/src/components/CentinelaAlerts.tsx` — tax/fiscal alerts
- `frontend/dashboard/src/components/ApprovalQueue.tsx` — HITL approve/reject UI
- `.env.production` / `.env.development`

## Done Criteria (Stage 11) — all met per `reports/2026-06-23-deployment.md`

- [x] Backend WebSocket endpoint live, JWT-authenticated
- [x] Frontend hook + 3 consuming components shipped
- [x] Railway + Vercel builds green
- [x] Health check passing in production
- [x] Deployment report filed

## Known gaps (not blockers, carried forward as follow-up if ever revisited)

- Manual browser/UAT testing (WebSocket connect, component rendering, approval E2E) was
  listed as "Next Steps" in the deployment report and was not confirmed completed in this
  session — no contradicting evidence found either; treat as unverified, not failed.
- This is the mechanism that should be extended for any future "live PWA data" need, instead
  of resurrecting the closed `contexia-pwa-data-layer-mvp` REST approach.
