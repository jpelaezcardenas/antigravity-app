## ADDED Requirements

### Requirement: Bridge processes only genuine incoming customer messages
The system SHALL expose `POST /webhook` and, for each Chatwoot payload received, SHALL process it
(schedule background handling) only when `event == "message_created"`, the message's
`message_type == "incoming"`, and the message is not `private`. All other payloads SHALL be
acknowledged with a `{"status": "skipped"}` response and SHALL NOT trigger any Hermes call, CRM
call, or Chatwoot reply.

#### Scenario: An incoming customer message is processed
- **WHEN** `POST /webhook` receives a payload with `event: "message_created"`,
  `message_type: "incoming"`, and `private: false`
- **THEN** the bridge schedules background processing and responds `{"status": "processing_started"}`

#### Scenario: An outgoing message is ignored (loop prevention)
- **WHEN** `POST /webhook` receives a payload with `event: "message_created"` and
  `message_type: "outgoing"`
- **THEN** the bridge responds `{"status": "skipped"}` and does not call Hermes

#### Scenario: A private agent note is ignored
- **WHEN** `POST /webhook` receives a payload with `event: "message_created"`,
  `message_type: "incoming"`, and `private: true`
- **THEN** the bridge responds `{"status": "skipped"}` and does not call Hermes

#### Scenario: A non-message event is ignored
- **WHEN** `POST /webhook` receives a payload with any `event` other than `"message_created"`
- **THEN** the bridge responds `{"status": "skipped"}` and does not call Hermes

### Requirement: Webhook calls are authenticated with a shared token
The system SHALL reject `POST /webhook` requests that do not present the configured
`WEBHOOK_TOKEN` (via query parameter or `X-Webhook-Token` header) with an HTTP 401 response, before
any event processing occurs.

#### Scenario: Request without a valid token is rejected
- **WHEN** `POST /webhook` is called without the correct `WEBHOOK_TOKEN`
- **THEN** the response is HTTP 401 and no background processing is scheduled

### Requirement: A `bot_off` label pauses the AI agent for that conversation
For an otherwise-processable incoming message, the system SHALL check the conversation's `labels`
list. If the configured `PAUSE_LABEL` (default `bot_off`) is present, the bridge SHALL NOT invoke
Hermes and SHALL respond `{"status": "paused", "reason": "bot_off tag active"}`.

#### Scenario: Conversation tagged bot_off is not answered by the AI
- **WHEN** an incoming message arrives on a conversation whose `labels` includes `"bot_off"`
- **THEN** the bridge responds `{"status": "paused", "reason": "bot_off tag active"}` and does not
  call the Hermes Gateway

#### Scenario: Removing the label restores AI handling
- **WHEN** an incoming message arrives on a conversation whose `labels` no longer includes
  `"bot_off"`
- **THEN** the bridge proceeds with normal processing (history, Hermes invocation, reply dispatch)

### Requirement: Hermes Gateway is invoked via its OpenAI-compatible chat completions API
For a processable incoming message, the bridge SHALL fetch up to `MAX_HISTORY` (default 10) prior
messages from the Chatwoot conversation, map them to `{role, content}` pairs, and SHALL call
`POST {HERMES_GATEWAY_URL}/v1/chat/completions` with `Authorization: Bearer {HERMES_API_KEY}`, body
`{"model": "taty-v1", "messages": [...history, current], "stream": false}`, with a 60-second
timeout.

#### Scenario: Hermes call includes recent conversation history
- **WHEN** the bridge processes an incoming message on a conversation with 15 prior messages
- **THEN** the Hermes request body's `messages` array contains at most the last `MAX_HISTORY` prior
  messages plus the current one, each mapped to `role: "user"` or `role: "assistant"`

#### Scenario: Hermes response is dispatched back to Chatwoot
- **WHEN** the Hermes Gateway responds successfully with generated text
- **THEN** the bridge posts that text to the Chatwoot conversation as an outgoing message

### Requirement: Bridge degrades gracefully when dependencies are unavailable
If the Hermes Gateway call times out (60s) or errors, the bridge SHALL send a fixed Spanish
fallback message to the conversation rather than leaving the customer without any reply, and SHALL
log the failure with a traceback. If the CRM intake or onboarding-trigger call fails, the bridge
SHALL log the failure and continue to the Hermes reply step rather than aborting the whole request.

#### Scenario: Hermes Gateway times out
- **WHEN** the Hermes Gateway does not respond within 60 seconds
- **THEN** the bridge sends a fixed Spanish apology message to the conversation and logs the error
  with a traceback

#### Scenario: CRM intake call fails but the conversation still gets an AI reply
- **WHEN** the call to `POST /api/v1/crm/leads/whatsapp-intake` fails (network error or 5xx)
- **THEN** the bridge logs the failure and still proceeds to fetch history, invoke Hermes, and
  dispatch a reply

### Requirement: New WhatsApp contacts trigger lead intake and are tagged as new
When the bridge processes the first processable incoming message for a conversation, it SHALL call
`POST /api/v1/crm/leads/whatsapp-intake` with the contact's phone number. If the response indicates
the lead is new (`is_new: true`), the bridge SHALL set the Chatwoot contact's custom attributes
`tipo_lead` and `estado: "nuevo"`.

The bridge SHALL NOT call `POST /api/v1/social-ops/onboarding/start` (or any other company/workspace
onboarding endpoint) from this flow. That endpoint's `OnboardingStartRequest` (`company_name`,
`customer_email`, `payment_reference`) represents the B2B/paid-customer 21-day workspace onboarding
that runs after a sale closes — a brand-new `NUEVOS`-stage lead has none of that information yet.
A fresh WhatsApp lead SHALL simply proceed to a normal qualifying conversation with Taty (via
Hermes), same as any other B2C channel; company onboarding is a separate, later-stage concern (see
`design.md` decision 5) out of scope for this bridge.

#### Scenario: First message from an unknown phone number tags the lead as new
- **WHEN** the bridge processes an incoming message from a WhatsApp contact not previously known to
  the CRM
- **THEN** `POST /api/v1/crm/leads/whatsapp-intake` returns `is_new: true`, the bridge sets the
  Chatwoot contact's `estado` attribute to `"nuevo"`, and the bridge does not call
  `POST /api/v1/social-ops/onboarding/start` or any other onboarding endpoint

#### Scenario: Returning contact is not re-tagged
- **WHEN** the bridge processes an incoming message from a WhatsApp contact already known to the CRM
- **THEN** `POST /api/v1/crm/leads/whatsapp-intake` returns `is_new: false` and the bridge does not
  set the contact's custom attributes again nor call any onboarding endpoint

### Requirement: Audio attachments receive a graceful text-only fallback
When an incoming message includes an attachment with `file_type == "audio"`, the bridge SHALL NOT
attempt transcription. It SHALL send a fixed, friendly Spanish reply asking the customer to send
their message as text, and SHALL NOT invoke Hermes for that message.

#### Scenario: A voice note is received
- **WHEN** an incoming message's attachments include one with `file_type: "audio"`
- **THEN** the bridge dispatches a fixed Spanish fallback reply asking for text and does not call
  the Hermes Gateway

### Requirement: Health check reflects Hermes Gateway reachability
The system SHALL expose `GET /` returning service status, and SHALL log the result of
`GET {HERMES_GATEWAY_URL}/v1/models` at startup so a misconfigured or wrong-profile Hermes Gateway
is immediately visible in logs.

#### Scenario: Health check succeeds
- **WHEN** `GET /` is called
- **THEN** the response is HTTP 200 with a JSON body identifying the service
