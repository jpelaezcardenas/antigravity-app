# centinela-alerts Specification

## Purpose
TBD - created by archiving change add-pgvector-agent-critic-phase-3. Update Purpose after archive.
## Requirements
### Requirement: Centinela enriches alerts with similar past decisions
When Centinela detects a DIAN ↔ Siigo anomaly, it queries the knowledge base for similar past approvals and includes them in the alert payload.

#### Scenario: Centinela alert includes similar decisions
- **WHEN** Centinela detects a transaction mismatch
- **THEN** system generates embedding for the transaction
- **AND** calls `/api/v1/kb/search-similar` to find related past approvals
- **AND** alert context includes: `{ similar_decisions: [...], best_match_confidence: 0.85 }`

#### Scenario: Resolution Agent can reference historical approval
- **WHEN** similar_decisions[0] is returned with high confidence (> 0.8)
- **THEN** Resolution Agent can optionally base new draft on historical approval reason
- **AND** new draft can inherit accounting treatment from similar case

#### Scenario: No similar decisions found
- **WHEN** Centinela query returns no matches (< threshold)
- **THEN** alert is still sent, similar_decisions = []
- **AND** Resolution Agent drafts from scratch (normal flow)

### Requirement: Centinela logs similarity match metrics
The system SHALL record how often similar decisions are found and used.

#### Scenario: Match metrics logged
- **WHEN** Centinela finds similar decisions for an alert
- **THEN** logs entry includes: transaction_id, best_similarity_score, num_matches, alert_timestamp

#### Scenario: Ops team can monitor compounding memory growth
- **WHEN** weekly metrics aggregated
- **THEN** shows: "60% of alerts now have similar decisions (up from 10% last month)"
- **AND** ops team can see knowledge base is learning

### Requirement: Centinela alert payload compatible with Hermes UI
The similarity search data in Centinela alert is formatted for display in Hermes Workspace Approval Queue UI.

#### Scenario: Alert JSON schema includes similar_decisions array
- **WHEN** Centinela publishes alert to Telegram or Hermes
- **THEN** JSON includes: `{ similar_decisions: [{ content, similarity, decided_by, timestamp }, ...] }`
- **AND** Hermes UI can render "Similar approvals" card inline with Centinela alert

