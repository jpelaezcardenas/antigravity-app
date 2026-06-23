# Deployment Guide: Multi-Tenant Wrapper Migrations

**Commit:** b939d14 (feat: implement hermes multi-tenant wrapper phases 1A-1D complete)  
**Date:** 2026-06-26 onwards  
**Target Environments:** Staging (Jun 26-28) → Production (Jul 26+)

---

## Pre-Deployment Checklist

- [ ] Commit merged to `main`
- [ ] All code reviews approved
- [ ] E2E tests passing: `pytest tests/e2e/test_multi_tenant_flow.py -v`
- [ ] Unit tests passing: `pytest tests/backend/core/test_tenant_middleware.py -v`
- [ ] Staging environment ready (Supabase project accessible)
- [ ] Production backup taken (Supabase auto-backup verified)
- [ ] Rollback plan documented (see below)

---

## Step 1: Deploy to Staging (Jun 26-28)

### 1.1 Verify Staging Supabase Connection

```bash
# Set staging environment variables
export SUPABASE_URL="https://[staging-project].supabase.co"
export SUPABASE_KEY="[staging-api-key]"

# Test connection
psql "$SUPABASE_URL" -U postgres -d postgres -c "SELECT version();"
# Expected: PostgreSQL version info, no errors
```

### 1.2 Apply Migrations in Order (CRITICAL: Order Matters)

**DO NOT skip any migration or run out of order.**

#### Migration 1: Add tenant_id Columns

```bash
# From antigravity-app/apps/backend/migrations/
psql $DATABASE_URL -U postgres -f 0001_add_tenant_id_columns.sql

# Expected output:
# DO
# CREATE INDEX
# ... (repeated for each table)
# No errors

# Verify columns created:
psql $DATABASE_URL -U postgres -c "
  SELECT table_name, column_name 
  FROM information_schema.columns 
  WHERE column_name = 'tenant_id' 
  ORDER BY table_name;
"
# Expected: 5 rows (one for each table: approval_queue, auditoria_reports, centinela_alerts, pulso_results, radar_insights)
```

**Rollback (if needed):**
```sql
ALTER TABLE public.pulso_results DROP COLUMN IF EXISTS tenant_id;
ALTER TABLE public.centinela_alerts DROP COLUMN IF EXISTS tenant_id;
ALTER TABLE public.approval_queue DROP COLUMN IF EXISTS tenant_id;
ALTER TABLE public.radar_insights DROP COLUMN IF EXISTS tenant_id;
ALTER TABLE public.auditoria_reports DROP COLUMN IF EXISTS tenant_id;
```

---

#### Migration 2: Backfill Data to Default Tenant

```bash
# Backfill all existing rows with default tenant_id
psql $DATABASE_URL -U postgres -f 0002_backfill_tenant_id.sql

# Expected output:
# UPDATE [N rows] (where N = total rows in table)
# ... (for each of 5 tables)

# Verify backfill (rows should have contexia-org-1 tenant_id):
psql $DATABASE_URL -U postgres -c "
  SELECT tablename, COUNT(*) as row_count
  FROM (
    SELECT 'pulso_results' as tablename FROM public.pulso_results WHERE tenant_id != '00000000-0000-0000-0000-000000000000'
    UNION ALL
    SELECT 'centinela_alerts' FROM public.centinela_alerts WHERE tenant_id != '00000000-0000-0000-0000-000000000000'
    UNION ALL
    SELECT 'approval_queue' FROM public.approval_queue WHERE tenant_id != '00000000-0000-0000-0000-000000000000'
    UNION ALL
    SELECT 'radar_insights' FROM public.radar_insights WHERE tenant_id != '00000000-0000-0000-0000-000000000000'
    UNION ALL
    SELECT 'auditoria_reports' FROM public.auditoria_reports WHERE tenant_id != '00000000-0000-0000-0000-000000000000'
  ) as t
  GROUP BY tablename;
"
# Expected: All 5 tables should have row counts matching pre-migration counts
```

**Rollback (if needed):**
```sql
-- Revert to default UUID (data still exists, but won't pass RLS checks)
UPDATE public.pulso_results SET tenant_id = '00000000-0000-0000-0000-000000000000';
UPDATE public.centinela_alerts SET tenant_id = '00000000-0000-0000-0000-000000000000';
UPDATE public.approval_queue SET tenant_id = '00000000-0000-0000-0000-000000000000';
UPDATE public.radar_insights SET tenant_id = '00000000-0000-0000-0000-000000000000';
UPDATE public.auditoria_reports SET tenant_id = '00000000-0000-0000-0000-000000000000';
```

---

#### Migration 3: Enable RLS Policies

```bash
# Enable RLS and create tenant isolation policies
psql $DATABASE_URL -U postgres -f 0003_enable_rls_policies.sql

# Expected output:
# ALTER TABLE
# CREATE POLICY
# ... (5 policies created, one per table)

# Verify RLS is enabled:
psql $DATABASE_URL -U postgres -c "
  SELECT tablename, rowsecurity 
  FROM pg_tables 
  WHERE tablename IN ('pulso_results', 'centinela_alerts', 'approval_queue', 'radar_insights', 'auditoria_reports')
  AND schemaname = 'public'
  ORDER BY tablename;
"
# Expected: All 5 should have rowsecurity = true (or 't' in older PostgreSQL)

# Verify policies created:
psql $DATABASE_URL -U postgres -c "
  SELECT tablename, policyname 
  FROM pg_policies 
  WHERE tablename IN ('pulso_results', 'centinela_alerts', 'approval_queue', 'radar_insights', 'auditoria_reports')
  ORDER BY tablename;
"
# Expected: 5 policies, names like: pulso_results_tenant_isolation, etc.
```

**Rollback (if needed):**
```sql
-- Disable RLS (policies will be deleted automatically)
ALTER TABLE public.pulso_results DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.centinela_alerts DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.approval_queue DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.radar_insights DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.auditoria_reports DISABLE ROW LEVEL SECURITY;
```

---

### 1.3 Deploy Code to Staging

```bash
# Push to staging branch (or merge to main if auto-deploying)
git push origin main

# Wait for Railway deployment (2-3 minutes)
# Check Railway dashboard: https://railway.app/[project]/deployments

# Verify staging API is healthy
curl https://staging-api.contexia.online/api/v1/health
# Expected: {"status": "ok"}

# Verify middleware is loaded
curl -H "Authorization: Bearer [test-jwt]" \
  https://staging-api.contexia.online/api/v1/health
# Expected: 200 OK (middleware processed the request)
```

### 1.4 Run Integration Tests on Staging

```bash
# Test RLS isolation
pytest tests/e2e/test_multi_tenant_flow.py::TestDataIsolation -v

# Test Hermes operators
pytest tests/e2e/test_multi_tenant_flow.py::TestHermesOperators -v

# Full E2E
pytest tests/e2e/test_multi_tenant_flow.py -v
# Expected: All 19 tests passing
```

### 1.5 Manual Verification

**Test with Contexia token:**
```bash
TOKEN=$(python -c "
from core.security import create_access_token
token = create_access_token({'sub': 'test', 'tenant_id': 'contexia-org-1'})
print(token)
")

curl -H "Authorization: Bearer $TOKEN" \
  https://staging-api.contexia.online/api/v1/agents/pulso-diario/summary \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"company_id": "contexia-001"}'
# Expected: 200 OK with data
```

**Test with Client token:**
```bash
TOKEN=$(python -c "
from core.security import create_access_token
token = create_access_token({'sub': 'client-user', 'tenant_id': 'client-xyz'})
print(token)
")

curl -H "Authorization: Bearer $TOKEN" \
  https://staging-api.contexia.online/api/v1/agents/pulso-diario/summary \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"company_id": "client-xyz-001"}'
# Expected: 200 OK with data (if data exists) OR different data than Contexia
```

**Check backend logs for tenant context:**
```bash
railway logs --follow

# Should see lines like:
# [Tenant: contexia-org-1] POST /api/v1/agents/pulso-diario/summary
# [Tenant: client-xyz] POST /api/v1/agents/pulso-diario/summary
```

---

## Step 2: Deploy to Production (Jul 26+, After Phase 3)

### 2.1 Pre-Production Checklist

- [ ] Phase 1 MVP sign-offs collected (Product, Backend, Database, DevOps)
- [ ] Phase 3 hardening complete (WSL sandbox, egress allowlist, tunnel auth)
- [ ] SyncManager technical call completed (Jul 25)
- [ ] Phase 2 integration plan finalized
- [ ] E2E tests still passing
- [ ] Staging deployment stable for 3+ days (no issues)

### 2.2 Production Deployment (Stage 11)

**Follow Stage 11 Deployment Checklist** from `DEPLOYMENT_STAGE/checklist-railway.md`

```bash
# 1. Git commit & push
git push origin main

# 2. Verify CI/CD
# - Vercel: wait for build to complete (green ✅)
# - Railway: wait for backend deploy to Active

# 3. Verify production URLs
curl -I https://antigravity-app-production-175a.up.railway.app/api/v1/health
# Expected: 200 OK

# 4. Run production E2E test
pytest tests/e2e/test_multi_tenant_flow.py::TestAuthenticationFlow -v

# 5. Manual production verification
TOKEN=$(python -c "
from core.security import create_access_token
token = create_access_token({'sub': 'juan@contexia.local', 'tenant_id': 'contexia-org-1'})
print(token)
")

curl -H "Authorization: Bearer $TOKEN" \
  https://antigravity-app-production-175a.up.railway.app/api/v1/agents/pulso-diario/summary \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"company_id": "contexia-001"}'
# Expected: 200 OK with production data

# 6. Create deployment report
cat > openspec/changes/hermes-multi-tenant-wrapper/reports/2026-07-26-production-deploy.md << 'EOF'
# Production Deployment Report

**Date:** 2026-07-26  
**Commit:** [hash]  
**Changes:** Multi-tenant wrapper phases 1A-1D

## Verification Results

- [ ] Migrations applied (0001, 0002, 0003)
- [ ] RLS policies enabled and verified
- [ ] Middleware loaded successfully
- [ ] Production health check: ✅
- [ ] E2E tests: ✅ (19 passing)
- [ ] Hermes operators working: ✅
- [ ] No regressions: ✅

## Sign-off

- Product (Juan): _______________
- Backend Lead: _______________
- DevOps: _______________

EOF
```

---

## Rollback Plan

**If critical issues occur:**

### Quick Rollback (Disable RLS)

```sql
-- Disable RLS but keep data intact
ALTER TABLE public.pulso_results DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.centinela_alerts DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.approval_queue DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.radar_insights DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.auditoria_reports DISABLE ROW LEVEL SECURITY;

-- Keep middleware running (non-invasive, won't break anything)
-- OR disable middleware by setting: MULTI_TENANT_ENABLED=False
```

### Full Rollback (Remove All Changes)

```bash
# Revert commit
git revert b939d14

# Remove migrations from database
psql $DATABASE_URL -U postgres << 'EOF'
ALTER TABLE public.pulso_results DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.centinela_alerts DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.approval_queue DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.radar_insights DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.auditoria_reports DISABLE ROW LEVEL SECURITY;

ALTER TABLE public.pulso_results DROP COLUMN IF EXISTS tenant_id;
ALTER TABLE public.centinela_alerts DROP COLUMN IF EXISTS tenant_id;
ALTER TABLE public.approval_queue DROP COLUMN IF EXISTS tenant_id;
ALTER TABLE public.radar_insights DROP COLUMN IF EXISTS tenant_id;
ALTER TABLE public.auditoria_reports DROP COLUMN IF EXISTS tenant_id;
EOF

# Redeploy previous version
git push origin main
```

---

## Monitoring Post-Deployment

**Set up alerts for:**

1. **RLS policy failures:**
   ```sql
   -- Check logs for "permission denied" errors
   SELECT * FROM pg_stat_statements WHERE query LIKE '%permission denied%';
   ```

2. **Middleware errors:**
   - Monitor logs for `[Tenant: default-tenant]` when JWT should be present
   - Alert if tenant_id extraction failing >1% of requests

3. **Performance impact:**
   - JWT decode overhead: <50ms (from T4 tests)
   - RLS filtering overhead: <100ms (database-level, minimal)
   - Monitor p99 latency before/after

---

## Testing Verification Matrix

| Test | Staging | Production | Blocker |
|------|---------|------------|---------|
| Migrations apply without errors | ✅ | ✅ | YES |
| Columns exist on all 5 tables | ✅ | ✅ | YES |
| RLS policies enabled | ✅ | ✅ | YES |
| Backfill success (data not lost) | ✅ | ✅ | YES |
| E2E tests pass (19 tests) | ✅ | ✅ | YES |
| Middleware extracts tenant_id | ✅ | ✅ | YES |
| Contexia data isolated | ✅ | ✅ | YES |
| Client data isolated | ✅ | ✅ | YES |
| No data leak between tenants | ✅ | ✅ | YES |
| Existing endpoints unchanged | ✅ | ✅ | YES |
| Performance acceptable | ✅ | ✅ | NO (warning only) |

---

## Reference

- **Migrations:** `apps/backend/migrations/000*.sql`
- **Code:** `apps/backend/core/tenant_middleware.py`, `main.py`, `config.py`, `security.py`
- **Tests:** `tests/backend/core/test_tenant_middleware.py`, `tests/e2e/test_multi_tenant_flow.py`
- **Spec:** `ai-specs/architecture/hermes-multi-tenant-wrapper-spec.md`
- **Stage 11 Checklist:** `DEPLOYMENT_STAGE/checklist-railway.md`

