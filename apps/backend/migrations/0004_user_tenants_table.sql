-- Migration 0004: Create user_tenants junction table (Phase 3A)
-- Purpose: Map users to tenants for multi-tenant isolation
-- Created: 2026-06-23
-- Status: Phase 3A - User Migration

DO $$
BEGIN
  -- Create user_tenants table if it doesn't exist
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='user_tenants') THEN
    CREATE TABLE public.user_tenants (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES public.usuarios(id) ON DELETE CASCADE,
      tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
      is_owner BOOLEAN DEFAULT FALSE,
      is_active BOOLEAN DEFAULT TRUE,
      created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
      CONSTRAINT unique_user_tenant UNIQUE(user_id, tenant_id)
    );

    -- Create indexes for performance
    CREATE INDEX idx_user_tenants_user_id ON public.user_tenants(user_id);
    CREATE INDEX idx_user_tenants_tenant_id ON public.user_tenants(tenant_id);
    CREATE INDEX idx_user_tenants_is_owner ON public.user_tenants(is_owner);
    CREATE INDEX idx_user_tenants_is_active ON public.user_tenants(is_active);

    RAISE NOTICE 'Created table user_tenants';
  ELSE
    RAISE NOTICE 'Table user_tenants already exists, skipping creation';
  END IF;

END $$;
