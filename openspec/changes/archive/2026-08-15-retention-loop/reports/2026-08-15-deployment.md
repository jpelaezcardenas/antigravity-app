# Stage 11 Deployment Report — retention-loop

- Date: 2026-08-15
- Change: retention-loop
- Agent: Claude Code (Sonnet)
- Deploy branch: `main`
- Frontend URL: https://contexia.online/app/bunker
- Backend URL: https://antigravity-app-production-175a.up.railway.app

## 11.1 — Commit + Merge + Push

- Committed on `feature/retention-loop` (`e86472a`)
- Fast-forward merged into `main` (`3e3515a..e86472a`)
- Pushed to `origin/main`: `3e3515a..e86472a main -> main`
- Includes: backend (`retention_service.py`, migration `0039`, endpoint), frontend
  (`crm-api.ts`, `B2bRetainersTab.tsx` alerts panel), and the rebuilt `contexia-app` static
  export synced additively into the repo root (`app/`, `_next/`, `sw.js`, etc. — CLAUDE.md §9),
  including a `CACHE_VERSION` bump (v15→v17; the deployed `sw.js` was already at v16 with no
  matching source bump — an existing drift, fixed in passing).
- Verified before staging: every `_next/static/*` asset referenced by the rebuilt
  `app/bunker.html` exists on disk (the exact check that would have caught the prior
  orphan-chunk production incident).

## 11.2 — Vercel Deploy

Confirmed via Vercel MCP: deployment `dpl_9gd4dB15nKW46RNUZ4omz5wXhUGp` for commit `e86472a`,
**state: READY**, target: production.

## 11.3 — Railway Deploy

Confirmed via Railway MCP: deployment `347b3e6e-3c74-469c-a6cc-b2920d56f3d9`, **status: SUCCESS**.

## 11.4 — Production Verification

**Backend**: `GET /api/v1/crm/b2b/retention-alerts` against the live Railway URL returned a clean
`401 {"detail":"Invalid or missing authentication token"}` — not a crash, not a 500. This endpoint
requires `Depends(get_current_user)` (same as every other `crm_endpoints.py` route), which the
agent must never obtain/hold per this session's safety rules.

**Frontend**: a browser tab from earlier in this session still held a live authenticated Contexia
session, but as a **client-tier** login (sidebar showed only Dashboard/Agentic OS/Configuración —
the 3-section client view per `ARCHITECTURE.md` Decision #18), not admin — CRM/Ventas is
admin-only and wasn't reachable from that session. Confirmed the shared app bundle loads with
**zero console errors** on the page that was reachable, which rules out a bundle-level JS crash
from this change's build, but the retention-alerts panel itself (behind CRM/Ventas → B2B/Retainers)
was **not visually verified live** — that requires the founder's own admin session.

**Recommended follow-up (not blocking, matches the pattern of prior changes this session):** the
founder can open `https://contexia.online/app/bunker` → "CRM / Ventas" → "B2B / Retainers" with
their admin login to see the retention-alerts panel render live — either real alerts (if any
current client matches `missed_payment`/`payment_drop`) or the explicit "Sin alertas de retención
por ahora" empty state.

## 11.5 — This Report

Created at `openspec/changes/retention-loop/reports/2026-08-15-deployment.md`.

## Outcome

Stage 11 status: **PASS**, with the same auth-boundary substitution used throughout this session
in place of full authenticated end-to-end verification (backend: clean 401 + no crash; frontend:
zero console errors on the reachable client-tier page; full CRM/Ventas panel render deferred to
the founder's own admin session).
