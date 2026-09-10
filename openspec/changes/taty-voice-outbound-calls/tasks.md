# Tasks: taty-voice-outbound-calls

**Change:** taty-voice-outbound-calls
**Status:** apply

---

## 1. `taty-followup-cadence` — ships first, no telephony, no consent dependency

- [x] 1.1 Write failing tests: unresponsive `NUEVOS` lead gets the next scripted touch at the
      right day threshold; a lead who replies exits the automated sequence; day-14 completion
      sends no further automated touch.
- [x] 1.2 Define the day-indexed message table (D1/D2/D4/D7/D14) adapted from Dapta's Lead
      Nurture playbook to Renta Natural — text only, no audio requiring `VOICE_OUTBOUND_CALLS_ENABLED`.
      D7's audio-summary idea from the playbook only if `VOICE_ENABLED` (existing, already
      unblocked) is on — otherwise falls back to text.
- [x] 1.3 Implement the cadence check as a new script (`apps/hermes-cadence-poller/` or similar,
      mirroring the existing poller pattern) that reads `crm_leads`, computes cadence position,
      and sends via the existing Chatwoot delivery path — no new send mechanism.
- [x] 1.4 Register Windows Scheduled Task, same pattern already fixed for the Siigo poller
      (PowerShell 5.1-compatible, `cmd /c cd /d <dir> && pythonw.exe main.py` if `.env` is
      loaded relative to cwd).
- [x] 1.5 Tests green. Deploy this piece independently — no reason to wait on the voice pieces
      below.

## 2. Backend: outbound-call trigger endpoint (built dark, `VOICE_OUTBOUND_CALLS_ENABLED=false`)

- [ ] 2.1 Write failing tests: missing `INTERNAL_API_KEY` → 503; caller-supplied phone number is
      ignored in favor of the resolved `crm_leads` number; a `business_interest` lead is refused.
- [ ] 2.2 Implement `POST /internal/voice/outbound-call` (`{lead_id, tenant_id}` only), resolving
      the phone server-side, following the `/internal/*` + `INTERNAL_API_KEY` pattern exactly.
- [ ] 2.3 Twilio account setup (founder action, external to this repo) — Colombian number(s)
      provisioned, credentials placed in Railway env vars only, never in the local bridge.
- [ ] 2.4 Call orchestration service: places the Twilio call, synthesizes the opening via
      VoiceBox using a GENERIC (non-cloned) voice profile by default.
- [ ] 2.5 Tests green.

## 3. STT activation (first real use of `LOCAL_WHISPER_URL`)

- [ ] 3.1 Write failing tests for the transcription call path.
- [ ] 3.2 Point `LOCAL_WHISPER_URL` at a running Whisper instance; wire the call-response
      transcription into the qualification flow.
- [ ] 3.3 Tests green.

## 4. Opening script + qualification flow

- [ ] 4.1 **Before finalizing wording**: check actual Colombian legal requirements for AI
      disclosure on an outbound call (do not assume Dapta's US/EU citations apply) — default to
      disclosing regardless of what this check finds, per the design's risk mitigation.
- [ ] 4.2 Write the opening script: identity + AI disclosure + reason in ≤10 words + question,
      not pitch (adapted from Dapta's opening anatomy).
- [ ] 4.3 Write the qualification flow: max 3 questions, situation→problem→urgency structure.
- [ ] 4.4 Wire call outcome → `CrmService` write path (no new "call outcomes" table) — qualified /
      not-interested / callback-requested / voicemail.
- [ ] 4.5 Voicemail outcome makes the lead eligible for `taty-followup-cadence`, not an automatic
      re-dial.

## 5. Non-goal guards (verify, don't build)

- [ ] 5.1 Confirm by reading the code that no B2B (`lead_type="business_interest"`) lead can ever
      reach the outbound-call endpoint.
- [ ] 5.2 Confirm Twilio credentials exist only in Railway env vars, never in
      `apps/chatwoot-bridge/`.
- [ ] 5.3 Confirm `VOICE_OUTBOUND_CALLS_ENABLED` and `VOICE_ENABLED` are fully independent flags
      — toggling one in tests must not affect the other's behavior.

## 6. Testing sweep

- [ ] 6.1 Full backend + chatwoot-bridge test sweep green, zero regressions against main
      (verify via git-stash comparison, same discipline as every other change this session).

## 7. Phase 1 — internal test calls (Dapta's launch discipline)

- [ ] 7.1 At least 5 people place internal test calls to themselves/each other using the agent.
- [ ] 7.2 Listen to 100% of the test recordings — not just summaries.
- [ ] 7.3 Adjust the prompt/script at least once based on real feedback before proceeding.
- [ ] 7.4 **Founder review-and-approve checkpoint, recorded here** — required before Task 8 starts.

## 8. Phase 2 — small real batch (10-20 calls, Renta Natural leads only)

- [ ] 8.1 Confirm real Twilio per-minute cost for Colombian outbound calls against the founder's
      cost tolerance before placing any real call.
- [ ] 8.2 Place 10-20 real calls to actual Renta Natural leads.
- [ ] 8.3 Listen to all recordings; log abandonment point, duration, and outcome per call.
- [ ] 8.4 **Founder review-and-approve checkpoint, recorded here** — required before scaling to
      Task 9.

## 9. Phase 3 — scale (50-100, then 200-500), weekly listen/adjust cycle

- [ ] 9.1 Scale to 50-100 calls only after Task 8's checkpoint. Weekly: listen to a sample,
      identify the 2 best and 2 worst calls, adjust the script.
- [ ] 9.2 **Founder review-and-approve checkpoint** before scaling to 200-500.
- [ ] 9.3 Scale to 200-500 calls.

## Stage 11. Deploy to Production (MANDATORY, per-piece — see Migration Plan in design.md)

**`taty-followup-cadence` (Task 1) — fully deployed and verified, 2026-09-09/10:**

- [x] 11.1a Migration `0051_crm_leads_cadence.sql` applied to Supabase with explicit founder
      confirmation; verified live (`last_inbound_at`, `cadence_day`, `cadence_completed_at` exist
      on `crm_leads`, correct types, no backfill).
- [x] 11.1b `ContexiaHermesCadencePoller` Windows Scheduled Task registered (via `schtasks.exe`
      directly — `Register-ScheduledTask`/CIM returned "Acceso denegado" in this session, same
      as the Siigo/Gmail pollers earlier), `.env` created matching the existing pollers'
      credentials, dry-run verified against 2 real eligible leads in production.
- [x] 11.1c git commit (`73d5498`) + push to main.
- [x] 11.1d Railway deploy `71c80e02` SUCCESS. `GET /api/v1/health` → 200.
      `POST /internal/cadence/send-touch` → 401 with a wrong key (mounted, auth enforced,
      matches the fail-closed pattern of every other `/internal/*` endpoint).
- [x] 11.1e Report: `openspec/changes/taty-voice-outbound-calls/reports/2026-09-10-cadence-deployment.md`.

**Tasks 2-9 (Twilio/voice) — untouched, still gated (see design.md's Migration Plan):**

- [ ] 11.2 Railway deploy active (backend endpoint, once Tasks 2-4 are ready).
- [ ] 11.3 Verify: a real or simulated `/internal/voice/outbound-call` request with a generic
      voice completes end-to-end against a test lead, with the correct `crm_leads` write.
- [ ] 11.4 **Gate, not yet crossed in this change**: `VOICE_OUTBOUND_CALLS_ENABLED` stays false in
      production until Tatiana's written, dated, revocable consent — scoped explicitly to
      outbound sales calls — exists outside this repo. Do not flip this flag based on a chat
      approval alone.
- [ ] 11.5 Create report for the voice piece once Tasks 2-9 are implemented (separate from the
      cadence report above).
