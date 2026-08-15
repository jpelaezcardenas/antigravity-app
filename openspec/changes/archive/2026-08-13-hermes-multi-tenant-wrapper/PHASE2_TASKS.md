# Phase 2: SyncManager Integration & Shadow GL — Tasks & Timeline

**Phase:** 2 (SyncManager Integration + Shadow GL Building)  
**Duration:** Jul 3-15, 2026 (13 days)  
**Status:** ⏳ **SCHEDULED (NOT STARTED)**  
**Milestone:** Jul 25 Technical Call + Live Demo  
**Owner:** Backend Dev + Hermes Admin

---

## 📋 Task Breakdown by Week

### Week 1: Jul 3-5 (Analysis & Design)

#### T1: SyncManager PDF Analysis (3 days)
**Owner:** Backend Dev  
**Deliverable:** Technical assessment report

- [ ] **T1.1** — Read SyncManager PDF (22 pages, 12MB)
  - [ ] Extract: API endpoints, data models, authentication
  - [ ] Extract: Rate limits, error handling, retry logic
  - [ ] Extract: Webhook structure, payload formats

- [ ] **T1.2** — Score against 37-question framework
  - [ ] API completeness (endpoints, methods, params)
  - [ ] Data model alignment (GL accounts, transactions, rollup)
  - [ ] Error handling (recovery, idempotency, timeouts)
  - [ ] Documentation quality (examples, edge cases)

- [ ] **T1.3** — Create technical assessment
  - [ ] Strengths: What SyncManager does well
  - [ ] Gaps: What we need to add/modify
  - [ ] Risks: Integration blockers, performance concerns
  - [ ] Timeline impact (on Phase 2 schedule)

**Acceptance:** Assessment doc + 37-question scorecard delivered

---

#### T2: Shadow GL Architecture Design (3 days)
**Owner:** Backend Dev + Database Lead  
**Deliverable:** Architecture specification document

- [ ] **T2.1** — Design data flow: DIAN → ERP → Shadow GL
  - [ ] Source: DIAN XML import (format, validation rules)
  - [ ] Source: ERP system (Siigo poller, sync frequency)
  - [ ] Transform: Reconciliation logic (matching rules)
  - [ ] Target: Shadow GL (pgvector indexing, query optimization)

- [ ] **T2.2** — Design Shadow GL schema
  - [ ] Table: gl_accounts (COD_CUENTA, NOMBRE, SALDO)
  - [ ] Table: gl_transactions (FECHA, CONCEPTO, DEBE, HABER, TENANT_ID)
  - [ ] Table: gl_reconciliations (TRANSACTION_ID, STATUS, DISCREPANCY)
  - [ ] Indexes: tenant_id, account_code, date_range (for fast queries)

- [ ] **T2.3** — Design Siigo poller
  - [ ] API endpoint: GET /api/v1/integrations/siigo/sync
  - [ ] Frequency: Hourly (configurable via env var)
  - [ ] Error handling: Exponential backoff, dead letter queue
  - [ ] Logging: All transactions + errors to audit table

- [ ] **T2.4** — Design DIAN XML parser
  - [ ] Input: XML files from DIAN upload endpoint
  - [ ] Validation: Schema, document structure, numeric ranges
  - [ ] Transform: XML → GL transaction objects
  - [ ] Output: Inserted into gl_transactions table

**Acceptance:** Architecture doc + schema diagrams + poller spec + parser spec delivered

---

### Week 2: Jul 6-12 (Implementation)

#### T3: Siigo API Integration (2 days)
**Owner:** Backend Dev  
**Deliverable:** Working endpoint + unit tests

- [ ] **T3.1** — Create SiigoPoll service
  - [ ] File: `services/siigo_poller.py`
  - [ ] Method: `poll_accounts()` → Fetch GL accounts from Siigo
  - [ ] Method: `poll_transactions(start_date, end_date)` → Fetch GL transactions
  - [ ] Error handling: Retry logic, exponential backoff
  - [ ] Logging: Info level for each poll, error level for failures

- [ ] **T3.2** — Create endpoint: POST /api/v1/integrations/siigo/sync
  - [ ] Trigger immediate sync (for manual testing)
  - [ ] Return: {status: "syncing", job_id: "...", eta: "..."}
  - [ ] Async: Run in background, don't block response
  - [ ] Rate limit: 1 sync per minute (prevent duplicate runs)

- [ ] **T3.3** — Create background job runner
  - [ ] File: `tasks/siigo_sync_task.py`
  - [ ] Celery task: poll_siigo_accounts, poll_siigo_transactions
  - [ ] Schedule: Hourly cron job (6am-6pm)
  - [ ] Tenant context: Run per-tenant (for multi-tenant isolation)

- [ ] **T3.4** — Unit tests
  - [ ] Test: Mock Siigo API, verify response parsing
  - [ ] Test: Verify transaction insertion to Shadow GL
  - [ ] Test: Verify tenant isolation (Context A ≠ Context B data)
  - [ ] Test: Verify error handling (timeout, 401, malformed response)
  - [ ] Tests: ≥4 tests, all passing

**Acceptance:** Endpoint working, unit tests passing, logs verified

---

#### T4: DIAN XML Parser (2 days)
**Owner:** Backend Dev  
**Deliverable:** Working parser + endpoint + tests

- [ ] **T4.1** — Create DIAN XML parser
  - [ ] File: `services/dian_xml_parser.py`
  - [ ] Class: `DIANXMLParser`
  - [ ] Method: `parse(xml_content: str) → List[GLTransaction]`
  - [ ] Validation: Schema check, numeric range validation
  - [ ] Error handling: Detailed error messages for invalid XML

- [ ] **T4.2** — Create endpoint: POST /api/v1/integrations/dian/upload
  - [ ] Accept: Multipart form upload (XML file)
  - [ ] Validate: File size (<50MB), format (.xml)
  - [ ] Parse: Extract GL transactions
  - [ ] Store: Insert into gl_transactions table
  - [ ] Response: {status: "success", rows_inserted: N, errors: [...]}
  - [ ] Error handling: 400 for parse errors, 413 for oversized file

- [ ] **T4.3** — Integration with ShadowGL
  - [ ] After parsing: Run reconciliation logic
  - [ ] Match: DIAN transactions ↔ Siigo transactions
  - [ ] Flag discrepancies: Insert into gl_reconciliations table
  - [ ] Audit: Log all uploads to auditoria_reports

- [ ] **T4.4** — Unit tests
  - [ ] Test: Valid XML → correct transaction parsing
  - [ ] Test: Invalid XML → detailed error message
  - [ ] Test: Oversized file → 413 response
  - [ ] Test: Reconciliation logic → matches correct transactions
  - [ ] Tests: ≥4 tests, all passing

**Acceptance:** Parser working, endpoint functional, unit tests passing

---

#### T5: Shadow GL Database Schema (1 day)
**Owner:** Database Lead  
**Deliverable:** Migration scripts + indexes

- [ ] **T5.1** — Create migration: Add Shadow GL tables
  - [ ] File: `apps/backend/migrations/0004_create_shadow_gl_schema.sql`
  - [ ] Tables: gl_accounts, gl_transactions, gl_reconciliations
  - [ ] Columns: Include tenant_id for all tables (RLS enforcement)
  - [ ] Indexes: tenant_id, account_code, date_range

- [ ] **T5.2** — Apply RLS policies to Shadow GL tables
  - [ ] File: `apps/backend/migrations/0005_enable_shadow_gl_rls.sql`
  - [ ] Policies: 3 tenant isolation policies (one per table)
  - [ ] Same pattern as Phase 1: tenant_id = JWT.tenant_id OR default

- [ ] **T5.3** — Create pgvector extension + embeddings table
  - [ ] File: `apps/backend/migrations/0006_enable_pgvector.sql`
  - [ ] Extension: CREATE EXTENSION IF NOT EXISTS vector
  - [ ] Table: gl_embeddings (transaction_id, embedding, metadata)
  - [ ] Index: IVFFLAT for similarity search

**Acceptance:** Migrations applied, tables created, indexes verified

---

#### T6: Integration Tests (1 day)
**Owner:** QA + Backend  
**Deliverable:** E2E test suite for Phase 2 flow

- [ ] **T6.1** — Test: Siigo sync → Shadow GL
  - [ ] Mock Siigo API
  - [ ] Trigger sync via endpoint
  - [ ] Verify transactions inserted
  - [ ] Verify tenant isolation

- [ ] **T6.2** — Test: DIAN upload → Reconciliation
  - [ ] Upload valid XML
  - [ ] Verify parsing
  - [ ] Verify reconciliation logic
  - [ ] Verify discrepancies flagged

- [ ] **T6.3** — Test: Multi-tenant isolation
  - [ ] Tenant A uploads DIAN
  - [ ] Tenant B uploads DIAN
  - [ ] Verify no cross-tenant data visibility
  - [ ] Verify RLS blocks unauthorized access

- [ ] **T6.4** — Performance tests
  - [ ] Parse 1000 DIAN transactions → <2s
  - [ ] Reconcile 1000 transactions → <5s
  - [ ] Query Shadow GL (100k rows) → <100ms

**Acceptance:** ≥6 integration tests passing, performance within SLA

---

### Week 3: Jul 13-15 (Verification & Demo Prep)

#### T7: Operators Registration (1 day)
**Owner:** Hermes Admin + Backend  
**Deliverable:** All 9 operators wired to Shadow GL tools

- [ ] **T7.1** — Register ShadowGL operator
  - [ ] Name: "Shadow GL" (emoji: 📊)
  - [ ] System prompt: "You are a financial auditor analyzing GL discrepancies"
  - [ ] Tools: 
    - [ ] `query_shadow_gl(account_code, date_range)` → Returns transactions
    - [ ] `get_discrepancies(tenant_id)` → Returns reconciliation issues
    - [ ] `generate_audit_report(period)` → Shadow GL summary

- [ ] **T7.2** — Register Siigo sync operator
  - [ ] Name: "Siigo Sync" (emoji: 🔄)
  - [ ] System prompt: "Trigger and monitor ERP GL synchronization"
  - [ ] Tools:
    - [ ] `trigger_siigo_sync()` → Manual sync
    - [ ] `get_sync_status()` → Last sync time, next scheduled

- [ ] **T7.3** — Verify all 9 operators can call backend tools
  - [ ] Pulso → /api/v1/agents/pulso-diario/summary ✅
  - [ ] Centinela → /api/v1/agents/centinela/generate-draft ✅
  - [ ] Radar → /api/v1/agents/radar/analyze
  - [ ] Auditoría → /api/v1/agents/auditoria-sombra/report
  - [ ] ShadowGL → /api/v1/integrations/shadow-gl/* (NEW)
  - [ ] Siigo Sync → /api/v1/integrations/siigo/* (NEW)
  - [ ] Critic → /api/v1/agents/critic/validate
  - [ ] Maestro → /api/v1/hermes/swarm/invoke
  - [ ] Approval Queue → /api/v1/approval-queue/enqueue ✅

- [ ] **T7.4** — Test Maestro orchestrating all 9 operators
  - [ ] Maestro decomposes complex task
  - [ ] Assigns subtasks to operators
  - [ ] Operators call respective backend tools
  - [ ] Results aggregated + returned to PWA

**Acceptance:** All 9 operators registered, E2E flow working

---

#### T8: Technical Call Preparation (1 day)
**Owner:** Product + Backend  
**Deliverable:** Call deck + live demo ready

- [ ] **T8.1** — Create call deck (5-10 slides)
  - [ ] Slide 1: Phase 1 recap (what was delivered)
  - [ ] Slide 2: Architecture diagram (Hermes → Backend → Supabase → Shadow GL)
  - [ ] Slide 3: SyncManager integration (Siigo + DIAN)
  - [ ] Slide 4: Multi-tenant isolation (RLS + JWT)
  - [ ] Slide 5: Demo outline (what we'll show live)
  - [ ] Slide 6: Timeline + next steps (Phase 3)

- [ ] **T8.2** — Prepare live demo (10-15 min)
  - [ ] Demo 1: Trigger Siigo sync → See GL accounts updated
  - [ ] Demo 2: Upload DIAN XML → Parse + reconcile
  - [ ] Demo 3: Hermes operator queries Shadow GL
  - [ ] Demo 4: Multi-tenant isolation (different tenants see different data)
  - [ ] Demo 5: Maestro orchestrating operators

- [ ] **T8.3** — Prepare Q&A talking points
  - [ ] How is data isolated? (RLS + tenant_id)
  - [ ] What about existing GL data? (Backfill + mapping)
  - [ ] How often does Siigo sync? (Hourly, configurable)
  - [ ] What if DIAN ≠ ERP? (Flagged in reconciliations)

- [ ] **T8.4** — Verify staging/production is ready
  - [ ] All endpoints responding
  - [ ] Health check: 200 OK
  - [ ] Logs: Clean (no errors)
  - [ ] Database: Responsive

**Acceptance:** Call deck complete, demo scripts tested, talking points ready

---

#### T9: Documentation & Handoff (1 day)
**Owner:** Backend Dev + Tech Writer  
**Deliverable:** Phase 2 documentation complete

- [ ] **T9.1** — Update HERMES_CONFIG.md
  - [ ] Add: SyncManager endpoints + env vars
  - [ ] Add: Shadow GL schema diagram
  - [ ] Add: Troubleshooting for sync failures

- [ ] **T9.2** — Create SHADOWGL_GUIDE.md
  - [ ] Overview: What is Shadow GL, why it matters
  - [ ] Schema: Tables, columns, indexes
  - [ ] Queries: Common patterns (account balance, reconcile)
  - [ ] Troubleshooting: Sync failures, discrepancies

- [ ] **T9.3** — Create SYNCMANAGER_INTEGRATION.md
  - [ ] Overview: Siigo + DIAN sources
  - [ ] Endpoints: /siigo/sync, /dian/upload
  - [ ] Error handling: Retry logic, dead letters
  - [ ] Monitoring: Logs, alerts

- [ ] **T9.4** — Update README.md
  - [ ] Add link to Phase 2 docs
  - [ ] Update architecture diagram (include Shadow GL)
  - [ ] Add: "Multi-tenant Hermes + SyncManager integration"

**Acceptance:** All docs updated, links verified, examples tested

---

## 📅 Timeline Summary

```
Jul 3-5 (Week 1):    T1, T2 (Analysis & Design)
Jul 6-12 (Week 2):   T3, T4, T5, T6 (Implementation & Integration)
Jul 13-15 (Week 3):  T7, T8, T9 (Operators & Demo Prep)
Jul 25 (Thu):        Technical Call + Live Demo (CUSTOMER-FACING)
```

---

## 🎯 Phase 2 Success Criteria

| Criterion | Target | How to Verify |
|-----------|--------|---------------|
| Siigo Poller | Working | POST /api/v1/integrations/siigo/sync → 200 |
| DIAN Parser | Working | POST /api/v1/integrations/dian/upload → 200 |
| Shadow GL | Live | Query gl_transactions → rows returned |
| Multi-tenant | Verified | Tenant A ≠ Tenant B data (RLS) |
| Operators | Registered | hermes list agents → 9 operators |
| E2E Test | Passing | pytest tests/e2e/test_phase2_syncmanager.py → all pass |
| Demo Ready | Ready | Live demo executes flawlessly |
| Docs | Complete | All Phase 2 docs linked + examples work |

---

## 🚀 Handoff to Phase 3

**Phase 2 Complete:** Jul 15, 2026  
**Phase 3 Begins:** Jul 16, 2026 (if approved in call)  
**Phase 3 Duration:** Jul 16-25 (Hardening + Security)

Phase 2 tasks are BLOCKED until Phase 1 is archived. Once archived, Phase 2 tasks become active.

---

**Created:** 2026-06-23  
**Status:** ⏳ **SCHEDULED (AWAITING PHASE 1 ARCHIVE)**  
**Next Action:** Archive Phase 1 → Activate Phase 2 tasks
