-- Empresas + payments tables for "Crear Empresa" wizard
-- Created 2026-05-20 for the Wompi integration

CREATE TABLE IF NOT EXISTS empresas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
  razon_social TEXT NOT NULL,
  tipo_sociedad TEXT NOT NULL,
  descripcion TEXT,
  ciiu TEXT,
  ciudad TEXT,
  departamento TEXT,
  direccion TEXT,
  capital_total_cop BIGINT,
  capital_suscrito_pct INT,
  capital_pagado_pct INT,
  accionistas JSONB,
  representante_legal JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  reference TEXT UNIQUE NOT NULL,
  lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
  empresa_id UUID REFERENCES empresas(id) ON DELETE SET NULL,
  base_amount_cop INT NOT NULL,
  discount_cop INT NOT NULL DEFAULT 0,
  final_amount_cop INT NOT NULL,
  amount_cents INT NOT NULL,
  currency TEXT NOT NULL DEFAULT 'COP',
  coupon_code TEXT,
  status TEXT NOT NULL DEFAULT 'PENDING',
  payment_method TEXT,
  wompi_transaction_id TEXT,
  wompi_raw_response JSONB,
  customer_email TEXT,
  customer_phone TEXT,
  customer_name TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  approved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_payments_reference ON payments(reference);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_lead_id ON payments(lead_id);
