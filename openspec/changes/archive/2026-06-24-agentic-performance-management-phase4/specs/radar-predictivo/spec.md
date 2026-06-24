## ADDED Requirements

### Requirement: Radar Predictivo computes a risk score and cashflow forecast
The system SHALL compute a deterministic risk score (0-100) and a short-horizon cashflow forecast from Shadow GL history, exposed as a read endpoint.

#### Scenario: Risk score computed from recent discrepancy rate
- **WHEN** a client calls `GET /api/v1/agents/radar-predictivo/risk-score`
- **THEN** system returns a `risk_score` between 0 and 100 derived from the tenant's recent `shadow_gl_discrepancies` rate and amount variance
- **AND** the computation is deterministic (same inputs always produce the same score)

#### Scenario: Cashflow forecast returned alongside risk score
- **WHEN** the risk-score endpoint is called
- **THEN** response also includes a `forecast_30d_minor` projection based on historical net flux from Pulso Diario data

### Requirement: Radar escalates to HITL only when risk crosses the critical threshold
The system SHALL apply conditional HITL: scores below the critical threshold return immediately with no queue entry; scores at or above it create an Approval Queue entry for human review.

#### Scenario: Risk below threshold returns without HITL
- **WHEN** computed `risk_score < 80`
- **THEN** the response is returned directly
- **AND** no `approval_queue` row is created

#### Scenario: Risk at or above threshold creates a review entry
- **WHEN** computed `risk_score >= 80`
- **THEN** system enqueues an `approval_queue` row with `draft_type = 'risk_review'` and the score/forecast as payload
- **AND** the HTTP response includes `hitl_triggered: true` and the queue entry id

#### Scenario: Repeated critical scores do not spam the queue
- **WHEN** an unresolved `risk_review` entry already exists for the tenant
- **THEN** a new critical score SHALL NOT create a duplicate queue entry
