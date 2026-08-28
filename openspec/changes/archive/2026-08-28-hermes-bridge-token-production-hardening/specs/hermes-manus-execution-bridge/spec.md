## MODIFIED Requirements

### Requirement: Operator-task bridge endpoints support optional machine bearer authentication
The system SHALL support an env-configured `HERMES_BRIDGE_TOKEN`. When unset, the 5 operator-task
endpoints (`GET /tasks/pending`, `POST /tasks`, `POST /campaigns/{id}/dispatch`,
`POST /tasks/{id}/status`, `POST /tasks/{id}/result`) SHALL behave exactly as they do today (no
auth required). When set, each of these endpoints SHALL require an `Authorization: Bearer <token>`
header matching the configured value, and SHALL reject requests missing or presenting an incorrect
token with a 401 error. In the canonical production environment, `HERMES_BRIDGE_TOKEN` SHALL be
configured, and the Hermes/Manus poller SHALL send a matching `Authorization: Bearer <token>`
header on every call to these 5 endpoints — the poller SHALL NOT send any other credential shape
(e.g. a self-signed JWT) as its means of authenticating to this bridge.

#### Scenario: Bridge token unset preserves today's open behavior
- **WHEN** `HERMES_BRIDGE_TOKEN` is not configured and Hermes calls any of the 5 operator-task
  endpoints with no `Authorization` header
- **THEN** the request succeeds exactly as before this change

#### Scenario: Bridge token set rejects an unauthenticated request
- **WHEN** `HERMES_BRIDGE_TOKEN` is configured and a caller omits the `Authorization` header
- **THEN** the request is rejected with a 401 error

#### Scenario: Bridge token set accepts a correctly authenticated request
- **WHEN** `HERMES_BRIDGE_TOKEN` is configured and a caller sends
  `Authorization: Bearer <matching-token>`
- **THEN** the request proceeds as normal

#### Scenario: The Hermes/Manus poller authenticates with a bearer token, not a JWT
- **WHEN** `HERMES_BRIDGE_TOKEN` is configured in both the canonical backend and the Hermes/Manus
  poller's local environment, and the poller polls `GET /tasks/pending`
- **THEN** the poller sends `Authorization: Bearer <token>` matching the configured value, and the
  request succeeds — the poller does not sign or send a JWT for this purpose

#### Scenario: Production requires the token to be configured
- **WHEN** the canonical production backend (`-175a`) is queried for its `HERMES_BRIDGE_TOKEN`
  configuration
- **THEN** the value is non-empty, and an unauthenticated call to any of the 5 operator-task
  endpoints against production is rejected with a 401 error
