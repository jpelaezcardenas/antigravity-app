# Task 4 — Frontend: public landing page in `contexia-app/` (b2c-social-lead-capture)

**Status: verified complete.** This dispatch found the implementation already present and
untracked (`git status`: `?? contexia-app/app/renta-natural/`, `?? contexia-app/components/
renta-natural/`, `?? contexia-app/lib/social-capture-api.ts`) — i.e. a prior implementer session
did the real work but never produced a progress report (the "lost dispatch" the leader flagged).
This report replaces the stale BLOCKED one and documents independent verification of what's
already on disk, plus a clean build run.

## What exists (verified by reading each file)

- `contexia-app/app/renta-natural/page.tsx` — Server Component, public landing page, no PWA
  shell (no TopBar/BottomNav), wraps the form in `<Suspense>` (required because the form uses
  `useSearchParams`).
- `contexia-app/app/renta-natural/layout.tsx` — standalone layout (dark gradient background),
  same pattern as `app/flujo-detalle/layout.tsx` — outside the `app/app/` route group.
- `contexia-app/components/renta-natural/RentaNaturalLandingForm.tsx` — `"use client"` form:
  name + WhatsApp phone fields, hidden `source` input populated from `?source=` query string,
  partial-capture fire-once-on-valid-phone via `handlePhoneChange`, full submit on form submit,
  explicit `idle/submitting/done/error` states, no silent fallback to mock data.
- `contexia-app/lib/social-capture-api.ts` — typed client for `POST /api/v1/crm/social-capture/
  partial`. Deliberately does not use `authenticated-fetch.ts` (anonymous visitor, no token) —
  plain `fetch`, matches `API_ENDPOINTS.socialCapturePartial` already wired in `lib/config.ts:24`.
- `contexia-app/lib/utils/phoneValidation.ts` — pure `isValidCapturePhone()`, deliberately
  permissive (>=10 digits) so it's never stricter than the backend's own normalization.
- `contexia-app/CLAUDE.md` — already updated with an "undécima excepción data-bound" section
  documenting `/renta-natural` under "Pantallas data-bound", consistent with how every other
  data-bound exception in this file is documented.

## Task-by-task verification against tasks.md

- **4.1** URL path — confirmed against `design.md` line 121: `~~Exact landing page URL/path~~ —
  DECIDED 2026-09-10 by the founder: contexia.online/renta-natural.` Matches the route folder
  `app/renta-natural/`.
- **4.2** Form — present with name, phone, and hidden `source` field sourced from
  `useSearchParams().get("source")`. Confirmed by reading the component (see above).
- **4.3** Partial-capture — `handlePhoneChange` calls `submitSocialCapture({ whatsappPhone, source
  })` (no `fullName`) the first time `isValidCapturePhone(value)` becomes true, tracked via
  `partialCaptured` state so it only fires once. Full submit calls the same
  `submitSocialCapture` with `fullName` added — same endpoint, per design.md Decision 2 (backend
  throttle makes the repeat call a safe no-op, not a duplicate lead/message — that's Task 2/3's
  responsibility, already implemented and reviewed per `progress/review_b2c_social_task2.md` and
  `progress/review_b2c_social_task3.md`).
- **4.4** Build check — see below.

## TDD note (frontend has no test runner)

`contexia-app/package.json` has no test script and no test-runner dependency (`jest`, `vitest`,
`@testing-library/*` all absent from `devDependencies` — confirmed by reading the file). This is
consistent with the rest of the frontend codebase: no `*.test.ts(x)` files exist anywhere in
`contexia-app/` (checked via `find . -iname "*.test.ts*" -not -path "*/node_modules/*"` — zero
results). `phoneValidation.ts` is deliberately split into a pure, dependency-free function with a
comment noting it's "kept separate... so it stays trivially testable if/when this repo adopts a
frontend test runner (none exists today)." TDD for this task's scope was therefore satisfied via
TypeScript strictness + the build check (4.4), matching the established convention for this
package — introducing a new test framework was out of scope for this task and would be a
dependency addition `contexia-app/CLAUDE.md`'s "No hacer" section explicitly discourages without
a stated need.

## Build check (subtask 4.4)

Command: `cd contexia-app && npm run build`

First few attempts hit transient Windows filesystem errors unrelated to the new code (`ENOENT`
on `.next/required-server-files.json`, `.next/static/.../_buildManifest.js.tmp...`,
`.next/server/pages-manifest.json`, and a stale `.next/lock` from a previously killed build) —
consistent with concurrent tooling/AV activity on this machine rather than a real build defect;
TypeScript compiled cleanly (`Finished TypeScript in ...`) in every attempt, including the failed
ones. After `rm -rf .next` and a clean retry, the build completed successfully:

```
✓ Compiled successfully in 10.8s
  Running TypeScript ...
  Finished TypeScript in 13.6s ...
  Collecting page data using 7 workers ...
  Generating static pages using 7 workers (0/14) ...
✓ Generating static pages using 7 workers (14/14) in 1571ms
  Finalizing page optimization ...

Route (app)
┌ ○ /
├ ○ /_not-found
├ ○ /app/bunker
├ ○ /app/config
├ ○ /app/fiscal
├ ○ /app/flujo-detalle
├ ○ /app/overview
├ ○ /app/patrimonio
├ ○ /app/radar
├ ○ /crear-empresa-wizard
├ ○ /flujo-detalle
├ ○ /manifest.webmanifest
└ ○ /renta-natural

ƒ Proxy (Middleware)
○  (Static)  prerendered as static content
```

`/renta-natural` is present in the route list as a statically-exported page, alongside every
pre-existing route (no regressions to other pages). `out/` was **not** synced to `app/` (repo
root) — per instructions, that's a separate deploy step, not part of this task.

## Files touched by this dispatch

None — no code was written or modified. This dispatch consisted entirely of verification: reading
the already-implemented files, confirming task-by-task compliance with `tasks.md`/`design.md`,
running a clean `npm run build`, and writing this report to replace the stale BLOCKED one.
`tasks.md` checkboxes 4.1-4.4 were already checked off (with citations) by the same earlier,
report-less session — verified those citations point to real files and are accurate; left as-is.

## Open issues / non-blocking notes

- No automated test coverage exists for `RentaNaturalLandingForm.tsx` or `social-capture-api.ts`
  because `contexia-app` has no test runner at all (repo-wide gap, not specific to this task).
- Backend Task 2/3 (the endpoint + throttle + WhatsApp trigger this form depends on) are already
  implemented and independently reviewed (APPROVED) per `progress/review_b2c_social_task2.md` and
  `progress/review_b2c_social_task3.md` — not re-verified here, out of this task's scope.
- Stage 11 (deploy) and Task 6 (full backend test sweep) remain unstarted, per `tasks.md`.
