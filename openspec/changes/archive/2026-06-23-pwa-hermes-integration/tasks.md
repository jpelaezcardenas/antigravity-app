# Tasks: pwa-hermes-integration

> Backfilled 2026-06-24 from `reports/2026-06-23-deployment.md` and direct code verification.
> See `proposal.md` for the backfill rationale.

## FASE A+B: WebSocket integration (backend + frontend wiring)
- [x] `apps/backend/api/websocket_handler.py` — endpoint + connection manager (commit `1c218de`)
- [x] Frontend `useAgentWebSocket.ts` hook

## FASE C: Session context propagation
- [x] `apps/backend/services/agent_context.py` — permission-aware context (commit `81c9be1`)

## FASE D: Deployment checklist/guide
- [x] Pre-deployment checks + dependency fixes (commit `6f6f5db`)
- [x] Local validation scripts (commit `3619e53`)

## Deployment
- [x] Git push to main
- [x] Railway build (production-175a) — green, ~6m34s
- [x] Vercel build (contexia.online) — green, ~2m18s
- [x] Health check: `GET /api/v1/health` → 200
- [x] WebSocket route registered (`/api/v1/ws`)
- [x] Deployment report: `reports/2026-06-23-deployment.md`

## Stage 11 — Deploy to Production
- [x] 11.1 git commit + push to main
- [x] 11.2 Vercel build complete
- [x] 11.3 Railway deploy active
- [x] 11.4 Production URL verified (health endpoint)
- [x] 11.5 Deployment report created

## Outstanding (not blockers — unverified, not failed)
- [ ] Manual browser test: WebSocket connects, "WebSocket connected" logged in console
- [ ] Manual test: `PulsaCard`, `CentinelaAlerts`, `ApprovalQueue` render with real data
- [ ] Manual test: approve/reject flow end-to-end
- [ ] Manual test: offline queueing + reconnect backoff
