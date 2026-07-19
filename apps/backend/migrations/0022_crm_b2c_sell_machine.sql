-- Migration 0022: CRM B2C sell-machine cockpit (Renta Natural 2026 funnel)
-- Date: 2026-07-19
-- Adds crm_leads (4-stage Kanban funnel), crm_tax_profiles (1:1 Taty memory),
-- and crm_wompi_transactions (payment record shape, seeded/simulated only in this change).
-- Tenant-scoped to Cliente Cero, admin-only RLS using the live role_type enum
-- (verified: admin | finance | marketing | growth | operator | viewer).

CREATE TABLE IF NOT EXISTS crm_leads (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  full_name text,
  whatsapp_phone text,
  email text,
  stage text NOT NULL DEFAULT 'NUEVOS',
  source text DEFAULT 'whatsapp',
  last_message text,
  score integer DEFAULT 0,
  assigned_agent text DEFAULT 'taty',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_crm_leads_tenant_phone UNIQUE (tenant_id, whatsapp_phone),
  CONSTRAINT chk_crm_leads_stage CHECK (stage IN ('NUEVOS', 'PROSPECTOS', 'POR_APROBAR', 'LISTOS_CONTADORA'))
);

CREATE TABLE IF NOT EXISTS crm_tax_profiles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  lead_id uuid NOT NULL REFERENCES crm_leads(id) ON DELETE CASCADE,
  es_asalariado boolean,
  topes jsonb DEFAULT '{}'::jsonb,
  rut_status text DEFAULT 'pending',
  extractos_status text DEFAULT 'pending',
  obligado_declarar boolean,
  notes text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_crm_tax_profiles_lead UNIQUE (lead_id),
  CONSTRAINT chk_crm_tax_profiles_rut_status CHECK (rut_status IN ('pending', 'collected')),
  CONSTRAINT chk_crm_tax_profiles_extractos_status CHECK (extractos_status IN ('pending', 'collected'))
);

CREATE TABLE IF NOT EXISTS crm_wompi_transactions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  lead_id uuid REFERENCES crm_leads(id) ON DELETE SET NULL,
  reference text NOT NULL,
  amount_cents bigint NOT NULL,
  currency text NOT NULL DEFAULT 'COP',
  status text NOT NULL DEFAULT 'PENDING',
  wompi_transaction_id text,
  wompi_raw_response jsonb,
  customer_email text,
  customer_phone text,
  customer_name text,
  approved_by text,
  approved_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_crm_wompi_transactions_reference UNIQUE (reference),
  CONSTRAINT chk_crm_wompi_transactions_status CHECK (status IN ('PENDING', 'APPROVED', 'DECLINED'))
);

CREATE INDEX IF NOT EXISTS idx_crm_leads_tenant_stage ON crm_leads (tenant_id, stage);
CREATE INDEX IF NOT EXISTS idx_crm_tax_profiles_tenant ON crm_tax_profiles (tenant_id);
CREATE INDEX IF NOT EXISTS idx_crm_wompi_transactions_lead ON crm_wompi_transactions (lead_id);
CREATE INDEX IF NOT EXISTS idx_crm_wompi_transactions_tenant_status ON crm_wompi_transactions (tenant_id, status);

-- updated_at triggers (reuse the function from 0020_crm_b2b_retainers.sql)
DROP TRIGGER IF EXISTS trg_crm_leads_updated_at ON crm_leads;
CREATE TRIGGER trg_crm_leads_updated_at
  BEFORE UPDATE ON crm_leads
  FOR EACH ROW
  EXECUTE FUNCTION update_crm_b2b_updated_at();

DROP TRIGGER IF EXISTS trg_crm_tax_profiles_updated_at ON crm_tax_profiles;
CREATE TRIGGER trg_crm_tax_profiles_updated_at
  BEFORE UPDATE ON crm_tax_profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_crm_b2b_updated_at();

DROP TRIGGER IF EXISTS trg_crm_wompi_transactions_updated_at ON crm_wompi_transactions;
CREATE TRIGGER trg_crm_wompi_transactions_updated_at
  BEFORE UPDATE ON crm_wompi_transactions
  FOR EACH ROW
  EXECUTE FUNCTION update_crm_b2b_updated_at();

-- Row Level Security: admin-only, using the live role_type enum (role = 'admin').
ALTER TABLE crm_leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE crm_tax_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE crm_wompi_transactions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS crm_leads_admin_only ON crm_leads;
CREATE POLICY crm_leads_admin_only ON crm_leads
  FOR ALL
  USING (
    auth.uid() IN (
      SELECT user_id FROM user_roles
      WHERE tenant_id = crm_leads.tenant_id
      AND role = 'admin'
    )
  )
  WITH CHECK (
    auth.uid() IN (
      SELECT user_id FROM user_roles
      WHERE tenant_id = crm_leads.tenant_id
      AND role = 'admin'
    )
  );

DROP POLICY IF EXISTS crm_tax_profiles_admin_only ON crm_tax_profiles;
CREATE POLICY crm_tax_profiles_admin_only ON crm_tax_profiles
  FOR ALL
  USING (
    auth.uid() IN (
      SELECT user_id FROM user_roles
      WHERE tenant_id = crm_tax_profiles.tenant_id
      AND role = 'admin'
    )
  )
  WITH CHECK (
    auth.uid() IN (
      SELECT user_id FROM user_roles
      WHERE tenant_id = crm_tax_profiles.tenant_id
      AND role = 'admin'
    )
  );

DROP POLICY IF EXISTS crm_wompi_transactions_admin_only ON crm_wompi_transactions;
CREATE POLICY crm_wompi_transactions_admin_only ON crm_wompi_transactions
  FOR ALL
  USING (
    auth.uid() IN (
      SELECT user_id FROM user_roles
      WHERE tenant_id = crm_wompi_transactions.tenant_id
      AND role = 'admin'
    )
  )
  WITH CHECK (
    auth.uid() IN (
      SELECT user_id FROM user_roles
      WHERE tenant_id = crm_wompi_transactions.tenant_id
      AND role = 'admin'
    )
  );

COMMENT ON TABLE crm_leads IS 'B2C Renta Natural 2026 lead funnel: NUEVOS -> PROSPECTOS -> POR_APROBAR -> LISTOS_CONTADORA.';
COMMENT ON TABLE crm_tax_profiles IS 'Per-lead tax-profile memory (Taty), 1:1 with crm_leads.';
COMMENT ON TABLE crm_wompi_transactions IS 'Payment record shape mirroring the wizard payments table. Seeded/simulated only until Change C wires real Wompi verification.';

SELECT '✅ 0022 crm_b2c_sell_machine complete' AS status;
