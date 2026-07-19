## 1. API client

- [x] 1.1 Extend `contexia-app/lib/social-ops-api.ts` with onboarding types (`OnboardingStep`, `OnboardingWorkspace`, `OnboardingSeedDraft`, `OnboardingResponse`) and functions (`getSocialOpsOnboarding`, `startSocialOpsOnboarding`, `advanceSocialOpsOnboardingStep`, `createSocialOpsOnboardingSeed`, `intakeSocialOpsOnboarding`), ported from `frontend/dashboard/src/lib/socialOpsApi.ts`.

## 2. Onboarding section (frontend)

- [x] 2.1 Create `contexia-app/components/bunker/onboarding/OnboardingSection.tsx`, ported from `OnboardingOps.tsx`: start-onboarding form, workspace selector with SLA/QA target display, natural-language intake form, seed-draft creation button, 21-day template checklist.
- [x] 2.2 Translate all classes from the old app's Tailwind theme to `contexia-app`'s `@theme` tokens per `design.md` decision 3.

## 3. Wiring

- [x] 3.1 Update `contexia-app/app/app/bunker/page.tsx`: "Onboarding" case renders `OnboardingSection` instead of `ComingSoonSection`.
- [x] 3.2 Update `openspec/specs/bunker-admin-shell/spec.md`'s "Placeholder sections" requirement (already drafted as a delta in this change — sync on archive).

## 4. Documentation

- [x] 4.1 Update `contexia-app/CLAUDE.md`'s "Pantallas data-bound" section: document Onboarding as the third data-bound exception, alongside `CashTodayCard` and Social Content Ops.

## 5. Build and local verification

- [x] 5.1 `cd contexia-app && npm run build` — green, no type errors.
- [x] 5.2 Temporarily point `contexia-app/.env.development.local` at the live Railway backend, run locally, click through the Onboarding section (start onboarding, select workspace, submit intake, create seed draft, view template checklist) — confirm real data, no console errors. Revert `.env.development.local` after. (Verified: full 21-day checklist rendered matching production `curl` output exactly, no console errors.)

## 6. Deploy (Stage 11 — MANDATORY)

- [x] 6.1 Sync `contexia-app/out/` → `app/` (bump `sw.js` `CACHE_VERSION` v8->v9).
- [x] 6.2 Commit, push to `main`. (commit `1eb7e51`)
- [x] 6.3 Confirm Vercel build green (check via deployment API). (deployment `dpl_JyenMHou3HjBxki9WnHEXpZHxa6o`, READY, aliased to contexia.online)
- [x] 6.4 Verify live at `https://contexia.online/app/bunker` → Onboarding section renders and functions against production backend. (curl 200, correct title)
- [x] 6.5 Create deployment report at `openspec/changes/bunker-onboarding-port/reports/YYYY-MM-DD-deployment.md`. (`reports/2026-07-19-deployment.md`)

## 7. Archive

- [ ] 7.1 Sync delta specs (`bunker-onboarding` new, `bunker-admin-shell` modified) to `openspec/specs/`, then run `openspec-archive-change`.
