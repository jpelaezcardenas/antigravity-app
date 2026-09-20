-- Migration: Recreate public.empresas and public.payments
-- Date: 2026-09-20
--
-- URGENT: these tables back the LIVE, actively-marketed "Crear tu empresa"
-- product ($1.200.000, "Lanzamiento" pricing) at contexia.online/crear-empresa-wizard
-- (contexia-app/app/crear-empresa-wizard/), whose payment step calls
-- POST /wizard/api/payments/create-transaction (contexia-wizard/app/api/payments/
-- create-transaction/route.ts -> lib/supabase/payments.ts -> .from("empresas")/
-- .from("payments")). Confirmed missing 2026-09-20 via PostgREST probing
-- (404 on both) during openspec/changes/wizard-iva-ecom-express-diagnostic --
-- every real customer attempting to pay through this live flow hits a 500
-- right now. This migration restores exactly what lib/supabase/payments.ts
-- and app/api/payments/webhook/route.ts already read/write; it does not
-- change any application code.
--
-- Column shapes are reverse-engineered from three still-live sources of
-- truth: lib/supabase/payments.ts (createEmpresa/createPayment/
-- updatePaymentStatus/getPaymentByReference), the webhook handler's read of
-- empresas.*, and the one surviving migration that originally created these
-- tables (20260520_create_payments.sql) -- reapplied here as IF NOT EXISTS
-- rather than assumed still applied, since it clearly wasn't.
--
-- Depends on public.leads existing first (empresas.lead_id and
-- payments.lead_id both FK-reference it) -- run
-- 20260920_recreate_leads_table.sql before this one.

CREATE TABLE IF NOT EXISTS empresas (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id uuid REFERENCES leads(id) ON DELETE SET NULL,
  razon_social text NOT NULL,
  tipo_sociedad text NOT NULL,
  descripcion text,
  ciiu text,
  ciudad text,
  departamento text,
  direccion text,
  capital_total_cop bigint,
  capital_suscrito_pct int,
  capital_pagado_pct int,
  accionistas jsonb,
  representante_legal jsonb,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS payments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  reference text UNIQUE NOT NULL,
  lead_id uuid REFERENCES leads(id) ON DELETE SET NULL,
  empresa_id uuid REFERENCES empresas(id) ON DELETE SET NULL,
  base_amount_cop int NOT NULL,
  discount_cop int NOT NULL DEFAULT 0,
  final_amount_cop int NOT NULL,
  amount_cents int NOT NULL,
  currency text NOT NULL DEFAULT 'COP',
  coupon_code text,
  status text NOT NULL DEFAULT 'PENDING',
  payment_method text,
  wompi_transaction_id text,
  wompi_raw_response jsonb,
  customer_email text,
  customer_phone text,
  customer_name text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  approved_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_payments_reference ON payments(reference);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_lead_id ON payments(lead_id);
CREATE INDEX IF NOT EXISTS idx_empresas_lead_id ON empresas(lead_id);

-- RLS: same defense-in-depth posture as leads (20260920_recreate_leads_table.sql)
-- -- all real access is through the service-role client
-- (supabaseAdmin in lib/supabase.ts), which bypasses RLS. This blocks the
-- anon key (used client-side elsewhere in this app) from ever reading or
-- writing real company/payment records directly.
ALTER TABLE empresas ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS empresas_no_anon_access ON empresas;
CREATE POLICY empresas_no_anon_access ON empresas
  FOR ALL
  USING (false)
  WITH CHECK (false);

DROP POLICY IF EXISTS payments_no_anon_access ON payments;
CREATE POLICY payments_no_anon_access ON payments
  FOR ALL
  USING (false)
  WITH CHECK (false);

COMMENT ON TABLE empresas IS 'Company-incorporation records from the live "Crear tu empresa" product ($1.200.000, contexia-app/app/crear-empresa-wizard/). Written exclusively via the service-role client in contexia-wizard/app/api/payments/create-transaction. Recreated 2026-09-20 after being found missing in production.';
COMMENT ON TABLE payments IS 'Wompi transaction records for the "Crear tu empresa" product. Status transitions (PENDING -> APPROVED/DECLINED) are driven by contexia-wizard/app/api/payments/webhook, signature-verified. Recreated 2026-09-20 after being found missing in production -- every real payment attempt was failing before this fix.';

SELECT '✅ 20260920_recreate_empresas_payments_tables complete' AS status;
