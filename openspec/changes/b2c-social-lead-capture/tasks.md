# Tasks: b2c-social-lead-capture

**Change:** b2c-social-lead-capture
**Status:** apply

---

## 1. `crm_leads.source` column

- [ ] 1.1 Create migration `00XX_crm_leads_source.sql` — nullable `source` text column, no
      default, no backfill (same additive pattern as `whatsapp-b2b-lead-bridge`'s `lead_type`).
- [ ] 1.2 Do not apply yet — requires explicit founder confirmation like every migration.

## 2. Backend: public, rate-limited capture endpoint

- [ ] 2.1 Write failing tests: unauthenticated request succeeds; IP throttle rejects excess
      requests; repeat phone number within the throttle window is a no-op, not a new lead/message.
- [ ] 2.2 Implement `POST /api/v1/crm/social-capture/partial` (confirm exact path), resolving to
      Cliente Cero, delegating to the same `CrmService` find-or-create `whatsapp-intake` uses —
      no duplicate implementation — stamping `source`.
- [ ] 2.3 Implement the IP + phone-number throttle (in-process or Supabase-backed, to decide
      during implementation — no existing global rate limiter to depend on, confirmed by reading
      `apps/backend/main.py`).
- [ ] 2.4 Tests green.

## 3. First-contact trigger (text only, no voice/Twilio dependency)

- [ ] 3.1 Write failing tests: a new capture sends exactly one WhatsApp message; a repeat capture
      of an already-contacted phone number sends no additional message.
- [ ] 3.2 Wire the trigger to the existing Chatwoot/Taty text-delivery path used elsewhere in the
      codebase — reuse, not a new send mechanism.
- [ ] 3.3 Tests green.

## 4. Frontend: public landing page in `contexia-app/`

- [ ] 4.1 Confirm exact URL path with the founder (open question in design.md).
- [ ] 4.2 Build the form (name, phone, hidden `source` from query string).
- [ ] 4.3 Implement partial-capture on valid-phone-entry (before full form submission) — calls
      the same endpoint as full submission.
- [ ] 4.4 Build check (Next.js).

## 5. Non-goal guards (verify, don't build)

- [ ] 5.1 Confirm by reading the code that this capability never touches
      `taty-voice-outbound-calls`, `hermes-hubspot-poller`, or any B2B path.
- [ ] 5.2 Confirm the orphaned `contexia-wizard/` app is untouched — this change does not fix or
      extend it (flagged separately in design.md, not in scope here).

## 6. Testing sweep

- [ ] 6.1 Full backend test sweep green, zero regressions against main (git-stash comparison,
      same discipline as every other change this session).

## Stage 11. Deploy to Production (MANDATORY)

- [ ] 11.1 Apply migration `00XX_crm_leads_source.sql` in Supabase — founder confirmation required.
- [ ] 11.2 git commit + push to main.
- [ ] 11.3 Vercel build complete (verde ✅) for `contexia-app/`.
- [ ] 11.4 Railway deploy active (backend endpoint).
- [ ] 11.5 Verify end-to-end: a real test submission on the live landing page produces a
      `crm_leads` row with `source` set, and a real WhatsApp message arrives at the test phone
      number within minutes.
- [ ] 11.6 Create report: `openspec/changes/b2c-social-lead-capture/reports/YYYY-MM-DD-deployment.md`.
