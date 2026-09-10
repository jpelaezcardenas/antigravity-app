## ADDED Requirements

### Requirement: Unresponsive WhatsApp leads receive a 14-day scheduled follow-up sequence
The system SHALL identify `crm_leads` rows whose `stage` is still `NUEVOS` and whose last inbound
message is older than a configured threshold, and SHALL send the next scripted WhatsApp touch per
a day-indexed table (D1, D2, D4, D7, D14), adapted from Dapta's Lead Nurture cadence to Renta
Natural. This requirement has no dependency on `taty-voice-outbound-calls` and SHALL function with
`VOICE_OUTBOUND_CALLS_ENABLED` and `VOICE_ENABLED` both false.

#### Scenario: A lead silent for the configured threshold receives the next scripted touch
- **WHEN** a `NUEVOS` lead's last inbound message exceeds the threshold for its current cadence
  day
- **THEN** the next scripted WhatsApp message for that day is sent, and the lead's cadence
  position advances

#### Scenario: A lead who responds exits the automated cadence
- **WHEN** a lead sends any inbound message during the cadence
- **THEN** the automated sequence stops advancing that lead; normal `route_lead_message` handling
  resumes

#### Scenario: A lead past day 14 with no response gets no further automated touches
- **WHEN** a lead completes the day-14 message without responding
- **THEN** no further automated cadence message is sent to that lead

### Requirement: The cadence runs as a scheduled task, same pattern as the existing pollers
The cadence check SHALL run on a Windows Scheduled Task, following the same pattern already
established for `ContexiaHermesSiigoPoller` and `ContexiaHermesGmailPoller` — inert without its
required configuration, never a silent no-op that looks successful.

#### Scenario: The task is inert without Chatwoot/backend credentials
- **WHEN** the cadence task runs without its required configuration
- **THEN** it logs an error and sends no messages, rather than failing silently as if nothing was
  due
