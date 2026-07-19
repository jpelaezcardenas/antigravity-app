## Why

The Búnker's "Onboarding" sidebar section is still a "coming soon" placeholder, but a real, working implementation already exists: `frontend/dashboard/src/components/ops/OnboardingOps.tsx` (the same old, unlinked Vite dashboard `bunker-social-content-ops-port` ported from). Its backend — the "Onboarding 21D" workflow (S1/S2/S3 + Go-Live, natural-language credential intake, seed drafts) — is already deployed and reachable in production (`SOCIAL_OPS_CANONICAL=true`, flipped in the prior change). Confirmed via `curl`: `GET /api/v1/social-ops/onboarding` returns 200 with real template data today. This work should not sit unreachable — it should be the live content in the Búnker's Onboarding section, same as Social Content Ops.

## What Changes

- Extend `contexia-app/lib/social-ops-api.ts` with the onboarding types/functions from the old `socialOpsApi.ts` (`getSocialOpsOnboarding`, `startSocialOpsOnboarding`, `advanceSocialOpsOnboardingStep`, `createSocialOpsOnboardingSeed`, `intakeSocialOpsOnboarding`) — no backend changes, all endpoints already live.
- Port `OnboardingOps.tsx` into `contexia-app/components/bunker/onboarding/OnboardingSection.tsx`: start-onboarding form (company/email/payment/plan/owner), workspace selector, natural-language intake form (AI extracts present/missing credentials), seed-draft creation, and the 21-day template checklist.
- Restyle from the old app's generic Tailwind classes to this project's own `@theme` tokens, per `contexia-app/CLAUDE.md`'s hard rule against ad-hoc colors — same translation table used for Social Content Ops.
- Wire `contexia-app/app/app/bunker/page.tsx`: "Onboarding" section renders `OnboardingSection` instead of `ComingSoonSection`.
- Document Onboarding as `contexia-app`'s third data-bound exception to the mock-first rule (alongside `CashTodayCard` and Social Content Ops) in `contexia-app/CLAUDE.md`.

## Capabilities

### New Capabilities
- `bunker-onboarding`: real, backend-wired Onboarding surface under the Búnker's sidebar — start onboarding, workspace selection, natural-language intake, seed drafts, 21-day template checklist, all reading/writing the canonical `/api/v1/social-ops/onboarding*` endpoints.

### Modified Capabilities
- `bunker-admin-shell`: the "Placeholder sections" requirement's scenario list changes — "Onboarding" is no longer a placeholder (only "Agentic OS" and "Configuración" remain).

## Impact

- New: `contexia-app/components/bunker/onboarding/OnboardingSection.tsx`.
- Modified: `contexia-app/lib/social-ops-api.ts` (extended, not replaced), `contexia-app/app/app/bunker/page.tsx`, `contexia-app/CLAUDE.md`.
- No backend changes — all endpoints already exist and are already live on `antigravity-app-production-175a`.
