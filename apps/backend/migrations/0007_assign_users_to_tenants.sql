-- Migration 0007: Assign users to Contexia SAS tenant (Phase 3A)
-- Purpose: Establish user-tenant relationships
-- Created: 2026-06-23
-- Status: Phase 3A - User Migration
-- Note: Idempotent - only inserts if not exists

DO $$
DECLARE
  contexia_tenant_id UUID := 'e2d30d09-6b96-4ebe-a79a-c6aff7a5df34';
  juan_user_id UUID := 'abf2af3a-f5bb-4628-850f-d2edd037c972';
  marketing_user_id UUID := '9c65171f-ee5f-4945-8351-06e9c62b78b6';
  demo_user_id UUID := '26216a03-9d4a-4590-bfc3-a4ddf0524d57';
BEGIN
  -- Assign Juan David as owner of Contexia SAS
  IF NOT EXISTS (
    SELECT 1 FROM public.user_tenants
    WHERE user_id = juan_user_id AND tenant_id = contexia_tenant_id
  ) THEN
    INSERT INTO public.user_tenants (user_id, tenant_id, is_owner, is_active)
    VALUES (juan_user_id, contexia_tenant_id, TRUE, TRUE);
    RAISE NOTICE 'Assigned Juan David (jpelaezcardenas@gmail.com) as owner of Contexia SAS';
  END IF;

  -- Assign marketing team to Contexia SAS
  IF NOT EXISTS (
    SELECT 1 FROM public.user_tenants
    WHERE user_id = marketing_user_id AND tenant_id = contexia_tenant_id
  ) THEN
    INSERT INTO public.user_tenants (user_id, tenant_id, is_owner, is_active)
    VALUES (marketing_user_id, contexia_tenant_id, FALSE, TRUE);
    RAISE NOTICE 'Assigned Marketing team (contexia.marketing@gmail.com) to Contexia SAS';
  END IF;

  -- Assign demo user to Contexia SAS
  IF NOT EXISTS (
    SELECT 1 FROM public.user_tenants
    WHERE user_id = demo_user_id AND tenant_id = contexia_tenant_id
  ) THEN
    INSERT INTO public.user_tenants (user_id, tenant_id, is_owner, is_active)
    VALUES (demo_user_id, contexia_tenant_id, FALSE, TRUE);
    RAISE NOTICE 'Assigned Demo user (cliente@demo.co) to Contexia SAS';
  END IF;

  RAISE NOTICE 'User-tenant assignments complete';
END $$;
