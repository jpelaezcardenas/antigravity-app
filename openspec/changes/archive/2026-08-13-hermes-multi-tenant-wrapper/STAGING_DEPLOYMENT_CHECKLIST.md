# Staging Deployment Checklist — Jun 26-28, 2026

**Status:** READY TO START ✅  
**Commit:** b939d14  
**Target:** Staging Supabase + Railway  
**Timeline:** 3 days (Jun 26, 27, 28)

---

## 📋 Pre-Deployment (Right Now)

- [ ] **Clone/pull latest code**
  ```bash
  cd C:\Users\contexia\Projects\antigravity-app
  git pull origin main
  git log --oneline -1
  # Should show: b939d14 feat: implement hermes multi-tenant wrapper...
  ```

- [ ] **Verify commit is present**
  ```bash
  ls -la apps/backend/core/tenant_middleware.py
  ls -la apps/backend/migrations/000*.sql
  # Should show: 0001, 0002, 0003 migrations exist
  ```

- [ ] **Set Staging Environment Variables**
  ```bash
  export SUPABASE_URL="https://[staging-project].supabase.co"
  export SUPABASE_KEY="[staging-api-key]"
  export ENVIRONMENT="staging"
  
  # Verify
  echo $SUPABASE_URL   # Should print URL
  echo $SUPABASE_KEY   # Should print key (masked)
  ```

- [ ] **Test Staging Connection**
  ```bash
  psql "$SUPABASE_URL" -U postgres -d postgres -c "SELECT version();"
  # Expected: PostgreSQL version info, no errors
  ```

---

## 🚀 Deployment Day 1 (Jun 26) — Migrations

**Time:** ~30 minutes

### Option A: Automated (Recommended)
```bash
cd antigravity-app/openspec/changes/hermes-multi-tenant-wrapper/

# Make script executable
chmod +x QUICK_START_STAGING.sh

# Run deployment
./QUICK_START_STAGING.sh
# Expected: ✅ ALL MIGRATIONS SUCCESSFUL
```

### Option B: Manual (Step-by-Step)
```bash
cd antigravity-app/apps/backend/migrations/

# Migration 1: Add tenant_id columns
echo "Running 0001_add_tenant_id_columns.sql..."
psql "$SUPABASE_URL" -U postgres -f 0001_add_tenant_id_columns.sql
echo "✅ Migration 0001 complete"

# Verify
psql "$SUPABASE_URL" -U postgres -c "
  SELECT COUNT(*) as tenant_id_columns 
  FROM information_schema.columns 
  WHERE column_name = 'tenant_id' AND table_schema = 'public';
"
# Expected: 5

# Migration 2: Backfill data
echo "Running 0002_backfill_tenant_id.sql..."
psql "$SUPABASE_URL" -U postgres -f 0002_backfill_tenant_id.sql
echo "✅ Migration 0002 complete"

# Verify
psql "$SUPABASE_URL" -U postgres -c "
  SELECT tablename, COUNT(*) as rows_with_tenant_id 
  FROM pg_tables t
  LEFT JOIN (SELECT COUNT(*) FROM public.pulso_results WHERE tenant_id != '00000000-0000-0000-0000-000000000000') 
  GROUP BY tablename;
"

# Migration 3: Enable RLS
echo "Running 0003_enable_rls_policies.sql..."
psql "$SUPABASE_URL" -U postgres -f 0003_enable_rls_policies.sql
echo "✅ Migration 0003 complete"

# Verify
psql "$SUPABASE_URL" -U postgres -c "
  SELECT tablename, rowsecurity 
  FROM pg_tables 
  WHERE tablename IN ('pulso_results', 'centinela_alerts', 'approval_queue', 'radar_insights', 'auditoria_reports')
  AND schemaname = 'public';
"
# Expected: All 5 should have rowsecurity = true
```

### Post-Migration Checks

- [ ] **All 5 tables have tenant_id column**
  ```bash
  psql "$SUPABASE_URL" -U postgres -c "
    SELECT table_name, COUNT(*) as col_count 
    FROM information_schema.columns 
    WHERE column_name = 'tenant_id' AND table_schema = 'public'
    GROUP BY table_name;
  "
  # Expected: 5 rows (one per table)
  ```

- [ ] **All data backfilled to contexia-org-1**
  ```bash
  psql "$SUPABASE_URL" -U postgres -c "
    SELECT tablename, COUNT(*) as row_count 
    FROM pg_tables 
    WHERE tablename IN ('pulso_results', 'centinela_alerts', 'approval_queue', 'radar_insights', 'auditoria_reports')
    AND schemaname = 'public'
    AND rowsecurity = true;
  "
  # Expected: All 5 = true
  ```

- [ ] **RLS policies enabled**
  ```bash
  psql "$SUPABASE_URL" -U postgres -c "
    SELECT tablename, policyname 
    FROM pg_policies 
    WHERE tablename IN ('pulso_results', 'centinela_alerts', 'approval_queue', 'radar_insights', 'auditoria_reports');
  "
  # Expected: 5 policies with names like *_tenant_isolation
  ```

**Status:** ✅ Staging database ready

---

## 🚢 Deployment Day 2 (Jun 27) — Code & Testing

**Time:** ~1 hour

### Deploy Code to Staging
```bash
cd antigravity-app

# Verify branch is main
git branch
# Should show: * main

# Push to staging (or just main if auto-deploying)
git push origin main

# Wait 2-3 minutes for Railway deployment
echo "Waiting for Railway to deploy..."
sleep 180

# Check deployment status
# Open: https://railway.app/[project]/deployments
# Expected: Latest deployment status = Active ✅
```

### Verify Staging API
- [ ] **Health check**
  ```bash
  curl https://staging-api.contexia.online/api/v1/health
  # Expected: 200 OK, {"status": "ok"}
  ```

- [ ] **Secrets health (if available)**
  ```bash
  curl https://staging-api.contexia.online/api/v1/secrets/health
  # Expected: 200 OK
  ```

### Run Unit Tests
- [ ] **Tenant middleware tests**
  ```bash
  pytest tests/backend/core/test_tenant_middleware.py -v
  # Expected: 6 passed ✅
  ```

### Run E2E Tests
- [ ] **Full multi-tenant flow**
  ```bash
  pytest tests/e2e/test_multi_tenant_flow.py -v
  # Expected: 19 passed ✅
  # This takes ~2-3 minutes
  ```

### Manual Verification
- [ ] **Test with Contexia token**
  ```bash
  python << 'EOF'
  from core.security import create_access_token
  token = create_access_token({'sub': 'test@contexia', 'tenant_id': 'contexia-org-1'})
  print(f"Contexia Token: {token}")
  EOF
  
  # Use token in curl
  CONTEXIA_TOKEN="[output from above]"
  curl -H "Authorization: Bearer $CONTEXIA_TOKEN" \
    https://staging-api.contexia.online/api/v1/agents/pulso-diario/summary \
    -X POST -H "Content-Type: application/json" \
    -d '{"company_id": "contexia-001"}'
  # Expected: 200 OK with Contexia data (or 404 if endpoint not fully wired)
  ```

- [ ] **Test with Client token**
  ```bash
  python << 'EOF'
  from core.security import create_access_token
  token = create_access_token({'sub': 'test@client', 'tenant_id': 'client-xyz'})
  print(f"Client Token: {token}")
  EOF
  
  # Use token in curl
  CLIENT_TOKEN="[output from above]"
  curl -H "Authorization: Bearer $CLIENT_TOKEN" \
    https://staging-api.contexia.online/api/v1/agents/pulso-diario/summary \
    -X POST -H "Content-Type: application/json" \
    -d '{"company_id": "client-xyz-001"}'
  # Expected: 200 OK with Client data (different from Contexia)
  ```

- [ ] **Check backend logs for tenant context**
  ```bash
  railway logs --follow
  # Should see:
  # [Tenant: contexia-org-1] POST /api/v1/agents/pulso-diario/summary
  # [Tenant: client-xyz] POST /api/v1/agents/pulso-diario/summary
  ```

**Status:** ✅ Staging code deployed and tested

---

## ✍️ Deployment Day 3 (Jun 28) — Sign-Off

**Time:** ~30 minutes

### Collect Sign-Offs

**Backend Lead:**
- [ ] Code review: ✅ No issues
- [ ] Tests passing: ✅ 6/6 unit + 19/19 E2E
- [ ] No regressions: ✅ Existing endpoints unchanged
- [ ] Signature: _________________ Date: _______

**Database Lead:**
- [ ] Migrations clean: ✅ Applied in order
- [ ] RLS policies working: ✅ Verified isolation
- [ ] Data integrity: ✅ No data loss
- [ ] Signature: _________________ Date: _______

**DevOps Lead:**
- [ ] Staging stable: ✅ No errors for 24h
- [ ] Monitoring set up: ✅ Alert on RLS failures
- [ ] Rollback tested: ✅ Can disable RLS if needed
- [ ] Signature: _________________ Date: _______

**Product (Juan):**
- [ ] MVP ready for Phase 2: ✅ Confirmed
- [ ] No blockers: ✅ Confirmed
- [ ] Ready for SyncManager call prep: ✅ Confirmed
- [ ] Signature: _________________ Date: _______

### Final Checklist

- [ ] All migrations applied successfully
- [ ] All tests passing (25/25 total)
- [ ] No regressions in staging
- [ ] Staging API stable for 24+ hours
- [ ] RLS policies verified working
- [ ] Tenant isolation confirmed
- [ ] All sign-offs collected
- [ ] Documentation reviewed
- [ ] Ready for Phase 2 kickoff

### Mark Complete

```bash
# Update checklist
# Edit: openspec/changes/hermes-multi-tenant-wrapper/MVP_READINESS_CHECKLIST.md
# Mark all Phase 1A-1D items as ✅

# Commit sign-offs
git add openspec/changes/hermes-multi-tenant-wrapper/MVP_READINESS_CHECKLIST.md
git commit -m "chore: phase 1 staging deployment complete, all sign-offs collected"

# Verify commit
git log --oneline -2
```

**Status:** ✅ Phase 1 Staging Complete

---

## 📞 Troubleshooting

| Issue | Solution |
|-------|----------|
| Migration fails (permission denied) | Check SUPABASE_KEY has admin access |
| API returns 500 after deploy | Check Railway logs for startup errors |
| Tests fail (connection refused) | Verify SUPABASE_URL is reachable |
| RLS not filtering (data leaks) | Verify policies in Supabase dashboard |
| Middleware logs missing | Check log level is DEBUG or INFO |

---

## 🎯 Next Steps (After Jun 28)

✅ **Staging deployment complete**

⏳ **Phase 2 (Jul 3-15) — SyncManager Integration**
- T16: Read & score SyncManager PDF
- T17: Design Shadow GL
- T18: Prep SyncManager call (Jul 25)

⏳ **Phase 3 (Jul 16-25) — Hardening**
- WSL sandbox setup
- Egress allowlist
- Tunnel authentication

📞 **SyncManager Call (Jul 25)**
- Live demo with tenant isolation
- Technical deep-dive
- Integration roadmap

⏳ **Production Deployment (Jul 26+)**
- Follow Stage 11 checklist
- Create deployment report
- Archive Phase 1

---

## ✨ Key Contacts

**Questions about:**
- **Deployment:** See `DEPLOYMENT_GUIDE.md`
- **Architecture:** See `ai-specs/architecture/hermes-multi-tenant-wrapper-spec.md`
- **Tasks:** See `tasks.md` (all 40 tasks)
- **Sign-offs:** See `MVP_READINESS_CHECKLIST.md`

**Emergency (if migration fails):**
1. Check error message above
2. Consult `DEPLOYMENT_GUIDE.md` Rollback section
3. Contact Database Lead

---

## 🚀 Ready to Deploy?

**Checkpoint:**
- ✅ Migrations exist (0001, 0002, 0003)
- ✅ Tests exist (unit + E2E)
- ✅ Code committed (b939d14)
- ✅ Staging credentials ready
- ✅ Documentation complete

**Go ahead:** Run `QUICK_START_STAGING.sh` or follow manual steps above.

**Timeline:** Jun 26-28 (3 days)  
**Status:** READY ✅

