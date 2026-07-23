## ADDED Requirements

### Requirement: Draft listing is scoped to the caller's tenant
`GET /api/v1/approval-queue` SHALL pass the caller's resolved tenant_id into
`ApprovalQueueService.list_drafts`, which already supports tenant filtering.

#### Scenario: Two tenants see disjoint draft lists
- **WHEN** tenant A and tenant B each have their own enqueued drafts
- **AND** a caller resolved to tenant A calls `GET /api/v1/approval-queue`
- **THEN** the response includes only tenant A's drafts, never tenant B's

#### Scenario: Unresolved authenticated caller sees an empty list
- **WHEN** an authenticated caller has no resolvable tenant membership
- **THEN** `GET /api/v1/approval-queue` returns an empty list, never Cliente Cero's drafts

### Requirement: Enqueue records the caller's tenant
`POST /api/v1/approval-queue/enqueue` SHALL pass the caller's resolved tenant_id into
`ApprovalQueueService.enqueue_draft`, which SHALL require it explicitly (no internal
Cliente Cero default).

#### Scenario: Enqueued draft carries the caller's tenant, not Cliente Cero
- **WHEN** an authenticated caller resolved to tenant A enqueues a draft
- **THEN** the persisted draft's `tenant_id` is tenant A's, not Cliente Cero's

### Requirement: Approve and reject verify draft ownership
`POST /api/v1/approval-queue/approve` and `/reject` SHALL fetch the target draft and
compare its tenant_id against the caller's resolved tenant before acting.

#### Scenario: Own-tenant draft is approved
- **WHEN** a caller resolved to tenant A approves a draft belonging to tenant A
- **THEN** the draft is approved normally

#### Scenario: Another tenant's draft id returns 404
- **WHEN** a caller resolved to tenant A attempts to approve or reject a draft belonging to
  tenant B
- **THEN** the endpoint returns HTTP 404
