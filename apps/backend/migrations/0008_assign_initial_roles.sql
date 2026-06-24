-- Migration 0008: Assign initial roles to users (Phase 3B)
-- Purpose: Set up role hierarchy
-- Created: 2026-06-23
-- Status: Phase 3B - Role Framework
-- Note: Idempotent - only inserts if not exists

DO $$
DECLARE
  contexia_tenant_id UUID := 'e2d30d09-6b96-4ebe-a79a-c6aff7a5df34';
  juan_user_id UUID := 'abf2af3a-f5bb-4628-850f-d2edd037c972';
  marketing_user_id UUID := '9c65171f-ee5f-4945-8351-06e9c62b78b6';
  demo_user_id UUID := '26216a03-9d4a-4590-bfc3-a4ddf0524d57';
BEGIN
  -- Assign admin role to Juan David (User 0)
  IF NOT EXISTS (
    SELECT 1 FROM public.user_roles
    WHERE user_id = juan_user_id AND tenant_id = contexia_tenant_id
  ) THEN
    INSERT INTO public.user_roles (user_id, tenant_id, role)
    VALUES (juan_user_id, contexia_tenant_id, 'admin'::role_type);
    RAISE NOTICE 'Assigned admin role to Juan David (User 0)';
  END IF;

  -- Assign marketing role to marketing team
  IF NOT EXISTS (
    SELECT 1 FROM public.user_roles
    WHERE user_id = marketing_user_id AND tenant_id = contexia_tenant_id
  ) THEN
    INSERT INTO public.user_roles (user_id, tenant_id, role)
    VALUES (marketing_user_id, contexia_tenant_id, 'marketing'::role_type);
    RAISE NOTICE 'Assigned marketing role to contexia.marketing@gmail.com';
  END IF;

  -- Assign viewer role to demo user
  IF NOT EXISTS (
    SELECT 1 FROM public.user_roles
    WHERE user_id = demo_user_id AND tenant_id = contexia_tenant_id
  ) THEN
    INSERT INTO public.user_roles (user_id, tenant_id, role)
    VALUES (demo_user_id, contexia_tenant_id, 'viewer'::role_type);
    RAISE NOTICE 'Assigned viewer role to demo user (cliente@demo.co)';
  END IF;

  RAISE NOTICE 'Initial role assignments complete';
END $$;
