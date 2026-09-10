# Tasks: b2c-social-lead-capture

**Change:** b2c-social-lead-capture
**Status:** apply

---

## 1. `crm_leads.source` column

- [x] 1.1 Create migration `0052_crm_leads_source.sql` — nullable `source` text column, no
      default, no backfill (same additive pattern as `whatsapp-b2b-lead-bridge`'s `lead_type`).
- [x] 1.2 Applied to Supabase (`kpynymwghfwshvcvevxq`) 2026-09-09 with explicit founder
      confirmation. Verified live: `crm_leads.source` is `text`, `is_nullable = 'YES'`.

## 2. Backend: public, rate-limited capture endpoint

- [x] 2.1 Write failing tests: unauthenticated request succeeds; IP throttle rejects excess
      requests; repeat phone number within the throttle window is a no-op, not a new lead/message.
- [x] 2.2 Implement `POST /api/v1/crm/social-capture/partial` (confirm exact path), resolving to
      Cliente Cero, delegating to the same `CrmService` find-or-create `whatsapp-intake` uses —
      no duplicate implementation — stamping `source`.
- [x] 2.3 Implement the IP + phone-number throttle (in-process or Supabase-backed, to decide
      during implementation — no existing global rate limiter to depend on, confirmed by reading
      `apps/backend/main.py`).
- [x] 2.4 Tests green.

      **Note (2026-09-10):** checkboxes 2.1-2.4 were marked retroactively per the reviewer's
      non-blocking "Required changes" note in `progress/review_b2c_social_task2.md` (verdict
      APPROVED, 18 tests independently re-run by the reviewer, `18 passed in 6.13s`). No new
      evidence generated here — this only closes the documentation gap the reviewer flagged.

## 3. First-contact trigger (text only, no voice/Twilio dependency)

- [x] 3.1 Write failing tests: a new capture sends exactly one WhatsApp message; a repeat capture
      of an already-contacted phone number sends no additional message.
- [x] 3.2 Wire the trigger to the existing Chatwoot/Taty text-delivery path used elsewhere in the
      codebase — reuse, not a new send mechanism.
- [x] 3.3 Tests green. Approved per progress/review_b2c_social_task3.md (APPROVED, 21 tests independently re-run).

## 4. Frontend: public landing page in `contexia-app/`

- [x] 4.1 Confirm exact URL path with the founder (open question in design.md). Confirmed
      2026-09-10: `contexia.online/renta-natural`. See `design.md`'s "Open Questions".
- [x] 4.2 Build the form (name, phone, hidden `source` from query string). See
      `contexia-app/components/renta-natural/RentaNaturalLandingForm.tsx`.
- [x] 4.3 Implement partial-capture on valid-phone-entry (before full form submission) — calls
      the same endpoint as full submission. Fires once, the first time the phone number becomes
      valid (`lib/utils/phoneValidation.ts`); full submission calls the same endpoint again with
      `full_name` — safe no-op on the backend's phone throttle.
- [x] 4.4 Build check (Next.js). `npm run build` passes; `/renta-natural` statically exported.
      See `progress/impl_b2c_social_task4.md` for command output.

## 5. Non-goal guards (verify, don't build)

- [x] 5.1 Confirm by reading the code that this capability never touches
      `taty-voice-outbound-calls`, `hermes-hubspot-poller`, or any B2B path. Verified 2026-09-09
      via grep — see `progress/impl_b2c_social_task5.md`.
- [x] 5.2 Confirm the orphaned `contexia-wizard/` app is untouched — this change does not fix or
      extend it (flagged separately in design.md, not in scope here). Verified 2026-09-09 via
      `git status`/`git log` — see `progress/impl_b2c_social_task5.md`.

## 6. Testing sweep

- [x] 6.1 Full backend test sweep green, zero regressions against main (git-stash comparison,
      same discipline as every other change this session). See
      `progress/impl_b2c_social_task6.md` — HEAD and stashed-main baseline both produce
      35 failed, 120 skipped, 3 errors, byte-identical failure list; HEAD has 23 more passed
      tests than baseline (1243 vs 1220) accounted for entirely by this change's new test
      files.

## Stage 11. Deploy to Production (MANDATORY)

- [x] 11.1 Migration `0052_crm_leads_source.sql` applied to Supabase 2026-09-09 with explicit
      founder confirmation (same event as Task 1.2 above).
- [x] 11.2 git commit + push to main (`1ec9d2b`, then `77f47b9` fixing a missing `vercel.json`
      rewrite discovered during verification — see report).
- [x] 11.3 Vercel build complete (verde ✅) — deployment `dpl_FFQieg1PM663DqVB1Zp3pXy2xFbW`,
      state `READY`, target `production`.
- [x] 11.4 Railway deploy active — `/api/v1/health` returns 200.
- [x] 11.5a Verified: `POST /api/v1/crm/social-capture/partial` against the live Railway backend
      creates a real `crm_leads` row with `source` set (smoke-tested with phone `573000000000`,
      row created then deleted immediately after — see report). `contexia.online/renta-natural`
      returns 200 with the real form content (confirmed post-fix, not the pre-fix 404).
- [ ] 11.5b **NOT verified**: an actual WhatsApp message arriving at a real phone number. The
      smoke test above used a fake test number specifically to avoid sending a real WhatsApp
      message without founder authorization — same caution `whatsapp-b2b-lead-bridge` applied.
      Founder action needed: submit the live landing page with a real phone number (or confirm
      it's fine to test with a specific number) to close this loop end-to-end.
- [x] 11.6 Create report: `openspec/changes/b2c-social-lead-capture/reports/2026-09-10-deployment.md`.
