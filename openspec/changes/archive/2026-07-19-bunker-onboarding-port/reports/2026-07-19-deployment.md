# Deployment Report — bunker-onboarding-port

**Date:** 2026-07-19

## What shipped

Búnker's "Onboarding" sidebar section: from "coming soon" placeholder to a fully functional surface, ported from the same old, unlinked Vite dashboard Social Content Ops was ported from (`frontend/dashboard/src/components/ops/OnboardingOps.tsx`), rewired to the real, already-live backend (same `SOCIAL_OPS_CANONICAL` flag flipped in the prior change — no backend changes needed here).

- Start onboarding (company/email/payment/plan/owner) → `POST /social-ops/onboarding/start`
- Workspace selector with SLA/QA target display
- Natural-language intake (AI extracts present/missing credentials) → `POST /social-ops/onboarding/{id}/intake`
- Seed draft creation (HITL `pending_approval`) → `POST /social-ops/onboarding/{id}/seed`
- 21-day template checklist (S1/S2/S3 + Go-Live) from `GET /social-ops/onboarding`

`lib/social-ops-api.ts` extended (not duplicated) with the onboarding functions. This is `contexia-app`'s third data-bound exception, documented in `CLAUDE.md` alongside `CashTodayCard` and Social Content Ops.

## Commits

- `1eb7e51` — feat(bunker): wire Onboarding to the real canonical backend

## Verification performed

- `npm run build` green, no type errors.
- Local verification: temporarily pointed `contexia-app/.env.development.local` at the live Railway backend, ran the app, clicked "Onboarding" in the sidebar — the full 21-day checklist rendered, text matching exactly the `curl` output already confirmed against production before this change (`S1 Kick-off` through `Post Go-Live`, all 11 steps with correct descriptions). No console errors. Reverted `.env.development.local` after.
- Production: `curl https://contexia.online/app/bunker` → 200, correct title (`Contexia — GPS Financiero`, confirming the Next.js page).
- Vercel: deployment `dpl_JyenMHou3HjBxki9WnHEXpZHxa6o`, commit `1eb7e51`, `READY`, aliased to `contexia.online`.

## Known follow-ups (not in this change's scope)

- Agentic OS remains a "coming soon" placeholder — its old implementation (`AgenticOpsView.tsx`) calls `/api/hermes/os-status`, which depends on Hermes, an on-prem-only service per `ARCHITECTURE.md` decision #1 (never reachable from the public internet by design). Porting it as-is would always show "unreachable" in production. Needs a user decision on an alternative approach before any code is written — tracked separately.
- `login.html` (demo-credential login screen) and `middleware.ts`'s `ADMIN_ONLY` gate remain untouched — explicitly paused by the user.
