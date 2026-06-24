-- Migration 0009: Seed default role permissions (Phase 3B)
-- Purpose: Define permission matrix for each role
-- Created: 2026-06-23
-- Status: Phase 3B - Role Framework
-- Note: Idempotent - uses ON CONFLICT DO NOTHING

DO $$
BEGIN
  -- ADMIN ROLE - Full access to everything
  INSERT INTO public.role_permissions (role, resource, action, description)
  VALUES
    ('admin'::role_type, 'all'::resource_type, 'admin'::action_type, 'Admin can do anything'),
    ('admin'::role_type, 'users'::resource_type, 'create'::action_type, 'Admin can create users'),
    ('admin'::role_type, 'users'::resource_type, 'read'::action_type, 'Admin can read users'),
    ('admin'::role_type, 'users'::resource_type, 'update'::action_type, 'Admin can update users'),
    ('admin'::role_type, 'users'::resource_type, 'delete'::action_type, 'Admin can delete users'),
    ('admin'::role_type, 'admin_panel'::resource_type, 'read'::action_type, 'Admin can access admin panel'),
    ('admin'::role_type, 'admin_panel'::resource_type, 'update'::action_type, 'Admin can modify settings')
  ON CONFLICT DO NOTHING;

  -- FINANCE ROLE - Financial operations
  INSERT INTO public.role_permissions (role, resource, action, description)
  VALUES
    ('finance'::role_type, 'shadow_gl'::resource_type, 'read'::action_type, 'Finance can read GL'),
    ('finance'::role_type, 'shadow_gl'::resource_type, 'create'::action_type, 'Finance can create GL entries'),
    ('finance'::role_type, 'shadow_gl'::resource_type, 'update'::action_type, 'Finance can update GL'),
    ('finance'::role_type, 'approval_queue'::resource_type, 'read'::action_type, 'Finance can read approvals'),
    ('finance'::role_type, 'approval_queue'::resource_type, 'update'::action_type, 'Finance can approve'),
    ('finance'::role_type, 'auditoria_reports'::resource_type, 'read'::action_type, 'Finance can read audit'),
    ('finance'::role_type, 'auditoria_reports'::resource_type, 'export'::action_type, 'Finance can export reports')
  ON CONFLICT DO NOTHING;

  -- MARKETING ROLE - Marketing operations
  INSERT INTO public.role_permissions (role, resource, action, description)
  VALUES
    ('marketing'::role_type, 'alerts'::resource_type, 'read'::action_type, 'Marketing can read alerts'),
    ('marketing'::role_type, 'radar_insights'::resource_type, 'read'::action_type, 'Marketing can read insights'),
    ('marketing'::role_type, 'radar_insights'::resource_type, 'create'::action_type, 'Marketing can create insights'),
    ('marketing'::role_type, 'auditoria_reports'::resource_type, 'read'::action_type, 'Marketing can read audit')
  ON CONFLICT DO NOTHING;

  -- GROWTH ROLE - Growth operations
  INSERT INTO public.role_permissions (role, resource, action, description)
  VALUES
    ('growth'::role_type, 'alerts'::resource_type, 'read'::action_type, 'Growth can read alerts'),
    ('growth'::role_type, 'alerts'::resource_type, 'update'::action_type, 'Growth can update alerts'),
    ('growth'::role_type, 'radar_insights'::resource_type, 'read'::action_type, 'Growth can read insights'),
    ('growth'::role_type, 'radar_insights'::resource_type, 'create'::action_type, 'Growth can create insights'),
    ('growth'::role_type, 'auditoria_reports'::resource_type, 'read'::action_type, 'Growth can read audit')
  ON CONFLICT DO NOTHING;

  -- OPERATOR ROLE - Operator execution
  INSERT INTO public.role_permissions (role, resource, action, description)
  VALUES
    ('operator'::role_type, 'operators'::resource_type, 'read'::action_type, 'Operator can read operator configs'),
    ('operator'::role_type, 'operators'::resource_type, 'update'::action_type, 'Operator can update configs'),
    ('operator'::role_type, 'approval_queue'::resource_type, 'read'::action_type, 'Operator can read queue'),
    ('operator'::role_type, 'alerts'::resource_type, 'read'::action_type, 'Operator can read alerts')
  ON CONFLICT DO NOTHING;

  -- VIEWER ROLE - Read-only access
  INSERT INTO public.role_permissions (role, resource, action, description)
  VALUES
    ('viewer'::role_type, 'alerts'::resource_type, 'read'::action_type, 'Viewer can read alerts'),
    ('viewer'::role_type, 'radar_insights'::resource_type, 'read'::action_type, 'Viewer can read insights'),
    ('viewer'::role_type, 'approval_queue'::resource_type, 'read'::action_type, 'Viewer can read queue'),
    ('viewer'::role_type, 'auditoria_reports'::resource_type, 'read'::action_type, 'Viewer can read audit')
  ON CONFLICT DO NOTHING;

  RAISE NOTICE 'Role permissions seeded successfully';
END $$;
