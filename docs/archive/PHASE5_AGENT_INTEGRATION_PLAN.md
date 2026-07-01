# PHASE 5: AGENT INTEGRATION — COMPREHENSIVE PLAN

**Status:** 📋 Ready for Implementation  
**Target:** Week 2 (2026-06-30 onwards)  
**Duration:** 3-5 days  
**Dependencies:** Phase 4 complete ✅

---

## OVERVIEW

Phase 5 connects real Hermes agents to the PWA components deployed in Phase 4. The WebSocket infrastructure is live; now we wire real data from agents to UI.

**Goal:** Complete end-to-end data flow from agents → backend → frontend → UI

---

## PHASE 5 BREAKDOWN

### STEP 1: Replace HTTP Stubs with Real Agent Endpoints (1 day)

**Current State:** `invoke_agent()` and `agent_output_listener()` are stubs returning placeholder data

**What to do:**

#### 1.1 Implement Real Agent Invocation

**File:** `apps/backend/api/websocket_handler.py`

**Current stub:**
```python
async def invoke_agent(agent: str, context: AgentContext, params: dict) -> dict:
    # Returns placeholder data
    return {
        "agent": agent,
        "status": "success",
        "result": {"placeholder": "Agent output will be populated here"}
    }
```

**To implement:**

```python
async def invoke_agent(agent: str, context: AgentContext, params: dict) -> dict:
    """Invoke real Hermes agent endpoint."""
    
    # Map agent names to endpoints
    AGENT_ENDPOINTS = {
        "pulso": "/api/v1/agents/pulso-diario/summary",
        "centinela": "/api/v1/centinela/generate-draft",
        "radar": "/api/v1/agents/radar-predictivo/risk-score",
        "taty": "/api/v1/agents/taty/invoke",
        "social-ops": "/api/v1/agents/social-ops/status",
        "audit": "/api/v1/agents/auditoria-sombra/report",
        "approval": "/api/v1/approval-queue/enqueue",
        "maestro": "/api/v1/hermes/swarm/invoke"
    }
    
    endpoint = AGENT_ENDPOINTS.get(agent)
    if not endpoint:
        return {"status": "error", "message": f"Unknown agent: {agent}"}
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Build headers with context
            headers = build_agent_headers(context)
            
            # Call agent endpoint
            response = await client.post(
                f"http://localhost:8000{endpoint}",  # or Railway URL
                json=build_agent_payload(context, params),
                headers=headers
            )
            
            if response.status_code >= 400:
                return {
                    "status": "error",
                    "code": response.status_code,
                    "message": response.text
                }
            
            return {
                "status": "success",
                "agent": agent,
                "data": response.json()
            }
    
    except Exception as e:
        logger.error(f"Agent invocation failed: {e}")
        return {"status": "error", "message": str(e)}
```

#### 1.2 Implement Real Agent Output Listener

**File:** `apps/backend/api/websocket_handler.py`

**Current stub:**
```python
async def agent_output_listener(agent: str, context: AgentContext, ...):
    # Just keeps listener alive
    while True:
        await asyncio.sleep(1)
```

**To implement:**

```python
async def agent_output_listener(
    agent: str,
    context: AgentContext,
    websocket: WebSocket,
    manager: ConnectionManager
) -> None:
    """Stream agent output via WebSocket."""
    
    AGENT_STREAMS = {
        "pulso": "/api/v1/agents/pulso-diario/stream",
        "centinela": "/api/v1/centinela/stream",
        "radar": "/api/v1/agents/radar-predictivo/stream",
        # ... etc
    }
    
    stream_endpoint = AGENT_STREAMS.get(agent)
    if not stream_endpoint:
        logger.warning(f"No stream endpoint for {agent}")
        return
    
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "GET",
                f"http://localhost:8000{stream_endpoint}",
                headers=build_agent_headers(context)
            ) as response:
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        await manager.send_personal(
                            websocket,
                            {
                                "type": "agent_output",
                                "agent": agent,
                                "data": data,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        )
                    except json.JSONDecodeError:
                        logger.debug(f"Non-JSON line from {agent}: {line}")
    
    except asyncio.CancelledError:
        logger.info(f"Agent listener cancelled: {agent}")
    except Exception as e:
        logger.error(f"Stream error ({agent}): {e}")
```

---

### STEP 2: Implement Data Transformations (1 day)

**Goal:** Format agent output for UI consumption

#### 2.1 Create Transformation Utilities

**File:** `apps/backend/services/agent_transformers.py` (NEW)

```python
from typing import Dict, Any
from decimal import Decimal
from datetime import datetime

class AgentTransformers:
    """Transform raw agent output for UI consumption."""
    
    @staticmethod
    def transform_pulso(data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Pulso daily summary for PulsaCard."""
        return {
            "caja_real": Decimal(data.get("cash_on_hand", 0)),
            "dinero_tuyo": Decimal(data.get("net_cash", 0)),
            "ventas_ayer": Decimal(data.get("yesterday_sales", 0)),
            "salidas_plata": Decimal(data.get("outflows", 0)),
            "estado_plata": data.get("status", "neutral"),  # bien/alerta/critico
            "timestamp": data.get("timestamp", datetime.utcnow().isoformat())
        }
    
    @staticmethod
    def transform_centinela(alerts: list) -> list:
        """Transform Centinela alerts for CentinelaAlerts."""
        return [
            {
                "id": alert.get("id"),
                "type": alert.get("alert_type"),  # iva-due, tax-warning, etc
                "title": alert.get("title"),
                "description": alert.get("description"),
                "urgency": alert.get("urgency", "medium"),
                "due_date": alert.get("due_date"),
                "action_label": alert.get("action", "Resolver con Taty")
            }
            for alert in alerts
        ]
    
    @staticmethod
    def transform_approval_queue(drafts: list) -> list:
        """Transform approval drafts for ApprovalQueue."""
        return [
            {
                "id": draft.get("id"),
                "type": draft.get("draft_type"),
                "title": draft.get("title"),
                "description": draft.get("description"),
                "agent": draft.get("agent"),
                "content": draft.get("content"),
                "status": draft.get("status", "pending"),
                "created_at": draft.get("created_at")
            }
            for draft in drafts
        ]
```

#### 2.2 Update WebSocket Handler to Use Transformers

**File:** `apps/backend/api/websocket_handler.py`

```python
from services.agent_transformers import AgentTransformers

async def invoke_agent(agent: str, context: AgentContext, params: dict) -> dict:
    # ... existing code ...
    
    # Apply transformations
    if agent == "pulso":
        data = AgentTransformers.transform_pulso(response.json())
    elif agent == "centinela":
        data = AgentTransformers.transform_centinela(response.json())
    elif agent == "approval":
        data = AgentTransformers.transform_approval_queue(response.json())
    else:
        data = response.json()
    
    return {
        "status": "success",
        "agent": agent,
        "data": data
    }
```

---

### STEP 3: Wire Components to Agents (1 day)

**Goal:** Update frontend components to consume real agent data

#### 3.1 Update useAgentWebSocket Hook

**File:** `frontend/dashboard/src/hooks/useAgentWebSocket.ts`

Currently, the hook receives data but components ignore it. Update to properly manage state:

```typescript
export function useAgentWebSocket(): UseAgentWebSocketReturn {
  // ... existing code ...
  
  // Add proper state management
  const [agentData, setAgentData] = useState<Record<string, AgentOutput>>({})
  
  // Update on WebSocket message
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data)
    
    if (msg.type === 'agent_output') {
      setAgentData(prev => ({
        ...prev,
        [msg.agent]: {
          agent: msg.agent,
          status: 'success',
          data: msg.data,
          timestamp: msg.timestamp
        }
      }))
    }
  }
  
  // ... rest of implementation
}
```

#### 3.2 Update PulsaCard Component

**File:** `frontend/dashboard/src/components/PulsaCard.tsx`

```typescript
import { useAgentWebSocket } from '../hooks/useAgentWebSocket'

export const PulsaCard: React.FC = () => {
  const { agentData, subscribe } = useAgentWebSocket()
  
  useEffect(() => {
    subscribe('pulso')
  }, [subscribe])
  
  const pulsoData = agentData.pulso?.data
  
  return (
    <div className="bg-slate-900 border border-purple-500/30 rounded-lg p-6">
      <h2 className="text-lg font-semibold text-white mb-1">Hoy en tu negocio</h2>
      
      {agentData.pulso?.status === 'pending' && (
        <p className="text-sm text-gray-500">Cargando...</p>
      )}
      
      {agentData.pulso?.status === 'error' && (
        <p className="text-sm text-red-500">Error: {agentData.pulso.error}</p>
      )}
      
      {pulsoData && (
        <>
          <div className="space-y-2">
            <p className="text-sm text-gray-400">Caja Real de Hoy</p>
            <div className="text-4xl font-bold text-cyan-400">
              {formatCurrency(pulsoData.caja_real)}
            </div>
            <p className="text-xs text-gray-500">
              Dinero tuyo: {formatCurrency(pulsoData.dinero_tuyo)}
            </p>
          </div>
          {/* ... rest of component ... */}
        </>
      )}
    </div>
  )
}
```

#### 3.3 Update CentinelaAlerts Component

**File:** `frontend/dashboard/src/components/CentinelaAlerts.tsx`

```typescript
export const CentinelaAlerts: React.FC = () => {
  const { agentData, subscribe } = useAgentWebSocket()
  
  useEffect(() => {
    subscribe('centinela')
  }, [subscribe])
  
  const alerts = agentData.centinela?.data || []
  
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white">Atento a esto</h3>
      
      {agentData.centinela?.status === 'pending' && (
        <div className="text-gray-500">Cargando alertas...</div>
      )}
      
      {alerts.map(alert => (
        <div key={alert.id} className="bg-slate-900 border rounded-lg p-4">
          <h4 className="font-semibold text-white">{alert.title}</h4>
          <p className="text-sm text-gray-400 mt-1">{alert.description}</p>
          {/* ... render buttons, etc ... */}
        </div>
      ))}
    </div>
  )
}
```

#### 3.4 Update ApprovalQueue Component

Similar pattern: subscribe to 'approval' agent, render drafts from agentData

---

### STEP 4: Error Handling & Edge Cases (1 day)

#### 4.1 Handle Missing Agents

If an agent endpoint is down, show graceful error in UI:

```typescript
{agentData[agent]?.status === 'error' && (
  <div className="bg-red-500/10 border border-red-500/50 rounded p-4">
    <p className="text-red-400">
      Error loading data: {agentData[agent].error}
    </p>
    <button 
      onClick={() => retry(agent)}
      className="text-sm text-red-500 hover:underline mt-2"
    >
      Retry
    </button>
  </div>
)}
```

#### 4.2 Handle Slow/Offline Agents

Use timeout + retry logic:

```python
async with client.post(
    endpoint,
    json=payload,
    headers=headers,
    timeout=10  # 10 second timeout
) as response:
    # Handle timeout, connection errors, etc
```

#### 4.3 Data Validation

Validate transformed data before sending to UI:

```python
from pydantic import BaseModel, validator

class PulsaOutput(BaseModel):
    caja_real: Decimal
    dinero_tuyo: Decimal
    ventas_ayer: Decimal
    estado_plata: str
    
    @validator('estado_plata')
    def validate_status(cls, v):
        if v not in ['bien', 'alerta', 'critico']:
            raise ValueError('Invalid status')
        return v
```

---

### STEP 5: End-to-End Testing (1 day)

#### 5.1 Component Integration Tests

```typescript
// frontend/dashboard/src/components/__tests__/PulsaCard.test.tsx
describe('PulsaCard', () => {
  it('renders Pulso data when agent_output arrives', async () => {
    // Mock WebSocket
    // Simulate agent_output message
    // Verify component updates
  })
  
  it('shows loading state while fetching', () => {
    // Verify "Cargando..." appears
  })
  
  it('shows error state on agent failure', () => {
    // Verify error message appears
  })
})
```

#### 5.2 End-to-End Workflow Test

```typescript
// Test complete flow: subscribe → receive data → render
describe('WebSocket Agent Integration', () => {
  it('receives Pulso data and renders in PulsaCard', async () => {
    // 1. Connect WebSocket
    // 2. Subscribe to 'pulso'
    // 3. Simulate agent_output
    // 4. Verify component renders data
    // 5. Verify permission checks work
  })
})
```

#### 5.3 Manual Browser Test

```
1. Open https://contexia.online/app/overview
2. Login
3. Open DevTools → Console
4. Verify:
   - "WebSocket connected"
   - "Subscribe: agent=pulso" logs
   - PulsaCard renders real data
   - Centinela alerts appear
   - ApprovalQueue shows drafts
5. Test interactions:
   - Click "Resolver con Taty" → invoke Taty agent
   - Click "Aprobar" → call approval endpoint
   - Disconnect/reconnect → message queueing works
```

---

## DELIVERABLES CHECKLIST

### Code Changes
- [ ] `websocket_handler.py` — Real agent invocation + streaming
- [ ] `agent_transformers.py` — Data transformation utilities
- [ ] `PulsaCard.tsx` — Connected to pulso agent
- [ ] `CentinelaAlerts.tsx` — Connected to centinela agent
- [ ] `ApprovalQueue.tsx` — Connected to approval agent
- [ ] Error handling — All components
- [ ] Validation — Pydantic models

### Testing
- [ ] Unit tests for transformers
- [ ] Component integration tests
- [ ] End-to-end browser test
- [ ] Manual UAT verification

### Documentation
- [ ] Agent endpoint mapping (updated)
- [ ] Data transformation guide (new)
- [ ] Deployment report (Stage 11)

---

## ACCEPTANCE CRITERIA

✅ **All criteria must pass before Phase 5 is done:**

- [x] Real agents respond to WebSocket requests
- [x] Data flows end-to-end: agent → backend → WebSocket → frontend → UI
- [x] Components render real data (not placeholders)
- [x] Error handling graceful (no console errors)
- [x] Permissions enforced (context passed correctly)
- [x] All browser tests pass
- [x] Manual UAT verification complete
- [x] Zero regressions in Phase 4 features

---

## TIMELINE

| Task | Duration | Owner | Dates |
|------|----------|-------|-------|
| Step 1: Real endpoints | 1 day | Backend | Jun 30 |
| Step 2: Transformations | 1 day | Backend | Jul 1 |
| Step 3: Component wiring | 1 day | Frontend | Jul 2 |
| Step 4: Error handling | 1 day | Full-stack | Jul 3 |
| Step 5: Testing | 1 day | QA | Jul 4 |

**Total:** 5 days (1 week)

---

## RISK MITIGATION

| Risk | Mitigation |
|------|-----------|
| Agent endpoint down | Graceful error UI + retry button |
| Slow agent response | 10s timeout + fallback to polling |
| Data format mismatch | Pydantic validation on backend |
| Missing permissions | Context-based checks enforced |
| Component regression | Unit + integration tests |

---

## SUCCESS METRICS

✅ **Phase 5 is successful when:**

1. Real agent data visible in all 3 components
2. All automated tests pass (0 failures)
3. Manual UAT complete and approved
4. No regressions in Phase 4
5. Production deployment ready
6. Stage 11 report filed

---

## NEXT AFTER PHASE 5

**Phase 6: Enhancement (Month 1)**
- Redux/Zustaend state management
- Error boundaries + toast notifications
- Analytics + monitoring
- Security audit + penetration testing

---

**Phase 5 Plan: READY FOR IMPLEMENTATION**

**Start date:** 2026-06-30  
**Target completion:** 2026-07-04  
**Status:** 📋 Awaiting implementation signal

