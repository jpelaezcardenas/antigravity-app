### Requirement: Onboarding section starts a new client onboarding
The Onboarding section SHALL render a form (company name, customer email, payment reference, plan name, owner handle) that calls `POST /social-ops/onboarding/start`, and select the newly created workspace on success.

#### Scenario: User starts onboarding for a new client
- **WHEN** the user submits the start-onboarding form
- **THEN** `POST /social-ops/onboarding/start` is called with the form values, the returned workspace becomes selected, and a confirmation message is shown

### Requirement: Workspace selector shows SLA and QA targets
The Onboarding section SHALL list existing onboarding workspaces from `GET /social-ops/onboarding` in a selector, and show the selected workspace's SLA (credential response hours) and QA adoption target.

#### Scenario: User selects a workspace
- **WHEN** the user selects a workspace from the dropdown
- **THEN** that workspace's SLA and QA target values are displayed

### Requirement: Natural-language intake extracts credentials
The Onboarding section SHALL provide a free-text intake form that calls `POST /social-ops/onboarding/{workspace_id}/intake`, displaying which credentials/data points were detected as present versus missing.

#### Scenario: User submits intake text
- **WHEN** the user submits natural-language intake text for the selected workspace
- **THEN** the response's `present` and `missing` lists are displayed

### Requirement: Seed draft creation
The Onboarding section SHALL allow creating a seed draft via `POST /social-ops/onboarding/{workspace_id}/seed`, landing in `pending_approval` per the HITL rule.

#### Scenario: User creates a seed draft
- **WHEN** the user clicks "Crear seed draft" with a workspace selected
- **THEN** `POST /social-ops/onboarding/{workspace_id}/seed` is called and a confirmation message is shown

### Requirement: 21-day template checklist is visible
The Onboarding section SHALL display the full 21-day onboarding template steps (S1 kick-off through Go-Live) returned by `GET /social-ops/onboarding`'s `template_steps`.

#### Scenario: Template steps render
- **WHEN** the Onboarding section loads
- **THEN** all template steps are listed with their label and description
