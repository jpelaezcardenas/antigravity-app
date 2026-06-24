-- Migration 0006: Create role_permissions table (Phase 3B)
-- Purpose: Define what each role can do
-- Created: 2026-06-23
-- Status: Phase 3B - Role Framework

DO $$
BEGIN
  -- Create actions enum type if it doesn't exist
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='action_type') THEN
    CREATE TYPE action_type AS ENUM (
      'create',
      'read',
      'update',
      'delete',
      'export',
      'admin'
    );
    RAISE NOTICE 'Created enum type action_type';
  ELSE
    RAISE NOTICE 'Enum type action_type already exists, skipping creation';
  END IF;

  -- Create resource enum type if it doesn't exist
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='resource_type') THEN
    CREATE TYPE resource_type AS ENUM (
      'alerts',
      'approval_queue',
      'radar_insights',
      'auditoria_reports',
      'shadow_gl',
      'operators',
      'users',
      'admin_panel',
      'all'
    );
    RAISE NOTICE 'Created enum type resource_type';
  ELSE
    RAISE NOTICE 'Enum type resource_type already exists, skipping creation';
  END IF;

  -- Create role_permissions table if it doesn't exist
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='role_permissions') THEN
    CREATE TABLE public.role_permissions (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      role role_type NOT NULL,
      resource resource_type NOT NULL,
      action action_type NOT NULL,
      description TEXT,
      created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
      CONSTRAINT unique_role_resource_action UNIQUE(role, resource, action)
    );

    -- Create indexes for performance
    CREATE INDEX idx_role_permissions_role ON public.role_permissions(role);
    CREATE INDEX idx_role_permissions_resource ON public.role_permissions(resource);
    CREATE INDEX idx_role_permissions_action ON public.role_permissions(action);

    RAISE NOTICE 'Created table role_permissions';
  ELSE
    RAISE NOTICE 'Table role_permissions already exists, skipping creation';
  END IF;

END $$;
