-- Migration: Harden approval_queue.tenant_id — drop the bogus zeros-UUID default and require
-- NOT NULL, so a future write that forgets tenant_id fails loudly instead of writing a ghost
-- tenant.
-- Date: 2026-07-23
-- Purpose: Close the loop on hermes-multi-tenant-wrapper's Ground Truth Correction #2 backfill
-- (migrations 0001/0002) and this change's application-layer tenant scoping
-- (approval-queue-tenant-scoping) by making the schema itself enforce what the service and
-- endpoint layers already require: every approval_queue row must carry a real tenant_id.
-- Idempotent: Can be run multiple times safely.
-- Prerequisites: 0001_add_tenant_id_columns.sql and 0002_backfill_tenant_id.sql must run first.
--
-- Live pre-work verification (2026-07-23, see design.md "Pre-work verification"): all 6 live
-- approval_queue rows already carry the real Cliente Cero UUID
-- (e2d30d09-6b96-4ebe-a79a-c6aff7a5df34), no NULL or zeros-UUID rows remain. Step 1 below is a
-- safety re-backfill only — a no-op today, kept so this migration is still correct if it's ever
-- re-run against a database that regressed.

-- 1. Safety re-backfill: any row that is still NULL or stamped with the bogus zeros-UUID
-- default gets the real Cliente Cero tenant. No-op today (verified above); guards against a
-- future NOT NULL violation on this same migration if it's re-run after a regression.
UPDATE public.approval_queue
SET tenant_id = (SELECT id FROM public.tenants WHERE is_cliente_cero = TRUE)
WHERE tenant_id IS NULL
   OR tenant_id = '00000000-0000-0000-0000-000000000000';

-- 2. Drop the zeros-UUID default (set by 0001_add_tenant_id_columns.sql) so a future INSERT
-- that omits tenant_id fails the NOT NULL constraint below instead of silently writing a ghost
-- tenant. Guarded so re-running this migration never errors even if the default was already
-- dropped by a prior run.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'approval_queue'
      AND column_name = 'tenant_id'
      AND column_default IS NOT NULL
  ) THEN
    ALTER TABLE public.approval_queue ALTER COLUMN tenant_id DROP DEFAULT;
  END IF;
END $$;

-- 3. Enforce NOT NULL. PostgreSQL allows re-running SET NOT NULL on an already-NOT-NULL column
-- without error (it re-validates and succeeds silently), so no additional idempotency guard is
-- needed here — this is the simplest correct form.
ALTER TABLE public.approval_queue ALTER COLUMN tenant_id SET NOT NULL;

-- Verification query (run after this migration is applied):
-- SELECT count(*) FROM public.approval_queue WHERE tenant_id IS NULL; -- expect 0
-- SELECT column_default, is_nullable FROM information_schema.columns
-- WHERE table_schema = 'public' AND table_name = 'approval_queue' AND column_name = 'tenant_id';
-- Expected: column_default IS NULL, is_nullable = 'NO'
