# Review — task 4 (b2c-social-lead-capture: Frontend public landing page)

**Verdict:** APPROVED

## Independent verification performed

1. **Canonical source only, `app/` untouched (CLAUDE.md §9 hard rule).**
   `git status --porcelain` on the touched paths shows only new files under
   `contexia-app/app/renta-natural/`, `contexia-app/components/renta-natural/`,
   `contexia-app/lib/social-capture-api.ts`, `contexia-app/lib/utils/phoneValidation.ts`, and a
   modified `contexia-app/CLAUDE.md`. `git status --porcelain app/` and `git diff --stat app/`
   against repo root both returned empty — `app/` build artifact was not hand-edited.

2. **Endpoint contract cross-checked against real backend code, not just the report's prose.**
   - Frontend: `contexia-app/lib/config.ts:24` →
     `socialCapturePartial: ${API_BASE_URL}/api/v1/crm/social-capture/partial`.
   - Backend: `apps/backend/presentation/router.py:94` mounts
     `social_capture_router` at prefix `/crm` (unconditional, no feature flag), and
     `apps/backend/presentation/social_capture_endpoints.py:55` defines
     `@router.post("/social-capture/partial")` → confirmed full path
     `/api/v1/crm/social-capture/partial` matches exactly.
   - Request body fields (`whatsapp_phone`, `full_name`, `source`) in
     `contexia-app/lib/social-capture-api.ts` match `SocialCapturePartialRequest` in the backend
     exactly. Response fields (`is_new`, `throttled_repeat`) match what the endpoint returns on
     the throttled-repeat path (`social_capture_endpoints.py:80`); the create/found path returns
     `get_crm_service().whatsapp_intake(...)`'s result, which the frontend only reads `is_new`/
     `throttled_repeat` from — extra fields are harmlessly ignored, no contract break.

3. **Build re-run independently** (`cd contexia-app && rm -rf .next && npm run build`), not
   accepted from the report. Result: `Compiled successfully`, TypeScript clean, static export
   route list includes `/renta-natural` alongside all pre-existing routes, no regressions. `out/`
   was not synced to `app/` — correctly deferred to a later Stage 11 deploy step, not part of
   this task.

4. **Partial-capture-once / full-submit logic** (`RentaNaturalLandingForm.tsx`) matches tasks.md
   4.3: `handlePhoneChange` fires `submitSocialCapture` exactly once, gated by `partialCaptured`
   state, the first time `isValidCapturePhone(value)` becomes true, without `fullName`. Full
   `handleSubmit` re-sends to the same endpoint with `fullName` included. Relies on the backend's
   phone throttle (Task 2/3, already approved) to make the second call a safe no-op — correctly
   scoped, not re-implemented client-side.

5. **No fabricated/mocked data paths.** No hardcoded success states — `submitState` only becomes
   `"done"` after a real `await submitSocialCapture(...)` resolves; failures set `"error"` with
   the real message. Partial-capture failures are silently swallowed by design (best-effort
   background call, does not block typing) — reasonable, does not fake a success state to the
   user. `phoneValidation.ts` is a pure client-side gate only, explicitly documented as
   deliberately permissive so it can never be stricter than the backend's real validation
   (`_normalize_whatsapp_phone`) — no invented business logic.

6. **`contexia-app/CLAUDE.md` update confirmed present on disk** (re-read fresh, not trusted from
   a stale diff): line 7's data-bound exception list includes `/renta-natural`, and the "undécima
   excepción data-bound" section (`grep -n "renta-natural"` → lines 7, 237, 239, 242) documents
   the new screen consistently with the file's existing pattern for prior exceptions. Note: a
   stale system-reminder briefly implied this file had reverted to an older state without the
   section — a fresh `Read` and `grep` immediately after showed the current section is present;
   this was reminder noise, not an actual revert, and is not a review finding.

## Checkpoints

- C1 (canonical source, no hand-edited `app/`): [x]
- C2 (endpoint contract matches real backend): [x]
- C3 (build independently verified, `/renta-natural` in route output): [x]
- C4 (partial-capture-once / full-submit logic matches tasks.md 4.3): [x]
- C5 (no fabricated/mocked data paths): [x]
- C6 (`contexia-app/CLAUDE.md` genuinely updated): [x]
- Docs-sync (ARCHITECTURE.md/CLAUDE.md kept current with the new container-level surface): [x] —
  `contexia-app/CLAUDE.md` documents the new data-bound exception; no root `ARCHITECTURE.md`
  container change was introduced by this task (endpoint/router wiring was Task 2, already
  reviewed separately).

## tasks.md accuracy

Task 4 checkboxes (4.1–4.4) were already checked by the implementer's prior session; this review
confirms all four citations point to real, verified work — accurate, no correction needed.

## Required changes

None.
