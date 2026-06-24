-- Migration 0012: Create onboarding_workflows audit table (Phase 3B)
-- Purpose: Audit trail for all onboarding operations
-- Created: 2026-06-23
-- Status: Phase 3B - Customer Onboarding

DO $$
BEGIN
  -- Create workflow_type enum if it doesn't exist
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='workflow_type') THEN
    CREATE TYPE workflow_type AS ENUM (
      'customer_registration',
      'team_onboarding',
      'role_update',
      'role_revoke',
      'user_offboarding'
    );
    RAISE NOTICE 'Created enum type workflow_type';
  END IF;

  -- Create workflow_status enum if it doesn't exist
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='workflow_status') THEN
    CREATE TYPE workflow_status AS ENUM ('pending', 'in_progress', 'completed', 'failed', 'cancelled');
    RAISE NOTICE 'Created enum type workflow_status';
  END IF;

  -- Create onboarding_workflows table if it doesn't exist
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='onboarding_workflows') THEN
    CREATE TABLE public.onboarding_workflows (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
      workflow_type workflow_type NOT NULL,

      -- Hermes operator executing this workflow
      operator_id TEXT,
      operator_version TEXT,

      -- User being affected by this workflow
      user_id UUID REFERENCES public.usuarios(id) ON DELETE SET NULL,

      -- Role assigned/updated/revoked
      role_assigned role_type,
      role_previous role_type,

      -- Workflow state
      status workflow_status NOT NULL DEFAULT 'pending',
      error_message TEXT,

      -- Timestamps
      created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
      started_at TIMESTAMPTZ,
      completed_at TIMESTAMPTZ,

      -- Metadata
      metadata JSONB DEFAULT '{}'::jsonb  -- For additional context
    );

    -- Create indexes for performance and audit queries
    CREATE INDEX idx_onboarding_workflows_tenant_id ON public.onboarding_workflows(tenant_id);
    CREATE INDEX idx_onboarding_workflows_user_id ON public.onboarding_workflows(user_id);
    CREATE INDEX idx_onboarding_workflows_operator_id ON public.onboarding_workflows(operator_id);
    CREATE INDEX idx_onboarding_workflows_status ON public.onboarding_workflows(status);
    CREATE INDEX idx_onboarding_workflows_type ON public.onboarding_workflows(workflow_type);
    CREATE INDEX idx_onboarding_workflows_created_at ON public.onboarding_workflows(created_at DESC);

    -- Composite index for audit queries
    CREATE INDEX idx_onboarding_workflows_tenant_type_status ON public.onboarding_workflows(tenant_id, workflow_type, status);

    RAISE NOTICE 'Created table onboarding_workflows';
  ELSE
    RAISE NOTICE 'Table onboarding_workflows already exists, skipping creation';
  END IF;

END $$;
