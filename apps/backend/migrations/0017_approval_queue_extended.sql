-- Migration 0017: Extend approval_queue schema for Phase 6 HITL workflows
--
-- Ensures approval_queue table has all columns needed for:
-- - Approval decision tracking (reviewed_at, reviewer_id)
-- - Audit trail (reason)
-- - Status validation (pending, approved, rejected)
--
-- Date: 2026-06-25
-- Phase: 6 (HITL Workflows + Hermes Integration)

-- Step 1: Create approval_queue table if not exists
CREATE TABLE IF NOT EXISTS public.approval_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  action_type TEXT NOT NULL,  -- e.g., "review_accounting_entry"
  data JSONB NOT NULL,  -- error, raw_input, timestamp, etc.
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
  created_at TIMESTAMP DEFAULT NOW(),
  reviewed_at TIMESTAMP,
  reviewer_id UUID,  -- Reference to users table (if exists)
  reason TEXT,  -- Approval/rejection reason

  CONSTRAINT approval_queue_tenant_fk FOREIGN KEY (tenant_id)
    REFERENCES public.tenants(id) ON DELETE CASCADE
);

-- Step 2: Enable RLS on approval_queue (if not already enabled)
ALTER TABLE public.approval_queue ENABLE ROW LEVEL SECURITY;

-- Step 3: Create RLS policies
-- Policy: Users can view approval_queue for their tenant
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'approval_queue' AND policyname = 'Users can view their tenant approval_queue'
  ) THEN
    CREATE POLICY "Users can view their tenant approval_queue"
      ON public.approval_queue FOR SELECT
      USING (
        auth.uid() IS NULL OR  -- Skip for service-role
        EXISTS (
          SELECT 1 FROM public.user_tenants
          WHERE user_tenants.tenant_id = approval_queue.tenant_id
            AND user_tenants.user_id = auth.uid()
        )
      );
  END IF;
END
$$;

-- Step 4: Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_approval_queue_tenant_status
  ON public.approval_queue(tenant_id, status);

CREATE INDEX IF NOT EXISTS idx_approval_queue_created_at
  ON public.approval_queue(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_approval_queue_reviewed_at
  ON public.approval_queue(reviewed_at DESC);

-- Step 5: Add columns if they don't exist (for idempotency)
ALTER TABLE public.approval_queue
  ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP,
  ADD COLUMN IF NOT EXISTS reviewer_id UUID,
  ADD COLUMN IF NOT EXISTS reason TEXT;

-- Step 6: Ensure CHECK constraint on status
ALTER TABLE public.approval_queue
  DROP CONSTRAINT IF EXISTS approval_queue_status_check;

ALTER TABLE public.approval_queue
  ADD CONSTRAINT approval_queue_status_check
  CHECK (status IN ('pending', 'approved', 'rejected'));

-- Step 7: Create audit log trigger (optional, for compliance)
CREATE OR REPLACE FUNCTION public.audit_approval_queue()
RETURNS TRIGGER AS $$
BEGIN
  -- Log approval/rejection events
  IF NEW.status != OLD.status THEN
    INSERT INTO public.audit_log (
      entity_type,
      entity_id,
      action,
      old_values,
      new_values,
      changed_by,
      changed_at
    ) VALUES (
      'approval_queue',
      NEW.id,
      'status_changed',
      jsonb_build_object('status', OLD.status),
      jsonb_build_object('status', NEW.status),
      NEW.reviewer_id,
      NEW.reviewed_at
    );
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger if audit_log table exists
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_log') THEN
    DROP TRIGGER IF EXISTS audit_approval_queue_trigger ON public.approval_queue;
    CREATE TRIGGER audit_approval_queue_trigger
      AFTER UPDATE ON public.approval_queue
      FOR EACH ROW
      EXECUTE FUNCTION public.audit_approval_queue();
  END IF;
END
$$;

-- Step 8: Verify final schema
-- SELECT column_name, data_type, is_nullable FROM information_schema.columns
-- WHERE table_name = 'approval_queue' ORDER BY ordinal_position;
