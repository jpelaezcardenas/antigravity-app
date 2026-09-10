## Why

Contexia is in peak Renta Natural (persona natural) tax-filing season and needs to convert more
leads faster. Two Dapta operational playbooks (`Playbook Lead Nurture IA.pdf`, `Playbook Apertura
en Llamadas IA.pdf`) quantify a real gap: leads that don't respond to Taty's first WhatsApp
message get no systematic follow-up today, and Dapta's own data shows 18-26% of annual closes come
from leads that didn't convert in the first 14 days. The founder approved adding outbound voice
calling to Taty (Twilio as carrier) and approved using Tatiana's cloned voice for it, "tal cual
usan el playbook en Dapta" (2026-09-09).

**Important caveat that shapes this proposal's scope**: `ARCHITECTURE.md` Decisión #24 blocks
enabling the cloned-voice flag on a written, dated, revocable consent from Tatiana Barbosa, stored
outside the repo — a verbal approval relayed in chat does not satisfy that. This change designs
and builds the full capability with `VOICE_ENABLED`-style flags OFF by default (dark launch, same
pattern as `voicebox-local-voice-adoption`), so implementation is not blocked, but the cloned-voice
path cannot go live until that document exists.

## What Changes

- New outbound-call trigger: a webhook-style internal endpoint (own contract, not Dapta's — Dapta
  doesn't publish one) that originates a Twilio call to a lead, following the same
  `INTERNAL_API_KEY` fail-closed pattern as the Siigo/Gmail/HubSpot pollers (Decisión #22).
- Voice pipeline for the call: TTS via the existing local VoiceBox provider (Decisión #24) —
  cloned voice gated behind a NEW flag separate from `VOICE_ENABLED` (WhatsApp voice notes), so
  enabling one never silently enables the other; STT via VoiceBox's currently-dormant
  `LOCAL_WHISPER_URL` path, activated for the first time.
- A 14-day, text-first follow-up cadence for WhatsApp leads that don't respond, adapting Dapta's
  Lead Nurture playbook to Contexia's existing `crm_leads`/`taty_lead_router.py` — does NOT depend
  on the voice/telephony piece and can ship first, independently.
- A phased rollout plan (clean single-purpose agent → internal test calls → small real batches
  10-20 → 50-100 → 200-500) adapting Dapta's launch playbook, scoped to Renta Natural (B2C) leads
  only — never triggered for B2B `crm_leads.lead_type="business_interest"` leads without a
  separate decision.
- Call-opening script structure (identity + AI disclosure + reason in ≤10 words + question-not-pitch)
  and a max-3-question qualification flow, adapted from Dapta's opening anatomy — **AI disclosure
  requirement to be verified against actual Colombian law before wording is finalized, not assumed
  from Dapta's US/EU-centric legal citations (Texas SB 140, EU AI Act Art. 50)**.

## Capabilities

### New Capabilities
- `taty-voice-outbound-calls`: originates outbound voice calls to Renta Natural leads via Twilio,
  synthesizes speech locally (VoiceBox), transcribes responses (VoiceBox STT), and feeds the
  qualification result back into `crm_leads`.
- `taty-followup-cadence`: 14-day multichannel (text-first) follow-up sequence for WhatsApp leads
  who don't respond to Taty's first message, independent of the voice capability.

### Modified Capabilities
(none — this is additive; does not change existing WhatsApp text behavior)

## Impact

- Backend: new presentation endpoint under `/internal/*` (Twilio call trigger), new service for
  call orchestration, extension of `voice_safety.py` with a second, independent gate for the
  cloned-voice path.
- `apps/chatwoot-bridge/`: STT activation (`LOCAL_WHISPER_URL`), no change to existing WhatsApp
  text/voice-note delivery.
- New external dependency: Twilio (account, Colombian number(s), approved by founder 2026-09-09).
- No change to `hermes-hubspot-poller` sync rules, no change to B2B `whatsapp-b2b-lead-bridge`
  behavior.
- **Blocking, non-code prerequisite before the cloned-voice flag is ever enabled**: written, dated,
  revocable consent from Tatiana Barbosa, stored outside the repo (same requirement as Decisión
  #24, restated here because this change reuses her cloned voice for a new use case — outbound
  sales calls — that the original consent scope may not have covered).
