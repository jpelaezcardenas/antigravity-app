## ADDED Requirements

### Requirement: Exactly one public WhatsApp ingress exists, and it authenticates Meta
The system SHALL expose exactly one HTTP endpoint that accepts inbound WhatsApp messages from
Meta, and that endpoint SHALL verify `X-Hub-Signature-256` as an HMAC-SHA256 over the exact raw
request body using a constant-time comparison before performing any side effect.

The ingress is `POST /api/v1/channels/whatsapp/webhook`, publicly reachable as
`https://contexia.online/api/v1/channels/whatsapp/webhook` through `vercel.json`'s
`/api/v1/:path*` rewrite to Railway. It is deliberately NOT tunnel- or DNS-delegation-dependent:
the domain's nameservers are at Hostinger, so a Cloudflare Named Tunnel hostname is not
available without delegating the zone, and delegation was rejected.

#### Scenario: An unsigned inbound payload is rejected
- **WHEN** `POST /api/v1/channels/whatsapp/webhook` receives a payload with a missing, malformed,
  or non-matching `X-Hub-Signature-256`
- **THEN** the backend SHALL respond `403` and SHALL NOT perform any side effect

#### Scenario: Signature verification uses the raw body
- **WHEN** a signed payload's key ordering or whitespace differs from Python's default JSON
  serialization
- **THEN** verification SHALL still succeed, proving the raw bytes were used

#### Scenario: No feature flag gates the live ingress
- **WHEN** the backend settings are inspected
- **THEN** no `WHATSAPP_CANONICAL` setting SHALL exist, and the router mount SHALL be
  unconditional — a flag on the production ingress can only cause a silent loss of customer
  messages, and authenticity is enforced by the signature instead

### Requirement: Exactly one Taty reply-generation path exists
Replies to a WhatsApp lead SHALL be produced by `services/taty_lead_router.py::route_lead_message`.
No other component SHALL generate a customer-facing sales reply for a WhatsApp lead.

#### Scenario: The bridge produces a reply through the sales router
- **WHEN** the bridge processes an incoming, non-private, non-paused Chatwoot message for a lead
- **THEN** it SHALL obtain the reply text from the backend's internal Taty reply endpoint
- **AND** it SHALL NOT call `hermes_client.invoke_chat_completion` to produce that reply

#### Scenario: Commercial capabilities survive the channel switch
- **WHEN** a lead sends a message classified as `sales_interest`
- **THEN** the reply SHALL be produced by the same router that generates Wompi payment links and
  reads `crm_wompi_transactions`, so pricing, payment links, and payment confirmation remain
  reachable through the Chatwoot channel

#### Scenario: Pre-LLM anonymization is not bypassed
- **WHEN** the reply path invokes a language model
- **THEN** it SHALL do so through `get_anonymized_ai_response`, preserving the masking/rehydration
  guarantee

### Requirement: The internal Taty reply endpoint is authenticated and lead-scoped
The backend SHALL expose an internal endpoint that returns Taty's reply for a given lead, requiring
authentication and taking the lead identifier the caller already holds.

#### Scenario: An authenticated bridge call returns a reply
- **WHEN** the bridge calls the endpoint with a valid token and a known `lead_id` and message text
- **THEN** the backend SHALL respond `200` with the router's reply text

#### Scenario: An unauthenticated call is rejected
- **WHEN** the endpoint is called without a valid authentication token
- **THEN** the backend SHALL respond `401`

#### Scenario: The endpoint does not create leads
- **WHEN** the endpoint is called with a `lead_id` that does not exist
- **THEN** the backend SHALL NOT create a lead, and SHALL respond `404`

### Requirement: Meta social webhooks verify payload authenticity
`POST /api/v1/channels/meta/webhook` SHALL verify Meta's `X-Hub-Signature-256` header as an HMAC-SHA256
over the exact raw request body, using a constant-time comparison, before processing any event.

#### Scenario: A correctly signed payload is processed
- **WHEN** a request arrives whose `X-Hub-Signature-256` matches the HMAC of the raw body computed
  with the configured app secret
- **THEN** the backend SHALL process the events normally

#### Scenario: An unsigned or wrongly signed payload is rejected
- **WHEN** a request arrives with a missing, malformed, or non-matching `X-Hub-Signature-256`
- **THEN** the backend SHALL respond `403` and SHALL NOT ingest any event

#### Scenario: Signature verification uses the raw body, not a re-serialized one
- **WHEN** a signed payload contains key ordering or whitespace that differs from Python's default
  JSON serialization
- **THEN** verification SHALL still succeed, proving the raw bytes were used

### Requirement: Webhook verify tokens fail closed
Webhook verification tokens SHALL have no hardcoded default value. When a verify token is not
configured, the corresponding verification handshake SHALL fail.

#### Scenario: An unconfigured verify token rejects the handshake
- **WHEN** `GET /api/v1/channels/meta/webhook` receives `hub.mode=subscribe` while no verify token
  is configured
- **THEN** the backend SHALL respond `403` rather than accepting a built-in default string
