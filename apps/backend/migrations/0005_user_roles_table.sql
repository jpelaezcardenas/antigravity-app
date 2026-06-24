-- Migration 0005: Create user_roles junction table (Phase 3B)
-- Purpose: Assign roles to users within tenants
-- Created: 2026-06-23
-- Status: Phase 3B - Role Framework

DO $$
BEGIN
  -- Create roles enum type if it doesn't exist
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='role_type') THEN
    CREATE TYPE role_type AS ENUM (
      'admin',
      'finance',
      'marketing',
      'growth',
      'operator',
      'viewer'
    );
    RAISE NOTICE 'Created enum type role_type';
  ELSE
    RAISE NOTICE 'Enum type role_type already exists, skipping creation';
  END IF;

  -- Create user_roles table if it doesn't exist
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='user_roles') THEN
    CREATE TABLE public.user_roles (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES public.usuarios(id) ON DELETE CASCADE,
      tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
      role role_type NOT NULL DEFAULT 'viewer',
      created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
      CONSTRAINT unique_user_tenant_role UNIQUE(user_id, tenant_id)
    );

    -- Create indexes for performance
    CREATE INDEX idx_user_roles_user_id ON public.user_roles(user_id);
    CREATE INDEX idx_user_roles_tenant_id ON public.user_roles(tenant_id);
    CREATE INDEX idx_user_roles_role ON public.user_roles(role);

    RAISE NOTICE 'Created table user_roles';
  ELSE
    RAISE NOTICE 'Table user_roles already exists, skipping creation';
  END IF;

END $$;
