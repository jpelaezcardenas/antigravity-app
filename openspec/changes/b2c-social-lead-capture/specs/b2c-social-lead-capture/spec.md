## ADDED Requirements

### Requirement: A public landing page captures a lead from social traffic
The system SHALL provide a public, unauthenticated landing page (in `contexia-app/`) with a short
form (name, E.164 phone, source/UTM tag from the query string) whose successful submission creates
or finds a `crm_leads` row via the existing find-or-create logic, exactly as
`POST /api/v1/crm/leads/whatsapp-intake` already does for WhatsApp-originated leads.

#### Scenario: A new phone number submitted from the landing page creates a lead
- **WHEN** a visitor submits the form with a phone number not present in `crm_leads`
- **THEN** a new `crm_leads` row is created with `stage: "NUEVOS"`, scoped to the Cliente Cero
  tenant, and the captured `source` value stored

#### Scenario: A repeat phone number is found, not duplicated
- **WHEN** a visitor submits the form with a phone number already present in `crm_leads`
- **THEN** no new row is created; the existing lead is reused

### Requirement: A partial submission (phone entered, form not finished) still captures the lead
The system SHALL persist a capture the moment a syntactically valid phone number is entered on
the landing form, even before the visitor finishes or submits the rest of it, adapting Dapta
Forms' partial-submission pattern, so an abandoned form still produces a contactable lead.

#### Scenario: Entering a valid phone number without submitting still captures the lead
- **WHEN** a visitor enters a valid phone number and abandons the page without clicking submit
- **THEN** a `crm_leads` row for that phone number still exists, as if the form had been submitted

### Requirement: The public capture endpoint is rate-limited and does not require authentication
`POST /api/v1/crm/social-capture/partial` (or the confirmed equivalent path) SHALL accept
unauthenticated requests, but SHALL throttle by both requesting IP and submitted phone number to
prevent abuse, since it has no bearer-token gate to rely on.

#### Scenario: Excessive requests from the same IP are throttled
- **WHEN** a single IP address submits far more requests than a reasonable visitor would in a
  short window
- **THEN** subsequent requests from that IP are rejected until the window resets

#### Scenario: The same phone number submitted repeatedly in a short window is not re-processed as new
- **WHEN** the same phone number is submitted multiple times within a short window
- **THEN** only the first submission triggers lead creation and first-contact; later ones are
  treated as no-ops, not new leads or new messages

### Requirement: A captured lead receives an automated WhatsApp first-contact, once, text-only
The system SHALL send an initial WhatsApp text message to a newly captured lead's phone number,
reusing the existing Chatwoot/Taty text-delivery path — never the voice/call capability, which is
a separate, still-gated capability. The message SHALL be sent at most once per unique phone
number, regardless of how many times that number is submitted through the capture form.

#### Scenario: A new capture triggers exactly one outbound WhatsApp message
- **WHEN** a phone number is captured for the first time
- **THEN** exactly one outbound WhatsApp text message is sent to it

#### Scenario: A phone number already contacted is never messaged again by this trigger
- **WHEN** a phone number that has already received the automated first-contact message is
  captured again (repeat form submission)
- **THEN** no additional automated message is sent as a result of this capability

### Requirement: Captured leads record their traffic source
`crm_leads` SHALL gain a nullable `source` field, populated from the landing page's UTM-style
query parameter at capture time. Existing leads (WhatsApp-originated, no landing-page source)
SHALL remain `NULL` — no backfill, no default value change.

#### Scenario: A lead captured from a tagged link records its source
- **WHEN** a visitor arrives via a link tagged `?source=tiktok_ad_renta2026` and submits the form
- **THEN** the resulting `crm_leads` row has `source = "tiktok_ad_renta2026"`

#### Scenario: Pre-existing WhatsApp-originated leads are unaffected
- **WHEN** a `crm_leads` row created before this capability existed is read
- **THEN** its `source` value is `NULL`, not backfilled to any guessed value
