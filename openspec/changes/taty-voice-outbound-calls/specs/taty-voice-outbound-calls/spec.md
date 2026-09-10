## ADDED Requirements

### Requirement: Outbound calls are triggered via an internal, fail-closed endpoint
The system SHALL expose `POST /internal/voice/outbound-call`, authenticated with the same
`X-Internal-Api-Key` fail-closed pattern as the Siigo/Gmail/HubSpot pollers (Decisión #22),
accepting only `{lead_id, tenant_id}` — never a phone number supplied directly by the caller. The
lead's phone number SHALL be resolved server-side from `crm_leads`.

#### Scenario: Missing internal key rejects the call trigger
- **WHEN** `INTERNAL_API_KEY` is not configured
- **THEN** `POST /internal/voice/outbound-call` returns 503 for every caller

#### Scenario: A caller cannot supply an arbitrary phone number
- **WHEN** a request includes a `phone` field directly
- **THEN** the field is ignored; the number used is always the one on the resolved `crm_leads` row

#### Scenario: A lead outside Renta Natural (B2C) is rejected
- **WHEN** the resolved lead has `crm_leads.lead_type = "business_interest"`
- **THEN** the endpoint refuses the call with an explicit error, never silently placing a B2B
  outbound call under this capability

### Requirement: Call origination uses Twilio, orchestrated from the backend
The system SHALL originate the PSTN call via Twilio from the backend (Railway), never from the
local Chatwoot bridge. Twilio credentials SHALL live only in Railway environment variables.

#### Scenario: Twilio credentials are never present in the local bridge
- **WHEN** `apps/chatwoot-bridge/` configuration is inspected
- **THEN** it contains no Twilio account SID, auth token, or API key

### Requirement: Call audio is synthesized locally; only finished audio crosses to Twilio
The system SHALL synthesize the agent's speech via the local VoiceBox provider, and SHALL
transmit only the finished audio bytes to Twilio — the same trust boundary already crossed by
Taty's existing WhatsApp voice notes (Decisión #24). Transcription of the lead's spoken responses
SHALL use VoiceBox's STT path (`LOCAL_WHISPER_URL`), activated for the first time by this change.

#### Scenario: No client-identifying text is sent to Twilio beyond the call itself
- **WHEN** a call is placed
- **THEN** Twilio receives only the destination number and the synthesized audio stream — no
  separate transcript or lead metadata payload

### Requirement: The cloned voice is gated by its own flag, independent of VOICE_ENABLED
The system SHALL introduce `VOICE_OUTBOUND_CALLS_ENABLED`, a flag wholly independent of the
existing `VOICE_ENABLED` (WhatsApp voice notes). Enabling one SHALL NOT enable the other. With
`VOICE_OUTBOUND_CALLS_ENABLED=false` (the default), the call flow SHALL function end-to-end using
a non-cloned, generic VoiceBox voice profile.

#### Scenario: Default configuration never uses the cloned voice
- **WHEN** `VOICE_OUTBOUND_CALLS_ENABLED` is unset or false
- **THEN** any outbound call synthesizes speech with a generic voice profile, never Tatiana's
  cloned voice

#### Scenario: Enabling WhatsApp voice notes does not enable outbound calls
- **WHEN** `VOICE_ENABLED=true` and `VOICE_OUTBOUND_CALLS_ENABLED` is unset
- **THEN** outbound calls still use the generic voice; WhatsApp voice notes are unaffected by this
  capability

### Requirement: The opening script discloses AI identity and asks before pitching
Every call's opening SHALL state the agent's identity, disclose that it is an AI, state the reason
for the call in 10 words or fewer, and ask a question before presenting any offer — never opening
with a sales pitch.

#### Scenario: The opening always discloses AI identity
- **WHEN** an outbound call connects
- **THEN** the first turn includes an explicit statement that the caller is an AI assistant

#### Scenario: The opening asks before pitching
- **WHEN** the opening script is inspected
- **THEN** its first question comes before any mention of price, plan, or offer

### Requirement: Qualification is capped at 3 questions per call
A single outbound call SHALL ask at most 3 qualification questions, following a
situation→problem→urgency structure. It SHALL NOT continue past 3 questions in one call.

#### Scenario: A fourth question is never asked in the same call
- **WHEN** 3 qualification questions have been asked and answered
- **THEN** the call proceeds to a close or handoff, not a fourth question

### Requirement: Call outcomes feed back into crm_leads via the existing CRM write path
A completed call's outcome (qualified / not-interested / callback-requested / voicemail) SHALL be
written to `crm_leads` through the existing `CrmService` methods already used by
`taty_lead_router.py` — never a separate "call outcomes" table.

#### Scenario: A qualified call advances the lead through the existing stage machinery
- **WHEN** a call outcome is "qualified"
- **THEN** the lead's `crm_leads` row is updated via `CrmService`, using the same stage-transition
  rules WhatsApp-sourced qualification already follows

#### Scenario: A voicemail outcome does not silently retry indefinitely
- **WHEN** a call reaches voicemail
- **THEN** the outcome is recorded and the lead becomes eligible for the follow-up cadence
  (`taty-followup-cadence`), not an immediate automatic re-dial loop

### Requirement: Rollout follows staged batches with a manual review gate per phase
The system SHALL NOT progress from internal test calls to real leads, nor from one real batch
size to the next larger one, without an explicit founder review-and-approve checkpoint recorded
in the change's task tracking. Batch sizes SHALL follow 10-20 → 50-100 → 200-500 real calls,
Renta Natural leads only.

#### Scenario: Scaling to the next batch requires a recorded approval
- **WHEN** a batch phase completes
- **THEN** progression to the next phase requires an explicit recorded founder approval, not an
  automatic timer or volume threshold
