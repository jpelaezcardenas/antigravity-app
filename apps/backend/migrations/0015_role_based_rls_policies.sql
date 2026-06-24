-- Migration 0015: Role-based RLS policies for identity + onboarding tables
-- Purpose: close the T8/T9 gap — user_tenants, user_roles, role_permissions,
--          customer_invites, team_invites currently have RLS enabled with ZERO policies,
--          which fail-closes all access via anon/authenticated roles (verified 2026-06-24).
-- OpenSpec: hermes-user-sync-and-onboarding

-- ============================================================================
-- user_tenants: self-read own memberships; admin reads all rows in own tenant
-- ============================================================================
CREATE POLICY "user_tenants_self_read" ON public.user_tenants
FOR SELECT
USING (user_id = auth.uid());

CREATE POLICY "user_tenants_admin_read_tenant" ON public.user_tenants
FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM public.user_roles ur
    WHERE ur.user_id = auth.uid()
      AND ur.tenant_id = user_tenants.tenant_id
      AND ur.role = 'admin'
  )
);

-- ============================================================================
-- user_roles: self-read own role; admin reads all roles in own tenant
-- ============================================================================
CREATE POLICY "user_roles_self_read" ON public.user_roles
FOR SELECT
USING (user_id = auth.uid());

CREATE POLICY "user_roles_admin_read_tenant" ON public.user_roles
FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM public.user_roles ur
    WHERE ur.user_id = auth.uid()
      AND ur.tenant_id = user_roles.tenant_id
      AND ur.role = 'admin'
  )
);

-- ============================================================================
-- role_permissions: read-only reference data, any authenticated user can read
-- ============================================================================
CREATE POLICY "role_permissions_authenticated_read" ON public.role_permissions
FOR SELECT
TO authenticated
USING (true);

-- ============================================================================
-- customer_invites: admin-only insert + read (Contexia-level admin action)
-- ============================================================================
CREATE POLICY "customer_invites_admin_insert" ON public.customer_invites
FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.user_roles ur
    WHERE ur.user_id = auth.uid()
      AND ur.role = 'admin'
  )
);

CREATE POLICY "customer_invites_admin_read" ON public.customer_invites
FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM public.user_roles ur
    WHERE ur.user_id = auth.uid()
      AND ur.role = 'admin'
  )
);

-- ============================================================================
-- team_invites: tenant-admin insert + tenant-scoped read
-- ============================================================================
CREATE POLICY "team_invites_tenant_admin_insert" ON public.team_invites
FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.user_roles ur
    WHERE ur.user_id = auth.uid()
      AND ur.tenant_id = team_invites.tenant_id
      AND ur.role = 'admin'
  )
);

CREATE POLICY "team_invites_tenant_scoped_read" ON public.team_invites
FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM public.user_roles ur
    WHERE ur.user_id = auth.uid()
      AND ur.tenant_id = team_invites.tenant_id
      AND ur.role = 'admin'
  )
);
