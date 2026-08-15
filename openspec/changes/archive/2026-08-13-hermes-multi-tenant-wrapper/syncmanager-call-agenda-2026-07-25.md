# SyncManager Technical Call — Agenda & Preparation

**Scheduled:** Friday, July 25, 2026  
**Duration:** 90 minutes  
**Format:** Zoom / Teams (TBD)  
**Attendees:**
- **Contexia:** Juan (Product Lead), Backend Architect, DevOps Lead
- **SyncManager:** Technical Lead, API Specialist, Support

---

## Purpose

Discuss technical integration of SyncManager API with Contexia's Hermes multi-tenant agent orchestration platform. Contexia is building a deterministic Shadow General Ledger (SGLedger) as a fallback strategy if SyncManager is deprecated or unavailable.

**Deliverable:** Detailed integration roadmap for Q3-Q4 2026.

---

## Pre-Call Preparation (Contexia Team)

### By Jul 20, 2026
- [ ] Read SyncManager proposal (22 pages) — assess against 37-question framework
- [ ] Prepare: Architecture diagram (Hermes ↔ SyncManager ↔ Supabase)
- [ ] Prepare: Live demo environment (Hermes operators, RLS-filtered data)
- [ ] List: 5 highest-priority integration questions

### By Jul 23, 2026
- [ ] Finalize slides (see Slide Deck section below)
- [ ] Test Zoom/Teams connection
- [ ] Assign note-taker

---

## Call Agenda (90 minutes)

### 1. Introductions & Context (5 min)
- Contexia mission: Financial intelligence for SMEs/freelancers (DIAN-compliant, Colombia)
- Hermes: Multi-tenant agent orchestrator (local-first, data sovereign)
- SyncManager role: Phase 1 MVP for DIAN/Siigo GL synchronization

### 2. Hermes Architecture Overview (15 min)
**Presenter:** Backend Architect

**Topics:**
- Multi-tenant isolation (JWT middleware + Supabase RLS)
- Operator model (9 agents calling Railway backend deterministically)
- Approval Queue + HITL workflow
- Data sovereignty (local-first, no cloud VPS)

**Diagram to show:**
```
Hermes Workspace (local WSL)
  ├─ Pulso (daily KPI summary)
  ├─ Centinela (risk alerts)
  ├─ Radar (predictive insights)
  └─ ... 6 more operators
         ↓ (JWT + tenant_id)
  Railway Backend (APIs)
         ↓
  Supabase (RLS-filtered data)
         ↓
  ✨ Goal: SyncManager here (Phase 1) or Shadow GL (Phase 2+)
```

**Demo:** Live show Hermes calling backend, returning tenant-filtered GL entries.

### 3. SyncManager API Deep Dive (20 min)
**Presenter:** SyncManager Technical Lead

**Expected Topics:**
- REST API endpoints (authentication, rate limits, retry policy)
- Data format: DIAN XML vs. SyncManager JSON/CSV
- Rate limits & quotas (requests/sec, monthly cap)
- Error handling & fallback strategies
- Webhook support (real-time notifications on GL changes)
- SLA & uptime guarantees

**Contexia Questions to Ask:**
1. What is the minimum integration: can we poll GL balances once per hour?
2. How do you handle multi-moneda (COP, USD, EUR)?
3. What's your data retention policy? Can we archive GL snapshots?
4. If SyncManager API fails, how should we gracefully degrade?
5. Do you have a sandbox/staging environment for testing?

### 4. Data Format & Mapping (15 min)
**Presenter:** Backend Architect (with SyncManager input)

**Topics:**
- Existing data model: `shadow_ledger_entries` (date, account, debit, credit, currency, source)
- SyncManager format: TBD (clarify in this call)
- Mapping layer needed?
  - DIAN XML → SyncManager → Hermes GL
  - OR: DIAN XML → SyncManager (parallel)
- Multi-moneda handling: account-level currency tracking

**Decision Points:**
- [ ] SyncManager as single source of truth, or parallel with DIAN XML?
- [ ] Frequency: real-time polling, hourly batch, daily snapshot?

### 5. Integration Roadmap (15 min)
**Presenter:** Backend Architect

**Proposed Timeline:**
- **Phase 1 (MVP):** Jul 16-31
  - SyncManager API stubs in Hermes
  - Test connectivity + data mapping
  - Manual GL comparison (SyncManager vs. local GL)
  - Ready for Jul 25 call

- **Phase 2a (SyncManager Live):** Aug 1-31
  - SyncManager API → live GL polling
  - Agents read SyncManager GL entries
  - Agent Critic validates: debit == credit, balance checks

- **Phase 2b (Shadow GL Parallel):** Aug-Sep
  - Build Contexia's own GL deterministic logic
  - DIAN XML parser + Siigo poller
  - pgvector learning loop (agent suggestions)
  - Fallback: if SyncManager unavailable, use Shadow GL

- **Phase 3 (Migration / Deprecation):** Oct+
  - Decision: keep SyncManager or migrate to Shadow GL?
  - Criteria: cost, reliability, feature parity

**Question:** SyncManager roadmap — any planned API changes or deprecations we should know about?

### 6. Error Handling & Fallback Strategy (10 min)
**Topics:**
- What happens if SyncManager is down?
  - Hermes should not crash; degrade gracefully
  - Fallback to cached GL entries or local Shadow GL
- Retry policy: exponential backoff, circuit breaker?
- Alerting: when should Contexia notify SyncManager support?
- Data consistency: what if SyncManager and local GL diverge?

**Proposed:** Implement dual-write for 60 days (SyncManager + Shadow GL in parallel), then decide which is source of truth.

### 7. Compliance & Security (10 min)
**Topics:**
- Data residency: SyncManager servers location? (Contexia needs LATAM if possible)
- Audit trail: can we get logs of all GL modifications?
- PII handling: does SyncManager store employee info, invoice PDFs, etc.? If yes, how is it protected?
- GDPR/CCPA compliance (if serving international clients)?
- Encryption in transit + at rest?

### 8. Questions & Deep Dive (TBD)
**Presenter:** Open floor

**Expected Blockers:**
- Rate limits too restrictive
- API latency unacceptable (Hermes needs <2s response)
- Data format incompatible with DIAN GL
- Cost per request prohibitive

---

## Slide Deck (5 slides)

**Slide 1: Title**
- Contexia + Hermes Overview
- Multi-Tenant Financial Intelligence for SMEs
- Date, attendees, agenda link

**Slide 2: Hermes Architecture**
- Diagram: Workspace → Operators → Railway Backend → Supabase
- 9 agents (Pulso, Centinela, Radar, Auditoría, Taty, etc.)
- Multi-tenant isolation via JWT + RLS
- Data sovereignty: local-first (WSL sandbox)

**Slide 3: Phase 1 MVP Status**
- TenantContextMiddleware ✅ (deployed Jun 23)
- Supabase RLS policies ✅ (deployed Jun 28)
- Hermes operator → backend calls ✅ (Jun 30)
- **Ready for SyncManager integration** (Jul 3-15)

**Slide 4: Proposed Integration Timeline**
- Phase 1 (Jul): SyncManager API stubs + testing
- Phase 2a (Aug-Sep): Live polling + agent integration
- Phase 2b (Aug-Sep): Parallel Shadow GL building
- Phase 3 (Oct+): Decision point (keep SyncManager or migrate?)

**Slide 5: Key Questions**
1. API rate limits & latency?
2. Multi-moneda support?
3. Graceful degradation if SyncManager down?
4. Data residency & compliance?
5. Sandbox environment for testing?

---

## Demo Script (if live demo during call)

**Duration:** 5 minutes (show in Slide 3 section)

**Setup:** Hermes Workspace running locally (WSL), backend API available

**Flow:**
1. Show Hermes Workspace UI (http://localhost:3000)
2. "Let's trigger Pulso operator — it calls backend to fetch daily GL summary"
3. Click: Operators → Pulso → Execute
4. Show browser console / backend logs: `[Tenant: contexia-org-1] POST /api/v1/agents/pulso-diario/summary`
5. Show Hermes response: GL entries for Contexia only (tenant-isolated)
6. "This is where SyncManager fits: Pulso asks backend 'what's GL balance for Contexia?' → backend asks SyncManager → SyncManager returns → Agent validates with Critic → Hermes aggregates"

---

## Post-Call (Action Items)

### Within 24 hours:
- [ ] Share meeting notes to team + SyncManager
- [ ] Update `openspec/changes/hermes-syncmanager-integration/spec.md` with SyncManager API details
- [ ] Flag any blockers to product (Juan)

### Within 1 week (Jul 29-Aug 4):
- [ ] Implement SyncManager API stubs in Hermes
- [ ] Set up sandbox environment
- [ ] Begin Phase 2a implementation

### Next sync (Aug 8):
- [ ] Mid-phase checkpoint (SyncManager stubs working?)
- [ ] Blockers & mitigation
- [ ] Adjust timeline if needed

---

## Email Template (Send to SyncManager)

Subject: **Technical Integration Call — Hermes + SyncManager (Jul 25)**

---

Hi [SyncManager PM/Tech Lead],

We're excited to explore integrating SyncManager with Hermes, Contexia's financial intelligence platform. We handle DIAN compliance for SMEs in Colombia and are building a deterministic GL orchestration layer powered by AI agents.

**Proposed Call:**
- **Date:** Friday, July 25, 2026, 2:00 PM ET (adjust to your timezone)
- **Duration:** 90 minutes
- **Format:** Zoom / Teams (we'll send link)
- **Attendees (Contexia):** Juan (Product), Backend Architect, DevOps Lead

**Topics:**
1. Hermes multi-tenant architecture (local-first, data sovereign)
2. SyncManager API capabilities, rate limits, data formats
3. Integration roadmap: Phase 1 MVP (Jul-Aug), Phase 2 (Aug-Oct)
4. Fallback strategy: we're building a parallel Shadow GL as insurance
5. Timeline alignment & next steps

We've built a multi-tenant MVP with local sandboxing, JWT isolation, and Supabase RLS policies. We're ready to integrate SyncManager as our Phase 1 GL source, with a plan to build our own GL deterministically if needed.

**Prep:** We'll review your proposal beforehand and come with 5 key technical questions.

Can you confirm availability? If the time doesn't work, please suggest alternatives.

Looking forward to it!

Best regards,  
Juan  
Product Lead, Contexia

---

## Logistics Checklist

- [ ] Calendar invite sent (SyncManager team, Contexia attendees)
- [ ] Zoom/Teams link generated and shared
- [ ] Slide deck finalized (share 24h before call)
- [ ] Demo environment tested and ready
- [ ] Note-taker assigned
- [ ] Backup contact (if someone can't make it)
- [ ] Dial-in numbers + international access verified

