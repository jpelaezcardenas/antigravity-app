-- Migration 0020: CRM B2B retainers cockpit
-- Date: 2026-07-19
-- Adds b2b_clients + b2b_payments (normalized ledger, one row per client per month).
-- Tenant-scoped to Cliente Cero, admin-only RLS using the live role_type enum.

CREATE TABLE IF NOT EXISTS b2b_clients (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name text NOT NULL,
  nit text,
  status text NOT NULL DEFAULT 'activo',
  monthly_fee_cents bigint,
  notes text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_b2b_clients_tenant_name UNIQUE (tenant_id, name),
  CONSTRAINT chk_b2b_clients_status CHECK (status IN ('activo', 'inactivo'))
);

CREATE TABLE IF NOT EXISTS b2b_payments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  client_id uuid NOT NULL REFERENCES b2b_clients(id) ON DELETE CASCADE,
  period date NOT NULL,
  amount_cents bigint NOT NULL DEFAULT 0,
  status text NOT NULL DEFAULT 'paid',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_b2b_payments_client_period UNIQUE (client_id, period),
  CONSTRAINT chk_b2b_payments_status CHECK (status IN ('paid', 'pending', 'waived')),
  CONSTRAINT chk_b2b_payments_period_is_month_start CHECK (period = date_trunc('month', period)::date)
);

CREATE INDEX IF NOT EXISTS idx_b2b_clients_tenant ON b2b_clients (tenant_id);
CREATE INDEX IF NOT EXISTS idx_b2b_payments_tenant_period ON b2b_payments (tenant_id, period);
CREATE INDEX IF NOT EXISTS idx_b2b_payments_client ON b2b_payments (client_id);

-- updated_at triggers (scoped to this migration, public schema)
CREATE OR REPLACE FUNCTION update_crm_b2b_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS trg_b2b_clients_updated_at ON b2b_clients;
CREATE TRIGGER trg_b2b_clients_updated_at
  BEFORE UPDATE ON b2b_clients
  FOR EACH ROW
  EXECUTE FUNCTION update_crm_b2b_updated_at();

DROP TRIGGER IF EXISTS trg_b2b_payments_updated_at ON b2b_payments;
CREATE TRIGGER trg_b2b_payments_updated_at
  BEFORE UPDATE ON b2b_payments
  FOR EACH ROW
  EXECUTE FUNCTION update_crm_b2b_updated_at();

-- Row Level Security: admin-only, using the live role_type enum (values verified live:
-- admin | finance | marketing | growth | operator | viewer). NOT role_name (0019) or
-- role_id+roles join (0013) or the JWT app_metadata label set used by the Vercel edge
-- middleware (admin|superadmin|contexia_admin) — those are unrelated to this Postgres enum.
ALTER TABLE b2b_clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE b2b_payments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS b2b_clients_admin_only ON b2b_clients;
CREATE POLICY b2b_clients_admin_only ON b2b_clients
  FOR ALL
  USING (
    auth.uid() IN (
      SELECT user_id FROM user_roles
      WHERE tenant_id = b2b_clients.tenant_id
      AND role = 'admin'
    )
  )
  WITH CHECK (
    auth.uid() IN (
      SELECT user_id FROM user_roles
      WHERE tenant_id = b2b_clients.tenant_id
      AND role = 'admin'
    )
  );

DROP POLICY IF EXISTS b2b_payments_admin_only ON b2b_payments;
CREATE POLICY b2b_payments_admin_only ON b2b_payments
  FOR ALL
  USING (
    auth.uid() IN (
      SELECT user_id FROM user_roles
      WHERE tenant_id = b2b_payments.tenant_id
      AND role = 'admin'
    )
  )
  WITH CHECK (
    auth.uid() IN (
      SELECT user_id FROM user_roles
      WHERE tenant_id = b2b_payments.tenant_id
      AND role = 'admin'
    )
  );

COMMENT ON TABLE b2b_clients IS 'Contexia''s own B2B retainer client roster (Cliente Cero), migrated from the manual Excel ledger.';
COMMENT ON TABLE b2b_payments IS 'Normalized monthly payment ledger: one row per (client, calendar month). amount_cents is COP minor units.';
COMMENT ON COLUMN b2b_payments.period IS 'First-of-month date, e.g. 2026-03-01 for March 2026.';

SELECT '✅ 0020 crm_b2b_retainers complete' AS status;
