### Requirement: Social Content Ops renders 9 functional tabs
The Búnker's "Social Content Ops" section SHALL render 9 tabs — Inbox, Pipeline, Comandos, Aprobaciones, Integraciones, Ideas, Calendario, Borradores, Métricas — each backed by real data from the canonical `/api/v1/social-ops/*` backend, not mock/placeholder content.

#### Scenario: User opens Social Content Ops
- **WHEN** the user selects "Social Content Ops" in the Búnker sidebar
- **THEN** the summary stats (leads activos, eventos inbox, riesgo alto, aprobaciones, canales activos) and the 9 tabs are visible, with "Inbox" active by default

### Requirement: Inbox and Pipeline show real inbound leads
The Inbox tab SHALL list real inbound events from `GET /social-ops/inbox`; the Pipeline tab SHALL show real leads grouped by pipeline stage from `GET /social-ops/pipeline`.

#### Scenario: Inbox displays events
- **WHEN** the Inbox tab loads
- **THEN** events returned by the backend are listed with channel, urgency, actor, and message text, and a "Diagnosticar" action calls `POST /social-ops/diagnose`

### Requirement: Ideas tab drives the Content Idea Generator agent
The Ideas tab SHALL list ideas from `GET /social-ops/ideas`, allow moving an idea's status via `POST /social-ops/ideas/{id}/status`, and generate an AI draft via `POST /social-ops/ideas/{id}/generate-draft`.

#### Scenario: User generates a draft from a selected idea
- **WHEN** the user clicks "Generar IA" on an idea with status `SELECCIONADA`
- **THEN** the backend's Content Idea Generator agent runs and returns draft text, and the idea's status updates to `USADA`

### Requirement: Calendario tab shows the editorial calendar
The Calendario tab SHALL list calendar entries from `GET /social-ops/calendario`, filterable by week (`semana`), showing publication date, título, pilar, formato, and status.

#### Scenario: User filters calendar by week
- **WHEN** the user selects week 2
- **THEN** only calendar entries with `semana=2` are shown, fetched via `GET /social-ops/calendario?semana=2`

### Requirement: Borradores tab supports draft review, edit, and approval
The Borradores tab SHALL list pending drafts from `GET /social-ops/borradores`, allow inline editing of hook/copy/CTA/hashtags via `POST /social-ops/borradores/{id}/update`, and allow approval via `POST /social-ops/borradores/{id}/approve`.

#### Scenario: User approves a draft
- **WHEN** the user clicks "Aprobar y Programar" on a draft
- **THEN** `POST /social-ops/borradores/{id}/approve` is called and the draft is removed from the pending list on success

### Requirement: Métricas tab shows publication performance
The Métricas tab SHALL show aggregate stats (alcance total, engagement promedio, posts, mejor score) and a per-publication detail table from `GET /social-ops/metrics`.

#### Scenario: Métricas tab has no data yet
- **WHEN** the backend returns zero metrics and zero publications
- **THEN** the tab shows an empty state with a "Simular métricas" action instead of a broken/blank table

### Requirement: Aprobaciones tab is the HITL gate
The Aprobaciones tab SHALL list pending drafts of all types from `GET /social-ops/approvals`, and every approve/reject action SHALL call `POST /social-ops/approvals/{type}/{id}/approve` or `/reject` — no draft-creation action anywhere in Social Content Ops SHALL bypass this gate.

#### Scenario: A lead-reply draft requires approval before sending
- **WHEN** a "Draft reply" action creates a lead reply draft
- **THEN** the draft has status `pending_approval` and only becomes actionable after an explicit approve action on the Aprobaciones tab
