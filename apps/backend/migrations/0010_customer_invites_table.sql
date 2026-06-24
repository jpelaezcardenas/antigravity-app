-- Migration 0010: Create customer_invites table (Phase 3B)
-- Purpose: Track pending customer registrations
-- Created: 2026-06-23
-- Status: Phase 3B - Customer Onboarding

DO $$
BEGIN
  -- Create plan_type enum if it doesn't exist
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='plan_type') THEN
    CREATE TYPE plan_type AS ENUM ('starter', 'pro', 'enterprise');
    RAISE NOTICE 'Created enum type plan_type';
  END IF;

  -- Create invite_status enum if it doesn't exist
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='invite_status') THEN
    CREATE TYPE invite_status AS ENUM ('pending', 'accepted', 'expired', 'cancelled');
    RAISE NOTICE 'Created enum type invite_status';
  END IF;

  -- Create customer_invites table if it doesn't exist
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='customer_invites') THEN
    CREATE TABLE public.customer_invites (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      created_by UUID NOT NULL REFERENCES public.usuarios(id) ON DELETE SET NULL,
      customer_name TEXT NOT NULL,
      customer_email TEXT NOT NULL UNIQUE,
      plan plan_type NOT NULL DEFAULT 'starter',
      invite_token TEXT NOT NULL UNIQUE DEFAULT encode(gen_random_bytes(32), 'hex'),
      invite_expires_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP + INTERVAL '7 days',
      status invite_status NOT NULL DEFAULT 'pending',
      created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
      accepted_at TIMESTAMPTZ,

      -- Hermes operator tracking
      operator_id TEXT,
      operator_executed_at TIMESTAMPTZ,

      -- Link to created tenant (after acceptance)
      created_tenant_id UUID REFERENCES public.tenants(id) ON DELETE SET NULL
    );

    -- Create indexes for performance
    CREATE INDEX idx_customer_invites_email ON public.customer_invites(customer_email);
    CREATE INDEX idx_customer_invites_status ON public.customer_invites(status);
    CREATE INDEX idx_customer_invites_token ON public.customer_invites(invite_token);
    CREATE INDEX idx_customer_invites_created_by ON public.customer_invites(created_by);
    CREATE INDEX idx_customer_invites_expires ON public.customer_invites(invite_expires_at);

    RAISE NOTICE 'Created table customer_invites';
  ELSE
    RAISE NOTICE 'Table customer_invites already exists, skipping creation';
  END IF;

END $$;
