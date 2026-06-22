# similarity-search Specification

## Purpose
TBD - created by archiving change add-pgvector-agent-critic-phase-3. Update Purpose after archive.
## Requirements
### Requirement: Similarity search returns past approved decisions
The system SHALL provide endpoint `/api/v1/kb/search-similar` that queries the knowledge base for decisions similar to a query embedding.

Request:
```json
{
  "query_embedding": [0.1, 0.2, ..., 1536 dims],
  "limit": 5,
  "threshold": 0.7
}
```

Response:
```json
{
  "matches": [
    {
      "id": "uuid",
      "content": "Contexia's own invoice, matches DIAN",
      "similarity": 0.85,
      "approval_id": "draft-uuid",
      "decided_by": "contador@contexia.com",
      "timestamp": "2026-06-20T14:30:00Z",
      "confidence": 1.0
    }
  ]
}
```

#### Scenario: Search returns similar decisions
- **WHEN** client calls `/kb/search-similar` with a query embedding
- **THEN** response includes up to N matches where similarity > threshold
- **AND** matches ordered by similarity (highest first)

#### Scenario: Search respects threshold
- **WHEN** `threshold = 0.7` (moderately similar)
- **THEN** only results with similarity >= 0.7 returned
- **AND** higher threshold results in fewer matches

#### Scenario: Empty results when no matches
- **WHEN** query embedding has no similar vectors
- **THEN** response.matches = [] (empty array)

### Requirement: Centinela uses similarity search to propose historical resolutions
The system SHALL integrate similarity search into Centinela alert workflow. When Centinela detects an anomaly, it queries for similar past decisions and includes them in the alert context.

#### Scenario: Similar decision attached to Centinela alert
- **WHEN** Centinela detects DIAN ↔ Siigo mismatch for transaction X
- **THEN** system generates embedding for transaction X
- **AND** queries `/kb/search-similar` with that embedding
- **AND** returns top-3 similar approvals with confidence > 0.7
- **AND** Centinela alert context includes: `{ similar_decisions: [...], historical_match_confidence: 0.82 }`

#### Scenario: Resolution Agent can reuse historical resolution
- **WHEN** Centinela alert includes similar_decisions[0] (highest confidence match)
- **THEN** Resolution Agent can optionally use historical approval reason as baseline
- **AND** human comptroller can fast-track approval if satisfied

#### Scenario: Low confidence matches not included
- **WHEN** similarity search returns matches with confidence < 0.7
- **THEN** these matches are filtered out before including in alert context

### Requirement: Similarity threshold is configurable
The system SHALL expose `PGVECTOR_SIMILARITY_THRESHOLD` environment variable. Default: 0.7.

#### Scenario: Custom threshold via env var
- **WHEN** `PGVECTOR_SIMILARITY_THRESHOLD=0.65` is set in Railway
- **THEN** similarity search uses 0.65 as default threshold
- **AND** can be overridden per request via `threshold` query param

#### Scenario: Threshold drift detection
- **WHEN** threshold is too high (>0.85): too few matches, low recommendation rate
- **THEN** Centinela logs metrics, ops team can tune down to 0.75 or 0.70

### Requirement: Search results include decision metadata
Each match SHALL include approval context so Entidad A can understand why a decision was approved before.

#### Scenario: Metadata helps human decision-making
- **WHEN** Centinela shows match with `decided_by: "contador@example.com", timestamp: "2026-06-01"`
- **THEN** Entidad A can see this was approved by colleague X on date Y
- **AND** can hover/click to see full approval reason if needed

### Requirement: Search is read-only (no side effects)
Similarity search SHALL NOT modify any state. It returns results only. No analytics tracking, no decision updating, no audit logging beyond standard query logs.

#### Scenario: Search does not create new state
- **WHEN** client calls `/kb/search-similar`
- **THEN** no rows inserted/updated/deleted
- **AND** response is deterministic (same query always returns same results)

