# Hermes Workspace Configuration — Multi-Tenant Setup (T11)

**Date:** 2026-06-29  
**Purpose:** Configure Hermes local gateway + Workspace to use multi-tenant JWT context  
**Target:** Phase 1C (Hermes JWT Integration)

---

## Overview

Hermes runs in a **local WSL2 distro** (hermes-ws) with environment variables that tell it which tenant to serve and how to authenticate with the Railway backend.

**Key variables:**
- `HERMES_TENANT_ID` — Which organization Hermes is serving (e.g., "contexia-org-1")
- `HERMES_JWT_SECRET` — Secret key for signing JWTs (or read from Bitwarden)
- `HERMES_API_URL` — Railway backend URL (http://127.0.0.1:8080/api/v1)
- `HERMES_WORKSPACE_PORT` — Workspace UI port (:3000)
- `HERMES_GATEWAY_PORT` — Gateway port (:8642)

---

## Step 1: Set Environment Variables in WSL

### Create/Update Hermes .env file

**Location:** `~/.hermes/.env` (inside hermes-ws distro)

```bash
# Hermes Multi-Tenant Configuration
# Generated: 2026-06-29

# ============================================================================
# TENANT CONTEXT
# ============================================================================
# Which organization this Hermes instance serves
HERMES_TENANT_ID=contexia-org-1
HERMES_ORG_NAME="Contexia S.A.S."

# ============================================================================
# API CONNECTIVITY
# ============================================================================
# Railway backend API (local tunnel or production)
HERMES_API_URL=http://127.0.0.1:8080/api/v1

# Hermes gateway port (WebSocket, skill invocations)
HERMES_GATEWAY_PORT=8642

# Hermes Workspace UI port
HERMES_WORKSPACE_PORT=3000

# ============================================================================
# AUTHENTICATION
# ============================================================================
# JWT secret (for signing tokens issued by Hermes)
# Read from Bitwarden or set directly
HERMES_JWT_SECRET=$(bw get item railway | jq -r '.fields[0].value' 2>/dev/null || echo "dev-secret-hermes-change-in-prod")

# JWT tenant claim name (must match Contexia backend)
HERMES_JWT_TENANT_CLAIM=tenant_id

# ============================================================================
# FEATURES
# ============================================================================
# Auto-detect gateway URL (disable if behind proxy/tunnel)
HERMES_AUTO_DETECT=false

# Log level
HERMES_LOG_LEVEL=debug

# ============================================================================
# OPTIONAL: Hermes Gateway Service (systemd)
# ============================================================================
# Enable systemd service for auto-restart on boot
HERMES_ENABLE_SERVICE=true

# Service name
HERMES_SERVICE_NAME=hermes-gateway.service
```

### Load Environment Variables

```bash
# Inside WSL distro (hermes-ws)
source ~/.hermes/.env

# Verify
echo $HERMES_TENANT_ID  # Should print: contexia-org-1
echo $HERMES_API_URL    # Should print: http://127.0.0.1:8080/api/v1
```

---

## Step 2: Configure Hermes Operators (Tool Registration)

Each Hermes operator (Pulso, Centinela, etc.) is registered as a **tool** that calls the Railway backend API.

### Operator Configuration Example

**File:** `~/.hermes/operators/pulso.yaml` (or via Workspace UI)

```yaml
name: "Pulso"
emoji: "📊"
model: "gemini-2.5-flash"
system_prompt: |
  You are Pulso, the financial KPI specialist.
  Provide daily financial health summaries for SMEs.
  Focus on: cash flow, AR/AP aging, inventory turnover, margins.
  Always cite sources (DIAN GL, Siigo, SyncManager).

tool:
  endpoint: "http://127.0.0.1:8080/api/v1/agents/pulso-diario/summary"
  method: "POST"
  auth_type: "bearer"
  auth_header: "Authorization"
  auth_value: "Bearer ${HERMES_JWT_TOKEN}"
  
  request_body:
    company_id: "{{ mission.company_id }}"
    date_range: "{{ mission.date_range }}"
  
  response_format: "json"
```

### Key Points

- **`auth_value`:** `Bearer ${HERMES_JWT_TOKEN}` — Hermes injects the JWT token here
- **Token contains:** `{"sub": "hermes-pulso", "tenant_id": "contexia-org-1", "exp": ...}`
- **TenantContextMiddleware** extracts tenant_id from token → `request.state.tenant_id`
- **RLS policies** at Supabase level filter: only rows with matching tenant_id are returned

---

## Step 3: Generate Hermes JWT Token

Hermes needs to sign JWTs when calling backend operators.

### Option A: Use existing Contexia JWT_SECRET

```bash
# Read from Railway env
export JWT_SECRET=$(railway env | grep JWT_SECRET | cut -d= -f2)

# Use in Hermes startup
export HERMES_JWT_SECRET=$JWT_SECRET
```

### Option B: Read from Bitwarden (Recommended)

```bash
# Get JWT secret from Bitwarden vault
export HERMES_JWT_SECRET=$(bw get item contexia | jq -r '.fields[] | select(.name=="JWT_SECRET") | .value')

# Verify
echo $HERMES_JWT_SECRET | wc -c  # Should be 44+ chars
```

### Option C: Use Hermes JWT Library

```python
# Inside Hermes initialization
from datetime import datetime, timedelta
from jose import jwt

HERMES_JWT_SECRET = os.getenv("HERMES_JWT_SECRET")

def create_hermes_token(tenant_id: str, user: str = "hermes-operator") -> str:
    """Create JWT for Hermes operators calling backend."""
    payload = {
        "sub": user,
        "tenant_id": tenant_id,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    token = jwt.encode(payload, HERMES_JWT_SECRET, algorithm="HS256")
    return token

# Usage
token = create_hermes_token("contexia-org-1")
# Token can be used in Authorization: Bearer {token}
```

---

## Step 4: Start Hermes Gateway & Workspace

### Start Gateway (Background)

```bash
# Inside WSL distro (hermes-ws)
hermes -p contexia gateway run

# Expected output:
# [INFO] Hermes Gateway started on 127.0.0.1:8642
# [INFO] Tenant context: contexia-org-1
# [INFO] Backend: http://127.0.0.1:8080/api/v1
```

### Start Workspace (Separate Terminal)

```bash
# Inside WSL distro (hermes-ws)
hermes -p contexia workspace run

# Expected output:
# [INFO] Hermes Workspace started on 127.0.0.1:3000
# Open: http://127.0.0.1:3000
```

### Verify Connection

```bash
# Test gateway health
curl http://127.0.0.1:8642/health
# Expected: {"status": "ok", "tenant": "contexia-org-1"}

# Test Workspace UI
open http://127.0.0.1:3000
# Should show Workspace dashboard with operators loaded
```

---

## Step 5: Test Operator Call with Tenant Context

### Manual Test: Trigger Pulso Operator

1. Go to Workspace UI: http://127.0.0.1:3000
2. Create mission: "Pulso: daily summary"
3. Click: Operators → Pulso → Execute
4. Monitor backend logs:
   ```bash
   # In Railway logs or local dev server
   # Should see:
   # [Tenant: contexia-org-1] POST /api/v1/agents/pulso-diario/summary
   ```

### Expected Flow

```
Hermes Workspace (:3000)
  ↓ (User triggers Pulso)
Hermes Gateway (:8642)
  ↓ (Creates JWT with tenant_id="contexia-org-1")
TenantContextMiddleware
  ↓ (Extracts tenant_id, injects into request.state)
Pulso Endpoint (/api/v1/agents/pulso-diario/summary)
  ↓ (Queries Supabase: SELECT * FROM pulso_results WHERE ...)
Supabase RLS Policy
  ↓ (Filters: only rows where tenant_id = 'contexia-org-1')
Response: Contexia data only
  ↓
Hermes Gateway receives response
  ↓
Workspace displays result
```

### Verify in Backend Logs

```
2026-06-30T14:23:45.123Z [Tenant: contexia-org-1] POST /api/v1/agents/pulso-diario/summary | User: hermes-pulso
2026-06-30T14:23:45.456Z [Tenant: contexia-org-1] Query: SELECT * FROM pulso_results WHERE tenant_id = 'a0000000-0000-0000-0000-000000000001'
2026-06-30T14:23:45.789Z [Tenant: contexia-org-1] Response: 2 rows returned (RLS filtered)
```

---

## Step 6: Multi-Tenant Testing (Optional, Phase 2+)

When adding a second tenant (e.g., Client XYZ), create a separate Hermes instance or use environment switching:

### Create Second Hermes Config

```bash
# ~/.hermes/client-xyz/.env
HERMES_TENANT_ID=client-xyz
HERMES_API_URL=http://127.0.0.1:8080/api/v1
HERMES_GATEWAY_PORT=8643  # Different port
HERMES_WORKSPACE_PORT=3001
```

### Run Both Instances (Different WSL Distros or Same Distro Different Ports)

```bash
# Terminal 1: Contexia instance
hermes -p contexia gateway run

# Terminal 2: Client XYZ instance
source ~/.hermes/client-xyz/.env
hermes -p contexia gateway run
# (Will fail because of port conflict; use Docker or separate distros for Phase 2)
```

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| "Connection refused" to 127.0.0.1:8080 | Railway backend not running | Start: `python -m uvicorn main:app --host 0.0.0.0 --port 8080` |
| "Unauthorized" (401) on operator call | JWT invalid or tenant_id missing | Verify: `echo $HERMES_JWT_SECRET` is set |
| "No data returned" from operator | RLS policy blocking access | Check: Does JWT have correct tenant_id? |
| Workspace shows "Welcome! Connect backend" | Gateway URL not found | Set: `HERMES_AUTO_DETECT=false` and explicit URL |
| "localhost:3000 not accessible from WSL" | Windows Firewall or network | Use IP: `http://172.x.x.x:3000` or `wsl -d hermes-ws -- hostname -I` |

---

## Next Steps (T12: End-to-End Test)

Once environment is configured:
1. ✅ Hermes gateway running (:8642)
2. ✅ Workspace UI accessible (:3000)
3. ✅ Operators registered with backend URLs
4. ✅ JWT token includes tenant_id
5. ⏭️ Run E2E test (T13): Trigger all 9 operators, verify tenant isolation

---

## Reference

- **Task:** T11 (Phase 1C, Jun 29-30)
- **Related:** T10 (JWT creation), T12 (E2E test)
- **Spec:** `ai-specs/architecture/hermes-multi-tenant-wrapper-spec.md`
- **OpenSpec:** `antigravity-app/openspec/changes/hermes-multi-tenant-wrapper/tasks.md`

