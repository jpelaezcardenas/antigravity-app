## ADDED Requirements

### Requirement: Preserve Bunker live shell and brand language
The system SHALL preserve the current Bunker live aesthetic, including the dark/cyan admin styling, sidebar-first layout, and top search behavior, while keeping "Social Media OPs Systems" as the visible operations brand.

#### Scenario: User opens the Bunker admin shell
- **WHEN** the user opens the Bunker application
- **THEN** the shell retains the current live look and feel
- **AND** the operations area still presents "Social Media OPs Systems"

### Requirement: Update the Bunker subtitle
The system SHALL display the subtitle `Motor de contenido orgánico para Facebook, Instagram, TikTok, LinkedIn y Telegram — Contexia.` in the Bunker admin experience.

#### Scenario: User views the Bunker header
- **WHEN** the user reaches the Bunker shell header
- **THEN** the updated subtitle is visible
- **AND** the previous subtitle is no longer the canonical copy

### Requirement: Expose Onboarding 21D only from the sidebar
The system SHALL place `Onboarding 21D` in the sidebar `Onboarding` entry and SHALL NOT duplicate that onboarding experience inside `Operaciones`.

#### Scenario: User navigates to onboarding
- **WHEN** the user clicks the sidebar `Onboarding` entry
- **THEN** the onboarding workflow is available there
- **AND** the same onboarding workflow is not duplicated inside the operations tabs

### Requirement: Keep Operations focused on the canonical Social Ops tabs
The system SHALL keep `Operaciones` focused on the canonical tabs `Ideas`, `Calendario`, `Borradores`, `Métricas`, `Inbox`, `Pipeline`, `Comandos`, `Aprobaciones`, and `Integraciones`.

#### Scenario: User opens Operaciones
- **WHEN** the user opens the operations area
- **THEN** the canonical tab set remains available
- **AND** onboarding is not presented as a duplicate operations tab

### Requirement: Route Ideas and Metrics through FastAPI only
The system SHALL have `Ideas` and `Métricas` consume the FastAPI Social Ops backend as their authoritative source and SHALL NOT route those flows through n8n or `contexia-content-os`.

#### Scenario: User loads Ideas or Metrics
- **WHEN** the user opens Ideas or Metrics
- **THEN** the UI reads from the FastAPI Social Ops API
- **AND** the flow does not depend on the retired Content OS deployment

### Requirement: Keep approval review as human-in-the-loop
The system SHALL keep Approval Queue as the human-in-the-loop gate for sensitive actions and outbound drafts.

#### Scenario: A sensitive draft is generated
- **WHEN** the system produces a draft that requires review
- **THEN** the draft remains pending until a human approves or rejects it
- **AND** the approval queue exposes the review action

### Requirement: Consolidate Social Ops backend in FastAPI
The system SHALL keep Social Ops endpoint handling consolidated in `apps/backend/presentation/social_ops_endpoints.py` and the mounted `/api/v1/social-ops` FastAPI router, with no duplicated legacy route mapping.

#### Scenario: A client calls Social Ops APIs
- **WHEN** a frontend or integration calls a Social Ops endpoint
- **THEN** the request resolves through the FastAPI backend
- **AND** there is no alternate runtime dependency on a separate Content OS service

### Requirement: Retire the dead Content OS dependency operationally
The system SHALL treat `contexia-content-os` as retired operationally and SHALL NOT depend on it for critical Social Ops behavior.

#### Scenario: The team documents runtime dependencies
- **WHEN** the Social Ops runtime contract is reviewed
- **THEN** `contexia-content-os` is documented as retired
- **AND** the canonical source of truth is `antigravity-app`

