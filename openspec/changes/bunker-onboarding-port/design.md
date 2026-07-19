## Context

`OnboardingOps.tsx` lives in the same old, unlinked Vite dashboard (`frontend/dashboard/src/components/ops/`) that `bunker-social-content-ops-port` already ported from. Unlike the "legacy" Calendario/Borradores tabs from that change (which queried a stale, undocumented Supabase project), `OnboardingOps.tsx` calls the canonical `socialOpsApi.ts` functions throughout — same pattern as `IdeasOps.tsx`/`MetricasDashboard.tsx`, which were ported as-is with no rework needed.

The backend side of this ("Onboarding 21D": kick-off, credential capture, historical sync, QA gate, handoff, shadow audit, go-live) is documented nowhere in `AGENTES.md`'s Tier 3 catalog explicitly, but its endpoints (`/social-ops/onboarding*`) live in the same `apps/backend/presentation/social_ops_endpoints.py` file, behind the same `SOCIAL_OPS_CANONICAL` flag already flipped to `true` in production. `GET /social-ops/onboarding` was verified live via `curl` before writing this proposal.

## Goals / Non-Goals

**Goals:**
- Make the Búnker's Onboarding section call the real, already-live backend — no new mock data.
- Match `contexia-app`'s design tokens throughout, consistent with the Social Content Ops port.
- Preserve the natural-language intake + seed-draft + 21-day checklist workflow exactly as implemented.

**Non-Goals:**
- No backend changes — every endpoint this section needs already exists and is live.
- No changes to Social Content Ops, CRM/Ventas, or the Infrastructure Dashboard.
- Not resolving Agentic OS's Hermes-locality question — tracked separately, out of scope here.

## Decisions

1. **Extend, don't duplicate, `social-ops-api.ts`.** The onboarding functions are added to the existing file (same backend, same `API_BASE_URL`), not a new API client — avoids two files fetching the same base URL with different conventions.
2. **One component, `OnboardingSection.tsx`.** `OnboardingOps.tsx` is single-file (~290 lines) with no internal sub-tabs — no need to split into multiple files the way Social Content Ops was (which had 9 distinct tabs).
3. **Token translation**: same mapping table as Social Content Ops (`bg-primary`→`bg-primary-container`/`bg-primary`, `text-obsidian`→`text-on-primary`, `text-ink`→`text-on-surface`, `text-muted`→`text-on-surface-variant`, `border-outline/40`→`border-outline-variant/40`, `rose`/`amber`/`emerald`→`status-critical`/`status-warning`/`status-success`).
4. **Third data-bound exception**, documented in `contexia-app/CLAUDE.md` alongside `CashTodayCard` and Social Content Ops — this section both reads and writes (starts onboarding, submits intake, creates seed drafts), same as Social Content Ops, not read-only like Caja Real.
5. **Update `bunker-admin-shell`'s spec**: the "Placeholder sections" requirement currently lists Onboarding as a placeholder example; this change updates that scenario since Onboarding will no longer be one.

## Risks / Trade-offs

- [A third data-bound exception continues eroding `contexia-app`'s "mock-first, simple" premise] → Mitigation: same tightly-scoped pattern each time (real, already-live endpoint only, no new backend surface), documented explicitly each time.
- [Onboarding workspace data is currently empty in production (no real onboarding started yet)] → Mitigation: the component's own loading/empty states (already implemented in the source) carry over unchanged — no crash, no blank screen.

## Migration Plan

1. Extend `contexia-app/lib/social-ops-api.ts` with onboarding types/functions.
2. Build `OnboardingSection.tsx`.
3. Wire into `contexia-app/app/app/bunker/page.tsx`.
4. Update `bunker-admin-shell`'s "Placeholder sections" scenario (delta spec in this change).
5. Build, verify locally against the live Railway backend (temporary `.env.development.local` swap, reverted after), sync `contexia-app/out/` → `app/`, commit, push, verify Vercel, verify live, Stage 11 report, archive.
6. Rollback: revert the commit; Vercel redeploys the prior (placeholder) build automatically — no backend or data to roll back.

## Open Questions

- None blocking.
