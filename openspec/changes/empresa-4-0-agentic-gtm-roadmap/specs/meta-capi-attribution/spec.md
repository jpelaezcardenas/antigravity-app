## ADDED Requirements

### Requirement: A server-side `Lead` conversion event fires from the real lead-creation path
The system SHALL send a Meta Conversions API (CAPI) `Lead` event from the backend when a lead is
actually created (`social_capture_partial` or the equivalent lead-creation service), not only from
the client-side pixel. This SHALL happen synchronously with, or immediately after, the `crm_leads`
row insert, and SHALL NOT block the lead-creation response on Meta's API being available.

#### Scenario: New lead triggers a server-side Lead CAPI event
- **WHEN** `social_capture_partial` successfully inserts a new `crm_leads` row
- **THEN** the system sends a Meta CAPI `Lead` event carrying available match keys (e.g. hashed
  email/phone if present) and the lead's creation timestamp

#### Scenario: Meta CAPI unavailability does not block lead capture
- **WHEN** the Meta Conversions API call fails or times out
- **THEN** the lead-capture request still succeeds and returns its normal response; the CAPI
  failure is logged, never surfaced to the visitor

#### Scenario: Duplicate lead does not fire a second Lead event
- **WHEN** an inbound capture matches an existing `crm_leads` row (already-throttled/repeat lead,
  per the existing dedup behavior)
- **THEN** no additional `Lead` CAPI event is sent for that same lead

### Requirement: The client-side pixel fires a `Lead` event at the same conversion point
In addition to the existing `PageView` event, the Meta Pixel on the landing page and the
`/renta-natural` funnel SHALL fire a client-side `fbq('track', 'Lead')` event at the point the
visitor completes the lead-capture form, as a secondary/redundant signal to the server-side event.

#### Scenario: Pixel fires Lead on successful form submission
- **WHEN** a visitor on `/renta-natural` (or the landing page's capture form) successfully submits
  the lead form
- **THEN** the page fires `fbq('track', 'Lead')` in addition to the existing `PageView` event

### Requirement: The Auditoría Sombra qualifier page fires PageView and a branch-selection event
`auditoria-sombra.html` (the funnel-qualifier page that splits visitors into the Persona Natural
and Empresa Formalizada funnels — found live 2026-09-23 to have zero Pixel installed) SHALL fire
the standard Meta Pixel `PageView` event on load, and a custom event `AuditoriaSombraBranchSelected`
(carrying which branch, `natural` or `formal`, was chosen) when a visitor selects a branch. This is
NOT a `Lead` event — no `crm_leads` row exists yet at this point, only a qualifier click.

#### Scenario: Page load fires PageView
- **WHEN** a visitor loads `auditoria-sombra.html`
- **THEN** the Meta Pixel fires `PageView`, matching the pattern already used on `landing.html`

#### Scenario: Selecting a branch fires the custom event, not Lead
- **WHEN** a visitor clicks either the "Persona Natural" or "Empresa Formalizada" option card
- **THEN** the page fires `fbq('trackCustom', 'AuditoriaSombraBranchSelected', {branch: '<natural|
  formal>'})`, and does NOT fire `Lead` (no lead-creation call has happened yet)

### Requirement: The Empresa Formalizada branch (contexia-wizard) fires its own Lead event
The `formal` branch of `auditoria-sombra.html` navigates to `/wizard/iva-ecom`, served by the
separate `contexia-wizard` project. That funnel's own lead-capture form SHALL fire a client-side
Meta Pixel `Lead` event at its real conversion point (its own form-submit success), mirroring the
same pattern as `RentaNaturalLandingForm.tsx` — client-side signal only; `contexia-wizard`'s own
backend (if any) firing a matching server-side CAPI event is out of scope for this spec, which
covers only `antigravity-app`'s Meta CAPI wiring.

#### Scenario: Wizard funnel fires Lead on its own successful submission
- **WHEN** a visitor completes `contexia-wizard`'s `/wizard/iva-ecom` lead-capture form
  successfully
- **THEN** the page fires `fbq('track', 'Lead')` using the same Pixel ID as `antigravity-app`'s
  other funnels

### Requirement: CAPI credentials never reach the frontend or a public repo file
The Meta CAPI access token SHALL be stored only as a backend environment variable (Railway), never
in `landing.html`, `contexia-app/`, or any committed file.

#### Scenario: Token is absent from client-served code
- **WHEN** any file served to the browser (landing page, renta-natural funnel bundle) is inspected
- **THEN** it contains no Meta CAPI access token — only the public Pixel ID, which is not a secret
