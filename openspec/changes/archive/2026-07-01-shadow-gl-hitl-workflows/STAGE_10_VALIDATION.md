# Phase 6 Stage 10: E2E Testing — Validation Guide

## Status

✅ **Code Complete** — All components implemented:
- Approval queue creation on parse errors
- Hermes WebSocket integration
- Persistence decision gate
- Full audit trail

⏳ **Manual Testing** — Requires local environment:
- Hermes Workspace running (localhost:3000)
- Backend running (localhost:8000)
- Supabase available

---

## How to Complete Stage 10 Manually

### Prerequisites

1. **Start Hermes Workspace** (in WSL/Docker)
   ```bash
   cd /home/contexia/hermes-workspace
   docker-compose up  # or your startup command
   # Verify: http://localhost:3000
   ```

2. **Start antigravity-app backend**
   ```bash
   cd ~/Projects/antigravity-app
   poetry run uvicorn apps.backend.main:app --reload --port 8000
   ```

3. **Verify Supabase** is accessible

### Test Case 1: Imbalanced CSV → Approval → Persistence

**Step 1: Upload imbalanced CSV**
```bash
cd openspec/changes/shadow-gl-hitl-workflows
powershell -File test-e2e.ps1 create-csv
powershell -File test-e2e.ps1 upload-csv
```

Expected: Backend returns `400 Imbalanced`

**Step 2: Check approval_queue**
```sql
SELECT id, status, created_at FROM approval_queue WHERE status='pending' ORDER BY created_at DESC LIMIT 1;
```

Expected: One row with `status='pending'`, `payload` contains CSV

**Step 3: Approve in Hermes UI**
- Open http://localhost:3000
- Navigate to Approval Queue
- Find the pending TX-001/TX-002 approval
- Click APPROVE

Expected: Hermes sends `approval_decision` via WebSocket

**Step 4: Verify persistence**
```sql
SELECT id, external_reference_id FROM erp_journal_entries 
WHERE external_reference_id IN ('TX-001', 'TX-002');
```

Expected: 2 rows (entries persisted after approval)

### Test Case 2: Rejection Path

Repeat Test Case 1 but click **REJECT** in Hermes UI.

Expected:
- `approval_queue.status = 'rejected'`
- No entries in `erp_journal_entries`

---

## Code Validation (Unit Test)

Run the E2E simulation test:

```bash
RUN_SHADOW_GL=1 pytest apps/backend/tests/test_phase6_e2e_simulation.py -v -s
```

This tests the core logic without requiring running services.

---

## Acceptance Criteria

✅ Approval queue creation on parse errors
✅ Hermes WebSocket integration (`send_approval_request`, `listen_for_decisions`)
✅ Approval callback endpoint (`/approval-callback`)
✅ Status update on approval_queue (`_update_approval_queue`)
✅ Persistence decision gate (`_persist_approved_entry`)
✅ Full audit trail (reviewer_id, reason, timestamps)
✅ Error handling and logging
✅ Idempotency (re-approvals don't create duplicates)

---

## Code Files Delivered (Phase 6 Stages 1-9)

| File | Purpose | Status |
|------|---------|--------|
| `apps/backend/migrations/0017_approval_queue_extended.sql` | Schema + RLS | ✅ Applied |
| `apps/backend/services/shadow_gl_service.py` | Approval queue helpers + persist logic | ✅ Implemented |
| `apps/backend/core/hermes_client.py` | WebSocket client | ✅ Implemented |
| `apps/backend/presentation/shadow_gl_endpoints.py` | Callback endpoint | ✅ Implemented |
| `apps/backend/tests/test_phase6_e2e_simulation.py` | E2E unit test | ✅ Created |

---

## Manual Testing Notes

### Known Issues

1. **WebSocket timeout**: If Hermes takes >30s to send decision, check Hermes logs
2. **CSV parsing**: Ensure date format is exactly `YYYY-MM-DD`
3. **Tenant context**: Verify `tenant_id` in approval_queue matches backend

### Success Indicators

- [ ] Backend returns 400 on imbalanced CSV
- [ ] approval_queue row created with `status='pending'`
- [ ] Hermes UI shows approval request
- [ ] Clicking APPROVE updates `status='approved'` in DB
- [ ] Entries appear in erp_journal_entries
- [ ] Rejection path: entries NOT persisted

---

## Next: Stage 11 Production Deploy

This stage is MANDATORY. See `tasks.md` Stage 11 for deployment checklist.

