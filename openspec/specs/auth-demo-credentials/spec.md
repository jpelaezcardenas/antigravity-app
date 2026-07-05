# auth-demo-credentials Specification

## Purpose
Establishes that demo/admin login credentials in `apps/backend/application/auth_service.py` are never hardcoded as real secrets in source, and that the demo login path defaults to a safe (disabled/fail-closed) state absent explicit configuration. Established by `remediate-gbrain-audit-findings` (2026-07-05), following the discovery that a real Bitwarden master password had been committed as a demo-admin login password and was live in production.

## Requirements

### Requirement: Demo Login Credentials Are Never Hardcoded
The system SHALL NOT contain any literal, real credential value (password, API key, connection string) in git-tracked source code for the demo/admin login path. Any password used by the demo login flow SHALL be read from an environment variable at runtime.

#### Scenario: Demo password sourced from environment
- **WHEN** `apps/backend/application/auth_service.py` is inspected
- **THEN** no `DEMO_USERS` entry contains a literal real-world password string; the admin demo entry's password is read from `settings.DEMO_ADMIN_PASSWORD`

#### Scenario: Non-secret placeholder passwords are permitted
- **WHEN** a demo user entry represents a fictitious, non-privileged test account (e.g. `cliente@demo.co`)
- **THEN** a literal placeholder value (e.g. `"demo"`) MAY remain hardcoded, since it is not a real credential tied to any external system

### Requirement: Demo Auth Defaults to Disabled When Unconfigured
`DEMO_AUTH_ENABLED` SHALL default to a safe state such that, absent explicit configuration, the demo login path either does not activate or fails closed if `DEMO_ADMIN_PASSWORD` is unset/empty.

#### Scenario: Demo login fails closed when password is unset
- **WHEN** `DEMO_AUTH_ENABLED` is true but `DEMO_ADMIN_PASSWORD` is empty or unset
- **THEN** the demo-admin login attempt is rejected rather than succeeding against an empty-string comparison

#### Scenario: Production explicitly disables demo auth
- **WHEN** the production environment (Railway) is inspected
- **THEN** `DEMO_AUTH_ENABLED` is explicitly set to `false`
