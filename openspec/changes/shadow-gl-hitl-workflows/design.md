# Design: Shadow GL HITL Workflows (Phase 6)

**Change ID:** `shadow-gl-hitl-workflows`  
**Status:** Design  
**Date:** 2026-06-25

## Architecture Decisions

### Decision D1: Approval Queue as First-Class Storage

**Choice:** Parsing errors create `approval_queue` records, not immediate 400 responses.

**Rationale:**
- Maintains audit trail: who approved/rejected, when, why
- Enables batch processing: admin can review multiple errors at once
- Decouples parsing from decision: error detection ≠ error response
- Aligns with HITL philosophy: humans make the call, system enforces it

**Consequence:** `approval_queue` becomes primary journal for discrepancies; periodic cleanup job archives resolved entries.

### Decision D2: Hermes WebSocket for Real-Time Notifications

**Choice:** Send approval requests to Hermes gateway (:8642) via WebSocket.

**Rationale:**
- Hermes is local-only (data sovereignty) → no cloud data transmission
- WebSocket enables real-time UI updates without polling
- Hermes is Nous native → Contexia provides config + FastAPI wiring only (no frontend build)
- Gateway handles protocol, workspace provides UI — clear separation

**Contract (TBD with Hermes team):**

**Request (antigravity-app → Hermes gateway):**
```json
{
  "type": "approval_request",
  "approval_queue_id": "uuid",
  "tenant_id": "uuid",
  "action_type": "review_accounting_entry",
  "data": {
    "entry_ref": "DOC-001",
    "error": "Imbalanced entry: debit=85000000, credit=84000000",
    "raw_input": "CSV line or XML snippet",
    "remediation": "Verify account codes 1105 and 4105 are correct"
  },
  "priority": "normal",
  "created_at": "2026-06-25T10:30:00Z"
}
```

**Callback (Hermes → antigravity-app):**
```json
{
  "type": "approval_decision",
  "approval_queue_id": "uuid",
  "status": "approved" | "rejected",
  "reviewer_id": "uuid",
  "reason": "Account codes verified against COA; re-balanced",
  "decided_at": "2026-06-25T10:35:00Z"
}
```

### Decision D3: Two-Phase Persistence (Parse → Store)

**Choice:** Separate parsing from storage; only store after approval.

**Rationale:**
- Parsing is idempotent (can retry without risk)
- Storage is consequential (creates audit trail)
- Decouples validation from decision

**Flow:**
1. Parse CSV/XML → detect error
2. Create `approval_queue` record with error + raw data
3. Send to Hermes
4. User approves → re-parse + insert to `erp_journal_entries` + `erp_journal_lines`
5. User rejects → mark queue row as rejected, notify admin

### Decision D4: Persistence Decision Gate

**Choice:** Approval status determines if entry is persisted.

**Rationale:**
- Approved = trust the entry; persist it
- Rejected = capture reason; don't persist (admin fixes upstream + reuploads)

**Implementation:**
```python
# After approval_decision callback
if approval_queue.status == "approved":
    # Re-parse from approval_queue.data, insert
    entry = parse_siigo_csv(approval_queue.data["raw_csv"])
    ingest_entry(tenant_id, entry)
elif approval_queue.status == "rejected":
    # Log rejection, don't insert
    logger.info(f"Entry {approval_queue.id} rejected: {approval_queue.reason}")
    # Notify admin to fix upstream
```

### Decision D5: Audit Trail & Compliance

**Choice:** `approval_queue` is the system of record for discrepancies.

**Schema additions (if not already present):**
```sql
ALTER TABLE approval_queue ADD COLUMN reason TEXT;
ALTER TABLE approval_queue ADD COLUMN reviewed_at TIMESTAMP;
ALTER TABLE approval_queue ADD COLUMN reviewer_id UUID REFERENCES users(id);
```

**Queryable audit:**
- `SELECT * FROM approval_queue WHERE status = 'rejected' AND created_at > NOW() - INTERVAL '7 days'`
- Finance can export approval history for SOX compliance

### Decision D6: Error Scenarios & Fallbacks

**Scenario 1: Hermes not reachable**
- Log error, create approval_queue row anyway
- Return 202 (Accepted, processing async) to client
- Retry WebSocket send on next heartbeat

**Scenario 2: Approval callback never arrives**
- Approval_queue row stays in "pending" for escalation (Phase 7)
- Admin manually resolves via dashboard (future)

**Scenario 3: Parallel approvals on same entry**
- Prevention: UNIQUE constraint on approval_queue.id (primary key)
- First approval wins, second approval receives 409 (Conflict)

## Data Flow Diagram

```
CSV Upload
    ↓
[Parse Siigo CSV]
    ↓
Validation OK? 
  ├─ YES → Insert to erp_journal_entries/lines → 200 OK
  └─ NO → Create approval_queue row → Send to Hermes (WebSocket)
             ↓
          [Hermes UI]
             ↓
       User Approve/Reject
             ↓
       Callback to antigravity-app
             ↓
    Approve: Re-parse + Insert to erp_journal_entries/lines
    Reject: Log + Notify admin
```

## Files to Modify

| File | Change | Lines |
|------|--------|-------|
| `apps/backend/services/shadow_gl_service.py` | Add `_create_approval_queue()`, update `ingest_siigo_csv()` + `ingest_dian_xml()` | ~50 |
| `apps/backend/presentation/shadow_gl_endpoints.py` | Add WebSocket callback handler for approval decisions | ~40 |
| `apps/backend/core/hermes_client.py` | New: WebSocket client for approval notifications | ~60 |
| `apps/backend/tests/test_shadow_gl_siigo_csv.py` | Add approval_queue tests | ~80 |
| `apps/backend/migrations/0017_approval_queue_extended.sql` | Add reason, reviewed_at, reviewer_id columns if missing | ~10 |

## Files to Create

| File | Purpose |
|------|---------|
| `docs/hermes-integration-guide.md` | Contract + WebSocket message format for approval workflows |
| `openspec/changes/shadow-gl-hitl-workflows/reports/YYYY-MM-DD-deployment.md` | Deployment verification (Stage 11) |

## Non-Functional Requirements

| Aspect | Requirement |
|--------|-------------|
| **Latency** | Approval request to Hermes: < 100ms; callback: < 200ms |
| **Reliability** | WebSocket: auto-retry on disconnection, exponential backoff |
| **Audit** | 100% of approvals logged with timestamp + reviewer_id |
| **Data Integrity** | Only approved entries reach erp_journal_entries; rejected entries logged forever |
| **Security** | Hermes API token validated; approval_queue data masked for PII if needed |

## Testing Strategy

| Level | Scope | Gate |
|-------|-------|------|
| **Unit** | Parse + approval_queue creation (no DB) | RUN_SHADOW_GL=1 |
| **Integration** | Approval_queue persistence (real Supabase) | RUN_SHADOW_GL=1 + SUPABASE_SERVICE_ROLE_KEY |
| **E2E** | Full workflow: parse → approve in Hermes UI → persist | Manual, requires Hermes running |
| **Smoke** | Production: approval flow works live | Post-deployment verification |

## Hermes Dependency

**Requirement:** Hermes Workspace running locally
- Gateway: `http://127.0.0.1:8642` (WebSocket endpoint)
- Workspace UI: `http://localhost:3000` (user approval interface)

**If Hermes unavailable:** Phase 6 cannot proceed; fallback is manual approval (non-scalable).

## Rollback Plan

### If approval_queue causes issues:

```bash
# 1. Revert code
git revert <commit-sha>

# 2. Push to main
git push origin main

# 3. Verify old behavior (errors go to 400, no queue)
curl -X POST -d @bad.csv https://antigravity-app-production-175a.up.railway.app/api/v1/shadow-gl/siigo-csv/ingest
# → Expected: 400 Bad Request

# 4. Cleanup (optional)
DELETE FROM approval_queue WHERE created_at > NOW() - INTERVAL '1 day';
```

**RTO:** < 10 minutes  
**RPO:** No data loss (approval_queue is new, no consumers yet)

## Open Questions

1. **Hermes WebSocket authentication:** How does antigravity-app authenticate to Hermes gateway? Token in header? Bearer scheme?
2. **Message versioning:** If Hermes API changes, how are old messages handled? Semver in message type?
3. **Approval timeout:** If user doesn't approve within X minutes, should we auto-reject or escalate?
4. **Batch approvals:** Can a user approve multiple entries at once via Hermes UI?

→ Defer to Stage 4-6 implementation phase once Hermes team provides contract details.
