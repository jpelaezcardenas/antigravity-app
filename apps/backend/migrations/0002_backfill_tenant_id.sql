-- Migration: Backfill existing data with the real Cliente Cero tenant_id
-- Date: 2026-06-26 (corrected 2026-07-21 — see hermes-multi-tenant-wrapper/tasks.md
-- "Ground Truth Correction #2")
-- Purpose: Set all existing rows in the 2 real tenant-scoped tables to the real Cliente Cero
-- tenant before RLS policies are relied upon.
-- Idempotent: Can be run multiple times safely (WHERE clauses only touch rows not already correct)
--
-- Corrected 2026-07-21:
-- 1. The original file used psql's `\set` meta-command, which only works under the `psql` CLI —
--    it is not valid SQL and cannot run via Supabase's SQL execution (MCP `apply_migration` /
--    dashboard SQL editor). Replaced with a literal UUID.
-- 2. The original file targeted pulso_results/radar_insights/auditoria_reports, which don't
--    exist as tables. Removed.
-- 3. The literal UUID used ('a0000000-0000-0000-0000-000000000001') did not match the real
--    Cliente Cero tenant row and was never applied consistently — centinela_alerts had already
--    been backfilled to it by an earlier ad-hoc fix, while approval_queue had 3 NULL rows and 3
--    rows already correctly stamped with the real tenant UUID by newer code
--    (services/operator_task_service.py's _resolve_cliente_cero_tenant_id). Replaced with the
--    real tenant UUID so both tables agree, confirmed live via:
--    SELECT id FROM tenants WHERE is_cliente_cero = true; → e2d30d09-6b96-4ebe-a79a-c6aff7a5df34

-- Backfill centinela_alerts: unify any row not already on the real Cliente Cero tenant
UPDATE public.centinela_alerts
SET tenant_id = 'e2d30d09-6b96-4ebe-a79a-c6aff7a5df34'
WHERE tenant_id IS NULL
   OR tenant_id != 'e2d30d09-6b96-4ebe-a79a-c6aff7a5df34';

-- Backfill approval_queue: unify any row not already on the real Cliente Cero tenant
UPDATE public.approval_queue
SET tenant_id = 'e2d30d09-6b96-4ebe-a79a-c6aff7a5df34'
WHERE tenant_id IS NULL
   OR tenant_id != 'e2d30d09-6b96-4ebe-a79a-c6aff7a5df34';

-- Verify backfill (should show 0 for both)
-- SELECT count(*) FROM public.centinela_alerts WHERE tenant_id IS DISTINCT FROM 'e2d30d09-6b96-4ebe-a79a-c6aff7a5df34';
-- SELECT count(*) FROM public.approval_queue WHERE tenant_id IS DISTINCT FROM 'e2d30d09-6b96-4ebe-a79a-c6aff7a5df34';
