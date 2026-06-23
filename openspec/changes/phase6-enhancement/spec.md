# Phase 6: Enhancement — Specification Document

**Date:** 2026-06-23  
**Status:** ✅ **SPEC** (Ready for Task Breakdown)

---

## 1. Feature Specifications

### 1.1 Zustand State Store

**Store File:** `frontend/dashboard/src/stores/agentStore.ts`

**Core Functionality:**
- Persist agentData, user profile, approvals, settings to localStorage
- Rehydrate on app boot (no data loss on refresh)
- Automatic merging of fresh backend data with cached data
- Support offline-first workflows (work while disconnected)

**Data Structure:**
```
agents: { pulso: {...}, centinela: {...}, ... }
user: { id, email, permissions }
approvals: [{ id, status, created_at, ... }]
settings: { theme, notifications_enabled }
```

**Persistence:**
- Storage backend: browser localStorage
- Key: "agent-store"
- Schema version: 1 (support migrations)
- Partialize: Only persist (agents, user, approvals, settings)
- Exclude: isLoading, error, lastSync (transient state)

---

### 1.2 Error Boundary + Toast UI

**Error Boundary:**
- Catches React component render errors (not async)
- Prevents blank white screens
- Shows fallback UI with "Reload" button
- Logs error to Sentry automatically

**Toast Notifications:**
- Four types: success (green), error (red), info (blue), warning (yellow)
- Auto-dismiss after 5 seconds
- Optional action button (e.g., "Retry" for failures)
- Max 3 toasts visible (stack vertically)
- Dedup: Don't show duplicate messages within 2 seconds

**Common Messages:**
- Success: "Approval sent successfully"
- Error: "Network error. Retry?"
- Info: "Processing..."
- Warning: "Session expiring in 5 minutes"

---

### 1.3 Sentry Error Tracking

**Configuration:**
- Initialize with DSN in main.tsx
- Capture unhandled React errors
- Capture unhandled promise rejections
- Capture fetch/network errors
- Session replay (watch user interactions before errors)

**Dashboard Features:**
- Real-time error feed
- Group by error type, severity, affected users
- Alerts for critical issues (>10 errors in 5 minutes)
- Error trends (up/down over time)
- Session replay (video of user actions)

---

### 1.4 Prometheus Metrics

**Metrics Exposed:**

1. **agent_latency_seconds**
   - Measurement: Time from agent invoke to response
   - Labels: agent (pulso, centinela, radar, ...)
   - Type: Histogram (0.1s, 0.5s, 1s, 2s, 5s buckets)

2. **agent_errors_total**
   - Measurement: Count of errors by type
   - Labels: agent, error_type (timeout, 500, validation)
   - Type: Counter

3. **websocket_connections_active**
   - Measurement: Current active WebSocket connections
   - Type: Gauge

4. **cache_hit_rate**
   - Measurement: Percentage of cache hits
   - Type: Gauge (0.0 - 1.0)

5. **request_duration_seconds**
   - Measurement: HTTP request latency
   - Labels: method, endpoint
   - Type: Histogram

**Grafana Dashboard Panels:**
- Agent latency trends (p50, p95, p99)
- Error rate by agent
- Cache hit rate over time
- WebSocket connection count
- API success rate

---

### 1.5 Security Audit

**Scope:**

1. **Dependency Audit**
   - npm audit (frontend)
   - pip audit (backend)
   - Report CVEs, severity, patch availability

2. **Code Review**
   - Authentication: JWT validation, token expiry
   - CORS: Allowed origins, no wildcard
   - Input Validation: XSS, SQL injection prevention
   - Secrets Management: No hardcoded credentials
   - Rate Limiting: API protection

3. **Penetration Testing**
   - XSS injection attempts
   - CSRF token validation
   - Authentication bypass
   - Unauthorized access attempts
   - API abuse

4. **Compliance**
   - GDPR: Data retention, user export
   - Access logs: All auth events logged
   - Encryption: HTTPS enforced
   - Audit trail: User actions logged

---

## 2. Testing Strategy

### Unit Tests
- Store selectors and actions
- Error Boundary error catching
- Toast show/hide, dedup, auto-dismiss
- Sentry initialization
- Prometheus metric collection

### Integration Tests
- Store + component rendering
- Store persistence + rehydration
- Error flow (API error → toast → retry)
- Sentry error capture
- Metrics collection

### E2E Tests
- User approval workflow with refresh
- Network error recovery
- Offline to online transition
- Session persistence across login/logout

---

## 3. Performance Targets

| Operation | Target |
|-----------|--------|
| App boot (with rehydration) | <2 seconds |
| Store update | <10ms |
| Toast render | <50ms |
| Error Boundary catch | <200ms |
| Sentry error send | <500ms (async) |
| Prometheus scrape | <2 seconds |

---

## 4. Deployment Steps

**Frontend:**
1. Create Zustand store
2. Create Error Boundary component
3. Create Toast component
4. Initialize Sentry
5. Wire components to store
6. Add error handling to all API calls
7. Build + test
8. Deploy to Vercel

**Backend:**
1. Create Prometheus metrics endpoint
2. Instrument agent invocations with metrics
3. Add structured JSON logging
4. Build + test
5. Deploy to Railway

**Infrastructure:**
1. Configure Sentry DSN in .env
2. Set up Prometheus scraper
3. Create Grafana dashboard
4. Run security audit
5. Patch vulnerabilities
6. Configure Sentry alerts

---

## 5. Success Criteria

- ✅ Store persists across refresh
- ✅ All errors show toast + recovery option
- ✅ Sentry dashboard shows errors in real-time
- ✅ Prometheus metrics visible in Grafana
- ✅ Security audit: <5 high findings
- ✅ All tests pass (unit + integration + E2E)
- ✅ Deployed to production
- ✅ No regressions from Phase 5

---

**Specification Status:** ✅ READY FOR TASK BREAKDOWN

Next step: Create 60-80 granular 4-hour tasks from this spec.
