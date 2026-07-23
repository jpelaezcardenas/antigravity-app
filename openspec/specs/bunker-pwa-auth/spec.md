## ADDED Requirements

### Requirement: All data-bound fetches attach the existing Supabase session token
The system SHALL route every data-bound API client (`api-client.ts`, `social-ops-api.ts`,
`crm-api.ts`, `sell-machine-api.ts`) through a shared `authenticated-fetch.ts` helper that attaches
`Authorization: Bearer <token>` from `localStorage["token"]` — the same key `login.html` already
populates with the Supabase access token on a successful sign-in.

#### Scenario: A data-bound request includes the bearer token
- **WHEN** any data-bound screen fetches its backend endpoint with a token present in
  `localStorage` (set by `login.html`'s existing sign-in flow)
- **THEN** the request includes `Authorization: Bearer <token>`

#### Scenario: No token present sends no Authorization header
- **WHEN** no token exists in `localStorage`
- **THEN** the request is sent without an `Authorization` header (server-side enforcement, not the
  client, decides what happens next)

### Requirement: The backend recognizes Supabase-issued JWTs, not only its own
The system SHALL extend `core/deps.py`'s `get_current_user` to accept a Supabase-issued JWT
(verified against `SUPABASE_JWT_SECRET`, HS256 — the same verification `middleware.ts` already
performs) as a fallback when the token doesn't verify against the backend's own `JWT_SECRET`. This
SHALL NOT change existing behavior for the backend's own JWTs (`AuthService.login`'s demo/DB-backed
tokens).

#### Scenario: A real Supabase session is recognized once enforcement is on
- **WHEN** `AUTH_ENFORCED=True` and a request includes a valid Supabase-issued JWT
- **THEN** the request is resolved to a valid identity and succeeds (not rejected)

#### Scenario: The backend's own JWT still works unchanged
- **WHEN** a request includes a valid JWT signed with the backend's own `JWT_SECRET`
- **THEN** the request is resolved exactly as before this change

### Requirement: Backend routers enforce authentication once AUTH_ENFORCED is true
The system SHALL add `Depends(get_current_user)` to `crm_endpoints.py` and
`social_ops_endpoints.py` (router-level), and to the Búnker-human-facing endpoints only in
`sell_machine_endpoints.py` (`/hooks/generate`, `/hooks/evaluate`, `POST /campaigns`,
`GET /campaigns`) — leaving the Hermes↔backend machine-to-machine bridge endpoints
(`/tasks/*`, `/campaigns/{id}/dispatch`, `/creative-loop/run`, `/telemetry/report`) unguarded,
since Hermes has no browser session. This SHALL NOT change behavior while `AUTH_ENFORCED=False`.
**Amendment (`hermes-task-queue-tenant-scoping`, 2026-07-23):** `/tasks/*` and
`/campaigns/{id}/dispatch` specifically now support a separate, optional
`HERMES_BRIDGE_TOKEN` bearer-token gate (distinct from `get_current_user`/`AUTH_ENFORCED`) — see
`openspec/changes/hermes-task-queue-tenant-scoping/design.md` D5/D7. Unset (the default) means
identical open behavior to before this change. `/creative-loop/run` and `/telemetry/report` are
unaffected and remain fully unguarded — out of scope for that change.

#### Scenario: An authenticated request succeeds once enforcement is on
- **WHEN** `AUTH_ENFORCED=True` and a request includes a valid bearer token (either scheme)
- **THEN** the request succeeds normally

#### Scenario: An unauthenticated request is rejected once enforcement is on
- **WHEN** `AUTH_ENFORCED=True` and a request has no valid bearer token
- **THEN** the request is rejected with `401`

#### Scenario: The Hermes bridge is unaffected
- **WHEN** Hermes calls `GET /sell-machine/tasks/pending` (no bearer token) and
  `HERMES_BRIDGE_TOKEN` is unset (the default)
- **THEN** the request is unaffected by this change, regardless of `AUTH_ENFORCED`

#### Scenario: The Hermes bridge token gate, once configured, is independent of AUTH_ENFORCED
- **WHEN** `HERMES_BRIDGE_TOKEN` is set and Hermes calls one of the 5 operator-task routes
  (`/tasks/pending`, `POST /tasks`, `/campaigns/{id}/dispatch`, `/tasks/{id}/status`,
  `/tasks/{id}/result`) with a missing, malformed, or incorrect `Authorization: Bearer <token>`
  header
- **THEN** the request is rejected with `401`, independent of `AUTH_ENFORCED` and of
  `get_current_user` (see `hermes-task-queue-tenant-scoping`)

### Requirement: login.html supports real self-service sign-up and password reset, Google-only SSO
The system SHALL remove the "Sign in with Microsoft" option from `login.html`, keeping only Google
SSO and email/password. `login.html` SHALL support a real sign-up mode
(`client.auth.signUp`), and a real "Forgot password?" flow
(`client.auth.resetPasswordForEmail` + a `reset-password.html` completion page using
`client.auth.updateUser`). Self-service sign-ups SHALL default to `role: cliente` (via a
database trigger), never `admin`.

#### Scenario: Signing up creates an account with the cliente role by default
- **WHEN** a new user signs up via `login.html`'s sign-up mode with no pre-existing role
- **THEN** the resulting `auth.users` row has `app_metadata.role = "cliente"`

#### Scenario: Forgot password sends a real reset email
- **WHEN** a user submits a non-empty email via "Forgot password?"
- **THEN** `client.auth.resetPasswordForEmail` is called with a redirect to
  `/reset-password.html`

#### Scenario: reset-password.html rejects a submission with no valid recovery session
- **WHEN** the reset-password form is submitted without a valid Supabase recovery session
  established (e.g. an expired or missing link)
- **THEN** the form shows an error and does not call `client.auth.updateUser`
