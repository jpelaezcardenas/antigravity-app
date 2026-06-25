# Proposal: Shadow GL HITL Workflows (Phase 6)

**Change ID:** `shadow-gl-hitl-workflows`  
**Status:** Proposal  
**Date:** 2026-06-25  
**Owner:** Juan David Peláez Cárdenas  
**Scope:** Phase 6 (post Phase 5 real data ingestion)

## Problem Statement

Phase 5 successfully deployed dual ingestion pipelines (XML DIAN + CSV Siigo) and validated with real data (20 transactions). However, the current implementation **lacks human-in-the-loop (HITL) approval workflows**:

- Parsing errors (imbalanced entries, invalid account codes) return HTTP 400 immediately
- No approval queue — rejected entries are discarded without audit trail
- No Hermes integration — manual accounting errors bypass review
- Accounting data quality depends entirely on upstream export accuracy (no human verification)

**Risk:** Invalid accounting entries could be rejected, requiring manual rework with no clear audit trail.

## Goal

Integrate **Hermes Workspace for HITL approval workflows** into the Shadow GL pipeline:

1. When parsing detects an error, create an `approval_queue` record (not error 400)
2. Send approval request to Hermes Workspace (WebSocket)
3. User reviews entry in Hermes UI and approves/rejects
4. Decision gate: approved entries persist to `erp_journal_entries` + `erp_journal_lines`; rejected entries are logged but not persisted
5. Audit trail: `approval_queue.reviewed_at`, `reviewer_id`, `reason` capture full history

## Success Criteria

- ✅ `approval_queue` table schema verified (exists from Phase 4)
- ✅ Approval logic implemented: parse error → create queue row
- [ ] Hermes WebSocket wired: queue row → Hermes notification
- [ ] Decision gate implemented: approve/reject → persist/log
- [ ] E2E test with real Hermes approval workflow
- [ ] Deployed to production + verified live
- [ ] Audit trail: approve/reject decisions logged + queryable

## Out of Scope

- Auto-escalation/timeout on pending approvals (Phase 7)
- Cost tracking for approval operations (agent-operations-multitenant-security)
- Live DIAN webhook (Phase 7)
- Dashboard UI for approval analytics

## Technical Approach

### 1. Approval Queue Record Creation

When `ingest_siigo_csv()` or `ingest_dian_xml()` detects an error:
- Instead of raising exception → return error 400
- Create row in `approval_queue`:
  ```python
  approval_queue.insert({
    "tenant_id": tenant_id,
    "action_type": "review_accounting_entry",
    "data": {
      "entry_ref": ref_id,
      "error": str(exception),
      "raw_csv_line": csv_line,  # or raw_xml
      "timestamp": datetime.now().isoformat()
    },
    "status": "pending",
    "created_at": datetime.now()
  })
  ```

### 2. Hermes WebSocket Integration

Send approval request to Hermes gateway (:8642):
- Message type: `approval_request`
- Payload: approval_queue record + remediation hints
- Hermes displays in UI, user approves/rejects
- Callback: `approval_decision` message → update `approval_queue.status`

### 3. Persistence Decision Gate

After approval_queue decision:
- **Approved:** Re-parse entry from `approval_queue.data`, insert to `erp_journal_entries` + `erp_journal_lines`
- **Rejected:** Mark `status = "rejected"`, store reason, return 400 with explanation

## Stakeholder Impact

- **Admin/Finance:** Accounting errors get human review before persistence
- **Audit:** Full trail of approved/rejected entries with reviewer info
- **Hermes Team:** New integration point validates WebSocket governance contract

## Dependencies

- Phase 5 complete (dual ingestion endpoints live)
- Hermes Workspace running locally (WSL port 3000, gateway :8642)
- `approval_queue` table schema exists (Phase 4 migration 0014)

## Timeline

- Design phase: 1 session (this document)
- Implementation + testing: 3–5 sessions (TDD, integration, E2E)
- Production deployment: Stage 11 (1–2 hours)
- Target completion: 2026-06-30
