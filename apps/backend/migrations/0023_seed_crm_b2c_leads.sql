-- Migration 0023: Seed sample B2C Renta Natural leads across all 4 funnel stages
-- Date: 2026-07-19
-- All names/phones/references are obvious placeholders (SEED- prefix) so they can never be
-- mistaken for real lead or payment activity. Idempotent: re-running upserts without duplicating.

DO $$
DECLARE
  v_tenant_id uuid;
  v_lead_maria uuid;
  v_lead_carlos uuid;
  v_lead_ana uuid;
  v_lead_pedro uuid;
BEGIN
  SELECT id INTO v_tenant_id FROM tenants WHERE is_cliente_cero = true LIMIT 1;

  IF v_tenant_id IS NULL THEN
    RAISE EXCEPTION 'No Cliente Cero tenant found; cannot seed crm_leads';
  END IF;

  -- NUEVOS
  INSERT INTO crm_leads (tenant_id, full_name, whatsapp_phone, email, stage, source, last_message, score)
  VALUES (v_tenant_id, 'Maria SEED (Nuevos)', 'SEED-WA-001', 'maria.seed@example.com', 'NUEVOS', 'whatsapp', 'Hola, vi el anuncio sobre declarar renta', 10)
  ON CONFLICT (tenant_id, whatsapp_phone) DO UPDATE SET stage = EXCLUDED.stage, full_name = EXCLUDED.full_name
  RETURNING id INTO v_lead_maria;

  -- PROSPECTOS
  INSERT INTO crm_leads (tenant_id, full_name, whatsapp_phone, email, stage, source, last_message, score)
  VALUES (v_tenant_id, 'Carlos SEED (Prospectos)', 'SEED-WA-002', 'carlos.seed@example.com', 'PROSPECTOS', 'whatsapp', 'Ya me enviaron el link de pago', 40)
  ON CONFLICT (tenant_id, whatsapp_phone) DO UPDATE SET stage = EXCLUDED.stage, full_name = EXCLUDED.full_name
  RETURNING id INTO v_lead_carlos;

  -- POR_APROBAR
  INSERT INTO crm_leads (tenant_id, full_name, whatsapp_phone, email, stage, source, last_message, score)
  VALUES (v_tenant_id, 'Ana SEED (Por Aprobar)', 'SEED-WA-003', 'ana.seed@example.com', 'POR_APROBAR', 'whatsapp', 'Ya pague, aqui esta el comprobante', 75)
  ON CONFLICT (tenant_id, whatsapp_phone) DO UPDATE SET stage = EXCLUDED.stage, full_name = EXCLUDED.full_name
  RETURNING id INTO v_lead_ana;

  -- LISTOS_CONTADORA
  INSERT INTO crm_leads (tenant_id, full_name, whatsapp_phone, email, stage, source, last_message, score)
  VALUES (v_tenant_id, 'Pedro SEED (Listos Contadora)', 'SEED-WA-004', 'pedro.seed@example.com', 'LISTOS_CONTADORA', 'whatsapp', 'Ya envie el RUT y los extractos', 95)
  ON CONFLICT (tenant_id, whatsapp_phone) DO UPDATE SET stage = EXCLUDED.stage, full_name = EXCLUDED.full_name
  RETURNING id INTO v_lead_pedro;

  -- Tax profiles: one per lead (idempotent upsert on lead_id)
  INSERT INTO crm_tax_profiles (tenant_id, lead_id, es_asalariado, topes, rut_status, extractos_status, obligado_declarar)
  VALUES
    (v_tenant_id, v_lead_maria, NULL, '{}'::jsonb, 'pending', 'pending', NULL),
    (v_tenant_id, v_lead_carlos, true, '{"ingresos_uvt": 1200}'::jsonb, 'pending', 'pending', true),
    (v_tenant_id, v_lead_ana, true, '{"ingresos_uvt": 1450}'::jsonb, 'pending', 'pending', true),
    (v_tenant_id, v_lead_pedro, false, '{"patrimonio_uvt": 4600}'::jsonb, 'collected', 'collected', true)
  ON CONFLICT (lead_id) DO UPDATE SET
    es_asalariado = EXCLUDED.es_asalariado,
    topes = EXCLUDED.topes,
    rut_status = EXCLUDED.rut_status,
    extractos_status = EXCLUDED.extractos_status,
    obligado_declarar = EXCLUDED.obligado_declarar;

  -- A pending Wompi transaction for the POR_APROBAR lead (obviously-fake reference)
  INSERT INTO crm_wompi_transactions (
    tenant_id, lead_id, reference, amount_cents, status, customer_email, customer_phone, customer_name
  )
  VALUES (
    v_tenant_id, v_lead_ana, 'SEED-REF-POR-APROBAR-001', 8900000, 'PENDING',
    'ana.seed@example.com', 'SEED-WA-003', 'Ana SEED (Por Aprobar)'
  )
  ON CONFLICT (reference) DO UPDATE SET status = EXCLUDED.status;

  -- An already-approved Wompi transaction for the LISTOS_CONTADORA lead (consistent history)
  INSERT INTO crm_wompi_transactions (
    tenant_id, lead_id, reference, amount_cents, status, customer_email, customer_phone, customer_name,
    approved_by, approved_at
  )
  VALUES (
    v_tenant_id, v_lead_pedro, 'SEED-REF-LISTOS-001', 8900000, 'APPROVED',
    'pedro.seed@example.com', 'SEED-WA-004', 'Pedro SEED (Listos Contadora)',
    'seed-migration', now()
  )
  ON CONFLICT (reference) DO UPDATE SET status = EXCLUDED.status;
END $$;

SELECT '✅ 0023 seed_crm_b2c_leads complete' AS status;
