## Context

Founder approved (2026-09-09) two things: Twilio as the outbound telephony carrier, and reusing
Tatiana's cloned voice for the calls "tal cual usan el playbook en Dapta". Prior research (this
session, against `docs.dapta.ai` live via WebFetch) established that Dapta itself assembles Twilio
(carrier) + Deepgram (STT) + ElevenLabs (TTS) + OpenAI/Claude (LLM) under its own orchestration —
it does not resell a third-party agent platform, and it does not publish its MCP tool contract or
its notetaker/database schema, so nothing here is "ported" from Dapta; it's an independent design
informed by the same playbooks Dapta publishes (`Playbook Lead Nurture IA.pdf`, `Playbook Apertura
en Llamadas IA.pdf`), read in full this session.

Of the 4 non-carrier pieces evaluated earlier, 3 already have a home in this codebase:
- LLM: the existing free-tier failover cascade (Decisión #7) + `TatyAgentService`.
- TTS: VoiceBox, already wired for Taty's WhatsApp voice notes (Decisión #24), `VOICE_ENABLED=false`.
- Orchestration/trigger: the established `/internal/*` + `INTERNAL_API_KEY` fail-closed pattern
  (Decisión #22), already used by 3 pollers.
Only the carrier (Twilio) and STT (VoiceBox's dormant `LOCAL_WHISPER_URL`, never activated) are
new ground.

## Goals / Non-Goals

**Goals:**
- Let Taty place outbound qualification/follow-up calls to Renta Natural leads, using the founder-
  approved Twilio + cloned-voice combination, but architected so the cloned-voice path cannot go
  live before its own written consent exists.
- Ship the 14-day text-first follow-up cadence (Dapta's Lead Nurture playbook) independently of
  the voice piece — it needs no telephony and can close a real, quantified gap immediately.
- Follow Dapta's phased-launch discipline (clean agent → internal tests → small real batches →
  scale) so a bad opening script doesn't burn real leads before it's caught.

**Non-Goals:**
- Not building a Dapta-equivalent no-code platform, MCP server, or multi-tenant agent builder —
  this is one purpose-built call flow for one use case (Renta Natural qualification/follow-up).
- Not applying this to B2B leads (`crm_leads.lead_type="business_interest"`) — out of scope, a
  separate decision if ever wanted.
- Not reusing Tatiana's cloned voice for anything beyond what her (still-pending) written consent
  actually covers — if that consent is scoped to WhatsApp voice notes only, this change needs its
  own, separately scoped consent, not an assumption that one document covers both.
- Not deciding AI-disclosure wording from Dapta's US/EU legal citations — Colombian law must be
  checked before the opening script is finalized (flagged as an open question below).

## Decisions

**1. Twilio integration lives in the backend (Railway), not the local bridge.**
Unlike TTS (VoiceBox, local-only per Decisión #24's soberanía-de-datos rule), placing a PSTN call
is not itself a data-sovereignty-sensitive operation the way processing a client's cloned voice or
financial data is — the call's *audio* is synthesized locally and only the resulting audio bytes
(same trust boundary text already crosses) go to Twilio via the backend. Twilio's own API keys
live in Railway env vars, same posture as any other backend integration secret.
Alternative considered: originate the call from the local machine directly against Twilio — rejected,
because Railway already owns outbound HTTP/webhook responsibilities for every other external
integration in this repo (Wompi, Chatwoot delivery, Gmail/Siigo ingestion triggers), and splitting
that pattern for just this one integration adds an inconsistent second egress path with no benefit.

**2. A second, independent flag gates the cloned-voice path — never conflated with `VOICE_ENABLED`.**
`VOICE_ENABLED` (backend) and its bridge counterpart already gate WhatsApp voice notes under the
Decisión #24 consent. This change introduces `VOICE_OUTBOUND_CALLS_ENABLED` (backend) as a wholly
separate flag. Rationale: the founder's message approves reusing the cloned voice "tal cual",
but the *scope* of Tatiana's actual written consent (once it exists) may or may not cover outbound
sales calls specifically — a single shared flag would silently extend one consent's scope to a
use case it was never asked about. Two flags means each can be turned on only when its own written
consent authorizes it.
Alternative considered: one flag reused as-is — rejected for the reason above; it also means this
change's own code can ship and be tested end-to-end (with a non-cloned/generic voice, or muted in
staging) without needing to wait on the consent document, which is exactly the "dark launch"
pattern `voicebox-local-voice-adoption` already established as acceptable.

**3. STT activation reuses `LOCAL_WHISPER_URL`, not a new provider.**
The bridge already has this config field, documented as "a placeholder, unused" (ARCHITECTURE.md
Decisión #24, "Fuera de alcance"). This change is the first to actually point it at a running
Whisper instance and wire the transcription call — no new STT dependency, no new vendor evaluation
needed, consistent with the "3 of 4 already free" finding from the earlier research pass.

**4. The call-trigger endpoint is Contexia's own contract, not a port of Dapta's.**
Confirmed this session (via WebFetch against `docs.dapta.ai/dapta-mcp/tools-reference.md`): Dapta
does not publish a tool/parameter schema for its MCP or its Flow Studio webhook trigger — "the docs
don't define a single, fixed JSON schema." There is nothing to port. The new endpoint follows this
repo's own established shape: `POST /internal/voice/outbound-call` behind `INTERNAL_API_KEY`,
payload `{lead_id, tenant_id}` (never a free-form phone number typed by a caller — always resolved
server-side from the lead record, closing the kind of spoofing gap Decisión #16 already fixed once
for Taty's WhatsApp endpoint).

**5. Qualification result feeds back into the same `crm_leads`/`taty_lead_router.py` machinery
Track A (`whatsapp-b2b-lead-bridge`) already established**, not a parallel table. A completed
call's outcome (qualified / not-interested / callback-requested / voicemail) writes to
`crm_leads.stage`/`last_message` through the existing `CrmService` methods — no new schema for
"call outcomes" distinct from what a WhatsApp message already produces, since from the CRM's
perspective a qualified lead is a qualified lead regardless of channel.

**6. The 14-day follow-up cadence (`taty-followup-cadence`) ships as its own independent piece,
with no telephony dependency.**
Dapta's Lead Nurture playbook's cadence is channel-agnostic in principle (call/WhatsApp/email);
Contexia's version for this season is WhatsApp/text-only — no voice, no Twilio, no new consent
needed. A new scheduled job (same Windows Task Scheduler pattern as the pollers) checks
`crm_leads` for leads whose last inbound message is >N hours old and stage is still `NUEVOS`, and
sends the next scripted touch per the day-by-day table Dapta's playbook documents (adapted: D0
already covered by Taty's real-time reply; D1/D2 WhatsApp reopen; D4 WhatsApp value-add; D7 WhatsApp
audio summary — audio requires `VOICE_ENABLED`, already live and unblocked, not the new cloned-voice
flag; D14 WhatsApp "breakup" message). This can ship and go live before the voice-call piece, since
it has no new external dependency and no consent question.

## Risks / Trade-offs

- **[Risk]** AI-disclosure legal requirement assumed from Dapta's playbook (Texas SB 140, EU AI
  Act) may not reflect Colombian law. → **Mitigation**: task explicitly requires checking Colombian
  regulation (Superintendencia de Industria y Comercio / Habeas Data framework already governs
  Contexia elsewhere) before finalizing the opening script; ship with an explicit "soy un asistente
  de inteligencia artificial" disclosure by default regardless (safest default, not contingent on
  the legal check's outcome).
- **[Risk]** Outbound calling to real phone numbers is inherently harder to "undo" than a text
  message — a bad opening script burns real leads' goodwill. → **Mitigation**: Dapta's own phased
  rollout (clean agent, 5+ internal test calls, 3+ review rounds, then 10-20 real calls before
  scaling) is adopted as-is; `tasks.md` gates each phase behind a manual "founder reviewed and
  approved recordings" checkpoint, not an automatic timer.
- **[Risk]** The cloned-voice consent may never arrive, or may arrive scoped narrower than "any
  Contexia use". → **Mitigation**: the whole call-qualification flow works with a *non-cloned*
  generic TTS voice from day one (VoiceBox supports multiple voice profiles) — the cloned voice is
  a swap-in enhancement behind its own flag, not a blocking dependency for anything else in this
  change.
- **[Trade-off]** Twilio cost is real and recurring once past trial credit — no free tier for
  production outbound calling to Colombian numbers. → Accepted by the founder's approval; `tasks.md`
  requires confirming actual per-minute cost against Twilio's published rates before scaling past
  the small-batch phase, not assuming a number.

## Migration Plan

1. `taty-followup-cadence` (no telephony, no consent question) — ship first, independently.
2. Twilio account setup + Colombian number provisioning (founder action, external to this repo).
3. Backend: `/internal/voice/outbound-call` endpoint, call orchestration service, `crm_leads`
   feedback wiring — built and tested with a generic (non-cloned) VoiceBox voice, `VOICE_OUTBOUND_
   CALLS_ENABLED=false` by default.
4. STT activation (`LOCAL_WHISPER_URL`) in the bridge.
5. Internal test calls (5+, per Dapta's checklist) with the generic voice — script iteration.
6. Small real batches (10-20 → 50-100 → 200-500), generic voice, Renta Natural leads only.
7. **Gate, not yet crossed**: once Tatiana's written/dated/revocable consent exists (scoped
   explicitly to outbound sales calls, not assumed from any prior WhatsApp-voice-note consent),
   `VOICE_OUTBOUND_CALLS_ENABLED` may be flipped — a config change, not a new deploy, same pattern
   as `VOICE_ENABLED`.

Rollback: both flags are additive env vars; disabling either reverts to current WhatsApp-only
behavior with zero data migration.

## Open Questions

- Exact Colombian legal requirement for AI-disclosure on an outbound sales call (defaulting to
  disclose regardless, per the risk mitigation above, pending confirmation this isn't itself
  insufficient for some other reason).
- Whether Tatiana's eventual consent, when it exists, should be scoped per-use-case (WhatsApp
  notes vs. outbound calls, requiring two documents) or as one document covering both — a
  question for her and the founder, not decided here.
- Real Twilio per-minute cost for Colombian outbound calls, to confirm against the founder's cost
  tolerance before committing to the 200-500 batch phase.
