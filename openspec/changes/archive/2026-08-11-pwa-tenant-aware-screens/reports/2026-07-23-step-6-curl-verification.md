# Step 6 Report — Manual Endpoint Testing with curl

- Date: 2026-07-23
- Change: pwa-tenant-aware-screens
- Agent: leader (Claude Opus 4.8), executed directly against a local `uvicorn` instance
  (`apps/backend`, port 8123, `AUTH_ENFORCED=False` default — no `.env` override).

## Setup

```
cd apps/backend && nohup python -m uvicorn main:app --port 8123 &
curl -s http://127.0.0.1:8123/api/v1/health   # {"status":"healthy", ...}
```

## GET /api/v1/centinela/alerts (new, Stage 2)

**No auth (staging identity → Cliente Cero):**
```
curl -s http://127.0.0.1:8123/api/v1/centinela/alerts
```
→ `200`, `alert_count: 20`, `source: "supabase"`, `risk_level: "low"` — real Cliente Cero
`centinela_alerts` rows (`SHADOW_GL_DISCREPANCY` rule), no demo fallback.

**Garbage bearer token:**
```
curl -s -H "Authorization: Bearer not-a-real-jwt" http://127.0.0.1:8123/api/v1/centinela/alerts
```
→ `200`, identical response to the no-auth case. Expected: with `AUTH_ENFORCED=False` (the local
default), `get_current_user` falls back to the permissive staging identity rather than rejecting
an unparseable token — this is existing, unmodified `core/deps.py` behavior (`/financials`
exhibits the same behavior, confirmed below), not something this change introduces or could fix
without touching auth middleware (out of scope). In production, `AUTH_ENFORCED=True`.

## GET /api/v1/financials/liquidity-bridge (new, Stage 3)

**No auth / garbage token (both → staging → Cliente Cero):**
```
curl -s http://127.0.0.1:8123/api/v1/financials/liquidity-bridge
```
→ `200`, `{"initial_balance":352000000,"inflows":0,"outflows":0,"final_balance":352000000,
"period":"2026-07","status":"ready"}` — identical for both auth states, same reasoning as above.

**Cross-check against `/financials` (sanity, confirms the spec's parity requirement live):**
```
curl -s http://127.0.0.1:8123/api/v1/financials
```
→ `{"caja_real":352000000, ...}` — **exactly matches** `liquidity-bridge`'s `final_balance`
(352000000), live-confirming the `pulso-financials-api` spec's "Final balance matches the
equivalent Caja Real balance" scenario against the running server, not just the unit tests.

## GET /centinela/alerts/{company_id} (legacy route, unaffected)

```
curl -s http://127.0.0.1:8123/api/v1/centinela/alerts/ctx-001
```
→ `200`, `source: "demo_fallback"`, 5 demo alerts (`R001`, `R005`, `R006`, `R009`, `R010`) —
identical shape/behavior to before this change. Confirms Hermes's `CentinelaAlertsTool`
integration is untouched.

## Not tested here (deferred to Stage 13)

A real per-tenant client JWT was not forged for this local test — per the same rule the
`per-tenant-client-access` change's Stage 6 followed (`reports/2026-07-22-deployment.md`):
never manufacture or use a production credential to bypass real login. The
own-tenant-vs-Cliente-Cero-vs-unresolved distinction is already covered by the 9 hermetic
unit tests (Stages 2.1/3.1) against real throwaway tenants in production Supabase — this curl
pass instead confirms the routes are reachable, correctly wired, return the right shape, and
that the staging-identity fallback path works end-to-end through the real HTTP server, not just
mocked. Real client-token verification happens at Stage 13.6 (founder logs in himself).

## Outcome

- Step 6 status: **PASS**
- Blocking issues: none.
