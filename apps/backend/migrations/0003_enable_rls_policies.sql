-- Migration: Enable Row-Level Security (RLS) and create tenant isolation policies
-- Date: 2026-06-27
-- Purpose: Enforce tenant isolation at database level
-- Prerequisites: 0001_add_tenant_id_columns.sql and 0002_backfill_tenant_id.sql must run first
-- Note: All rows must have non-null tenant_id before enabling RLS

-- Enable RLS on all org-scoped tables
-- Note: Enabling RLS blocks all access by default until policies are created
ALTER TABLE public.pulso_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.centinela_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.approval_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.radar_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.auditoria_reports ENABLE ROW LEVEL SECURITY;

-- Policy: pulso_results tenant isolation
-- Users can only see rows where tenant_id matches their JWT tenant_id claim
-- Fallback to 'a0000000-0000-0000-0000-000000000001' (Contexia default) if claim missing
CREATE POLICY pulso_results_tenant_isolation
ON public.pulso_results
FOR ALL
USING (tenant_id = COALESCE(auth.jwt()->>'tenant_id'::uuid, 'a0000000-0000-0000-0000-000000000001'::uuid))
WITH CHECK (tenant_id = COALESCE(auth.jwt()->>'tenant_id'::uuid, 'a0000000-0000-0000-0000-000000000001'::uuid));

-- Policy: centinela_alerts tenant isolation
CREATE POLICY centinela_alerts_tenant_isolation
ON public.centinela_alerts
FOR ALL
USING (tenant_id = COALESCE(auth.jwt()->>'tenant_id'::uuid, 'a0000000-0000-0000-0000-000000000001'::uuid))
WITH CHECK (tenant_id = COALESCE(auth.jwt()->>'tenant_id'::uuid, 'a0000000-0000-0000-0000-000000000001'::uuid));

-- Policy: approval_queue tenant isolation
CREATE POLICY approval_queue_tenant_isolation
ON public.approval_queue
FOR ALL
USING (tenant_id = COALESCE(auth.jwt()->>'tenant_id'::uuid, 'a0000000-0000-0000-0000-000000000001'::uuid))
WITH CHECK (tenant_id = COALESCE(auth.jwt()->>'tenant_id'::uuid, 'a0000000-0000-0000-0000-000000000001'::uuid));

-- Policy: radar_insights tenant isolation
CREATE POLICY radar_insights_tenant_isolation
ON public.radar_insights
FOR ALL
USING (tenant_id = COALESCE(auth.jwt()->>'tenant_id'::uuid, 'a0000000-0000-0000-0000-000000000001'::uuid))
WITH CHECK (tenant_id = COALESCE(auth.jwt()->>'tenant_id'::uuid, 'a0000000-0000-0000-0000-000000000001'::uuid));

-- Policy: auditoria_reports tenant isolation
CREATE POLICY auditoria_reports_tenant_isolation
ON public.auditoria_reports
FOR ALL
USING (tenant_id = COALESCE(auth.jwt()->>'tenant_id'::uuid, 'a0000000-0000-0000-0000-000000000001'::uuid))
WITH CHECK (tenant_id = COALESCE(auth.jwt()->>'tenant_id'::uuid, 'a0000000-0000-0000-0000-000000000001'::uuid));

-- Verification query (run after policies are created):
-- SELECT tablename, rowsecurity FROM pg_tables
-- WHERE tablename IN ('pulso_results', 'centinela_alerts', 'approval_queue', 'radar_insights', 'auditoria_reports')
-- AND schemaname = 'public';
-- Expected: All should have rowsecurity = true
