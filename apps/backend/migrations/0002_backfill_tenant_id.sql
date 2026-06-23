-- Migration: Backfill existing data with default tenant_id
-- Date: 2026-06-26
-- Purpose: Set all existing rows to the default tenant (Contexia) before RLS policies
-- WARNING: Must run AFTER 0001_add_tenant_id_columns.sql and BEFORE 0003_enable_rls_policies.sql
-- Idempotent: Can be run multiple times safely (sets where clause filters already-set rows)

-- Default tenant UUID for Contexia S.A.S.
-- This is the primary Contexia organization in multi-tenant setup
\set default_tenant_id 'a0000000-0000-0000-0000-000000000001'

-- Backfill pulso_results: Set all rows with default UUID to contexia-org-1
UPDATE public.pulso_results
SET tenant_id = :'default_tenant_id'
WHERE tenant_id = '00000000-0000-0000-0000-000000000000';

-- Backfill centinela_alerts: Set all rows with default UUID to contexia-org-1
UPDATE public.centinela_alerts
SET tenant_id = :'default_tenant_id'
WHERE tenant_id = '00000000-0000-0000-0000-000000000000';

-- Backfill approval_queue: Set all rows with default UUID to contexia-org-1
UPDATE public.approval_queue
SET tenant_id = :'default_tenant_id'
WHERE tenant_id = '00000000-0000-0000-0000-000000000000';

-- Backfill radar_insights: Set all rows with default UUID to contexia-org-1
UPDATE public.radar_insights
SET tenant_id = :'default_tenant_id'
WHERE tenant_id = '00000000-0000-0000-0000-000000000000';

-- Backfill auditoria_reports: Set all rows with default UUID to contexia-org-1
UPDATE public.auditoria_reports
SET tenant_id = :'default_tenant_id'
WHERE tenant_id = '00000000-0000-0000-0000-000000000000';

-- Verify backfill (should show row counts for each table)
-- SELECT table_name, COUNT(*) as rows_with_contexia_tenant
-- FROM (
--   SELECT 'pulso_results' as table_name FROM public.pulso_results WHERE tenant_id = :'default_tenant_id'
--   UNION ALL
--   SELECT 'centinela_alerts' FROM public.centinela_alerts WHERE tenant_id = :'default_tenant_id'
--   UNION ALL
--   SELECT 'approval_queue' FROM public.approval_queue WHERE tenant_id = :'default_tenant_id'
--   UNION ALL
--   SELECT 'radar_insights' FROM public.radar_insights WHERE tenant_id = :'default_tenant_id'
--   UNION ALL
--   SELECT 'auditoria_reports' FROM public.auditoria_reports WHERE tenant_id = :'default_tenant_id'
-- ) grouped
-- GROUP BY table_name;
