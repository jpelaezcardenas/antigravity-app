-- Migration: Enable Row-Level Security (RLS) and create tenant isolation policies
-- Date: 2026-06-27 (corrected 2026-07-21 — see hermes-multi-tenant-wrapper/tasks.md
-- "Ground Truth Correction #2")
-- Purpose: Enforce tenant isolation at database level
-- Prerequisites: 0001_add_tenant_id_columns.sql and 0002_backfill_tenant_id.sql must run first
-- Note: All rows must have non-null tenant_id before enabling RLS
--
-- Corrected 2026-07-21: this file originally targeted 5 tables; only centinela_alerts and
-- approval_queue exist. The fallback UUID ('a0000000-...-001') was an ungrounded placeholder,
-- corrected here to the real Cliente Cero tenant UUID for documentation accuracy.
--
-- NOT re-applied live as-is: both tables already have PERMISSIVE `qual=true` policies from a
-- separate change (approval_queue_anon_all; centinela_alerts_select/insert/update) that coexist
-- with *_tenant_isolation below. Postgres ORs multiple PERMISSIVE policies for the same command,
-- so as long as those allow-all policies exist, the isolation policy below has no effect — this
-- is intentional today, since approval_queue_service.py/centinela_service.py query via the
-- anon-key client (no per-request user JWT reaches Postgres), and would return zero rows without
-- the allow-all policies. Dropping them is a separate, explicitly-deferred decision (see
-- tasks.md) — not bundled into this correction.

-- Enable RLS on the 2 real org-scoped tables
-- Note: Enabling RLS blocks all access by default until policies are created
ALTER TABLE public.centinela_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.approval_queue ENABLE ROW LEVEL SECURITY;

-- Policy: centinela_alerts tenant isolation
-- Users can only see rows where tenant_id matches their JWT tenant_id claim
-- Fallback to the real Cliente Cero tenant UUID if the claim is missing/non-UUID
CREATE POLICY centinela_alerts_tenant_isolation
ON public.centinela_alerts
FOR ALL
USING (tenant_id = COALESCE(auth.jwt()->>'tenant_id'::uuid, 'e2d30d09-6b96-4ebe-a79a-c6aff7a5df34'::uuid))
WITH CHECK (tenant_id = COALESCE(auth.jwt()->>'tenant_id'::uuid, 'e2d30d09-6b96-4ebe-a79a-c6aff7a5df34'::uuid));

-- Policy: approval_queue tenant isolation
CREATE POLICY approval_queue_tenant_isolation
ON public.approval_queue
FOR ALL
USING (tenant_id = COALESCE(auth.jwt()->>'tenant_id'::uuid, 'e2d30d09-6b96-4ebe-a79a-c6aff7a5df34'::uuid))
WITH CHECK (tenant_id = COALESCE(auth.jwt()->>'tenant_id'::uuid, 'e2d30d09-6b96-4ebe-a79a-c6aff7a5df34'::uuid));

-- Verification query (run after policies are created):
-- SELECT tablename, rowsecurity FROM pg_tables
-- WHERE tablename IN ('centinela_alerts', 'approval_queue')
-- AND schemaname = 'public';
-- Expected: All should have rowsecurity = true
