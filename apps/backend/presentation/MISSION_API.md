# Mission API (T11.8)

RESTful API for Hermes mission management with real-time WebSocket updates.

## Base URL

```
https://contexia.online/api/v1
```

## Authentication

All endpoints require Bearer token in Authorization header:

```
Authorization: Bearer <JWT_TOKEN>
```

Multi-tenant isolation is enforced via RLS policies.

## Endpoints

### List All Missions

```
GET /missions
```

**Query Parameters:**
- `skip` (optional, int, default: 0) - Pagination offset
- `limit` (optional, int, default: 100, max: 1000) - Max results per page

**Response:**
```json
[
  {
    "id": "mission-qxyz1234",
    "type": "customer_registration",
    "status": "executing",
    "objective": "Register customer@example.com (pro plan)",
    "tasks": [
      {
        "id": "task-001",
        "type": "create_auth_user",
        "operator": "auth_operator",
        "payload": {"email": "customer@example.com"},
        "status": "completed"
      }
    ],
    "checkpoints": [
      {
        "timestamp": "2026-06-23T20:15:30Z",
        "task_type": "auth_operator",
        "status": "✅",
        "proof": {"user_id": "uuid-123"},
        "operator_id": "auth_operator",
        "duration_ms": 120,
        "cost": 0.001
      }
    ],
    "cost": 0.047,
    "cost_breakdown": {
      "auth_operator": 0.001,
      "db_operator": 0.002,
      "comms_operator": 0.01
    },
    "progress": 100.0,
    "created_at": "2026-06-23T20:00:00Z",
    "started_at": "2026-06-23T20:05:00Z",
    "completed_at": "2026-06-23T20:20:00Z",
    "duration_seconds": 900
  }
]
```

**Status:** 200 OK

### Start New Mission

```
POST /missions
```

**Request Body:**
```json
{
  "invite_id": "invite-qxyz1234",
  "customer_email": "customer@example.com",
  "plan": "pro"
}
```

**Response:**
```json
{
  "id": "mission-qxyz1234",
  "type": "customer_registration",
  "status": "pending",
  "objective": "Register customer@example.com (pro plan)",
  "tasks": [],
  "checkpoints": [],
  "cost": 0.0,
  "cost_breakdown": {},
  "progress": 0.0,
  "created_at": "2026-06-23T20:00:00Z"
}
```

**Status:** 200 OK (mission created)

**Status:** 400 Bad Request (invalid plan)

**Status:** 409 Conflict (invite already used)

### Get Mission Details

```
GET /missions/{mission_id}
```

**Path Parameters:**
- `mission_id` (string, required) - Mission ID (e.g., `mission-qxyz1234`)

**Response:**
```json
{
  "id": "mission-qxyz1234",
  "type": "customer_registration",
  "status": "executing",
  "objective": "Register customer@example.com (pro plan)",
  "tasks": [...],
  "checkpoints": [...],
  "cost": 0.047,
  "cost_breakdown": {...},
  "progress": 50.0,
  "created_at": "2026-06-23T20:00:00Z",
  "started_at": "2026-06-23T20:05:00Z"
}
```

**Status:** 200 OK

**Status:** 404 Not Found (mission doesn't exist)

### Get Mission Checkpoints

```
GET /missions/{mission_id}/checkpoints
```

Returns proof of task completion for a mission.

**Response:**
```json
[
  {
    "timestamp": "2026-06-23T20:15:30Z",
    "task_type": "auth_operator",
    "status": "✅",
    "proof": {
      "user_id": "12345678-1234-1234-1234-123456789abc",
      "email": "customer@example.com",
      "created_at": "2026-06-23T20:15:30Z"
    },
    "operator_id": "auth_operator",
    "duration_ms": 120,
    "cost": 0.001
  },
  {
    "timestamp": "2026-06-23T20:15:35Z",
    "task_type": "db_operator",
    "status": "✅",
    "proof": {
      "tenant_id": "87654321-4321-4321-4321-fedcba987654",
      "customer_email": "customer@example.com"
    },
    "operator_id": "db_operator",
    "duration_ms": 150,
    "cost": 0.002
  }
]
```

**Status:** 200 OK

**Status:** 404 Not Found (mission doesn't exist)

### Get Mission Cost Breakdown

```
GET /missions/{mission_id}/cost
```

Returns cost tracking for a mission.

**Response:**
```json
{
  "total_cost": 0.047,
  "breakdown": {
    "auth_operator": 0.001,
    "db_operator": 0.002,
    "roles_operator": 0.0005,
    "comms_operator": 0.01,
    "workflow_operator": 0.0002
  }
}
```

**Cost Matrix:**
| Operation | Cost |
|-----------|------|
| auth_create | $0.001 |
| db_write_tenant | $0.002 |
| db_write_user | $0.0005 |
| db_write_role | $0.0005 |
| email_send | $0.01 |
| rls_check | $0.0001 |
| workflow_log | $0.0002 |

**Status:** 200 OK

**Status:** 404 Not Found (mission doesn't exist)

### Get Mission Progress

```
GET /missions/{mission_id}/progress
```

Returns real-time progress of a mission.

**Response:**
```json
{
  "mission_id": "mission-qxyz1234",
  "progress": 75.0,
  "status": "executing",
  "tasks_completed": 3,
  "tasks_total": 4
}
```

**Fields:**
- `progress` (float, 0-100) - Percentage of tasks completed
- `status` (string) - Current mission status (pending/executing/completed/failed/blocked)
- `tasks_completed` (int) - Number of completed tasks
- `tasks_total` (int) - Total number of tasks in mission

**Status:** 200 OK

**Status:** 404 Not Found (mission doesn't exist)

## WebSocket

### Subscribe to Real-Time Updates

```
WS /kanban/subscribe
```

Establishes a WebSocket connection for real-time mission updates.

**Protocol:**
1. Client connects to WebSocket
2. Server accepts connection
3. Client sends heartbeat ping every 30 seconds
4. Server broadcasts mission updates to all connected clients
5. Client can disconnect at any time

**Heartbeat (Client → Server):**
```json
{
  "type": "ping"
}
```

**Heartbeat Response (Server → Client):**
```json
{
  "type": "pong"
}
```

**Mission Update Broadcast (Server → Client):**
```json
{
  "type": "mission_update",
  "mission_id": "mission-qxyz1234",
  "status": "executing",
  "data": {
    "progress": 50.0,
    "tasks_completed": 2,
    "tasks_total": 4,
    "last_checkpoint": {
      "timestamp": "2026-06-23T20:15:35Z",
      "task_type": "db_operator",
      "status": "✅",
      "cost": 0.002
    }
  }
}
```

**Example (JavaScript):**
```javascript
const ws = new WebSocket("wss://contexia.online/api/v1/kanban/subscribe");

ws.onopen = () => {
  console.log("Connected to mission updates");
  // Send heartbeat every 30s
  setInterval(() => {
    ws.send(JSON.stringify({ type: "ping" }));
  }, 30000);
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === "mission_update") {
    console.log(`Mission ${message.mission_id}: ${message.status}`);
    console.log(`Progress: ${message.data.progress}%`);
    // Update UI with new data
  }
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};

ws.onclose = () => {
  console.log("Disconnected from mission updates");
};
```

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error description"
}
```

### Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid parameters) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (no permission for this tenant) |
| 404 | Not found (mission/checkpoint doesn't exist) |
| 422 | Validation error (malformed request body) |
| 409 | Conflict (e.g., invite already used) |
| 500 | Internal server error |

## Rate Limiting

- GET requests: 100 per minute per user
- POST requests: 10 per minute per user
- WebSocket connections: 1 per user (previous connection is closed)

## Pagination

List endpoints support pagination via query parameters:

```
GET /missions?skip=0&limit=50
```

- `skip`: Number of items to skip (default: 0)
- `limit`: Max items to return (default: 100, max: 1000)

## Filtering (Future)

Planned filters for list endpoints:

```
GET /missions?status=executing&created_after=2026-06-23&plan=pro
```

## Examples

### Complete Mission Flow

```bash
# 1. Start a mission
curl -X POST https://contexia.online/api/v1/missions \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "invite_id": "invite-xyz",
    "customer_email": "john@acme.com",
    "plan": "pro"
  }'

# Response:
# {
#   "id": "mission-abc123",
#   "status": "pending",
#   ...
# }

# 2. Monitor progress via WebSocket (in JavaScript)
const ws = new WebSocket("wss://contexia.online/api/v1/kanban/subscribe");
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.mission_id === "mission-abc123") {
    console.log(`Progress: ${msg.data.progress}%`);
  }
};

# 3. Or poll progress endpoint
curl https://contexia.online/api/v1/missions/mission-abc123/progress \
  -H "Authorization: Bearer TOKEN"

# Response:
# {
#   "mission_id": "mission-abc123",
#   "progress": 75.0,
#   "status": "executing",
#   "tasks_completed": 3,
#   "tasks_total": 4
# }

# 4. Get cost breakdown when complete
curl https://contexia.online/api/v1/missions/mission-abc123/cost \
  -H "Authorization: Bearer TOKEN"

# Response:
# {
#   "total_cost": 0.047,
#   "breakdown": {...}
# }
```

## Implementation Notes

- All endpoints are asynchronous (async/await)
- Multi-tenant isolation enforced via RLS policies
- WebSocket broadcasts to all connected clients
- Mission state is cached in SQLite (missions table)
- Checkpoints are immutable (create-only)
- Cost is calculated in real-time from checkpoints

## Related

- [Kanban Dashboard](../src/components/README.md) - Frontend component for visualization
- [useKanban Hook](../src/hooks/useKanban.ts) - React hook for API integration
- [Conductor](../operators/conductor.py) - Mission orchestration
