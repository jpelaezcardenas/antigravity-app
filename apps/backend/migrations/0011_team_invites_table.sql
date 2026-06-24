-- Migration 0011: Create team_invites table (Phase 3B)
-- Purpose: Track pending team member invitations
-- Created: 2026-06-23
-- Status: Phase 3B - Customer Onboarding

DO $$
BEGIN
  -- Create team_invites table if it doesn't exist
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='team_invites') THEN
    CREATE TABLE public.team_invites (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
      invited_by UUID NOT NULL REFERENCES public.usuarios(id) ON DELETE SET NULL,
      invitee_email TEXT NOT NULL,
      role role_type NOT NULL DEFAULT 'viewer',
      invite_token TEXT NOT NULL UNIQUE DEFAULT encode(gen_random_bytes(32), 'hex'),
      invite_expires_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP + INTERVAL '7 days',
      status invite_status NOT NULL DEFAULT 'pending',
      created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
      accepted_at TIMESTAMPTZ,

      -- Hermes operator tracking
      operator_id TEXT,
      operator_executed_at TIMESTAMPTZ,

      -- Link to created user (after acceptance)
      created_user_id UUID REFERENCES public.usuarios(id) ON DELETE SET NULL,

      -- Constraint: ensure uniqueness per tenant
      CONSTRAINT unique_team_invite UNIQUE(tenant_id, invitee_email)
    );

    -- Create indexes for performance
    CREATE INDEX idx_team_invites_tenant_id ON public.team_invites(tenant_id);
    CREATE INDEX idx_team_invites_email ON public.team_invites(invitee_email);
    CREATE INDEX idx_team_invites_status ON public.team_invites(status);
    CREATE INDEX idx_team_invites_token ON public.team_invites(invite_token);
    CREATE INDEX idx_team_invites_role ON public.team_invites(role);
    CREATE INDEX idx_team_invites_expires ON public.team_invites(invite_expires_at);

    RAISE NOTICE 'Created table team_invites';
  ELSE
    RAISE NOTICE 'Table team_invites already exists, skipping creation';
  END IF;

END $$;
