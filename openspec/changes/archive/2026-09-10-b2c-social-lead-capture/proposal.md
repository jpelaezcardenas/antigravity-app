## Why

Contexia is running paid/organic content on Facebook, Instagram, and TikTok during peak Renta
Natural season, but there is no landing page or form to capture a lead from that traffic —
`crm-b2c-sell-machine`'s funnel starts at `POST /api/v1/crm/leads/whatsapp-intake`, which requires
someone to already be messaging Taty on WhatsApp. A social ad click has nowhere authoritative to
land. This was identified as the largest concrete gap in the master plan (2026-09-10): the
research into Dapta's playbooks quantified that contacting a lead in under 5 minutes gives 391%
more qualification probability than waiting 5 minutes, and at 30 minutes 78% of the potential is
already lost — but Contexia has no capture surface to even start that clock from social traffic.

## What Changes

- New public landing page (`contexia.online/renta` or similar path, to confirm exact URL during
  design) with a short lead-capture form: name, phone (E.164), and which social platform/campaign
  it came from (UTM-style source tag).
- **Partial-submission capture**, adapting Dapta Forms' pattern: the moment a visitor enters a
  valid phone number (before finishing the rest of the form), that partial submission is
  persisted — so an abandoned form still produces a contactable lead, not a lost one.
- Immediate automated first-contact trigger: within the 5-minute window the research quantified,
  an outbound WhatsApp message from Taty is sent to the captured phone number — text only, reusing
  the existing Chatwoot delivery path, no dependency on `taty-voice-outbound-calls` (Twilio/voice
  is a separate, still-gated capability; this ships independently and does not wait on it).
- The captured lead becomes a real `crm_leads` row via the existing
  `POST /api/v1/crm/leads/whatsapp-intake` (Cliente Cero tenant, `stage: "NUEVOS"`) — no new lead
  table, no parallel storage.
- Source/UTM tag persisted on the lead so ad performance per platform (Instagram vs. TikTok vs.
  Facebook) is queryable later — a lightweight, additive field, not a full attribution/analytics
  system.

## Capabilities

### New Capabilities
- `b2c-social-lead-capture`: public landing page + partial-capture form + immediate WhatsApp
  first-contact trigger for social-traffic leads, feeding the existing `crm-b2c-sell-machine`
  funnel.

### Modified Capabilities
- `crm-b2c-sell-machine`: `crm_leads` gains a `source` (or reuses an existing similar field if one
  is found during design) to record where a lead came from — additive, does not change existing
  stage/funnel behavior.

## Impact

- Frontend: new public page (likely in `contexia-app/` or the existing landing surface — to
  confirm which app owns public marketing pages during design), no auth required to view/submit.
- Backend: reuses `POST /api/v1/crm/leads/whatsapp-intake` as-is for the final lead creation;
  needs a new, unauthenticated-but-rate-limited endpoint for the partial-capture write (a public
  form cannot carry a tenant-scoped bearer token) — rate limiting and abuse prevention are a real
  design concern for a public, unauthenticated endpoint.
- Does not touch `taty-voice-outbound-calls`, `hermes-hubspot-poller`, or any B2B path — this is
  exclusively a B2C/Renta Natural capture surface.
- Out of scope for this change: designing the actual ad creatives/copy, the ad spend/targeting on
  Meta/TikTok, and any campaign-performance dashboard — this change builds only the capture
  infrastructure the campaign lands on, not the campaign itself or its analytics.
