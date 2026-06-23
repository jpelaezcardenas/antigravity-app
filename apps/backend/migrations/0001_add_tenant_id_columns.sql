-- Migration: Add tenant_id columns to all org-scoped tables
-- Date: 2026-06-26
-- Purpose: Enable multi-tenant isolation via Supabase RLS policies
-- Non-breaking: Uses DEFAULT, no rewrite required
-- Idempotent: Can be run multiple times safely

-- Add tenant_id UUID column to pulso_results table
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'pulso_results' AND column_name = 'tenant_id'
  ) THEN
    ALTER TABLE public.pulso_results
    ADD COLUMN tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000000';
    CREATE INDEX idx_pulso_results_tenant_id ON public.pulso_results(tenant_id);
  END IF;
END $$;

-- Add tenant_id UUID column to centinela_alerts table
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'centinela_alerts' AND column_name = 'tenant_id'
  ) THEN
    ALTER TABLE public.centinela_alerts
    ADD COLUMN tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000000';
    CREATE INDEX idx_centinela_alerts_tenant_id ON public.centinela_alerts(tenant_id);
  END IF;
END $$;

-- Add tenant_id UUID column to approval_queue table
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'approval_queue' AND column_name = 'tenant_id'
  ) THEN
    ALTER TABLE public.approval_queue
    ADD COLUMN tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000000';
    CREATE INDEX idx_approval_queue_tenant_id ON public.approval_queue(tenant_id);
  END IF;
END $$;

-- Add tenant_id UUID column to radar_insights table
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'radar_insights' AND column_name = 'tenant_id'
  ) THEN
    ALTER TABLE public.radar_insights
    ADD COLUMN tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000000';
    CREATE INDEX idx_radar_insights_tenant_id ON public.radar_insights(tenant_id);
  END IF;
END $$;

-- Add tenant_id UUID column to auditoria_reports table
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'auditoria_reports' AND column_name = 'tenant_id'
  ) THEN
    ALTER TABLE public.auditoria_reports
    ADD COLUMN tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000000';
    CREATE INDEX idx_auditoria_reports_tenant_id ON public.auditoria_reports(tenant_id);
  END IF;
END $$;

-- Note: After this migration, run backfill_tenant_id.sql to assign all existing rows
-- to the default tenant (contexia-org-1) before enabling RLS policies.
