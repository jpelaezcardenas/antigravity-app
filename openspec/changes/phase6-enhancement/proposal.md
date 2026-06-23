# Phase 6: Enhancement — OpenSpec Proposal

**Date:** 2026-06-23  
**Status:** 📋 **PROPOSAL** (Ready for Design)  
**Target Start:** 2026-06-24  
**Target Duration:** 1 week (5-7 days)  
**Author:** Claude Code + User (jpelaezcardenas@gmail.com)

---

## Executive Summary

Phase 6 enhances the Contexia PWA with production-grade UX, observability, and security improvements. Building on Phase 5's real-time agent integration, Phase 6 adds:

- **Redux/Zustand state management** — Persist complex UI state, cache agent data, support offline workflows
- **Error boundaries + toast UI** — User-friendly error handling, visual feedback for async operations
- **Analytics & monitoring** — Production observability (Prometheus, Grafana, error tracking)
- **Security hardening** — Penetration testing, compliance audit, vulnerability patching

**Impact:** Users get a polished, resilient financial platform with clear error messaging and enterprise-grade reliability.

---

## Problem Statement

### Current State (Phase 5 Complete)
- ✅ All 8 agents operational (real data streaming)
- ✅ Components render correctly
- ✅ WebSocket connection stable
- ❌ **No state persistence** (refresh = lose all data)
- ❌ **No error boundaries** (crashes show blank screens)
- ❌ **No error UI** (network errors not user-friendly)
- ❌ **No observability** (can't monitor production issues)
- ❌ **No security audit** (vulnerability status unknown)

### Business Impact
- Users can't persist approvals across refreshes
- Errors crash the app instead of showing recovery options
- No visibility into production failures
- Compliance/security status unclear

---

## Solution Scope

### In Scope: What Phase 6 Delivers

#### 1. State Management (Redux/Zustand)
**Problem:** Component state lost on refresh, no cache, offline support poor

**Solution:** 
- Store: agentData, permissions, user profile, approval drafts
- Persist: localStorage for offline access
- Sync: Rehydrate on boot, merge with fresh data from backend

**Framework Choice:** Zustand (simpler, smaller, no boilerplate)
- Store: `src/stores/agentStore.ts`
- Slices: agents, user, approvals, settings
- Middleware: localStorage persistence

**Expected:** Users can refresh without losing context

#### 2. Error Boundaries + Toast UI
**Problem:** Errors crash components, users see blank screens

**Solution:**
- Error Boundary wrapper (catches React errors)
- Toast notifications (network errors, validation failures, success messages)
- Graceful degradation (show "retry" button instead of blank)

**Implementation:**
- Component: `src/components/ErrorBoundary.tsx`
- Component: `src/components/Toast.tsx` (Radix UI)
- Hook: `useToast()` (emit toast from anywhere)
- Pattern: Wrap components, emit errors to toast

**Expected:** Users see helpful error messages, can retry operations

#### 3. Analytics & Monitoring
**Problem:** No visibility into production errors, latency, user behavior

**Solution:**
- **Error tracking:** Sentry integration (captures unhandled errors, sends to dashboard)
- **Performance monitoring:** Prometheus metrics (response time, agent latency, cache hit rate)
- **Log aggregation:** Structured logging to central store
- **Dashboards:** Grafana for real-time visualization

**Implementation:**
- Sentry: Error boundary + API wrapper
- Prometheus: Expose `/metrics` endpoint (agent latency, cache stats, error count)
- Logging: Structured JSON logs (timestamp, level, agent, user_id, error)

**Expected:** Ops team can see production health in real-time

#### 4. Security Hardening
**Problem:** No security audit, vulnerability status unknown

**Solution:**
- **Penetration testing:** Manual + automated scans
- **Dependency audit:** npm audit, pip audit
- **Code review:** Security-focused review (auth, CORS, XSS, SQL injection)
- **Compliance:** GDPR, data retention, access logs

**Expected:** Clear security posture, no critical vulnerabilities

### Out of Scope
- Mobile app (Phase 7)
- Advanced filtering/search (Phase 8)
- Multi-language support (Phase 9)
- AI-powered insights (Phase 10)

---

## Success Criteria

| Criterion | Success Indicator |
|-----------|------------------|
| State persists across refresh | localStorage: agentData survives F5 |
| Errors handled gracefully | No blank screens, all errors show toast + retry |
| Observability in place | Sentry + Grafana dashboard live, 0 blind spots |
| Security audit complete | <0 critical, <5 high, all medium/low triaged |
| Performance baseline | Agent latency p99 < 2s, page load < 3s |
| Production ready | All features in main branch, deployed to Vercel/Railway |

---

## Implementation Plan

### Stage 1: State Management (1-2 days)
- Create Zustand store with slices (agents, user, approvals, settings)
- Add localStorage persistence middleware
- Wire components to store (replace useState → useStore)
- Test: Refresh app → data persists ✓

### Stage 2: Error Boundaries + Toast (1-2 days)
- Create Error Boundary component (catches React errors)
- Create Toast component (Radix UI toast library)
- Wrap root components with Error Boundary
- Add toast on API errors, validation errors, success messages
- Test: Break API → toast appears, user sees retry button ✓

### Stage 3: Analytics & Monitoring (1-2 days)
- Integrate Sentry (init in main.tsx, wrap error boundary)
- Add Prometheus metrics endpoint in backend
- Create Grafana dashboard (agent latency, error rate, success rate)
- Test: Trigger error in Sentry → error appears in dashboard ✓

### Stage 4: Security Audit (1 day)
- Run npm audit + pip audit
- Manual penetration test (auth, CORS, XSS injection)
- Code review security checklist
- Patch vulnerabilities

### Stage 5: Testing & Deployment (1 day)
- Unit tests for store, error boundary, toast
- Integration tests (state + component rendering)
- E2E tests (user workflow: login → refresh → approvals still there)
- Deploy to production

---

## Architecture

### State Management (Zustand)
```typescript
// src/stores/agentStore.ts
export const useAgentStore = create((set) => ({
  agents: {},
  user: null,
  approvals: [],
  
  setAgentData: (agent, data) => set(...),
  setUser: (user) => set(...),
  addApproval: (draft) => set(...),
}));

// In component
const agentData = useAgentStore(state => state.agents);
```

### Error Handling
```typescript
// Wrap root app
<ErrorBoundary>
  <App />
</ErrorBoundary>

// In component
try {
  await api.invoke('pulso');
} catch (error) {
  useToast().error(error.message, { retry: () => retry() });
}
```

### Observability
```python
# Backend metrics endpoint
@app.get("/metrics")
async def metrics():
  return f"""
  agent_latency_ms{{agent="pulso"}} {500}
  error_count{{agent="centinela"}} {2}
  cache_hit_rate 0.85
  """

# Frontend: Sentry + Grafana
```

---

## Technical Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| State | Zustand | Small, simple, no boilerplate |
| UI Errors | Radix UI Toast | Accessible, unstyled, composable |
| Error Tracking | Sentry | Industry standard, real-time alerts |
| Metrics | Prometheus | Lightweight, cloud-native |
| Dashboards | Grafana | Real-time, open-source |
| Testing | Vitest + React Testing Library | Fast, modern, great DX |

---

## Risk Mitigation

| Risk | Mitigation |
|-----|-----------|
| State corruption on sync | Versioned localStorage schema, migration strategy |
| Toast spam (too many messages) | Dedup toasts by message + type, auto-close after 5s |
| Sentry noise (too many errors) | Filter non-actionable errors, sample large events |
| Performance regression | Monitor bundle size, lazy-load heavy dependencies |
| Security audit finding | Patch critical immediately, schedule others |

---

## Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Stage 1: State Management | 1-2 days | 📋 |
| Stage 2: Error Boundaries | 1-2 days | 📋 |
| Stage 3: Analytics & Monitoring | 1-2 days | 📋 |
| Stage 4: Security Audit | 1 day | 📋 |
| Stage 5: Testing & Deployment | 1 day | 📋 |
| **Total** | **5-7 days** | 📋 |

---

## Success Metrics (Post-Deployment)

| Metric | Target |
|--------|--------|
| Uptime | >99.9% |
| Error rate | <0.1% |
| Agent latency p99 | <2s |
| Cache hit rate | >85% |
| Sentry errors/day | <10 new |
| Security audit findings | 0 critical |
| User satisfaction | >4.5/5 (NPS) |

---

## Dependencies & Blockers

- ✅ Phase 5 complete (agents live)
- ✅ Redux/Zustand stable versions available
- ✅ Sentry + Grafana cloud accounts available
- ⏳ Security audit team availability

---

## Next Steps

1. ✅ **This proposal approved** → Move to Design stage
2. Design: Detailed architecture, component design, data flow
3. Spec: Detailed API contracts, error codes, metrics schema
4. Tasks: Break into granular 4-hour tasks
5. Apply: Implement all tasks
6. Deploy: Stage 11 deployment verification
7. Archive: Close Phase 6 formally

---

## Sign-Off

**Proposal Status:** 📋 READY FOR DESIGN  
**Complexity:** Medium (State management + observability)  
**Risk Level:** Low (No breaking changes, pure additions)  
**Effort Estimate:** 40-56 hours (5-7 days, 1 developer)

---

**Phase 6: Enhancement** — Taking Contexia from good to great. Building production resilience on Phase 5's real-time agent foundation.
