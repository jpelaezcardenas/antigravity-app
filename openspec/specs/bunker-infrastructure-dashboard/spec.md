### Requirement: Infrastructure summary cards
The Dashboard section SHALL display 4 summary cards: estimated monthly cloud spend, count of production services, count of active AI layers, and count of on-prem/local agents (Hermes).

#### Scenario: Dashboard section shows summary cards
- **WHEN** the user opens the "Dashboard" section
- **THEN** 4 summary cards are visible showing the monthly cloud spend estimate, production service count, active AI layer count, and local agent count, each using this project's existing `@theme` design tokens

### Requirement: Per-service infrastructure cards
The Dashboard section SHALL display individual service cards grouped by category (Cloud Infrastructure: Vercel, Railway, Supabase; AI Layer: GLM, Groq, OpenRouter; Tools/Dev: Claude/Anthropic, GCP, Hermes Desktop), each showing service name, status badge, key metrics, and estimated monthly cost.

#### Scenario: Service card shows status and cost
- **WHEN** the user views the Dashboard section
- **THEN** each service card (e.g. Vercel) shows a status badge (e.g. LIVE, WARNING, LOCAL), at least one metric, and an estimated monthly cost value

### Requirement: Cost breakdown visualization without external chart library
The Dashboard section SHALL display a visual cost breakdown (relative spend per service) using this project's design tokens, without loading Chart.js or any CDN script.

#### Scenario: Cost breakdown renders without external dependencies
- **WHEN** the Dashboard section loads
- **THEN** a cost breakdown visualization is visible built from native elements styled with existing tokens, and no `<script src="https://...">` or new npm chart dependency is present

### Requirement: Technical stack summary table
The Dashboard section SHALL display a table summarizing the full technical stack (layer, technology, function, estimated cost, status) across frontend, backend, database, AI, and tooling layers.

#### Scenario: Stack table lists all layers
- **WHEN** the user views the Dashboard section
- **THEN** a table is visible with one row per stack layer (Frontend, Backend/API, Database, AI Principal, AI Fallback, Dev Copilot, AI Orchestration, GCP), each showing technology, function, cost, and status

### Requirement: Alerts and pending actions
The Dashboard section SHALL display a list of infrastructure alerts/pending actions (e.g. expired tokens, missing auth hardening), each with a severity indicator (danger/warning/ok).

#### Scenario: Alerts panel shows pending actions
- **WHEN** the user views the Dashboard section
- **THEN** an alerts panel is visible listing pending infrastructure items, each visually distinguished by severity (danger, warning, or ok)

### Requirement: Static data, no backend calls
All Dashboard content SHALL be static/hardcoded values with no fetch to any backend or third-party API, consistent with the mock-first rule governing the rest of `contexia-app`.

#### Scenario: Dashboard loads with no network requests
- **WHEN** the Dashboard section renders
- **THEN** no network request is made to fetch dashboard data (all values are inline/hardcoded in the component)
