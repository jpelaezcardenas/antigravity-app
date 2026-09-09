# Stage 11 — Deployment report (2026-09-09)

**Status: DEPLOYED AND VERIFIED IN PRODUCTION.**

Continuation of the founder-authorised plan ("archiva el change y despues continua... hasta
finalizar con todo el plan"). No migration required — no schema change in this change.

| | |
|---|---|
| Merged | `29bfdfa..821d693` → `main`, fast-forward |
| Pushed | `origin/main` |
| Railway | deployment `d5925dd6-873c-43ed-a5ed-907d35dbb8e3` |
| Vercel | `contexia.online/app/bunker` → 200 |

## Verified live

**Backend:**

| Route | Result |
|---|---|
| `GET /api/v1/health` | 200 |
| `GET /api/v1/pricing/pre-cotizacion` | 401 (self route, unchanged) |
| `GET /api/v1/pricing/pre-cotizacion/cliente/x` | **401** — new operator route mounted, auth enforced |
| `GET /api/v1/financials` | 401 (sibling, unchanged) |

**Frontend — chain walked end to end, not just a 200:**

| Check | Result |
|---|---|
| `contexia.online/app/bunker` | 200 |
| Live `sw.js` `CACHE_VERSION` | `v20-2026-09-09` |
| Served page references the new chunk | yes (`11bepc041jvkm.js`) |
| That chunk, fetched from production, contains `Pre-cotizar` | yes |

## Isolation from concurrent work

Built in a dedicated worktree (`antigravity-app-pricing`) created specifically for this change,
to avoid the branch/checkout collision the previous pricing change hit twice with a concurrent
session. No files outside this change's scope were touched.

## What this closes

`pricing-quote-engine` shipped an engine that resolved the CALLER's tenant — unusable from the
Búnker, where the caller is always a Contexia operator. This change adds the operator-only route
that lets Tatiana pre-quote a specific roster client, prices the suggestion from a real catalog
(previously undefined anywhere in the repo), and surfaces fee/band coherence — closing the loop
from "engine deployed" to "engine usable".

## Deliberately not done

- No change to `apps/backend/core/plan_features.py`.
- No wiring of the catalog into Taty's WhatsApp sales prompt — flagged for the founder as a
  separate commercial decision (docs/pricing.md, "Known follow-up").
- No reconciliation of `TenantInfoCard.tsx` / `UpgradePlanBanner.tsx` drifted commercial names —
  those files carry another session's uncommitted work.
