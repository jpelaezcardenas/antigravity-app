# E2E Testing Plan — PHASE 2 Staging Demo
**Date**: 2026-05-24 | **Status**: Ready for Execution | **Environment**: Staging (Not Production)

---

## Overview

This document outlines the end-to-end testing plan for PHASE 2 (Taty Contadora + Centinela Rules + Telegram Integration) in a live staging environment. All testing uses **real Contexia credentials** but in a non-production sandbox. Security token hardening (TELEGRAM_BOT_TOKEN regeneration, vault setup) deferred to post-testing phase.

---

## Credentials & Access

| Component | Credential | Notes |
|-----------|-----------|-------|
| **Web App Login** | Email: `contexia.marketing@gmail.com` | Dashboard + internal app |
| | Password: `Lindafea0712` | |
| **Company ID** | `ctx-001` (Contexia SAS) | Hardcoded in Taty widget |
| **Telegram Bot** | @taty_contexia_bot | Bidirectional testing |
| **Supabase Project** | `kpynymwghfwshvcvevxq` | Real database (non-prod tables) |

---

## Testing Scope

### ✓ In Scope
- [x] Taty Contadora via Dashboard avatar chat
- [x] Taty Contadora via internal app chat interface
- [x] Telegram bot (@taty_contexia_bot) bidirectional messaging
- [x] Centinela rule evaluation (10 rules)
- [x] Centinela alerts display in Pulso dashboard
- [x] Mobile PWA (iOS Safari, Android Chrome) full functionality
- [x] Desktop PWA (Windows/Mac Chrome) full functionality
- [x] LLM failover chain resilience
- [x] Response latency (target P95 < 4s)
- [x] Citation accuracy and RAG retrieval

### ✗ Out of Scope (Deferred)
- [ ] TELEGRAM_BOT_TOKEN regeneration (do after successful testing)
- [ ] Vault integration (1Password/AWS Secrets Manager)
- [ ] Production security hardening
- [ ] Load testing (staging only, small dataset)
- [ ] Compliance audit (post-MVP)

---

## Test Environment URLs

| Component | URL | Status |
|-----------|-----|--------|
| **Web App** | https://antigravity-app-production-175a.up.railway.app | ✓ Live |
| **Telegram Webhook** | https://antigravity-app-production-175a.up.railway.app/api/v1/channels/telegram/webhook | ✓ Active |
| **Supabase Dashboard** | https://supabase.com/dashboard/project/kpynymwghfwshvcvevxq | ✓ Access granted |
| **Telegram Bot** | https://t.me/taty_contexia_bot | ✓ Deployed |

---

## Test Categories

### 1. Authentication & Login (T1)

**Objective**: Verify user authentication and session persistence across devices.

**Steps**:

1. **Web Browser (Desktop)**
   - [ ] Navigate to https://antigravity-app-production-175a.up.railway.app
   - [ ] Click "Login" / "Sign In"
   - [ ] Enter email: `contexia.marketing@gmail.com`
   - [ ] Enter password: `Lindafea0712`
   - [ ] Verify: Dashboard loads with Pulso tab active
   - [ ] Verify: Bottom navigation shows 4 tabs (Pulso, Fiscal, Radar, Config)
   - [ ] Verify: User name/avatar displays in top bar

2. **Mobile Browser (iOS Safari)**
   - [ ] Open same URL on iPhone/iPad
   - [ ] Repeat steps 1-3 above
   - [ ] Verify: Layout responsive, bottom nav stacks correctly
   - [ ] Verify: Tap "Add to Home Screen" → PWA installs
   - [ ] Verify: Launch from home screen → app loads in fullscreen

3. **Mobile Browser (Android Chrome)**
   - [ ] Open same URL on Android device
   - [ ] Repeat steps 1-3
   - [ ] Verify: "Install app" prompt appears
   - [ ] Accept install → app adds to home screen
   - [ ] Verify: Launch from home screen → fullscreen experience

4. **Session Persistence**
   - [ ] Login on desktop, open DevTools → Application tab
   - [ ] Verify: authToken (JWT or session cookie) stored
   - [ ] Close browser completely
   - [ ] Reopen app → verify auto-logged-in (no re-enter credentials)

**Success Criteria**:
- ✓ All 3 devices (desktop, iOS, Android) login successful
- ✓ Session persists across browser restarts
- ✓ No 401 / authentication errors
- ✓ Avatar/user info displays correctly

---

### 2. Taty Contadora — Avatar Chat (T2)

**Objective**: Verify Taty responds to fiscal questions via dashboard avatar chat component.

**Steps**:

1. **Navigate to Taty Page**
   - [ ] From any tab, look for "Taty" or "Asesora Fiscal" link (may be in Config or separate page)
   - [ ] Alternative: Navigate to `/app/taty` directly
   - [ ] Verify: Page loads with heading "Taty - Asesora Fiscal IA"
   - [ ] Verify: Input field shows placeholder "Pregunta a Taty sobre fiscal..."
   - [ ] Verify: Two info cards visible ("Fuentes confiables", "Escalaciones")

2. **Test In-Scope Question (Fiscal/DIAN)**
   - [ ] Type question: "¿Cuál es el límite de ingresos para Régimen Simple 2026?"
   - [ ] Click send button (or press Enter)
   - [ ] Verify: Loading spinner appears ("Taty está procesando...")
   - [ ] Wait for response (target < 4s)
   - [ ] Verify: Response card appears with:
     - [ ] "Respuesta de Taty" header
     - [ ] Answer text (should mention 160 UVT ≈ $8.38M COP)
     - [ ] Latency displayed (e.g., "⏱️ 2341ms")
     - [ ] Confidence score (e.g., "📊 92% confianza")
   - [ ] Verify: Citations section below answer
   - [ ] Verify: At least 1 citation with source + fragment

3. **Test Out-of-Scope Question (Escalation)**
   - [ ] Type question: "¿Debo instaurar una demanda contra mi socio por robo?"
   - [ ] Click send
   - [ ] Wait for response
   - [ ] Verify: Response includes warning badge "⚠️ Requiere revisión de CFO"
   - [ ] Verify: "Contactar CFO" button appears in action section
   - [ ] Verify: Answer acknowledges specialization required

4. **Test Multiple Questions**
   - [ ] Click "Nueva pregunta" button
   - [ ] Type: "¿Cuál es la tasa de retención en la fuente para servicios?"
   - [ ] Verify: Input cleared, new response loads
   - [ ] Click "Nueva pregunta" again
   - [ ] Type: "¿Qué es la provisión de cuentas por cobrar?"
   - [ ] Verify: Third question processed without errors

5. **Test Error Handling**
   - [ ] Type empty question, try to send
   - [ ] Verify: Send button disabled (or error message)
   - [ ] Type very long question (>500 chars)
   - [ ] Verify: Sends successfully, response within time budget
   - [ ] Type special characters: "¿Qué pasa con €, ©, ñ, á, é, í, ó, ú?"
   - [ ] Verify: UTF-8 handling correct, no mojibake

**Success Criteria**:
- ✓ In-scope question answered correctly (mentions UVT limits, retention rates, etc.)
- ✓ Out-of-scope question flagged for human review (escalation badge)
- ✓ Citations displayed with source + fragment
- ✓ Response latency < 4 seconds (majority cases)
- ✓ Multiple sequential questions handled cleanly
- ✓ No 500 errors or crashes
- ✓ UTF-8 characters render correctly

---

### 3. Taty Contadora — Internal App Chat (T3)

**Objective**: Verify Taty accessible via internal dashboard chat (if different from T2 avatar page).

**Steps**:

1. **Locate Chat Interface**
   - [ ] Look for chat icon in top bar or bottom nav
   - [ ] Alternative: Check Config tab → Chat Settings
   - [ ] If no separate chat UI: Skip this test (avatar page T2 sufficient)
   - [ ] If chat exists: Verify it's visually distinct from T2 avatar

2. **Test Chat Functionality**
   - [ ] Type same in-scope question as T2: "¿Cuál es el límite de ingresos para Régimen Simple 2026?"
   - [ ] Send
   - [ ] Verify: Response matches T2 (same answer, citations, latency)
   - [ ] Verify: Chat history preserved (can scroll up to see previous questions)

3. **Test Chat History**
   - [ ] Send 5 questions in rapid succession
   - [ ] Verify: All appear in chat thread (alternating user/Taty bubbles)
   - [ ] Scroll up to earliest question
   - [ ] Verify: Timestamp or conversation ID visible for audit

**Success Criteria**:
- ✓ Chat interface loads and responds
- ✓ Taty answers consistent across avatar chat and internal chat
- ✓ Chat history preserved and scrollable
- ✓ No duplicate messages or loss of responses

---

### 4. Telegram Bot Integration (T4)

**Objective**: Verify bidirectional Telegram messaging with @taty_contexia_bot.

**Steps**:

1. **Setup**
   - [ ] Open Telegram app (or web.telegram.org)
   - [ ] Search for bot: `@taty_contexia_bot`
   - [ ] Click "Start" button to initialize conversation
   - [ ] Verify: Welcome message received (if bot sends one)

2. **Send In-Scope Question**
   - [ ] Type message: "¿Cuál es el límite de ingresos para Régimen Simple 2026?"
   - [ ] Send
   - [ ] Wait 3-5 seconds for response
   - [ ] Verify: Taty response arrives as Telegram message
   - [ ] Verify: Answer matches web avatar chat (T2/T3)
   - [ ] Note: Latency may be higher due to webhook overhead (acceptable up to 6s)

3. **Send Out-of-Scope Question**
   - [ ] Type: "¿Debo demandar a mi socio?"
   - [ ] Send
   - [ ] Verify: Response includes human review recommendation
   - [ ] Verify: Escalation context noted in message

4. **Send Multiple Messages**
   - [ ] Rapid-fire 3 questions (with 2s pause between)
   - [ ] Verify: All receive responses
   - [ ] Verify: No rate limiting or timeout errors
   - [ ] Check response order (should be FIFO)

5. **Test Error Handling**
   - [ ] Send empty message
   - [ ] Verify: Graceful handling (no crash, possibly "empty question" message)
   - [ ] Send very long message (>4000 chars)
   - [ ] Verify: Truncated appropriately or sent as-is

6. **Verify Webhook Logs (Optional)**
   - [ ] Access Supabase dashboard → Logs
   - [ ] Filter for `/api/v1/channels/telegram/webhook`
   - [ ] Verify: 200 OK responses for each message
   - [ ] Verify: HMAC signature validation passed (no 401s)
   - [ ] Verify: Latency < 2s per webhook invocation

**Success Criteria**:
- ✓ Bot responds to all questions within 6 seconds
- ✓ Answers consistent across web and Telegram
- ✓ Escalation context preserved in Telegram format
- ✓ Multiple rapid messages handled correctly (no loss, no duplicates)
- ✓ No 500 errors or webhook timeouts
- ✓ Telegram logs show successful HMAC verification

---

### 5. Centinela Rules Engine (T5)

**Objective**: Verify 10 fiscal rules evaluate correctly and generate alerts.

**Prerequisites**:
- Access to Supabase SQL editor
- Understanding of 10 rule thresholds (UVT limits, retention %, margin ranges, etc.)

**Steps**:

1. **Manual Rule Evaluation via API**
   - [ ] Use Postman or `curl` to POST to `/api/v1/centinela/evaluate`
   - [ ] Request body (Rule 1: UVT Excedido):
     ```json
     {
       "company_id": "ctx-001",
       "data": {
         "regimen": "Régimen Simple",
         "annual_revenue": 10000000
       }
     }
     ```
   - [ ] Expected response: Alert for Rule1UVTExcedido (10M > 8.38M limit)
   - [ ] Verify: `rule_id: "R001"`, `severity: "warning"`, description mentions UVT

2. **Test All 10 Rules**
   - [ ] R001 UVT: annual_revenue = 10M (Simple regime) → Alert
   - [ ] R001 UVT: annual_revenue = 5M (Simple regime) → No alert
   - [ ] R002 Retención: service_revenue = 1M, retention_paid = 10k (< 3%) → Alert (Critical)
   - [ ] R002 Retención: service_revenue = 1M, retention_paid = 30k (≥ 3%) → No alert
   - [ ] R003 Facturación: invoices = [100, 101, 105, 106] → Alert (gap 101→105)
   - [ ] R003 Facturación: invoices = [100, 101, 102] → No alert
   - [ ] R004 Cambio Régimen: last_regime_change_date = 2026-01-15, dian_notified = false → Alert (Critical)
   - [ ] R004 Cambio Régimen: dian_notified = true → No alert
   - [ ] R005 Provisiones: accounts_receivable = 1M, allowance = 40k (< 5%) → Alert
   - [ ] R005 Provisiones: allowance = 50k (= 5%) → No alert
   - [ ] R006 Margen Bruto: sector = "Servicios Digitales", gross_margin = 35% (< 40% min) → Alert
   - [ ] R006 Margen Bruto: gross_margin = 50% (40-70% range) → No alert
   - [ ] R007 Operación Relacionada: related_party = [party1], declared = [] → Alert (Critical)
   - [ ] R007 Operación Relacionada: declared = [party1] → No alert
   - [ ] R008 Activo Sobrevaluado: total_cost = 1M, accumulated_depreciation = 40k (4%) → Alert
   - [ ] R008 Activo Sobrevaluado: accumulated_depreciation = 60k (6%) → No alert
   - [ ] R009 Deuda DIAN: dian_debt = 500k, overdue_days = 30 → Alert (Critical)
   - [ ] R009 Deuda DIAN: dian_debt = 0 → No alert
   - [ ] R010 Inconsistencia: assets = 1M, liabilities = 600k, equity = 300k (mismatch) → Alert (Critical)
   - [ ] R010 Inconsistencia: equity = 400k (1M = 600k + 400k) → No alert

3. **Risk Level Calculation**
   - [ ] Trigger 2+ Critical rules → risk_level = "critical"
   - [ ] Trigger 1 Critical OR 3+ Warnings → risk_level = "high"
   - [ ] Trigger 1+ Warnings (no Critical) → risk_level = "medium"
   - [ ] No alerts → risk_level = "low"

4. **Database Verification**
   - [ ] Connect to Supabase SQL editor
   - [ ] Run: `SELECT * FROM centinela_alerts WHERE company_id = 'ctx-001' ORDER BY created_at DESC LIMIT 10;`
   - [ ] Verify: All triggered alerts persisted
   - [ ] Verify: Columns populated: rule_id, severity, title, description, recommendation, evidence (JSON)

5. **Health Check**
   - [ ] GET `/api/v1/centinela/health`
   - [ ] Expected: `{"status": "ok"}` or 200 OK

**Success Criteria**:
- ✓ All 10 rules trigger correctly on threshold violations
- ✓ No alerts when data within acceptable ranges
- ✓ Risk level calculated correctly (critical/high/medium/low)
- ✓ Alerts persisted to Supabase with complete evidence
- ✓ Health check endpoint responds
- ✓ Latency < 1s for single rule evaluation

---

### 6. Centinela Alerts — Pulso Dashboard (T6)

**Objective**: Verify Centinela alerts display in Pulso (Overview) tab.

**Steps**:

1. **Navigate to Pulso Tab**
   - [ ] Login if not already
   - [ ] Click "Pulso" in bottom navigation (first tab)
   - [ ] Verify: Dashboard loads with overview metrics

2. **Locate Alert Section**
   - [ ] Look for "Alertas" / "Centinela" / "Riesgos Fiscales" section
   - [ ] Verify: Card or panel displays
   - [ ] Verify: Color-coded by severity (Critical = red, High = orange, Medium = yellow, Low = gray)

3. **Test Alert Display**
   - [ ] Trigger a Centinela rule via API (from T5)
   - [ ] Example: POST `/api/v1/centinela/evaluate` with annual_revenue = 10M (trigger R001)
   - [ ] Return to Pulso dashboard, refresh (F5)
   - [ ] Verify: New alert appears in alerts section
   - [ ] Verify: Rule name, description, recommendation visible
   - [ ] Verify: Severity badge matches rule severity

4. **Test Semáforo (Traffic Light) Status**
   - [ ] If "8AM semáforo" feature implemented: verify status indicator
   - [ ] Expected: 🔴 Red (critical risk), 🟡 Yellow (medium), 🟢 Green (low risk)
   - [ ] Verify: Color updates when new alerts triggered

5. **Test Alert Interactions (if available)**
   - [ ] Click on alert card
   - [ ] Verify: Expands to show full details (evidence, links to remediation)
   - [ ] Verify: "Marcar como resuelto" button (marks status = resolved)
   - [ ] Click button, refresh
   - [ ] Verify: Alert no longer appears (or moved to "Resolved" section)

6. **Test Alert Filtering (if available)**
   - [ ] Look for filter buttons (By Severity, By Rule, By Date)
   - [ ] Click "Críticos" / "Critical"
   - [ ] Verify: Only critical alerts show
   - [ ] Click "Todos" / "All"
   - [ ] Verify: All alerts return

**Success Criteria**:
- ✓ Alerts appear in Pulso dashboard within 5 seconds of being triggered
- ✓ Severity badges display with correct color coding
- ✓ Alert details (title, description, recommendation, evidence) complete
- ✓ Semáforo status reflects overall risk level (if implemented)
- ✓ Alert interactions (expand, resolve, filter) functional
- ✓ No lag or loading delays when refreshing dashboard

---

### 7. Mobile PWA — Full Functionality (T7)

**Objective**: Verify all app features work on mobile PWA (iPhone & Android).

**Prerequisites**:
- iOS device (iPhone 12+) with Safari
- Android device (Android 10+) with Chrome
- Both devices on same WiFi as testing machine (optional, for local testing)

**Steps**:

1. **iOS PWA Installation**
   - [ ] On iPhone, open Safari
   - [ ] Navigate to: https://antigravity-app-production-175a.up.railway.app
   - [ ] Tap Share icon (bottom center)
   - [ ] Scroll down, tap "Add to Home Screen"
   - [ ] Name: "Contexia"
   - [ ] Tap "Add"
   - [ ] Verify: Icon added to home screen
   - [ ] Tap icon to launch app
   - [ ] Verify: App opens in fullscreen (no Safari chrome)

2. **Android PWA Installation**
   - [ ] On Android, open Chrome
   - [ ] Navigate to same URL
   - [ ] Tap menu (3 dots, top right)
   - [ ] Tap "Install app" or "Add to Home screen"
   - [ ] Confirm
   - [ ] Verify: Icon on home screen
   - [ ] Tap to launch
   - [ ] Verify: Fullscreen app mode (no Chrome address bar)

3. **Test Core Features on iOS**
   - [ ] Login with contexia.marketing@gmail.com / Lindafea0712
   - [ ] Navigate Pulso tab (overview) → verify layout responsive
   - [ ] Navigate Fiscal tab → verify tables/charts readable
   - [ ] Navigate Radar tab → verify charts render (SVG or canvas)
   - [ ] Navigate Config tab → verify form inputs accessible
   - [ ] Open Taty page (if in menu) → test avatar chat (T2 steps)
   - [ ] Verify: All text readable (no overflow, proper font sizing)
   - [ ] Verify: Buttons/links tappable (min 44x44pt touch area)
   - [ ] Verify: Scrolling smooth (no jank)

4. **Test Core Features on Android**
   - [ ] Repeat step 3 above
   - [ ] Verify: Same functionality on Android Chrome

5. **Test Offline Behavior (Optional)**
   - [ ] On iOS PWA: Turn on Airplane mode
   - [ ] Try to open new question in Taty
   - [ ] Expected: Error message or cached response (if service worker implemented)
   - [ ] Turn off Airplane mode
   - [ ] Retry → should work

6. **Test Notifications (Optional, if PWA push implemented)**
   - [ ] Check if app requests notification permission on first load
   - [ ] Accept permission
   - [ ] Wait 30 seconds or trigger alert via API
   - [ ] Verify: Push notification arrives on device
   - [ ] Tap notification → app opens to alert detail

7. **Test Performance**
   - [ ] On iOS: Developer Tools (Safari → Develop → [Device] → [App])
   - [ ] Monitor console for errors
   - [ ] Note: App should load in < 3 seconds
   - [ ] On Android: Chrome DevTools (chrome://inspect)
   - [ ] Same checks

**Success Criteria**:
- ✓ PWA installs on both iOS and Android
- ✓ App launches in fullscreen mode (no browser chrome)
- ✓ All tabs and features accessible on mobile
- ✓ Touch interaction responsive (buttons, inputs, navigation)
- ✓ Text readable without zoom (responsive layout)
- ✓ No console errors on any feature
- ✓ Load time < 3 seconds
- ✓ Offline mode graceful (if implemented)

---

### 8. Desktop PWA — Full Functionality (T8)

**Objective**: Verify all app features work on desktop PWA (Windows/Mac Chrome).

**Steps**:

1. **Desktop PWA Installation (Windows/Mac)**
   - [ ] Open Chrome
   - [ ] Navigate to: https://antigravity-app-production-175a.up.railway.app
   - [ ] Click install icon (top right of address bar, or menu → "Install app")
   - [ ] Click "Install"
   - [ ] Verify: App window opens (standalone, no Chrome chrome)
   - [ ] Verify: App icon appears in taskbar (Windows) or dock (Mac)

2. **Test All Features**
   - [ ] Login with contexia.marketing@gmail.com / Lindafea0712
   - [ ] **Pulso Tab**: Verify dashboard overview, metrics, semáforo status
   - [ ] **Fiscal Tab**: Verify tax reporting tables, drill-down into details
   - [ ] **Radar Tab**: Verify scenario selector (pesimista/base/optimista), chart rendering
   - [ ] **Config Tab**: Verify settings form, save functionality
   - [ ] **Taty Chat**: Test fiscal questions (T2 steps), verify latency < 4s
   - [ ] **Centinela Alerts**: Verify alert list, filtering, resolution (T6 steps)

3. **Test Keyboard Navigation**
   - [ ] Press Tab repeatedly to navigate through all interactive elements
   - [ ] Verify: Focus visible (outline or highlight)
   - [ ] Verify: No focus trap (can Tab out of any component)
   - [ ] Test input fields: type, clear, submit via Enter key
   - [ ] Test select dropdowns: Tab to focus, Arrow keys to navigate options

4. **Test Window Resizing**
   - [ ] Resize window to tablet width (768px)
   - [ ] Verify: Layout responsive, no horizontal scroll
   - [ ] Resize to mobile width (375px)
   - [ ] Verify: Mobile layout adapts correctly
   - [ ] Resize back to desktop (1280px+)
   - [ ] Verify: Returns to desktop layout

5. **Test Multi-Monitor (if available)**
   - [ ] Open app on primary monitor
   - [ ] Drag app window to secondary monitor
   - [ ] Verify: Renders correctly on secondary monitor (no distortion)

6. **Monitor DevTools**
   - [ ] Open Chrome DevTools (F12)
   - [ ] Console tab: verify no errors
   - [ ] Network tab: verify all requests 200 OK
   - [ ] Performance tab: record page load
   - [ ] Verify: First Paint < 1.5s, Largest Contentful Paint < 3s

**Success Criteria**:
- ✓ PWA installs and launches on desktop
- ✓ All tabs and features fully functional
- ✓ Responsive layout adapts to window size (375px to 1920px+)
- ✓ Keyboard navigation complete (Tab through all elements)
- ✓ No console errors or warnings
- ✓ Network requests all successful
- ✓ Performance meets targets (FCP < 1.5s, LCP < 3s)

---

### 9. Cross-Device Data Sync (T9)

**Objective**: Verify data consistency between mobile and desktop PWAs and web browsers.

**Steps**:

1. **Setup**
   - [ ] Have desktop browser, iOS PWA, and Android PWA open simultaneously
   - [ ] All logged in as contexia.marketing@gmail.com
   - [ ] Have Telegram bot open as well (4 channels)

2. **Test Data Sync — Taty Chat History**
   - [ ] Ask question on Desktop: "¿Cuál es el UVT 2026?"
   - [ ] Wait for response
   - [ ] Switch to iOS PWA → navigate to Taty page
   - [ ] Verify: Same question visible in chat history (if persistent)
   - [ ] Switch to Android PWA → same verification
   - [ ] Switch to Telegram bot → ask different question
   - [ ] Switch back to Desktop → verify Telegram question appears (if shared history)

3. **Test Data Sync — Centinela Alerts**
   - [ ] Trigger alert via API on desktop (curl/Postman)
   - [ ] Refresh Pulso tab on iOS PWA
   - [ ] Verify: New alert appears
   - [ ] Refresh Pulso tab on Android PWA
   - [ ] Verify: Same alert visible
   - [ ] Desktop browser (non-PWA) → refresh
   - [ ] Verify: Alert appears (real-time or within 5 seconds)

4. **Test Alert Resolution Sync**
   - [ ] On Desktop: Mark alert as "Resuelto"
   - [ ] On iOS: Refresh Pulso
   - [ ] Verify: Alert marked as resolved (or removed from active list)
   - [ ] On Android: Refresh
   - [ ] Verify: Same state

5. **Test Telegram Sync**
   - [ ] Ask question on Telegram bot
   - [ ] Check Desktop Taty page → verify message appears (if shared history)
   - [ ] Ask question on Desktop Taty
   - [ ] Check Telegram → question does NOT appear (one-way is acceptable, but note limitation)

**Success Criteria**:
- ✓ Taty chat history consistent across all web/PWA instances
- ✓ Centinela alerts synced in real-time (≤ 5 seconds) across all devices
- ✓ Alert state changes (resolved) reflected immediately on all devices
- ✓ User session valid across all platforms (no 401 errors on device switch)
- ✓ No data corruption or duplication when viewing from multiple devices

---

### 10. Performance & Latency (T10)

**Objective**: Verify response times and resource usage meet specifications.

**Requirements**:
- Taty response latency: P95 < 4 seconds
- Centinela evaluation: < 1 second
- Page load time: FCP < 1.5s, LCP < 3s
- Telegram webhook: < 2s round-trip

**Steps**:

1. **Taty Latency Measurement**
   - [ ] Ask 5 fiscal questions on Desktop
   - [ ] Record response time for each (displayed in response card as "⏱️ XXms")
   - [ ] Expected values: 1500-3500ms (depends on LLM provider)
   - [ ] Calculate average and P95
   - [ ] Verify: Average < 3s, P95 < 4s
   - [ ] Repeat on iOS PWA (may be slightly higher due to mobile latency)
   - [ ] Repeat on Telegram bot (may be 4-6s due to webhook overhead)

2. **Centinela Latency**
   - [ ] Use curl/Postman to measure `/api/v1/centinela/evaluate` response time
   - [ ] Example:
     ```bash
     curl -w "@curl-format.txt" -o /dev/null -s https://antigravity-app-production-175a.up.railway.app/api/v1/centinela/evaluate \
       -X POST \
       -H "Content-Type: application/json" \
       -d '{"company_id":"ctx-001","data":{"regimen":"Régimen Común","dian_debt":500000}}'
     ```
   - [ ] Measure 5 requests
   - [ ] Expected: 300-800ms
   - [ ] Verify: All < 1s

3. **Page Load Performance (Desktop)**
   - [ ] Clear cache: DevTools → Application → Clear storage
   - [ ] Navigate to home page
   - [ ] Open Performance tab, click Record
   - [ ] Wait for full load
   - [ ] Stop recording
   - [ ] Check metrics:
     - [ ] First Contentful Paint (FCP): target < 1.5s
     - [ ] Largest Contentful Paint (LCP): target < 3s
     - [ ] Cumulative Layout Shift (CLS): target < 0.1
   - [ ] Repeat 3 times, average results

4. **Page Load Performance (Mobile)**
   - [ ] On iOS PWA: Open Safari Dev Tools (Develop → [Device] → [App])
   - [ ] Measure load time (note: PWA may load from cache, so measure cold start if possible)
   - [ ] Expected: 1-4 seconds
   - [ ] Repeat on Android

5. **Telegram Webhook Performance**
   - [ ] Use Postman to measure webhook latency
   - [ ] Send test Telegram message (or simulate via curl)
   - [ ] Measure round-trip time (request sent → response received)
   - [ ] Expected: < 2s
   - [ ] Repeat 5 times, average

6. **Database Query Performance**
   - [ ] Check Supabase logs for slow queries
   - [ ] Expected: All queries < 500ms
   - [ ] Look for any N+1 queries (e.g., loading all messages + per-message operations)

7. **Resource Usage (Optional)**
   - [ ] iOS PWA: Monitor memory via Xcode instruments or Safari dev tools
   - [ ] Android: Chrome DevTools → More tools → Task manager
   - [ ] Desktop: Chrome Task Manager (Shift+Esc)
   - [ ] Expected: App uses < 100MB memory (mobile), < 200MB (desktop)
   - [ ] No memory leaks (memory usage stable after 10 minutes of use)

**Success Criteria**:
- ✓ Taty latency: 1.5-3.5s average, P95 < 4s
- ✓ Centinela latency: < 1s (target 300-800ms)
- ✓ Page FCP < 1.5s, LCP < 3s
- ✓ CLS < 0.1 (no layout shift)
- ✓ Telegram webhook < 2s
- ✓ All database queries < 500ms
- ✓ Memory usage stable (no leaks)

---

## Test Execution Order

**Day 1 (Today)**
1. T1: Authentication & Login (30 min)
2. T2: Taty Avatar Chat (30 min)
3. T5: Centinela Rules (30 min)

**Day 2 (Tomorrow)**
4. T3: Taty Internal Chat (20 min)
5. T4: Telegram Bot (30 min)
6. T6: Centinela Pulso Dashboard (20 min)

**Day 3**
7. T7: Mobile PWA (45 min)
8. T8: Desktop PWA (30 min)

**Day 4**
9. T9: Cross-Device Sync (20 min)
10. T10: Performance & Latency (30 min)

---

## Test Results Template

For each test, fill in results:

```
## T{N}: {Test Name}
**Date**: 2026-05-{DD}  
**Tester**: [Your name]  
**Environment**: Staging (Production-175a)  
**Status**: ✓ PASS / ⚠ PARTIAL / ✗ FAIL  

### Observed Behavior
[Detailed notes of what happened]

### Expected vs Actual
- Expected: [What should happen]
- Actual: [What did happen]

### Issues Found
- [ ] Issue 1: [Description] (Severity: Critical/High/Medium/Low)
- [ ] Issue 2: ...

### Performance Metrics
- Taty latency: [XXXms] (target < 4s)
- Page load FCP: [XXXms] (target < 1.5s)
- Memory usage: [XXMb]

### Evidence
[Screenshots, curl output, logs, links to Supabase logs]

### Sign-Off
✓ Approved for next phase / ⚠ Conditional (with notes) / ✗ Blocked (issues must be resolved)
```

---

## Troubleshooting Guide

### Issue: Taty returns "Error desconocido"
**Possible Causes**:
1. Backend service not running or crashed
2. LLM provider (Groq) down, failover not working
3. Supabase connection lost
4. Anonymization module error

**Debug Steps**:
- Check backend logs: `journalctl -u antigravity-app -f` (if systemd) or Cloud logging (Railway)
- Test LLM failover: `curl https://api.groq.com/healthcheck` → should return 200
- Test Supabase: Open SQL editor, run `SELECT NOW()` → should respond
- Review `/apps/backend/agents/anonymizer.py` for regex errors

---

### Issue: Centinela alerts not appearing in Pulso
**Possible Causes**:
1. Alerts evaluated but not saved to DB
2. Frontend not refreshing/polling
3. Company ID mismatch

**Debug Steps**:
- Verify alert saved: `SELECT * FROM centinela_alerts WHERE company_id = 'ctx-001' ORDER BY created_at DESC LIMIT 1;`
- Verify company_id in request matches Supabase: `SELECT company_id FROM agent_profiles LIMIT 1;`
- Check frontend polling interval (should refresh every 30-60s or use WebSocket)

---

### Issue: Telegram bot not responding
**Possible Causes**:
1. Webhook URL not registered with Telegram
2. TELEGRAM_WEBHOOK_SECRET mismatch
3. Webhook endpoint returning non-200 status
4. Telegram token revoked

**Debug Steps**:
- Verify webhook registered: `curl -X POST https://api.telegram.org/bot{TOKEN}/setWebhook -d "url={URL}"`
- Check webhook logs: `tail -f /var/log/webhook.log` or Rails/Railway logging
- Test HMAC: Generate signature locally, compare with header value

---

### Issue: PWA not updating after new deployment
**Possible Causes**:
1. Service worker cached old version
2. Browser cache not cleared
3. App shell not invalidating on new version

**Debug Steps**:
- Uninstall PWA: iOS → Settings → Safari → Downloaded Apps → [App] → Remove
- Android → Long-press app → Uninstall or App info → Uninstall
- Clear browser cache: Ctrl+Shift+Delete (Windows) or Cmd+Shift+Delete (Mac)
- Reinstall PWA

---

## Sign-Off Criteria

**All tests PASS**:
- ✓ Proceed to security hardening (DAY 2: TELEGRAM_BOT_TOKEN regen, vault setup)
- ✓ Plan production deployment

**Some tests PARTIAL/FAIL**:
- ⚠ Categorize issues: Blocking vs Non-blocking
- ⚠ For blocking issues: create bug fix branch, update spec, re-test
- ⚠ For non-blocking: log as tech debt, proceed with mitigations documented

**Critical Issues Block Go-Live**:
- ✗ Auth failures (T1)
- ✗ Taty non-functional (T2/T3/T4)
- ✗ Centinela crashes (T5/T6)
- ✗ Mobile/Desktop unusable (T7/T8)

---

## Next Steps (Post-Testing)

1. **If all tests pass**:
   - [ ] Document test results in this file (append section "## Test Results — 2026-05-XX")
   - [ ] Create issue: "Regenerate TELEGRAM_BOT_TOKEN via Telegram Bot Father"
   - [ ] Create issue: "Setup vault (1Password/AWS Secrets Manager)"
   - [ ] Merge feature/phase2-llm-taty-centinela into staging
   - [ ] Schedule production deployment for 2026-05-27 or later

2. **If tests fail**:
   - [ ] File GitHub issues for each blocking failure
   - [ ] Update spec `specs/phase2-llm-integration.md` with findings
   - [ ] Create hotfix branches, re-test
   - [ ] Document lessons learned in `CLAUDE.md`

3. **DAY 2 — Monday 2026-05-27**:
   - [ ] Port `llm_analyzer.py` from `copiloto-contratos-eafit` to antigravity-app agents
   - [ ] Implement dual A/B orchestration (Entidad A vs Entidad B)
   - [ ] Activate Neurocontabilidad real-time indexing
   - [ ] Setup Centinela cron (nightly evaluation of all clients)

---

**Document Status**: Ready for Execution  
**Last Updated**: 2026-05-24  
**Next Review**: After T1 completion (2026-05-24 EOD)
