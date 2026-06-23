# Phase 6: Enhancement — Design Document

**Date:** 2026-06-23  
**Status:** 📋 **DESIGN** (Ready for Spec)

---

## 1. Architectural Overview

### Layer Stack (Existing + New)

```
┌─ USER BROWSER ──────────────────────────┐
│                                         │
│  React Components + Zustand Store       │ ← NEW: State persistence
│  Error Boundary + Toast UI              │ ← NEW: Error handling
│  Sentry Client                          │ ← NEW: Error tracking
│                                         │
└──────────┬──────────────────────────────┘
           │ HTTPS
           ▼
┌─ VERCEL (Frontend) ──────────────────────┐
│                                         │
│  Next.js + React 18                    │
│  Zustand store (persisted)             │
│  Error boundaries                       │
│  Sentry SDK                            │
│                                         │
└──────────┬──────────────────────────────┘
           │ HTTPS
           ▼
┌─ RAILWAY (Backend) ──────────────────────┐
│                                         │
│  FastAPI + 8 Agents                    │
│  Prometheus /metrics endpoint           │ ← NEW
│  Structured JSON logging               │ ← NEW
│  WebSocket handler                     │
│                                         │
└──────────┬──────────────────────────────┘
           │
           ├─ Sentry API (error reporting)
           ├─ Prometheus scraper (metrics collection)
           └─ Log aggregation service
```

---

## 2. Component Design

### 2.1 State Management: Zustand Store

**File:** `src/stores/agentStore.ts`

```typescript
interface AgentState {
  // Data
  agents: Record<string, AgentOutput>;
  user: UserProfile | null;
  approvals: DraftApproval[];
  settings: UserSettings;
  
  // Metadata
  isLoading: boolean;
  error: string | null;
  lastSync: number;
  
  // Actions
  setAgentData: (agent: string, data: AgentOutput) => void;
  setUser: (user: UserProfile) => void;
  addApproval: (draft: DraftApproval) => void;
  clearError: () => void;
  reset: () => void;
}

const useAgentStore = create<AgentState>(
  persist(
    (set) => ({
      agents: {},
      user: null,
      approvals: [],
      settings: {},
      isLoading: false,
      error: null,
      lastSync: 0,
      
      setAgentData: (agent, data) => 
        set((state) => ({
          agents: { ...state.agents, [agent]: data },
          lastSync: Date.now(),
        })),
      
      setUser: (user) => set({ user }),
      addApproval: (draft) => 
        set((state) => ({
          approvals: [...state.approvals, draft],
        })),
      clearError: () => set({ error: null }),
      reset: () => set(initialState),
    }),
    {
      name: "agent-store",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        agents: state.agents,
        user: state.user,
        approvals: state.approvals,
        settings: state.settings,
      }),
    }
  )
);
```

**Key Design Decisions:**
- **Slice pattern:** Separate slices for agents, user, approvals (single flat store)
- **Persistence:** localStorage (survives refresh), JSON serialization
- **Partialize:** Only persist data, not loading/error state
- **Version:** localStorage schema v1 (track migrations)

**Component Usage:**
```typescript
function PulsaCard() {
  const { agents } = useAgentStore();
  const pulsoData = agents.pulso?.data;
  
  return <Card title="Caja Real">{pulsoData?.caja_real}</Card>;
}
```

### 2.2 Error Boundaries + Toast UI

**File:** `src/components/ErrorBoundary.tsx`

```typescript
interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: (error: Error, retry: () => void) => React.ReactNode;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps> {
  state = { hasError: false, error: null };
  
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    Sentry.captureException(error, { contexts: { react: errorInfo } });
    console.error("Error caught:", error);
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="error-fallback">
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message}</p>
          <button onClick={() => window.location.reload()}>
            Reload Page
          </button>
        </div>
      );
    }
    
    return this.props.children;
  }
}
```

**File:** `src/components/Toast.tsx`

```typescript
import * as Toast from "@radix-ui/react-toast";

interface ToastContextType {
  success: (message: string, options?: ToastOptions) => void;
  error: (message: string, options?: ToastOptions) => void;
  info: (message: string, options?: ToastOptions) => void;
  warning: (message: string, options?: ToastOptions) => void;
}

const ToastContext = React.createContext<ToastContextType>(null!);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = React.useState<Toast[]>([]);
  
  const showToast = (type: ToastType, message: string, options: ToastOptions) => {
    const id = Math.random();
    setToasts((prev) => [...prev, { id, type, message, ...options }]);
    
    // Auto-dismiss after 5s
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  };
  
  return (
    <ToastContext.Provider
      value={{
        success: (msg, opts) => showToast("success", msg, opts),
        error: (msg, opts) => showToast("error", msg, opts),
        info: (msg, opts) => showToast("info", msg, opts),
        warning: (msg, opts) => showToast("warning", msg, opts),
      }}
    >
      {children}
      <ToastViewport>
        {toasts.map((toast) => (
          <ToastRoot key={toast.id} type={toast.type}>
            <ToastTitle>{toast.message}</ToastTitle>
            {toast.action && (
              <ToastAction altText="Retry">
                <button onClick={toast.action}>Retry</button>
              </ToastAction>
            )}
          </ToastRoot>
        ))}
      </ToastViewport>
    </ToastContext.Provider>
  );
};

export const useToast = () => React.useContext(ToastContext);
```

**Usage:**
```typescript
function ApprovalForm() {
  const toast = useToast();
  
  const handleApprove = async (draftId: string) => {
    try {
      await api.approve(draftId);
      toast.success("Approval sent successfully");
    } catch (error) {
      toast.error(error.message, {
        action: () => handleApprove(draftId),
      });
    }
  };
}
```

### 2.3 Error Tracking: Sentry Integration

**File:** `src/main.tsx`

```typescript
import * as Sentry from "@sentry/react";
import { BrowserTracing } from "@sentry/tracing";

Sentry.init({
  dsn: process.env.VITE_SENTRY_DSN,
  environment: process.env.VITE_ENV,
  tracesSampleRate: 0.1,
  integrations: [
    new BrowserTracing(),
    new Sentry.Replay({
      maskAllText: true,
      blockAllMedia: true,
    }),
  ],
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
});

const App = Sentry.withProfiler(AppComponent);
```

**Capture errors automatically:**
- Unhandled exceptions (via ErrorBoundary)
- Failed API calls (via fetch interceptor)
- Performance slowdowns (via tracing)

**Sentry dashboard:** https://sentry.io/contexia (real-time error feed, trends, alerts)

### 2.4 Performance Monitoring: Prometheus

**File:** `apps/backend/api/metrics.py`

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Metrics
agent_latency = Histogram(
    'agent_latency_seconds',
    'Agent response latency',
    labelnames=['agent'],
)

error_count = Counter(
    'agent_errors_total',
    'Total agent errors',
    labelnames=['agent', 'error_type'],
)

cache_hits = Gauge(
    'cache_hit_rate',
    'Cache hit rate (0-1)',
)

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")

# Usage in websocket handler
with agent_latency.labels(agent='pulso').time():
    result = await invoke_agent('pulso', params, context)
```

**Prometheus scraper configuration:**
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'contexia-api'
    static_configs:
      - targets: ['antigravity-app-production-175a.up.railway.app:8080']
    metrics_path: '/metrics'
```

**Grafana dashboard:** Real-time visualization of:
- Agent latency (p50, p95, p99)
- Error rate by agent
- Cache hit rate
- WebSocket connection count

---

## 3. Data Flow: State Persistence

### Scenario: User Approves Draft, Then Refreshes

```
1. User clicks "Approve Draft"
   ↓
2. API call: POST /api/v1/approval-queue/approve
   ↓
3. Success: update Zustand store
   store.addApproval({ id, status: 'approved', timestamp })
   ↓
4. Zustand persists to localStorage
   localStorage['agent-store'] = JSON.stringify(state)
   ↓
5. Toast: "Approval sent successfully"
   ↓
6. User refreshes browser (F5)
   ↓
7. App boots, Zustand rehydrates from localStorage
   state.approvals = [{id, status: 'approved', ...}]
   ↓
8. Component renders: ApprovalQueue shows approved draft ✓
```

### Scenario: Network Error During Approval

```
1. User clicks "Approve Draft"
   ↓
2. API call fails (network timeout)
   ↓
3. Catch error, emit toast
   toast.error("Network error. Retry?", { 
     action: () => handleApprove(draftId)
   })
   ↓
4. User clicks "Retry"
   ↓
5. API call succeeds (if network recovered)
   ↓
6. Store updated, toast success
```

---

## 4. Error Handling Strategy

### Hierarchy

```
Top Level: ErrorBoundary (catches React render errors)
  ↓
Component Level: try-catch (API calls, async operations)
  ↓
Toast UI: User-friendly message + retry option
  ↓
Sentry: Automatic error capture for debugging
```

### Error Types & Handling

| Error | Handling | User Sees |
|-------|----------|-----------|
| Network timeout | Retry in toast | "Network error. Retry?" |
| 401 Unauthorized | Redirect to login | "Session expired. Sign in again." |
| 422 Validation | Show field errors | Form highlighting + message |
| 500 Server error | Sentry + toast | "Server error. Our team is notified." |
| React crash | ErrorBoundary | "Something went wrong. Reload?" |

---

## 5. localStorage Schema

### Version 1 (Phase 6)

```json
{
  "agent-store": {
    "state": {
      "agents": {
        "pulso": {
          "data": { "caja_real": "1234567.89", ... },
          "timestamp": 1687543200000
        }
      },
      "user": {
        "id": "user-123",
        "email": "user@example.com",
        "permissions": ["READ_PULSO", "WRITE_APPROVAL"]
      },
      "approvals": [
        {
          "id": "draft-123",
          "status": "pending",
          "created_at": "2026-06-23T...",
          "updated_at": "2026-06-23T..."
        }
      ],
      "settings": {
        "theme": "light",
        "notifications_enabled": true
      }
    },
    "version": 1
  }
}
```

**Migration Strategy:**
- If `version` < 1: clear store (first install)
- If `version` > 1: implement migration script

---

## 6. Testing Strategy

### Unit Tests
- Zustand store: selectors, actions, persistence
- Error Boundary: error catching, fallback rendering
- Toast: show/hide, auto-dismiss, dedup

### Integration Tests
- Flow: Update store → localStorage persists → Rehydrate on boot
- Error flow: API error → toast appears → user retries → success
- State + component: Store updates → component re-renders

### E2E Tests
- User approval workflow with refresh
- Network error recovery
- Offline → online transition

---

## 7. Deployment Considerations

### Environment Variables (Frontend)

```
VITE_SENTRY_DSN=https://xxx@sentry.io/yyy
VITE_ENV=production
VITE_API_BASE_URL=https://antigravity-app-production-175a.up.railway.app/api/v1
```

### Environment Variables (Backend)

```
PROMETHEUS_ENABLED=true
SENTRY_DSN=https://xxx@sentry.io/yyy
LOG_FORMAT=json
```

### Dependencies Added

**Frontend:**
- zustand@4.4.0
- @radix-ui/react-toast@1.1.5
- @sentry/react@7.72.0

**Backend:**
- prometheus-client@0.18.0
- python-json-logger@2.0.0 (structured logging)

---

## 8. Performance Characteristics

| Operation | Latency | Notes |
|-----------|---------|-------|
| localStorage read (rehydrate) | <50ms | On page load |
| Store update + persist | <10ms | Async write to localStorage |
| Toast render | <50ms | Radix primitive |
| Sentry error capture | <100ms | Async, non-blocking |
| Prometheus scrape | <500ms | Backend metric generation |

---

## 9. Monitoring & Alerting

### Sentry Alerts
- **Critical:** >10 errors in 5 minutes
- **Warning:** New error type appears
- **Info:** Error trend up >20%

### Prometheus Alerts
- **Critical:** Agent latency p99 > 5s
- **Warning:** Error rate > 1%
- **Info:** Cache hit rate < 70%

---

## 10. Future Enhancements (Phase 7+)

- IndexedDB for larger offline data
- Service workers for background sync
- Redux DevTools integration (state time-travel debugging)
- Advanced error recovery (conflict resolution for offline changes)
- A/B testing framework (feature flags)

---

**Design Status:** ✅ READY FOR SPEC
