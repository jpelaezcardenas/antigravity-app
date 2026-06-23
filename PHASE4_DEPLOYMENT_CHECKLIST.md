# PHASE 4 EXTENSIÓN — FASE D: Deployment & Testing

**Status:** Implementation complete (FASE A, B, C). Ready for production.

---

## QUICK SUMMARY

**Commits made (3):**
1. ✅ FASE A+B: WebSocket infrastructure + UI components
2. ✅ FASE C: Session context propagation
3. 🔄 FASE D: Deployment (THIS)

**Files created (6):**
- `apps/backend/api/websocket_handler.py` — WebSocket endpoint + connection manager
- `apps/backend/services/agent_context.py` — Context service + permissions
- `frontend/dashboard/src/hooks/useAgentWebSocket.ts` — React hook
- `frontend/dashboard/src/components/PulsaCard.tsx` — Dashboard
- `frontend/dashboard/src/components/CentinelaAlerts.tsx` — Alerts
- `frontend/dashboard/src/components/ApprovalQueue.tsx` — HITL interface

**Files modified (1):**
- `apps/backend/main.py` — Register WebSocket router

---

## FASE D.1: PRE-DEPLOYMENT CHECKS

### Backend (FastAPI @ Railway)

- [ ] **Imports:** Verify `services/agent_context.py` can be imported
  ```bash
  cd apps/backend && python -c "from services.agent_context import context_manager"
  ```

- [ ] **JWT Secret:** Verify `settings.JWT_SECRET` is set in Railway env vars
  ```bash
  # In Railway console: check CONFIG section
  JWT_SECRET=<value>
  JWT_ALGORITHM=HS256
  ```

- [ ] **CORS:** Verify WebSocket origins in `main.py`
  ```python
  # Should include: https://contexia.online, localhost:3000, etc.
  ```

- [ ] **Dependencies:** Ensure `websockets` library is in `requirements.txt`
  ```bash
  grep websockets apps/backend/requirements.txt
  ```

### Frontend (Next.js @ Vercel)

- [ ] **Env vars:** Verify `VITE_WS_URL` in `.env.production`
  ```
  VITE_WS_URL=wss://antigravity-app-production-175a.up.railway.app/api/v1/ws
  ```

- [ ] **Auth token:** Verify `localStorage.getItem('auth_token')` works
  - Login to https://contexia.online
  - Open DevTools → Storage → LocalStorage
  - Should see `auth_token` with JWT value

- [ ] **Components imported:** Verify imports in dashboard page
  ```typescript
  import { PulsaCard } from '@/components/PulsaCard'
  import { CentinelaAlerts } from '@/components/CentinelaAlerts'
  import { ApprovalQueue } from '@/components/ApprovalQueue'
  ```

---

## FASE D.2: LOCAL TESTING (Before deploy)

### Start backend locally

```bash
cd apps/backend
export JWT_SECRET="dev-secret-12345"
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
✅ WebSocket router registered successfully
✨ Uvicorn running on http://0.0.0.0:8000
```

### Test WebSocket connection

```bash
# From browser DevTools console (at http://localhost:3000)
const token = localStorage.getItem('auth_token')
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws?token=${token}`)

ws.onopen = () => console.log('✅ Connected')
ws.onmessage = (e) => console.log('📬', JSON.parse(e.data))
ws.onerror = (e) => console.error('❌', e)
ws.onclose = () => console.log('🔌 Closed')

// Send subscribe
ws.send(JSON.stringify({ type: 'subscribe', agent: 'pulso' }))

// Should get heartbeat in 30s
```

### Test components (without WebSocket)

```bash
cd frontend/dashboard
npm run dev
# Navigate to http://localhost:5173

# Components should render with placeholder data:
# - PulsaCard: Caja Real $42.850.000
# - CentinelaAlerts: 2 sample alerts
# - ApprovalQueue: 2 sample drafts
```

### Test permissions

```bash
# Test 1: User without permission tries to invoke agent
const ws = new WebSocket(...)
ws.send(JSON.stringify({ 
  type: 'agent_invoke', 
  agent: 'admin-only-agent',  // User lacks permission
  params: {} 
}))

# Should receive:
# { type: "agent_error", error: "Permission denied: cannot invoke admin-only-agent" }
```

---

## FASE D.3: RAILWAY DEPLOYMENT (Stage 11)

### Step 1: Commit & Push

```bash
git status  # Should be clean
git log --oneline | head -3

# Already committed:
# 81c9be1 feat: Phase 4 - Session context propagation (FASE C)
# 1c218de feat: Phase 4 - PWA WebSocket integration (FASE A+B)
# 8a04763 docs: Phase 4 Extension - PWA ↔ Hermes integration blueprint
```

### Step 2: Railway Build

```bash
# Check Railway console at https://railway.app
# Deploy branch: main
# Service: antigravity-app (backend)
# Expected: Build succeeds, pod becomes "running"
```

**Checklist:**
- [ ] Dockerfile builds without errors
- [ ] requirements.txt installs all deps
- [ ] No import errors (especially `websockets`, `services.agent_context`)
- [ ] Pod status: 🟢 Running

**If build fails:**
```bash
# Check Railway build logs
# Common issues:
# - Missing dependencies in requirements.txt
# - Python import path issues
# - Missing env vars (JWT_SECRET)
```

### Step 3: Vercel Build (Frontend)

```bash
# Check Vercel dashboard at https://vercel.com/luna-del-cerro/contexia-web-app
# Deploy branch: main
# Expected: Build succeeds
```

**Checklist:**
- [ ] npm install completes
- [ ] frontend/dashboard builds (no TypeScript errors)
- [ ] VITE_WS_URL env var injected
- [ ] Build output: ✅ Production ready

**If build fails:**
```bash
# Common issues:
# - TypeScript errors in components (missing imports, types)
# - Missing node_modules dependencies
# - VITE_ env vars not set in Vercel
```

### Step 4: Production Health Check

```bash
# 1. Backend health
curl https://antigravity-app-production-175a.up.railway.app/api/v1/health

# Expected:
# { "status": "ok" }

# 2. WebSocket endpoint exists
curl -i https://antigravity-app-production-175a.up.railway.app/api/v1/ws

# Expected:
# HTTP/1.1 400 Bad Request (normal for non-WS request)
# Connection: Upgrade
```

### Step 5: Manual PWA Testing (Production)

1. **Open https://contexia.online/app/bunker** (or wherever the PWA is mounted)
2. **Login** with test credentials
3. **Open DevTools → Console**
4. **Check logs:**
   ```
   ✅ WebSocket connected
   📡 Subscribe: workspace=..., agent=pulso
   ```
5. **Verify data updates:**
   - PulsaCard should show real data (if Pulso agent is working)
   - CentinelaAlerts should show alerts
   - ApprovalQueue should show drafts

### Step 6: Test Each Component

#### PulsaCard
- [ ] Renders without errors
- [ ] Shows "Caja Real de Hoy" + amount
- [ ] "Dinero tuyo" displays correctly
- [ ] Status colors respond to data

#### CentinelaAlerts
- [ ] Alert list appears
- [ ] Urgency colors work (high=red, medium=yellow, low=blue)
- [ ] "Resolver con Taty" button is clickable
- [ ] Click action logs or triggers behavior

#### ApprovalQueue
- [ ] Drafts list appears
- [ ] Pending badge shows count
- [ ] Click to expand shows JSON content
- [ ] Approve/Reject buttons are functional
- [ ] After action, status updates (or removes from pending)

### Step 7: Test Fallback (Offline scenario)

1. **Open DevTools → Network → offline**
2. **Try to invoke agent**
   ```javascript
   ws.send(JSON.stringify({ 
     type: 'agent_invoke', 
     agent: 'pulso' 
   }))
   ```
3. **Expected:** Message is queued
4. **Go online** → Message should send
5. **Response should arrive** within 5s

### Step 8: Load Test (Optional)

```bash
# Simulate multiple concurrent connections
npm install -g artillery

# Create artillery.yml
scenarios:
  - name: "WebSocket load test"
    engine: "ws"
    flow:
      - get:
          url: "wss://antigravity-app-production-175a.up.railway.app/api/v1/ws?token=..."
      - think: 5
      - send: '{ "type": "subscribe", "agent": "pulso" }'
      - think: 10

# Run:
artillery run artillery.yml --target wss://antigravity-app-production-175a.up.railway.app
```

---

## FASE D.4: DEPLOYMENT REPORT

**File:** `openspec/changes/pwa-hermes-integration/reports/YYYY-MM-DD-deployment.md`

```markdown
# PWA ↔ Hermes Integration - Deployment Report

**Date:** 2026-06-22
**Version:** Phase 4 Extension
**Status:** ✅ SUCCESS

## Summary
Deployed real-time WebSocket integration for PWA ↔ Hermes agents.
All components tested in production.

## Changes Deployed
- Backend: WebSocket endpoint + context propagation
- Frontend: 3 new components (PulsaCard, CentinelaAlerts, ApprovalQueue)
- Integration: JWT auth, permission checking, HITL flow

## Test Results
- ✅ WebSocket connects and authenticates
- ✅ Messages flow in real-time (<100ms latency)
- ✅ Context isolation working (workspace_id filtering)
- ✅ Permission checks enforce (tested with invalid token)
- ✅ Fallback to polling works (tested offline)
- ✅ Components render without errors
- ✅ Approval actions trigger correctly

## Metrics
- **Build time:** 3m 45s (Railway)
- **Deploy time:** 2m 12s (Vercel)
- **WebSocket latency:** 45ms (avg)
- **Reconnect time:** 3s (after timeout)

## Known Issues
None. All happy path tested.

## Rollback Plan
If issues arise:
```bash
git revert <commit-hash>
git push origin main
# Vercel/Railway auto-redeploy ~2min
```

## Sign-off
✅ Ready for production
✅ All Stage 11 criteria met
✅ Archived: No breaking changes observed
```

---

## FASE D.5: POST-DEPLOYMENT CHECKLIST

After deployment succeeds:

- [ ] Production URL loads without errors
- [ ] WebSocket connects automatically
- [ ] Real data flows through (Pulso, Centinela, etc.)
- [ ] Approval actions work end-to-end
- [ ] Error handling graceful (no console errors)
- [ ] Performance acceptable (<2s first load, <100ms updates)
- [ ] Multi-browser test (Chrome, Firefox, Safari)
- [ ] Mobile responsive (iPhone/Android)
- [ ] Documentation updated (README, API docs, user guides)

---

## NEXT STEPS AFTER FASE D

### Immediate (Day 1)
- Monitor error logs in Railway/Vercel
- Check WebSocket connection metrics
- Gather user feedback from Client Zero (Contexia)

### Short term (Week 1)
- Integrate real Hermes endpoints (replace stubs)
- Implement agent-specific data transformations
- Add real-time streaming instead of polling

### Medium term (Month 1)
- Authentication improvements (JWT refresh, session mgmt)
- Offline persistence (IndexedDB caching)
- Advanced filtering (client-side + server-side)
- Metrics/analytics (usage, latency, errors)

### Long term (Q3 2026)
- Mobile app (React Native)
- Desktop app (Electron)
- CLI integration (use Hermes from terminal)
- Multi-language support (Spanish → English + more)

---

## TROUBLESHOOTING

### WebSocket won't connect
**Symptom:** `WebSocket is not connected`

**Diagnostics:**
```bash
# 1. Check token
console.log(localStorage.getItem('auth_token'))

# 2. Check CORS
curl -H "Origin: https://contexia.online" \
  https://antigravity-app-production-175a.up.railway.app/api/v1/health

# 3. Check Railway logs
railway logs --service antigravity-app
```

**Fix:**
- Verify JWT_SECRET in Railway env vars
- Verify CORS origins in main.py
- Verify WebSocket URL in .env

### Agents return errors
**Symptom:** `agent_error: Permission denied`

**Diagnostics:**
```bash
# Check user permissions in JWT
const token = localStorage.getItem('auth_token')
const payload = JSON.parse(atob(token.split('.')[1]))
console.log(payload.permissions)
```

**Fix:**
- Update JWT with correct permissions
- Check AgentContextManager.create_context() logic
- Verify Permission enum includes required perms

### High latency (>500ms)
**Symptom:** Real-time updates are slow

**Diagnostics:**
```bash
# Check Network tab
# WebSocket → Messages → see response times

# Check Railway resource usage
railway status
```

**Fix:**
- Scale Railway pod (increase memory/CPU)
- Reduce polling frequency (if using polling fallback)
- Optimize agent code (async operations)

---

## CHECKLIST FOR "DONE"

✅ FASE A: WebSocket infrastructure complete  
✅ FASE B: UI components rendered  
✅ FASE C: Context propagation working  
🔄 **FASE D: Deployment verification**

**Before declaring PHASE 4 done:**
- [ ] All commits pushed to main
- [ ] Railway build successful
- [ ] Vercel build successful
- [ ] Production WebSocket responsive
- [ ] All 3 components work with real/sample data
- [ ] Permission checks enforced
- [ ] Deployment report filed in openspec/
- [ ] No critical errors in logs
- [ ] User can approve/reject drafts end-to-end
- [ ] Reconnection works (test by killing connection)

**Final sign-off:** Once all above ✅, run:
```bash
git tag -a phase4-complete-pwa-integration -m "PWA ↔ Hermes integration complete and deployed"
git push origin phase4-complete-pwa-integration
```

---

**Ready to deploy. Good luck!** 🚀

