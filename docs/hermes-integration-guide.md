# Hermes Integration Guide — Approval Workflows

**Version:** 1.0  
**Date:** 2026-06-25  
**Status:** Phase 6 (HITL Workflows)

## Overview

This guide documents the WebSocket contract between antigravity-app (backend) and Hermes Workspace (approval UI) for human-in-the-loop accounting entry approval workflows.

## Architecture

```
antigravity-app                  Hermes Workspace
   (FastAPI)                     (Nous native app)
      │                              │
      ├─ Parser                      │
      ├─ Approval Queue              │
      │                              │
      └──── WebSocket ──────────────→ Gateway (:8642)
                                        │
                                        └── Dashboard UI (:3000)
                                            [User approves/rejects]
                                        │
                                        └──→ Callback WebSocket
                                        │
            ←──────────────────────────┘
      │
      └─ Update approval_queue.status
      └─ Persist or log (decision gate)
```

## WebSocket Connection

### Endpoint

```
ws://127.0.0.1:8642/ws/approvals
```

### Subprotocol

```
hermes.approval.v1
```

### Authentication

**Bearer Token (in connection header):**

```
Authorization: Bearer contexia-dev-token-123
```

(Token configured in `.env` as `HERMES_API_TOKEN`)

### Connection Lifecycle

1. **Client (antigravity-app) initiates:**
   ```python
   ws = await websockets.connect(
       "ws://127.0.0.1:8642/ws/approvals",
       subprotocols=["hermes.approval.v1"],
       extra_headers={
           "Authorization": "Bearer contexia-dev-token-123"
       }
   )
   ```

2. **Server (Hermes) responds with ACK**
3. **Client sends approval_request**
4. **Server routes to dashboard UI**
5. **User approves/rejects**
6. **Server sends approval_decision callback**
7. **Client processes and closes**

---

## Message Format: approval_request

**Direction:** antigravity-app → Hermes

**When:** Accounting entry fails validation (parse error, imbalance, etc.)

**Schema:**

```json
{
  "type": "approval_request",
  "approval_queue_id": "550e8400-e29b-41d4-a716-446655440000",
  "tenant_id": "e2d30d09-6b96-4ebe-a79a-c6aff7a5df34",
  "action_type": "review_accounting_entry",
  "data": {
    "entry_ref": "INV-001",
    "error": "Imbalanced entry: debit=85000000, credit=84000000",
    "raw_input": "transaction_date,account_code,debit_amount,credit_amount,memo,external_reference_id,currency_code\n2026-06-25,1105,850000.00,,Invoice,INV-001,COP\n2026-06-25,4105,,840000.00,Revenue,INV-001,COP",
    "timestamp": "2026-06-25T10:30:00Z",
    "remediation": "Verify account codes 1105 and 4105; re-balance debit/credit amounts"
  },
  "priority": "normal",
  "created_at": "2026-06-25T10:30:00Z"
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | ✅ | Always `"approval_request"` |
| `approval_queue_id` | UUID | ✅ | Reference to `approval_queue.id` in antigravity-app |
| `tenant_id` | UUID | ✅ | Tenant context (for multi-tenant UI isolation) |
| `action_type` | string | ✅ | Always `"review_accounting_entry"` (extensible for future) |
| `data` | object | ✅ | Contains error details + raw input |
| `data.entry_ref` | string | ✅ | Document/transaction reference (e.g., INV-001, DOC-123) |
| `data.error` | string | ✅ | Human-readable error message |
| `data.raw_input` | string | ✅ | Original CSV/XML that failed parsing |
| `data.timestamp` | string | ✅ | When error was detected (ISO 8601) |
| `data.remediation` | string | ⚠️ | Suggested fix (optional, helps user) |
| `priority` | string | ⚠️ | `"normal"` \| `"high"` (for sorting in UI) |
| `created_at` | string | ✅ | Timestamp of approval_request (ISO 8601) |

### Example: CSV Siigo Parse Error

```json
{
  "type": "approval_request",
  "approval_queue_id": "550e8400-e29b-41d4-a716-446655440000",
  "tenant_id": "e2d30d09-6b96-4ebe-a79a-c6aff7a5df34",
  "action_type": "review_accounting_entry",
  "data": {
    "entry_ref": "DOC-0892",
    "error": "Row 3: Invalid date format '2026/06/25'; expected ISO 8601 (YYYY-MM-DD)",
    "raw_input": "transaction_date,account_code,debit_amount,credit_amount,memo,external_reference_id,currency_code\n2026-06-25,1105,50000.00,,Transfer,DOC-0892,COP\n2026-06-25,4105,,50000.00,Received,DOC-0892,COP",
    "timestamp": "2026-06-25T14:22:15Z",
    "remediation": "Fix date in source spreadsheet to YYYY-MM-DD format, then re-upload"
  },
  "priority": "normal",
  "created_at": "2026-06-25T14:22:15Z"
}
```

### Example: XML DIAN Parse Error

```json
{
  "type": "approval_request",
  "approval_queue_id": "550e8400-e29b-41d4-a716-446655440001",
  "tenant_id": "e2d30d09-6b96-4ebe-a79a-c6aff7a5df34",
  "action_type": "review_accounting_entry",
  "data": {
    "entry_ref": "CUFE-ABC123XYZ",
    "error": "Missing required field: AccountingCustomerParty NIT",
    "raw_input": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<Invoice xmlns=\"urn:oasis:names:specification:ubl:schema:xsd:Invoice-2\">...",
    "timestamp": "2026-06-25T14:25:00Z",
    "remediation": "DIAN invoice missing receiver NIT. Contact DIAN provider."
  },
  "priority": "high",
  "created_at": "2026-06-25T14:25:00Z"
}
```

---

## Message Format: approval_decision

**Direction:** Hermes → antigravity-app (callback)

**When:** User approves or rejects entry in Hermes UI

**Schema:**

```json
{
  "type": "approval_decision",
  "approval_queue_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "approved",
  "reviewer_id": "550e8400-e29b-41d4-a716-446655440099",
  "reviewer_name": "Juan Pérez (Finance)",
  "reason": "Verified account codes against COA; re-balanced amounts",
  "decided_at": "2026-06-25T10:35:00Z"
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | ✅ | Always `"approval_decision"` |
| `approval_queue_id` | UUID | ✅ | Matches `approval_request.approval_queue_id` |
| `status` | string | ✅ | `"approved"` or `"rejected"` |
| `reviewer_id` | UUID | ✅ | User ID in Hermes (for audit trail) |
| `reviewer_name` | string | ⚠️ | Display name (optional, for logging) |
| `reason` | string | ✅ | Why approved/rejected (stored in audit trail) |
| `decided_at` | string | ✅ | When decision was made (ISO 8601) |

### Example: Approved

```json
{
  "type": "approval_decision",
  "approval_queue_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "approved",
  "reviewer_id": "550e8400-e29b-41d4-a716-446655440099",
  "reviewer_name": "Juan Pérez",
  "reason": "Verified amounts with bank statement; entry is correct",
  "decided_at": "2026-06-25T10:35:00Z"
}
```

### Example: Rejected

```json
{
  "type": "approval_decision",
  "approval_queue_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "rejected",
  "reviewer_id": "550e8400-e29b-41d4-a716-446655440099",
  "reviewer_name": "Juan Pérez",
  "reason": "Entry doesn't match invoice; request sender correct it and re-upload",
  "decided_at": "2026-06-25T10:35:00Z"
}
```

---

## Error Codes & Handling

### Connection Errors

| Code | Meaning | Retry |
|------|---------|-------|
| `1000` | Normal close | No |
| `1006` | Abnormal close | Yes (exponential backoff) |
| `1011` | Server error | Yes |

### Message Errors

**Invalid JSON:**
```json
{
  "type": "error",
  "code": "INVALID_JSON",
  "message": "Failed to parse request JSON",
  "approval_queue_id": null
}
```

**Missing required field:**
```json
{
  "type": "error",
  "code": "MISSING_FIELD",
  "message": "Missing required field: approval_queue_id",
  "approval_queue_id": null
}
```

**Duplicate approval_queue_id:**
```json
{
  "type": "error",
  "code": "DUPLICATE_REQUEST",
  "message": "Approval request already processing for this queue_id",
  "approval_queue_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Client Response (ACK)

After receiving approval_decision, antigravity-app must ACK:

```json
{
  "type": "ack",
  "approval_queue_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processed",
  "processed_at": "2026-06-25T10:35:01Z"
}
```

---

## Fallback Behavior

### If Hermes is unreachable

1. Log error: `HERMES_UNREACHABLE: Connection refused to 127.0.0.1:8642`
2. Create approval_queue row anyway (will have `status = "pending"`)
3. Return HTTP 202 (Accepted) to client
4. On next heartbeat (every 5 min), retry WebSocket connection
5. Once Hermes is back, approval_request will be sent with existing queue_id

### If approval_decision never arrives

1. approval_queue row stays in `status = "pending"`
2. Admin can manually resolve via dashboard (Phase 7)
3. Escalation: After 24h, create alert in `audit_log`

### If approval_request is lost

1. Hermes may re-request: "What's the status of queue_id X?"
2. antigravity-app responds with current `approval_queue.status`
3. If already approved/rejected, Hermes acknowledges and updates its UI

---

## Testing

### Manual Test: approval_request

```bash
# Start Hermes locally
cd ~/hermes-workspace && pnpm dev

# Upload bad CSV to trigger approval_request
curl -X POST \
  -H "Content-Type: text/csv" \
  https://antigravity-app-production-175a.up.railway.app/api/v1/shadow-gl/siigo-csv/ingest \
  --data-binary @test_imbalanced.csv

# Check Hermes UI at http://localhost:3000
# Should see approval request for the entry
```

### Manual Test: approval_decision

```bash
# In Hermes UI, click "Approve" for the entry
# Backend should log: "Approval decision received: queue_id-uuid → approved"
# Verify entry was persisted: curl https://... | grep INV-001
```

### Integration Test (Python)

```python
import asyncio
import json
import websockets

async def test_hermes_contract():
    async with websockets.connect(
        "ws://127.0.0.1:8642/ws/approvals",
        subprotocols=["hermes.approval.v1"],
        extra_headers={"Authorization": "Bearer contexia-dev-token-123"}
    ) as ws:
        # Send approval_request
        request = {
            "type": "approval_request",
            "approval_queue_id": "test-queue-001",
            "tenant_id": "test-tenant-001",
            "action_type": "review_accounting_entry",
            "data": {
                "entry_ref": "TEST-001",
                "error": "Test error",
                "raw_input": "test_data",
                "timestamp": "2026-06-25T00:00:00Z"
            },
            "priority": "normal",
            "created_at": "2026-06-25T00:00:00Z"
        }
        
        await ws.send(json.dumps(request))
        print("Sent approval_request")
        
        # Listen for decision (or error)
        while True:
            message = await ws.recv()
            data = json.loads(message)
            print(f"Received: {data['type']}")
            
            if data.get("type") == "approval_decision":
                print(f"Decision: {data['status']}")
                
                # Send ACK
                ack = {
                    "type": "ack",
                    "approval_queue_id": data["approval_queue_id"],
                    "status": "processed",
                    "processed_at": "2026-06-25T00:00:01Z"
                }
                await ws.send(json.dumps(ack))
                break
            elif data.get("type") == "error":
                print(f"Error: {data['message']}")
                break

asyncio.run(test_hermes_contract())
```

---

## Known Limitations & Future Work

1. **Timeout handling:** No auto-escalation if user doesn't approve within X minutes (Phase 7)
2. **Batch approvals:** Can't approve multiple entries at once yet
3. **Rich UI:** Currently plain JSON messages; Phase 7 may add HTML/Markdown formatting
4. **Rate limiting:** No limits on approval_request frequency (Phase 7)

---

## Support & Debugging

### Check Hermes gateway health

```bash
curl -s http://127.0.0.1:8642/health
# Expected: {"status": "healthy", "timestamp": "..."}
```

### Check antigravity-app WebSocket logs

```bash
# In Railway logs, filter for "hermes_client" or "approval_decision"
railway logs -f | grep -i hermes
```

### Verify approval_queue table

```sql
SELECT id, tenant_id, status, created_at, reviewed_at, reason
FROM public.approval_queue
WHERE created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-06-25 | Initial contract for Phase 6 |

---

**Next:** Phase 6 Implementation (Stage 1–11)
