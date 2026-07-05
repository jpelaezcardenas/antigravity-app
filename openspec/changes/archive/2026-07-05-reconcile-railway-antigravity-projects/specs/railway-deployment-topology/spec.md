## ADDED Requirements

### Requirement: A Single Documented Canonical Backend
`ARCHITECTURE.md` and `CLAUDE.md` SHALL identify exactly one Railway project as the canonical `antigravity-app` backend, matching the project Vercel's `/api/v1/*` rewrite actually targets.

#### Scenario: Docs match live routing
- **WHEN** `vercel.json`'s API rewrite target is compared against `ARCHITECTURE.md`'s documented canonical backend URL
- **THEN** they reference the same Railway project

#### Scenario: No second undocumented production-labeled deployment
- **WHEN** Railway projects are enumerated
- **THEN** at most one is documented as canonical production; any other running `antigravity-app` deployment is either explicitly labeled non-canonical/pending-decommission or does not exist

### Requirement: Canonical Backend Has No Empty Required Secrets in Production
The canonical backend SHALL NOT run with `DEBUG=False` and `ENVIRONMENT=production` while any of its required secrets (`JWT_SECRET`, `SUPABASE_URL`, `SUPABASE_KEY`) are empty or placeholder values. This SHALL be enforced by actually invoking existing validation at startup, not merely defining it.

#### Scenario: Startup validation actually runs
- **WHEN** the backend application starts in production mode
- **THEN** `validate_production_config()` (or equivalent) is called as part of startup, not merely defined and unreferenced

#### Scenario: Empty JWT_SECRET is rejected
- **WHEN** the backend starts with `ENVIRONMENT=production`, `DEBUG=False`, and an empty `JWT_SECRET`
- **THEN** startup fails loudly with a clear error, rather than succeeding silently with a forgeable auth secret

#### Scenario: Valid production config starts cleanly
- **WHEN** the backend starts with a real, sufficiently long `JWT_SECRET` and valid Supabase credentials
- **THEN** startup succeeds and the validation check passes without side effects

### Requirement: Duplicate Deployment Env Var Parity for Genuinely-Used Variables
Environment variables confirmed to be read by real code paths (e.g., LLM fallback provider keys, JWT signing config) SHALL be present with working values on the canonical backend, even if they originated on a non-canonical duplicate deployment. Variables tied to insecure patterns already flagged separately (e.g., Bitwarden master-password-based secrets) SHALL NOT be replicated onto the canonical backend.

#### Scenario: LLM fallback providers available on canonical backend
- **WHEN** the canonical backend's environment is inspected
- **THEN** `GEMINI_API_KEY`, `MISTRAL_API_KEY`, and `CEREBRAS_API_KEY` are present and match working values (not placeholders)

#### Scenario: Bitwarden master-password pattern is not replicated
- **WHEN** the canonical backend's environment is inspected
- **THEN** `BW_MASTER_PASSWORD` is absent — migrating it would spread a known insecure pattern rather than fix it

### Requirement: No Decommission Without Verified End-to-End Functionality
A duplicate deployment SHALL NOT be decommissioned until the canonical backend is verified to handle everything the duplicate was relied on for (at minimum: health check passing, and Telegram bot functionality if/when re-enabled), and an explicit, separate decommission decision is made.

#### Scenario: Decommission requires prior verification
- **WHEN** a decommission of a duplicate Railway project is considered
- **THEN** the canonical backend has already passed a documented end-to-end verification pass covering the duplicate's known unique responsibilities

#### Scenario: Decommission is a separate explicit action
- **WHEN** this change's tasks are all complete
- **THEN** the duplicate project is still running — decommissioning it is not an automatic consequence of closing this change
