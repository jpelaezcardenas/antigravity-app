-- Migration 0039: retention_alerts (retention-loop)
-- Date: 2026-08-15
-- Persists B2B churn/risk alerts (missed_payment, payment_drop) computed by
-- services/retention_service.py. Mirrors centinela_alerts' shape and RLS policy pattern
-- (0020_crm_b2b_retainers.sql, admin-only via the live role_type enum).

CREATE TABLE IF NOT EXISTS retention_alerts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  client_id uuid NOT NULL REFERENCES b2b_clients(id) ON DELETE CASCADE,
  rule_id text NOT NULL,
  severity text NOT NULL DEFAULT 'warning',
  message text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chk_retention_alerts_severity CHECK (severity IN ('info', 'warning', 'critical'))
);

CREATE INDEX IF NOT EXISTS idx_retention_alerts_tenant ON retention_alerts (tenant_id);
CREATE INDEX IF NOT EXISTS idx_retention_alerts_client ON retention_alerts (client_id);

ALTER TABLE retention_alerts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS retention_alerts_admin_only ON retention_alerts;
CREATE POLICY retention_alerts_admin_only ON retention_alerts
  FOR ALL
  USING (
    auth.uid() IN (
      SELECT user_id FROM user_roles
      WHERE tenant_id = retention_alerts.tenant_id
      AND role = 'admin'
    )
  )
  WITH CHECK (
    auth.uid() IN (
      SELECT user_id FROM user_roles
      WHERE tenant_id = retention_alerts.tenant_id
      AND role = 'admin'
    )
  );

COMMENT ON TABLE retention_alerts IS 'B2B churn/risk alerts (missed_payment, payment_drop) computed by retention_service.py against b2b_payments history.';

SELECT '✅ 0039 retention_alerts complete' AS status;
