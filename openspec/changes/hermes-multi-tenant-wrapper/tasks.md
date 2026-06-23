# Tasks: Hermes Multi-Tenant Wrapper (MVP → Production)

**Timeline:** 32 days (Jun 23 → Jul 25, 2026)  
**Scope:** Non-invasive multi-tenant isolation (JWT middleware + RLS policies + Hermes integration)  
**Phases:** 1A (middleware) → 1B (schema) → 1C (Hermes JWT) → 1D (E2E) → 2 (SyncManager prep) → 3 (hardening) → 6 (deploy)

---

## Grouping & Dependencies

```
Phase 1 (MVP):     Jun 23-30   T1-T20  (Core infrastructure)
  1A: Middleware   Jun 23-25   T1-T4   (TenantContextMiddleware)
  1B: Schema       Jun 26-28   T5-T9   (tenant_id columns + RLS)
  1C: Hermes JWT   Jun 29-30   T10-T12 (integrate with Workspace)
  1D: E2E          Jul 1-2     T13-T15 (testing + documentation)

Phase 2 (Sync):    Jul 3-15    T16-T25 (SyncManager API + Shadow GL planning)

Phase 3 (Harden):  Jul 16-25   T26-T35 (sandbox, tunnel security, token rotation)

Stage 6 (Deploy):  Jul 26+     T36-T40 (E2E verification + Stage 11 production deploy)
```

---

## Phase 1A: Core Middleware (3 days, Jun 23-25)

### T1: Create TenantContextMiddleware Class

**Objective:** Build non-invasive middleware that extracts tenant_id from JWT and injects into request context.

**Deliverable:** `apps/backend/core/tenant_middleware.py`

**Requirements:**
- Extract `tenant_id` from JWT bearer token
- Inject into `request.state.tenant_id`
- Log tenant_id for observability
- Handle missing/invalid tokens gracefully
- Zero changes to existing endpoints

**Steps:**
1. Create file: `apps/backend/core/tenant_middleware.py`
2. Implement `TenantContextMiddleware` class:
   ```python
   from fastapi import Request
   from core.security import verify_token
   import logging
   
   logger = logging.getLogger("tenant-middleware")
   
   class TenantContextMiddleware:
       async def __call__(self, request: Request, call_next):
           tenant_id = None
           user_id = None
           
           # Extract JWT from Authorization header
           auth_header = request.headers.get("Authorization", "")
           if auth_header.startswith("Bearer "):
               token = auth_header[7:]
               payload = verify_token(token)
               if payload:
                   tenant_id = payload.get("tenant_id")
                   user_id = payload.get("sub")
           
           # Inject into request context
           request.state.tenant_id = tenant_id or "default-tenant"
           request.state.user_id = user_id
           
           logger.debug(f"[Tenant: {request.state.tenant_id}] {request.method} {request.url.path}")
           
           response = await call_next(request)
           return response
   ```
3. Verify syntax: `python -m py_compile apps/backend/core/tenant_middleware.py`
4. Add type hints: All parameters fully typed
5. No print statements; logging only

**Acceptance:** File created, syntax valid, imports pass, no errors on `python -c "import core.tenant_middleware"`.

**Owner:** Backend Dev  
**Effort:** 1.5 hours  
**Deadline:** 2026-06-23  
**Status:** ⏳ Ready

---

### T2: Integrate TenantContextMiddleware in main.py

**Objective:** Register middleware in FastAPI app without disrupting existing middleware stack.

**Deliverable:** Updated `apps/backend/main.py`

**Steps:**
1. Import middleware:
   ```python
   from core.tenant_middleware import TenantContextMiddleware
   ```
2. Add middleware to app (AFTER other security middleware, BEFORE routers):
   ```python
   # In main.py, after apply_middleware(app):
   app.add_middleware(TenantContextMiddleware)
   ```
3. Verify startup:
   ```bash
   python apps/backend/main.py
   # Should start without errors; log: "[STARTUP] TenantContextMiddleware loaded"
   ```
4. Test that existing endpoints still work:
   ```bash
   curl http://localhost:8080/api/v1/health
   # Should return 200 (no auth required for health check)
   ```

**Acceptance:** main.py compiles, app starts, health endpoint responds 200.

**Owner:** Backend Dev  
**Effort:** 30 min  
**Deadline:** 2026-06-23  
**Status:** ⏳ Ready

---

### T3: Add MULTI_TENANT_ENABLED Config Flag

**Objective:** Feature gate multi-tenant mode for backwards compatibility.

**Deliverable:** Updated `apps/backend/config.py`

**Steps:**
1. Add to Settings class:
   ```python
   MULTI_TENANT_ENABLED: bool = True
   JWT_TENANT_CLAIM: str = "tenant_id"
   KNOWN_TENANTS: str = "contexia-org-1,client-xyz"
   ```
2. Add to `.env.example`:
   ```
   MULTI_TENANT_ENABLED=True
   KNOWN_TENANTS=contexia-org-1,client-xyz
   ```
3. Update docstrings:
   ```python
   MULTI_TENANT_ENABLED: bool = True  # Enable tenant_id extraction from JWT
   ```
4. Verify config loads:
   ```python
   from config import settings
   print(settings.MULTI_TENANT_ENABLED)  # True
   ```

**Acceptance:** config.py compiles, settings.MULTI_TENANT_ENABLED exists and is True by default.

**Owner:** Backend Dev  
**Effort:** 30 min  
**Deadline:** 2026-06-23  
**Status:** ⏳ Ready

---

### T4: Unit Test for TenantContextMiddleware

**Objective:** Verify middleware correctly extracts and injects tenant_id.

**Deliverable:** `tests/backend/core/test_tenant_middleware.py`

**Steps:**
1. Create test file with pytest fixtures:
   ```python
   import pytest
   from fastapi import FastAPI
   from fastapi.testclient import TestClient
   from core.tenant_middleware import TenantContextMiddleware
   from core.security import create_access_token
   
   @pytest.fixture
   def app_with_middleware():
       app = FastAPI()
       app.add_middleware(TenantContextMiddleware)
       
       @app.get("/test")
       async def test_endpoint(request):
           return {"tenant_id": request.state.tenant_id}
       
       return app
   
   def test_middleware_extracts_tenant_id():
       app = app_with_middleware()
       client = TestClient(app)
       
       # Create token with tenant_id
       token = create_access_token({"sub": "user-1", "tenant_id": "org-1"})
       response = client.get("/test", headers={"Authorization": f"Bearer {token}"})
       
       assert response.status_code == 200
       assert response.json()["tenant_id"] == "org-1"
   
   def test_middleware_defaults_to_default_tenant():
       app = app_with_middleware()
       client = TestClient(app)
       
       # No auth header
       response = client.get("/test")
       assert response.json()["tenant_id"] == "default-tenant"
   ```
2. Run tests:
   ```bash
   pytest tests/backend/core/test_tenant_middleware.py -v
   # target: 4 passed
   ```

**Acceptance:** All 4 tests passing, >90% code coverage for middleware.

**Owner:** Backend QA  
**Effort:** 1 hour  
**Deadline:** 2026-06-24  
**Status:** ⏳ Ready

---

## Phase 1B: Database Schema & RLS (3 days, Jun 26-28)

### T5: Create Migration — Add tenant_id Columns

**Objective:** Add tenant_id column to all org-scoped tables, non-breaking.

**Deliverable:** `apps/backend/migrations/0XX_add_tenant_id_columns.sql`

**Steps:**
1. Create migration file:
   ```sql
   -- Migration: Add tenant_id columns to all org-scoped tables
   -- Date: 2026-06-26
   -- Non-breaking: Uses DEFAULT, no rewrite required
   
   ALTER TABLE public.pulso_results ADD COLUMN tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000000';
   ALTER TABLE public.centinela_alerts ADD COLUMN tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000000';
   ALTER TABLE public.approval_queue ADD COLUMN tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000000';
   ALTER TABLE public.radar_insights ADD COLUMN tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000000';
   ALTER TABLE public.auditoria_reports ADD COLUMN tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000000';
   
   -- Create indexes for performance
   CREATE INDEX idx_pulso_results_tenant_id ON public.pulso_results(tenant_id);
   CREATE INDEX idx_centinela_alerts_tenant_id ON public.centinela_alerts(tenant_id);
   CREATE INDEX idx_approval_queue_tenant_id ON public.approval_queue(tenant_id);
   CREATE INDEX idx_radar_insights_tenant_id ON public.radar_insights(tenant_id);
   CREATE INDEX idx_auditoria_reports_tenant_id ON public.auditoria_reports(tenant_id);
   ```
2. Test locally:
   ```bash
   supabase db reset  # or manual test on staging
   # Verify columns added:
   SELECT column_name FROM information_schema.columns WHERE table_name = 'pulso_results' AND column_name = 'tenant_id';
   # Should return: tenant_id
   ```

**Acceptance:** Migration file created, SQL syntax valid, columns added on test database.

**Owner:** Database Dev  
**Effort:** 1 hour  
**Deadline:** 2026-06-26  
**Status:** ⏳ Ready

---

### T6: Backfill Existing Data with Default Tenant

**Objective:** Set all existing rows to the default tenant (Contexia) before RLS policies are enforced.

**Deliverable:** Backfill SQL script, executed on production

**Prerequisites:** T5 (tenant_id columns exist)

**Steps:**
1. Create backfill script: `apps/backend/migrations/backfill_tenant_id.sql`
   ```sql
   -- Backfill: Set all existing rows to default tenant
   -- Must run BEFORE RLS policies are enforced (T7)
   
   UPDATE public.pulso_results 
   SET tenant_id = 'contexia-org-1'::uuid 
   WHERE tenant_id = '00000000-0000-0000-0000-000000000000';
   
   UPDATE public.centinela_alerts 
   SET tenant_id = 'contexia-org-1'::uuid 
   WHERE tenant_id = '00000000-0000-0000-0000-000000000000';
   
   UPDATE public.approval_queue 
   SET tenant_id = 'contexia-org-1'::uuid 
   WHERE tenant_id = '00000000-0000-0000-0000-000000000000';
   
   UPDATE public.radar_insights 
   SET tenant_id = 'contexia-org-1'::uuid 
   WHERE tenant_id = '00000000-0000-0000-0000-000000000000';
   
   UPDATE public.auditoria_reports 
   SET tenant_id = 'contexia-org-1'::uuid 
   WHERE tenant_id = '00000000-0000-0000-0000-000000000000';
   ```
2. Test on staging database:
   ```bash
   # Execute backfill script
   psql $STAGING_DATABASE < apps/backend/migrations/backfill_tenant_id.sql
   
   # Verify:
   SELECT COUNT(*) FROM pulso_results WHERE tenant_id = 'contexia-org-1'::uuid;
   # Should return: (actual row count)
   ```
3. Document in change log: "Backfill completed, all existing data assigned to contexia-org-1"

**Acceptance:** Backfill script created, tested on staging, all rows updated, zero failures.

**Owner:** Database Dev  
**Effort:** 1 hour  
**Deadline:** 2026-06-27  
**Status:** ⏳ Ready

---

### T7: Create Migration — Enable RLS Policies

**Objective:** Enable row-level security and create isolation policies for tenant_id.

**Deliverable:** `apps/backend/migrations/0XX_enable_rls_policies.sql`

**Prerequisites:** T6 (backfill complete)

**Steps:**
1. Create RLS migration:
   ```sql
   -- Migration: Enable RLS and create tenant isolation policies
   -- Date: 2026-06-27
   -- Prerequisite: All rows have non-null tenant_id (from backfill)
   
   -- Enable RLS on all org-scoped tables
   ALTER TABLE public.pulso_results ENABLE ROW LEVEL SECURITY;
   ALTER TABLE public.centinela_alerts ENABLE ROW LEVEL SECURITY;
   ALTER TABLE public.approval_queue ENABLE ROW LEVEL SECURITY;
   ALTER TABLE public.radar_insights ENABLE ROW LEVEL SECURITY;
   ALTER TABLE public.auditoria_reports ENABLE ROW LEVEL SECURITY;
   
   -- Create isolation policy: users can only see their tenant's data
   CREATE POLICY pulso_results_tenant_isolation ON public.pulso_results
     FOR ALL USING (tenant_id = COALESCE(auth.jwt()->>'tenant_id', 'contexia-org-1'::uuid));
   
   CREATE POLICY centinela_alerts_tenant_isolation ON public.centinela_alerts
     FOR ALL USING (tenant_id = COALESCE(auth.jwt()->>'tenant_id', 'contexia-org-1'::uuid));
   
   CREATE POLICY approval_queue_tenant_isolation ON public.approval_queue
     FOR ALL USING (tenant_id = COALESCE(auth.jwt()->>'tenant_id', 'contexia-org-1'::uuid));
   
   CREATE POLICY radar_insights_tenant_isolation ON public.radar_insights
     FOR ALL USING (tenant_id = COALESCE(auth.jwt()->>'tenant_id', 'contexia-org-1'::uuid));
   
   CREATE POLICY auditoria_reports_tenant_isolation ON public.auditoria_reports
     FOR ALL USING (tenant_id = COALESCE(auth.jwt()->>'tenant_id', 'contexia-org-1'::uuid));
   ```
2. Test on staging:
   ```bash
   # Apply migration
   psql $STAGING_DATABASE < apps/backend/migrations/0XX_enable_rls_policies.sql
   
   # Verify RLS is enabled
   SELECT tablename, rowsecurity FROM pg_tables 
   WHERE tablename IN ('pulso_results', 'centinela_alerts', 'approval_queue');
   # Should return: rowsecurity = true for all tables
   ```

**Acceptance:** RLS migration created, policies enabled on staging, table scan confirms RLS active.

**Owner:** Database Dev  
**Effort:** 1 hour  
**Deadline:** 2026-06-27  
**Status:** ⏳ Ready

---

### T8: Test RLS Policies (Multi-Tenant Isolation)

**Objective:** Verify RLS policies correctly isolate data by tenant_id.

**Deliverable:** Test script + results report

**Prerequisites:** T7 (RLS policies enabled)

**Steps:**
1. Create test data (two tenants):
   ```sql
   -- Insert test data for two different tenants
   INSERT INTO public.pulso_results (tenant_id, company_id, metrics)
   VALUES 
     ('contexia-org-1'::uuid, 'contexia-001', '{...}'),
     ('client-xyz'::uuid, 'client-xyz-001', '{...}');
   ```
2. Test isolation:
   ```bash
   # Simulate User A (tenant_id = contexia-org-1)
   # Query: SELECT * FROM pulso_results
   # Expected: Only rows with tenant_id = contexia-org-1
   
   # Simulate User B (tenant_id = client-xyz)
   # Query: SELECT * FROM pulso_results
   # Expected: Only rows with tenant_id = client-xyz
   ```
3. Verify with curl test:
   ```bash
   # Token for contexia
   TOKEN_CONTEXIA=$(curl -X POST ... | jq .access_token)
   curl -H "Authorization: Bearer $TOKEN_CONTEXIA" \
     https://staging-api.contexia.online/api/v1/pulso/results
   # Should return: Only contexia data
   
   # Token for client-xyz
   TOKEN_CLIENT=$(curl -X POST ... | jq .access_token)
   curl -H "Authorization: Bearer $TOKEN_CLIENT" \
     https://staging-api.contexia.online/api/v1/pulso/results
   # Should return: Only client-xyz data (or 403 if no access)
   ```

**Acceptance:** RLS policies correctly filter data by tenant_id; no data leaks between tenants.

**Owner:** Backend QA  
**Effort:** 2 hours  
**Deadline:** 2026-06-28  
**Status:** ⏳ Ready

---

### T9: Deploy Schema Changes to Staging

**Objective:** Apply T5-T7 migrations to staging database; verify no errors.

**Deliverable:** Staging database updated with tenant_id + RLS

**Prerequisites:** T5, T6, T7, T8 (all migrations created and tested locally)

**Steps:**
1. Push migrations to Git:
   ```bash
   git add apps/backend/migrations/0XX_add_tenant_id_columns.sql
   git add apps/backend/migrations/backfill_tenant_id.sql
   git add apps/backend/migrations/0XX_enable_rls_policies.sql
   git commit -m "feat: add tenant_id columns and RLS policies"
   ```
2. Deploy to staging (Supabase CLI):
   ```bash
   supabase db push --linked  # Or manual execution on staging Supabase project
   ```
3. Verify in Supabase dashboard:
   - Check tables: pulso_results, centinela_alerts, etc.
   - Verify tenant_id column exists
   - Verify RLS is enabled: Look in "Authentication" → "Policies"
4. Test staging endpoint:
   ```bash
   curl https://staging-api.contexia.online/api/v1/agents/pulso-diario/summary \
     -H "Authorization: Bearer <STAGING_JWT>"
   # Should return 200 (queries still work, RLS filtering silently applied)
   ```

**Acceptance:** Staging database updated, RLS policies active, staging endpoint returns 200.

**Owner:** DevOps / Backend Dev  
**Effort:** 1 hour  
**Deadline:** 2026-06-28  
**Status:** ⏳ Ready

---

## Phase 1C: Hermes JWT Integration (2 days, Jun 29-30)

### T10: Update JWT Creation Logic (Add tenant_id)

**Objective:** When issuing JWTs, include tenant_id in the token payload.

**Deliverable:** Updated `apps/backend/core/security.py`

**Steps:**
1. Update `create_access_token()` function:
   ```python
   def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
       to_encode = data.copy()
       
       # Ensure tenant_id is present (fallback to default if not provided)
       if "tenant_id" not in to_encode:
           to_encode["tenant_id"] = "contexia-org-1"
       
       # Set expiration
       if expires_delta:
           expire = datetime.now(timezone.utc) + expires_delta
       else:
           expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
       
       to_encode.update({"exp": expire})
       encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
       return encoded_jwt
   ```
2. Update all login endpoints to include tenant_id:
   - Find: `@app.post("/api/v1/auth/login")`
   - After user auth succeeds, fetch their tenant_id from database
   - Include in JWT: `create_access_token({"sub": user.id, "email": user.email, "tenant_id": user.tenant_id})`
3. Test locally:
   ```python
   token = create_access_token({"sub": "user-1", "tenant_id": "contexia-org-1"})
   payload = verify_token(token)
   assert payload["tenant_id"] == "contexia-org-1"
   ```

**Acceptance:** Security.py compiles, `create_access_token()` includes tenant_id, token decoding returns tenant_id field.

**Owner:** Backend Dev  
**Effort:** 1.5 hours  
**Deadline:** 2026-06-29  
**Status:** ⏳ Ready

---

### T11: Configure Hermes Workspace with tenant_id (ENV)

**Objective:** Set Hermes environment variables so all operator calls carry the tenant context.

**Deliverable:** Updated Hermes `.env` file (local WSL distro)

**Steps:**
1. Create/update `.env` in Hermes gateway directory:
   ```bash
   # Hermes environment (on local WSL)
   HERMES_TENANT_ID=contexia-org-1
   HERMES_ORG_NAME="Contexia S.A.S."
   HERMES_API_URL=http://127.0.0.1:8080/api/v1
   HERMES_JWT_SECRET=$(bw get item railway | jq -r '.login.password')  # Or read from Bitwarden
   HERMES_WORKSPACE_PORT=3000
   HERMES_GATEWAY_PORT=8642
   HERMES_AUTO_DETECT=false
   ```
2. Verify Hermes reads env vars:
   ```bash
   source .env
   echo $HERMES_TENANT_ID  # Should print: contexia-org-1
   ```
3. Update Hermes operator registrations to use tenant_id in tool calls:
   - Each operator tool endpoint includes: `Authorization: Bearer <JWT with tenant_id>`
   - Example: Pulso operator calls `POST /api/v1/agents/pulso-diario/summary` with auth header

**Acceptance:** Hermes .env file exists, HERMES_TENANT_ID set to "contexia-org-1", readable by Workspace.

**Owner:** DevOps / Hermes Admin  
**Effort:** 1 hour  
**Deadline:** 2026-06-29  
**Status:** ⏳ Ready

---

### T12: Test Hermes Operator → Backend Call with Tenant Context

**Objective:** Verify a Hermes operator (e.g., Pulso) calls the backend with tenant_id in JWT.

**Deliverable:** Test log showing successful operator call with tenant isolation

**Prerequisites:** T10 (JWT includes tenant_id), T11 (Hermes env configured)

**Steps:**
1. Start Hermes Workspace locally (WSL):
   ```bash
   hermes -p contexia gateway run  # Starts :8642
   hermes -p contexia workspace run  # Starts :3000 (separate terminal)
   ```
2. Via Hermes UI, trigger Pulso operator:
   - Go to Workspace UI (http://localhost:3000 or WSL IP:3000)
   - Create mission: "Pulso: daily summary"
   - Operators → Pulso → Execute
3. Monitor backend logs (Railway or local dev server):
   ```bash
   # Should see log line:
   # [Tenant: contexia-org-1] POST /api/v1/agents/pulso-diario/summary
   ```
4. Verify response:
   - Pulso returns tenant-filtered data (only Contexia's pulso_results rows)
   - No data from other orgs (even if they existed)

**Acceptance:** Hermes operator calls backend, middleware logs tenant_id, RLS filters results correctly.

**Owner:** Backend Dev + Hermes Admin  
**Effort:** 1.5 hours  
**Deadline:** 2026-06-30  
**Status:** ⏳ Ready

---

## Phase 1D: E2E Testing & Documentation (2 days, Jul 1-2)

### T13: End-to-End Test: Multi-Tenant Request Flow

**Objective:** Complete E2E test: Hermes operator → middleware → RLS → Supabase → response (correctly filtered).

**Deliverable:** Test script + test report

**Prerequisites:** T12 (Hermes integration works)

**Steps:**
1. Set up test scenario:
   - Insert test data for two tenants (Contexia + Client XYZ)
   - Create JWTs for each tenant with correct tenant_id
2. Run E2E tests:
   ```bash
   pytest tests/e2e/test_multi_tenant_flow.py -v
   ```
3. Test cases:
   - **Test 1:** Hermes (Contexia) queries Pulso → gets only Contexia data
   - **Test 2:** Manual curl with Client XYZ JWT → gets only Client XYZ data (or 403)
   - **Test 3:** Same endpoint, different tenants → different results
   - **Test 4:** Missing tenant_id in JWT → defaults to "contexia-org-1"
4. Expected output:
   ```
   test_contexia_sees_only_contexia_data PASSED
   test_client_xyz_sees_only_client_xyz_data PASSED
   test_no_data_leak_between_tenants PASSED
   test_missing_tenant_id_uses_default PASSED
   
   4 passed in 2.34s
   ```

**Acceptance:** All 4 E2E tests passing, zero data leaks, default fallback works.

**Owner:** Backend QA  
**Effort:** 2 hours  
**Deadline:** 2026-07-01  
**Status:** ⏳ Ready

---

### T14: Create Architecture Documentation

**Objective:** Document multi-tenant architecture, JWT structure, RLS policies, Hermes integration.

**Deliverable:** `ai-specs/architecture/hermes-multi-tenant-wrapper-spec.md` (ALREADY CREATED)

**Update steps:**
1. Verify file exists and has all sections (already created in this session)
2. Add implementation links:
   - T1-T4 → Phase 1A section
   - T5-T9 → Phase 1B section
   - T10-T12 → Phase 1C section
   - T13-T15 → Phase 1D section
3. Add "Phase 1 MVP Checklist" section:
   ```markdown
   - [ ] TenantContextMiddleware deployed
   - [ ] tenant_id columns added to all tables
   - [ ] RLS policies enabled and tested
   - [ ] Hermes operators call backend with tenant context
   - [ ] E2E tests passing
   - [ ] Architecture doc complete
   ```

**Acceptance:** Documentation file exists, complete, with all phases documented.

**Owner:** Tech Lead / Architect  
**Effort:** 1 hour  
**Deadline:** 2026-07-01  
**Status:** ⏳ Ready

---

### T15: MVP Readiness Check & Approval Gate

**Objective:** Verify Phase 1 complete; ready for Phase 2 (SyncManager integration).

**Deliverable:** MVP sign-off checklist

**Prerequisites:** T1-T14 complete

**Steps:**
1. **Code Review:**
   - T1-T4 (middleware) reviewed and merged
   - T5-T9 (schema) reviewed and merged
   - T10-T12 (Hermes JWT) reviewed and merged
2. **Testing:**
   - T13 (E2E tests) all passing
   - T8 (RLS tests) all passing
   - Zero failures in production-like staging environment
3. **Documentation:**
   - T14 (architecture doc) complete and accurate
   - T11 (Hermes .env) documented
4. **Sign-off:**
   - Juan (Product): "MVP ready for SyncManager integration call"
   - Backend Lead: "Code quality green, zero regressions"
   - DevOps: "Staging deployment stable"
5. **Gate Decision:**
   - **GO:** Proceed to Phase 2 (T16+)
   - **HOLD:** Resolve blockers (list them), re-check
   - **NO-GO:** Descope Phase 2, extend Phase 1

**Acceptance:** MVP checklist 100% complete, all stakeholders sign off.

**Owner:** Product + Engineering  
**Effort:** 1 hour  
**Deadline:** 2026-07-02  
**Status:** ⏳ Ready

---

## Phase 2: SyncManager Integration Planning (13 days, Jul 3-15)

**Objective:** Plan and design Shadow General Ledger + SyncManager API integration.  
**Gate:** Depends on SyncManager technical call (Jul 25).

### T16: Read & Score SyncManager PDF (22 pages)

**Objective:** Analyze SyncManager proposal against 37-question framework (A: API, B: data exposure, C: ops, D: privacy, E: commercial, F: continuity, G: ERP-specific).

**Deliverable:** `openspec/changes/hermes-multi-tenant-wrapper/syncmanager-assessment.md`

**Steps:**
1. Read all 22 pages of SyncManager proposal (available at C:\Users\contexia\Downloads\propuesta syncmaster.pdf)
2. Score against 37-question framework (from prior context):
   - **Section A (API technical):** 6 questions → score each
   - **Section B (data exposure):** 5 questions → score each
   - **Section C (operations):** 8 questions → score each
   - **Section D (privacy/compliance):** 6 questions → score each
   - **Section E (commercial):** 5 questions → score each
   - **Section F (continuity):** 4 questions → score each
   - **Section G (ERP-specific):** 3 questions → score each
3. Create summary: High-level findings, risk/benefit analysis
4. Output format:
   ```markdown
   # SyncManager Assessment (Jul 3, 2026)
   
   ## Summary
   - Overall score: X/37
   - Verdict: [Recommended / Conditionally Recommended / Not Recommended]
   - Key risks: [...]
   - Key benefits: [...]
   
   ## Detailed Scores
   - A (API): 5/6 (missing: rate limit granularity)
   - B (data): 4/5 (missing: PII masking)
   - ... etc.
   ```

**Acceptance:** Assessment complete, all 37 questions scored, summary written.

**Owner:** Tech Lead (Architect)  
**Effort:** 4 hours  
**Deadline:** 2026-07-03  
**Status:** ⏳ Ready

---

### T17: Design Shadow General Ledger (SGLedger) Architecture

**Objective:** Plan how to build Contexia's own deterministic GL in parallel with SyncManager (Phase 2b).

**Deliverable:** `openspec/specs/shadow-general-ledger/spec.md`

**Scope:**
- Stateful mirroring of DIAN XML + Siigo data
- Multi-moneda handling (COP, USD, EUR, etc.)
- pgvector learning loop (agent suggestions)
- Agent Critic validation (hard arithmetic checks)
- Fallback if SyncManager fails or is deprecated

**Steps:**
1. Define SGLedger schema:
   - Tables: `shadow_ledger_entries`, `shadow_ledger_balances`, `shadow_ledger_audit`
   - Columns: date, account_code, debit, credit, currency, source (DIAN/Siigo), validation_status
2. Define data flow:
   - DIAN XML → parse → shadow entries
   - Siigo API → poll → shadow entries
   - Agents read shadow entries → suggestions (pgvector)
   - Agent Critic validates: debit == credit, balance checks
3. Define Phase 2b timeline (Jul 16-31):
   - Week 1: Schema design + DIAN XML parser
   - Week 2: Siigo poller + multi-moneda logic
   - Week 3: pgvector learning loop integration
   - Week 4: Agent Critic validation layer

**Acceptance:** SGLedger spec created, schema defined, Phase 2b timeline locked.

**Owner:** Backend Architect  
**Effort:** 3 hours  
**Deadline:** 2026-07-05  
**Status:** ⏳ Ready

---

### T18: Schedule SyncManager Technical Call (Jul 25)

**Objective:** Book 90-min technical call with SyncManager team to discuss:
- API availability & limits
- Data formats (XML, JSON, CSV)
- Compliance & audit trail
- Fallback strategy (if integration fails)

**Deliverable:** Calendar invite + agenda

**Steps:**
1. Email SyncManager: "Hi, we're integrating Hermes + Contexia with SyncManager for DIAN reporting. Can we schedule a 90-min technical deep-dive on Jul 25?"
2. Prepare agenda:
   - (30 min) SyncManager API capabilities & rate limits
   - (20 min) Data format mapping (DIAN GL ↔ SyncManager)
   - (20 min) Error handling & fallback strategy
   - (20 min) Phase 2 timeline & integration plan
3. Confirm attendees:
   - Contexia: Juan (product), Backend Lead, Architect
   - SyncManager: Technical lead, API specialist, support
4. Send agenda 5 days before call

**Acceptance:** Call scheduled, attendees confirmed, agenda shared.

**Owner:** Product (Juan)  
**Effort:** 30 min  
**Deadline:** 2026-07-10  
**Status:** ⏳ Ready

---

### T19: Phase 2 OpenSpec Tasks (Design Integration)

**Objective:** Create formal OpenSpec for SyncManager integration + Shadow GL.

**Deliverable:** `openspec/changes/hermes-syncmanager-integration/tasks.md`

**Scope:**
- T1-T5: SyncManager API integration (stubs → real endpoints)
- T6-T10: Shadow GL building (schema → DIAN/Siigo polling → pgvector loop)
- T11-T15: Agent Critic validation layer
- T16-T20: E2E testing + Stage 11 deploy

**Steps:**
1. Create directory: `antigravity-app/openspec/changes/hermes-syncmanager-integration/`
2. Create `tasks.md` following same format as this document
3. Define 20 tasks (Phase 2b, Jul 16-31)
4. Set dependencies & critical path
5. Get sign-off from architecture team

**Acceptance:** Phase 2 OpenSpec created, tasks defined, dependencies clear.

**Owner:** Architect  
**Effort:** 2 hours  
**Deadline:** 2026-07-10  
**Status:** ⏳ Ready

---

### T20: Prepare SyncManager Call Deck (Slides + Live Demo)

**Objective:** Create presentation + live demo for Jul 25 call to showcase MVP.

**Deliverable:** Presentation deck + demo environment

**Content:**
- Slide 1: Contexia + Hermes overview
- Slide 2: Multi-tenant architecture (diagram from T14)
- Slide 3: Phase 1 MVP (middleware + RLS + Hermes integration)
- Slide 4: Phase 2 plan (SyncManager + Shadow GL)
- Slide 5: Questions & technical deep-dive
- **Live demo:** Hermes operator calling backend, showing tenant-isolated data

**Steps:**
1. Create deck: `openspec/changes/hermes-multi-tenant-wrapper/presentations/syncmanager-call-2026-07-25.pdf`
2. Record live demo (Loom or similar):
   - Show Hermes Workspace UI
   - Trigger Pulso operator
   - Show backend logs with tenant_id
   - Show Supabase with RLS filtering
   - Narrate: "Multi-tenant ready, only Contexia data visible"
3. Share with team 3 days before call for feedback

**Acceptance:** Deck created, demo recorded, shared with team.

**Owner:** Product (Juan)  
**Effort:** 2 hours  
**Deadline:** 2026-07-22  
**Status:** ⏳ Ready

---

## Phase 3: Hardening & Security (10 days, Jul 16-25)

### T21: Implement Dedicated WSL Distro (hermes-ws)

**Objective:** Create isolated WSL instance for Hermes to prevent prompt-injection / local-file exfiltration.

**Deliverable:** WSL2 distro `hermes-ws` with sandboxing controls

**Steps:**
1. Create distro:
   ```bash
   wsl --import hermes-ws C:\wsl-distros\hermes-ws C:\wsl-backups\ubuntu-20.04.tar.gz
   # Or: fresh Ubuntu instance via Windows Store
   ```
2. Disable automount of Windows drives:
   ```bash
   # In hermes-ws: /etc/wsl.conf
   [automount]
   enabled = false
   ```
3. Create least-privilege user:
   ```bash
   wsl -d hermes-ws -- useradd -m -s /bin/bash contexia
   wsl -d hermes-ws -- usermod -aG sudo contexia
   ```
4. Restrict filesystem scope:
   ```bash
   # Hermes can ONLY read/write /home/contexia/hermes/workspace
   # Mount only this directory; block access to /mnt/c/Users/...
   ```

**Acceptance:** WSL distro created, user login works, personal files inaccessible.

**Owner:** DevOps  
**Effort:** 1.5 hours  
**Deadline:** 2026-07-16  
**Status:** ⏳ Ready

---

### T22: Configure Network Egress Allowlist

**Objective:** Restrict outbound traffic from hermes-ws to only Railway backend, Gemini API, Telegram.

**Deliverable:** UFW / iptables rules, documented

**Steps:**
1. Enable UFW:
   ```bash
   wsl -d hermes-ws -- sudo ufw enable
   ```
2. Default deny outbound:
   ```bash
   wsl -d hermes-ws -- sudo ufw default deny outgoing
   ```
3. Allow only allowlisted hosts:
   ```bash
   # Railway backend
   wsl -d hermes-ws -- sudo ufw allow out to 175.1.2.3/32 port 443  # Example IP
   
   # Gemini API
   wsl -d hermes-ws -- sudo ufw allow out to 35.192.0.0/11 port 443  # Google Cloud
   
   # Telegram API
   wsl -d hermes-ws -- sudo ufw allow out to 149.154.160.0/20 port 443  # Telegram
   
   # DNS
   wsl -d hermes-ws -- sudo ufw allow out 53/udp
   ```
4. Test:
   ```bash
   wsl -d hermes-ws -- curl https://railway.app  # Should work
   wsl -d hermes-ws -- curl https://google.com   # Should fail
   ```

**Acceptance:** UFW rules in place, allowed hosts reachable, denied hosts blocked.

**Owner:** DevOps  
**Effort:** 1.5 hours  
**Deadline:** 2026-07-16  
**Status:** ⏳ Ready

---

### T23: Hardened Railway→Laptop Tunnel (cloudflared + Auth)

**Objective:** Secure the Cloudflare tunnel that exposes Hermes gateway to Railway.

**Deliverable:** Updated tunnel config with auth + allowlist

**Existing:** `antigravity-app/api/hermes/status.ts` (Vercel) → cloudflared tunnel → local :8642

**Steps:**
1. Update tunnel config in `antigravity-app/.cloudflared/config.yaml`:
   ```yaml
   tunnel: [tunnel-id]
   credentials-file: ~/.cloudflared/[tunnel-id].json
   
   ingress:
     - hostname: hermes-gateway.contexia.local
       service: http://localhost:8642
       # Add auth requirement
       options:
         Header:
           - Authorization: Bearer <strong-token>
   ```
2. Update Vercel endpoint:
   - Route: `api/hermes/status.ts`
   - Before proxying to tunnel, validate auth token:
     ```typescript
     const token = req.headers.authorization?.split("Bearer ")[1];
     if (token !== process.env.HERMES_TUNNEL_TOKEN) {
       return res.status(401).json({ error: "Unauthorized" });
     }
     // proxy to tunnel
     ```
3. Rotate old token (`contexia-dev-token-123`):
   - Generate new token: `openssl rand -hex 32`
   - Store in Bitwarden: `Contexia/Infrastructure/Hermes-Tunnel-Token`
   - Update Railway env: `HERMES_TUNNEL_TOKEN=[new]`
   - Update Vercel env: `HERMES_TUNNEL_TOKEN=[new]`

**Acceptance:** Tunnel auth required, old token invalidated, new token in Bitwarden.

**Owner:** DevOps / Security  
**Effort:** 2 hours  
**Deadline:** 2026-07-18  
**Status:** ⏳ Ready

---

### T24: Rotate All Secrets (Bitwarden as Source of Truth)

**Objective:** Ensure all sensitive values are in Bitwarden, remove hardcoded values, rotate any old tokens.

**Deliverable:** Secrets audit report

**Steps:**
1. Audit codebase for secrets:
   ```bash
   grep -r "dev-token\|secret-key\|apikey" apps/ --include="*.py" --include="*.ts" --include=".env*"
   ```
2. For each found secret:
   - Move to Bitwarden item
   - Replace in code with env var
   - Document in AGENTS.md (already done in Phase 1)
3. Rotate critical tokens:
   - Railway API token: rotate if older than 30 days
   - JWT_SECRET: already managed by Railway env
   - Hermes tunnel token: already done in T23
   - LLM provider keys: verify in Bitwarden
4. Create audit report:
   ```markdown
   ## Secrets Audit (Jul 18)
   - Hardcoded secrets in code: 0
   - Secrets in Bitwarden: 12 (Groq, Gemini, OpenAI, Railway, Vercel, Supabase, etc.)
   - Old tokens rotated: Railway, Hermes tunnel
   - Status: ✅ All secrets managed via Bitwarden
   ```

**Acceptance:** Zero hardcoded secrets, all values in Bitwarden, report signed off.

**Owner:** Security / Infra  
**Effort:** 1.5 hours  
**Deadline:** 2026-07-18  
**Status:** ⏳ Ready

---

### T25: Security Audit of Local Sandbox

**Objective:** Verify Phase 3 hardening controls are working.

**Deliverable:** Security audit checklist + sign-off

**Steps:**
1. **Filesystem scope test:**
   ```bash
   wsl -d hermes-ws -- ls /mnt/c/Users/contexia  # Should fail or be empty
   wsl -d hermes-ws -- ls /home/contexia/hermes  # Should succeed
   ```
2. **Egress allowlist test:**
   ```bash
   wsl -d hermes-ws -- curl https://railway.app  # Should work (allowed)
   wsl -d hermes-ws -- curl https://facebook.com # Should fail (blocked)
   ```
3. **Secrets access test:**
   ```bash
   wsl -d hermes-ws -- bw get item groq  # Should work (via Bitwarden)
   # Verify: no hardcoded API keys in /home/contexia/.env or memory
   ```
4. **Tunnel auth test:**
   ```bash
   curl -H "Authorization: Bearer <old-token>" \
     https://hermes-gateway.contexia.local  # Should fail (401)
   
   curl -H "Authorization: Bearer <new-token>" \
     https://hermes-gateway.contexia.local  # Should work (200)
   ```
5. **Document results:**
   ```markdown
   ## Security Audit Results (Jul 19)
   
   - [ ] Filesystem isolation: ✅ PASS (personal files inaccessible)
   - [ ] Network egress: ✅ PASS (only Railway/Gemini/Telegram allowed)
   - [ ] Secrets management: ✅ PASS (all via Bitwarden, no hardcoding)
   - [ ] Tunnel authentication: ✅ PASS (old token blocked, new token works)
   
   **Overall: APPROVED for production**
   ```

**Acceptance:** All security tests pass, audit report signed off.

**Owner:** Security / DevOps  
**Effort:** 2 hours  
**Deadline:** 2026-07-19  
**Status:** ⏳ Ready

---

## Phase 4: E2E Verification + Stage 11 Production Deploy (Jul 26+)

### T26: End-to-End Production Test Scenario

**Objective:** Run full E2E test in production environment before Stage 11.

**Deliverable:** E2E test report + pass/fail log

**Steps:**
1. **Test scenario:**
   - 9 operators run in parallel via Maestro: Pulso, Centinela, Radar, Auditoría, Taty, Social-Ops, Metrics, Content, Lead
   - Local cron fires at 6/8/9/10/12/2 UTC (confirms 24/7 gateway)
   - Telegram round-trip <5s (bot responds quickly)
   - PWA components show live data (WebSocket bridge from Phase 4)
   - ApprovalQueue approve/reject flow works (HITL)
2. **Run tests:**
   ```bash
   pytest tests/e2e/test_multi_tenant_full_flow.py -v --tb=short
   ```
3. **Expected results:**
   ```
   test_maestro_swarm_9_operators_parallel PASSED
   test_local_cron_fires_at_scheduled_times PASSED
   test_telegram_round_trip_latency_ok PASSED
   test_pwa_receives_live_hermes_data PASSED
   test_approval_queue_hitl_workflow PASSED
   
   5 passed, 0 failed
   ```

**Acceptance:** All E2E tests pass in production-like environment.

**Owner:** QA / Backend  
**Effort:** 2 hours  
**Deadline:** 2026-07-23  
**Status:** ⏳ Ready

---

### T27: Stage 11 — Production Deployment Checklist

**Objective:** Execute full Stage 11 deployment checklist per CLAUDE.md.

**Deliverable:** `openspec/changes/hermes-multi-tenant-wrapper/reports/2026-07-26-deployment.md`

**Reference:** `DEPLOYMENT_STAGE/checklist-railway.md` (backend) + `checklist-vercel.md` (frontend)

**Steps:**

**Stage 11.1: Git Commit & Push**
```bash
git add -A
git commit -m "feat: hermes multi-tenant wrapper (phases 1-3 complete)

- TenantContextMiddleware for JWT tenant_id extraction
- Supabase RLS policies for row-level isolation
- Hermes Workspace integration with tenant context
- WSL sandbox hardening + egress allowlist
- Tunnel authentication + secret rotation
- Ready for SyncManager integration (Phase 2)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"

git push origin main
```

**Stage 11.2: Verify CI/CD**
- Vercel build: wait for ✅ green
- Railway backend deploy: wait for ✅ Active

**Stage 11.3: Verify Production URLs**
```bash
# Frontend
curl -I https://contexia.online/app/bunker
# Expected: 200 OK

# Backend health
curl https://antigravity-app-production-175a.up.railway.app/api/v1/health
# Expected: {"status": "ok"}

# Secrets health
curl https://antigravity-app-production-175a.up.railway.app/api/v1/secrets/health
# Expected: {"status": "healthy", ...}
```

**Stage 11.4: Test Production Endpoints**
```bash
# Hermes operator call (via Workspace)
# Trigger: Pulso → Monitor logs for [Tenant: contexia-org-1]
# Expected: operator returns data, RLS filters correctly

# Manual test with curl
curl -H "Authorization: Bearer <PROD_JWT_CONTEXIA>" \
  https://antigravity-app-production-175a.up.railway.app/api/v1/agents/pulso-diario/summary
# Expected: 200, data filtered by tenant_id
```

**Stage 11.5: Create Deployment Report**
```markdown
# Deployment Report: Hermes Multi-Tenant Wrapper

**Date:** 2026-07-26  
**Deployed by:** [Name]  
**Components:** TenantContextMiddleware, RLS policies, Hermes JWT, sandbox hardening

## Deployment Summary
- Frontend: ✅ Vercel deployed (no UI changes)
- Backend: ✅ Railway deployed (middleware + schema migrations)
- Database: ✅ Migrations applied (tenant_id + RLS)
- Hermes: ✅ Configured with tenant context

## Verification Tests
- [ ] Production health check: 200 OK
- [ ] Hermes operator → backend call: successful
- [ ] Tenant isolation (RLS): data correctly filtered
- [ ] Secrets management: all via Bitwarden
- [ ] Tunnel auth: old token blocked, new token works
- [ ] E2E test suite: all passing

## Rollback Plan
If critical issue detected:
1. Revert main branch to previous commit
2. Delete tenant_id columns (or disable RLS)
3. Restart Railway backend

## Sign-off
- [ ] Product (Juan): Approved
- [ ] Backend Lead: Approved
- [ ] DevOps: Approved
- [ ] QA: All tests pass
```

Save to: `openspec/changes/hermes-multi-tenant-wrapper/reports/2026-07-26-deployment.md`

**Acceptance:** Deployment checklist 100% complete, all tests pass, report filed, sign-off obtained.

**Owner:** DevOps / Backend Lead  
**Effort:** 2 hours  
**Deadline:** 2026-07-26  
**Status:** ⏳ Ready

---

### T28: Archive OpenSpec Change

**Objective:** Mark change as complete and archived.

**Deliverable:** `ARCHIVED.md` marker + change moved to archive/

**Steps:**
1. Create file: `openspec/changes/hermes-multi-tenant-wrapper/ARCHIVED.md`
   ```markdown
   # Archived: Hermes Multi-Tenant Wrapper

   **Status:** COMPLETE  
   **Deployed:** 2026-07-26  
   **Stage:** 11 (Production Deploy)

   All phases complete (1A-1D, 2-3, 6). Ready for Phase 2 SyncManager integration.
   ```
2. Move to archive:
   ```bash
   mv openspec/changes/hermes-multi-tenant-wrapper \
      openspec/changes/archive/2026-07-26-hermes-multi-tenant-wrapper
   ```
3. Update config.yaml to reflect archive

**Acceptance:** Change archived, ARCHIVED.md filed, status marked complete.

**Owner:** Architect  
**Effort:** 30 min  
**Deadline:** 2026-07-26  
**Status:** ⏳ Ready

---

## Summary Table

| Phase | Tasks | Effort | Dates | Critical Path |
|-------|-------|--------|-------|---|
| 1A: Middleware | T1-T4 | 4h | Jun 23-25 | T1→T2→T3→T4 |
| 1B: Schema | T5-T9 | 6h | Jun 26-28 | T5→T6→T7→T8→T9 |
| 1C: Hermes JWT | T10-T12 | 4h | Jun 29-30 | T10→T11→T12 |
| 1D: E2E | T13-T15 | 4h | Jul 1-2 | T13→T14→T15 |
| 2: SyncManager | T16-T20 | 12h | Jul 3-15 | T16→T18→T19 |
| 3: Hardening | T21-T25 | 9h | Jul 16-25 | T21→T22→T23→T24→T25 |
| 6: Deploy | T26-T28 | 5h | Jul 26+ | T26→T27→T28 |

**Total Effort:**
- Backend Dev: 20 hours
- DevOps/Infra: 12 hours
- QA: 6 hours
- Product/Architect: 8 hours
- **Total: 46 hours (≈ 2 weeks elapsed, concurrent execution)**

**Critical Path:** T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8 → T9 → T10 → T11 → T12 → T13 → T14 → T15 → **[SyncManager call 2026-07-25]** → T26 → T27 → T28

---

## Phase Dependencies & Gates

```
Jun 23  ─── Phase 1A (Middleware) ───┐
Jun 26  ─── Phase 1B (Schema) ───────┤
Jun 29  ─── Phase 1C (Hermes JWT) ───┤
Jul 1   ─── Phase 1D (E2E) ──────────┤
                                     ├─→ [MVP GATE] ✅
                                     │   (Approval: Phase 1 complete)
                                     │
Jul 3   ─── Phase 2 (SyncManager) ───┤
        ─── [SyncManager Call 2026-07-25]
Jul 16  ─── Phase 3 (Hardening) ─────┤
Jul 26  ─── Phase 6 (Production Deploy)
```

---

## Mandatory OpenSpec Updates

If any of these occur **STOP** and update OpenSpec artifacts:
- JWT structure changes → update T10 (JWT Creation)
- RLS policy bypass discovered → update T7-T9 (Schema/RLS)
- Hermes integration fails → update T10-T12 (JWT Integration)
- SyncManager API unavailable on Jul 25 → reschedule T18, update timeline
- Sandbox hardening insufficient → escalate security findings to T25
- Production deploy blocked → document blocker, update T27 checklist

---

## Total Timeline

**Start:** Jun 23, 2026 (Monday)  
**Phase 1 Complete:** Jul 2, 2026 (Wednesday)  
**SyncManager Call:** Jul 25, 2026 (Friday)  
**Phase 3 Complete:** Jul 25, 2026 (Friday)  
**Production Deploy:** Jul 26, 2026 (Saturday)  
**Archived:** Jul 26, 2026 (Saturday)

**Elapsed:** 34 days (Jun 23 → Jul 26)  
**Concurrent execution:** ~2 weeks calendar time  
**Ready for Phase 2 SyncManager integration:** Jul 3 onwards (parallel with Phase 3)

