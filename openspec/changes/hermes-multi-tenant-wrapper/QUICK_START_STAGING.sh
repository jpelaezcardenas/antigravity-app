#!/bin/bash
# Quick-Start Staging Deployment Script
# Purpose: Deploy Hermes multi-tenant wrapper to Staging
# Date: 2026-06-26
# Prerequisites: psql, git, Railway CLI access

set -e

echo "=========================================="
echo "Hermes Multi-Tenant Wrapper"
echo "Staging Deployment — Jun 26-28, 2026"
echo "=========================================="
echo ""

# Pre-flight checks
echo "✓ Pre-flight Checklist"
echo "---"

if ! command -v psql &> /dev/null; then
    echo "❌ BLOCKER: psql not found. Install PostgreSQL CLI."
    exit 1
fi
echo "  ✅ psql available"

if [ -z "$SUPABASE_URL" ]; then
    echo "❌ BLOCKER: SUPABASE_URL not set. Export it:"
    echo "   export SUPABASE_URL='https://[project].supabase.co'"
    exit 1
fi
echo "  ✅ SUPABASE_URL set: $SUPABASE_URL"

if [ -z "$SUPABASE_KEY" ]; then
    echo "❌ BLOCKER: SUPABASE_KEY not set. Export it:"
    echo "   export SUPABASE_KEY='[api-key]'"
    exit 1
fi
echo "  ✅ SUPABASE_KEY set"

# Test connection
echo ""
echo "✓ Testing Supabase Connection..."
if psql "$SUPABASE_URL" -U postgres -d postgres -c "SELECT version();" > /dev/null 2>&1; then
    echo "  ✅ Connection successful"
else
    echo "❌ BLOCKER: Cannot connect to Supabase. Check credentials."
    exit 1
fi

# Navigation
cd "$(dirname "$0")"
MIGRATIONS_DIR="../../apps/backend/migrations"

if [ ! -d "$MIGRATIONS_DIR" ]; then
    echo "❌ BLOCKER: Migrations directory not found: $MIGRATIONS_DIR"
    exit 1
fi
echo "  ✅ Migrations directory found"

echo ""
echo "=========================================="
echo "STEP 1/3: Migration 0001 (Add tenant_id columns)"
echo "=========================================="
echo "Applying: 0001_add_tenant_id_columns.sql"
echo ""

if psql "$SUPABASE_URL" -U postgres -f "$MIGRATIONS_DIR/0001_add_tenant_id_columns.sql"; then
    echo ""
    echo "✅ Migration 0001 SUCCESS"
    echo ""
    echo "Verifying columns created..."
    RESULT=$(psql "$SUPABASE_URL" -U postgres -t -c "SELECT COUNT(*) FROM information_schema.columns WHERE column_name = 'tenant_id' AND table_schema = 'public';")
    if [ "$RESULT" -eq 5 ]; then
        echo "  ✅ All 5 tables have tenant_id column"
    else
        echo "  ⚠️  Expected 5 columns, found $RESULT. Check logs."
    fi
else
    echo "❌ Migration 0001 FAILED. See errors above."
    exit 1
fi

echo ""
echo "=========================================="
echo "STEP 2/3: Migration 0002 (Backfill to default tenant)"
echo "=========================================="
echo "Applying: 0002_backfill_tenant_id.sql"
echo ""

if psql "$SUPABASE_URL" -U postgres -f "$MIGRATIONS_DIR/0002_backfill_tenant_id.sql"; then
    echo ""
    echo "✅ Migration 0002 SUCCESS"
    echo ""
    echo "Verifying data backfilled..."
    RESULT=$(psql "$SUPABASE_URL" -U postgres -t -c "SELECT COUNT(*) FROM public.pulso_results WHERE tenant_id != '00000000-0000-0000-0000-000000000000';")
    echo "  ✅ Rows with contexia-org-1 tenant_id: $RESULT"
else
    echo "❌ Migration 0002 FAILED. See errors above."
    echo "⚠️  Note: You may need to run backfill manually if it failed."
    exit 1
fi

echo ""
echo "=========================================="
echo "STEP 3/3: Migration 0003 (Enable RLS policies)"
echo "=========================================="
echo "Applying: 0003_enable_rls_policies.sql"
echo ""

if psql "$SUPABASE_URL" -U postgres -f "$MIGRATIONS_DIR/0003_enable_rls_policies.sql"; then
    echo ""
    echo "✅ Migration 0003 SUCCESS"
    echo ""
    echo "Verifying RLS policies enabled..."
    RESULT=$(psql "$SUPABASE_URL" -U postgres -t -c "SELECT COUNT(*) FROM pg_tables WHERE tablename IN ('pulso_results', 'centinela_alerts', 'approval_queue', 'radar_insights', 'auditoria_reports') AND schemaname = 'public' AND rowsecurity = true;")
    if [ "$RESULT" -eq 5 ]; then
        echo "  ✅ All 5 tables have RLS enabled"
    else
        echo "  ⚠️  Expected 5, found $RESULT. Check Supabase dashboard."
    fi
else
    echo "❌ Migration 0003 FAILED. See errors above."
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ ALL MIGRATIONS SUCCESSFUL"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Deploy code to staging:"
echo "   git push origin main"
echo ""
echo "2. Wait 2-3 minutes for Railway deployment"
echo "   Check: https://railway.app/[project]/deployments"
echo ""
echo "3. Verify staging API:"
echo "   curl https://staging-api.contexia.online/api/v1/health"
echo ""
echo "4. Run E2E tests:"
echo "   pytest tests/e2e/test_multi_tenant_flow.py -v"
echo ""
echo "5. Collect sign-offs (see MVP_READINESS_CHECKLIST.md)"
echo ""
echo "Questions? See: DEPLOYMENT_GUIDE.md"
echo ""
