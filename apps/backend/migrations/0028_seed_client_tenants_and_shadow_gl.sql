-- Migration 0028: Per-client tenants + distinct synthetic Shadow GL + CÓDIGO 520
-- Date: 2026-07-20
-- Creates one OWN tenant per B2B retainer client (+ new client CÓDIGO 520, not yet paying),
-- backfills b2b_clients contact/linkage from the source ledger (Excel), and seeds distinct
-- synthetic Shadow GL per client tenant so GET /api/v1/financials returns a materially
-- different Caja Real per client once financials_endpoints becomes tenant-aware (0029/backend).
--
-- All synthetic journal rows are tagged via `memo` prefix 'SYNTH:per-tenant-client-access' so
-- they are identifiable and reversible without touching real Cliente Cero data.
-- Idempotent: re-running upserts tenants/contact fields; re-seeding journals is guarded by
-- external_reference_id uniqueness per client.

DO $$
DECLARE
  v_client record;
  v_tenant_id uuid;
  v_entry_id uuid;
  v_ext_prefix text;
BEGIN
  -- (name, nit, email, phone, contact_name, opening_cents, venta_ayer_cents, gasto_ayer_cents)
  FOR v_client IN
    SELECT * FROM (VALUES
      ('Repuestos Don Álvaro', 'SYN-900100001', 'repuestosdonalvaro@gmail.com', '3156511210', 'Repuestos Don Álvaro', 850000000::bigint, 45000000::bigint, 18000000::bigint),
      ('Medic',                 'SYN-900100002', 'gabi.medic@gmail.com',        '3155654430', 'Gabi (Medic)',         2200000000::bigint, 120000000::bigint, 60000000::bigint),
      ('Nia Cano',              'SYN-900100003', NULL,                          NULL,          'Nia Cano',             180000000::bigint,  9000000::bigint,  4000000::bigint),
      ('Lavadero de Carros',    'SYN-900100004', 'cesaralvaro71@gmail.com',      '3233729587', 'César (Lavadero)',     320000000::bigint,  21000000::bigint, 9500000::bigint),
      ('Carnicería Los López',  'SYN-900100005', 'carnicerialoslopez@gmail.com', '3188860723', 'Carnicería Los López', 640000000::bigint,  70000000::bigint, 38000000::bigint),
      ('Ferez',                 'SYN-900100006', 'federicogutierrez.96@gmail.com', '3182543988', 'Federico Gutiérrez', 410000000::bigint,  32000000::bigint, 15000000::bigint),
      ('Variedades Carlos',     'SYN-900100007', 'variedadescarlos65@gmail.com', '3042023846', 'Variedades Carlos',    290000000::bigint,  18000000::bigint, 9000000::bigint),
      ('Surge',                 'SYN-900100008', 'surgeenergycol@gmail.com',     '3008051789', 'Surge Energy',         95000000::bigint,   6000000::bigint,  3000000::bigint),
      ('Clinic Estetic',        'SYN-900100009', 'portia.daniela@gmail.com',     '3044536603', 'Daniela (Clinic Estetic)', 530000000::bigint, 40000000::bigint, 21000000::bigint),
      ('Maderas y Maderas',     'SYN-900100010', 'paula.2026@gmail.com',         '3017373074', 'Paula (Maderas y Maderas)', 760000000::bigint, 52000000::bigint, 26000000::bigint)
    ) AS t(name, nit, email, phone, contact_name, opening_cents, venta_ayer_cents, gasto_ayer_cents)
  LOOP
    -- 1. Create (or reuse) the client's OWN tenant
    INSERT INTO tenants (nit, legal_name, is_cliente_cero)
    VALUES (v_client.nit, v_client.name, false)
    ON CONFLICT (nit) DO UPDATE SET legal_name = EXCLUDED.legal_name
    RETURNING id INTO v_tenant_id;

    -- 2. Backfill b2b_clients contact + linkage (matched by name within Cliente Cero roster)
    UPDATE b2b_clients
    SET email = v_client.email,
        phone = v_client.phone,
        contact_name = v_client.contact_name,
        client_tenant_id = v_tenant_id,
        provision_status = CASE WHEN v_client.email IS NULL THEN 'pending_email' ELSE provision_status END
    WHERE name = v_client.name
      AND tenant_id = (SELECT id FROM tenants WHERE is_cliente_cero = true LIMIT 1);

    -- 3. Seed distinct synthetic Shadow GL for this client's OWN tenant (skip if already seeded)
    v_ext_prefix := 'SYNTH-' || v_client.nit;

    IF NOT EXISTS (
      SELECT 1 FROM erp_journal_entries
      WHERE tenant_id = v_tenant_id AND external_reference_id = v_ext_prefix || '-OPEN'
    ) THEN
      -- Opening balance (~180 days ago): Dr 1110 (Bancos) / Cr 3105 (Capital)
      INSERT INTO erp_journal_entries (tenant_id, memo, entry_date, source, external_reference_id)
      VALUES (v_tenant_id, 'SYNTH:per-tenant-client-access opening balance — ' || v_client.name,
              CURRENT_DATE - INTERVAL '180 days', 'manual', v_ext_prefix || '-OPEN')
      RETURNING id INTO v_entry_id;

      INSERT INTO erp_journal_lines (entry_id, tenant_id, account_code, debit_minor, credit_minor, memo)
      VALUES
        (v_entry_id, v_tenant_id, '1110', v_client.opening_cents, 0, 'Saldo inicial sintético'),
        (v_entry_id, v_tenant_id, '3105', 0, v_client.opening_cents, 'Capital — saldo inicial sintético');

      -- "Yesterday" sale (only if the client has any sales — CÓDIGO 520 has none, handled below)
      IF v_client.venta_ayer_cents > 0 THEN
        INSERT INTO erp_journal_entries (tenant_id, memo, entry_date, source, external_reference_id)
        VALUES (v_tenant_id, 'SYNTH:per-tenant-client-access venta de ayer — ' || v_client.name,
                CURRENT_DATE - INTERVAL '1 day', 'manual', v_ext_prefix || '-SALE')
        RETURNING id INTO v_entry_id;

        INSERT INTO erp_journal_lines (entry_id, tenant_id, account_code, debit_minor, credit_minor, memo)
        VALUES
          (v_entry_id, v_tenant_id, '1110', v_client.venta_ayer_cents, 0, 'Venta de ayer sintética'),
          (v_entry_id, v_tenant_id, '4105', 0, v_client.venta_ayer_cents, 'Ingreso operacional sintético');
      END IF;

      -- "Yesterday" expense
      IF v_client.gasto_ayer_cents > 0 THEN
        INSERT INTO erp_journal_entries (tenant_id, memo, entry_date, source, external_reference_id)
        VALUES (v_tenant_id, 'SYNTH:per-tenant-client-access gasto de ayer — ' || v_client.name,
                CURRENT_DATE - INTERVAL '1 day', 'manual', v_ext_prefix || '-EXPENSE')
        RETURNING id INTO v_entry_id;

        INSERT INTO erp_journal_lines (entry_id, tenant_id, account_code, debit_minor, credit_minor, memo)
        VALUES
          (v_entry_id, v_tenant_id, '5135', v_client.gasto_ayer_cents, 0, 'Gasto operacional sintético'),
          (v_entry_id, v_tenant_id, '1110', 0, v_client.gasto_ayer_cents, 'Gasto operacional sintético');
      END IF;
    END IF;
  END LOOP;

  -- CÓDIGO 520: new prospective client, NOT YET PAYING — thin cash, an expense, no sales.
  INSERT INTO tenants (nit, legal_name, is_cliente_cero)
  VALUES ('SYN-900100011', 'CÓDIGO 520', false)
  ON CONFLICT (nit) DO UPDATE SET legal_name = EXCLUDED.legal_name
  RETURNING id INTO v_tenant_id;

  INSERT INTO b2b_clients (tenant_id, name, status, email, phone, contact_name, client_tenant_id, provision_status)
  VALUES (
    (SELECT id FROM tenants WHERE is_cliente_cero = true LIMIT 1),
    'CÓDIGO 520', 'inactivo', 'paulaandrea@gmail.com', '3148140882', 'Paula Andrea',
    v_tenant_id, 'not_provisioned'
  )
  ON CONFLICT (tenant_id, name) DO UPDATE SET
    email = EXCLUDED.email, phone = EXCLUDED.phone, contact_name = EXCLUDED.contact_name,
    client_tenant_id = EXCLUDED.client_tenant_id;

  IF NOT EXISTS (
    SELECT 1 FROM erp_journal_entries
    WHERE tenant_id = v_tenant_id AND external_reference_id = 'SYNTH-SYN-900100011-OPEN'
  ) THEN
    INSERT INTO erp_journal_entries (tenant_id, memo, entry_date, source, external_reference_id)
    VALUES (v_tenant_id, 'SYNTH:per-tenant-client-access opening balance — CÓDIGO 520',
            CURRENT_DATE - INTERVAL '30 days', 'manual', 'SYNTH-SYN-900100011-OPEN')
    RETURNING id INTO v_entry_id;

    INSERT INTO erp_journal_lines (entry_id, tenant_id, account_code, debit_minor, credit_minor, memo)
    VALUES
      (v_entry_id, v_tenant_id, '1110', 35000000, 0, 'Saldo inicial sintético — sin pago a Contexia aún'),
      (v_entry_id, v_tenant_id, '3105', 0, 35000000, 'Capital — saldo inicial sintético');

    INSERT INTO erp_journal_entries (tenant_id, memo, entry_date, source, external_reference_id)
    VALUES (v_tenant_id, 'SYNTH:per-tenant-client-access gasto de ayer — CÓDIGO 520',
            CURRENT_DATE - INTERVAL '1 day', 'manual', 'SYNTH-SYN-900100011-EXPENSE')
    RETURNING id INTO v_entry_id;

    INSERT INTO erp_journal_lines (entry_id, tenant_id, account_code, debit_minor, credit_minor, memo)
    VALUES
      (v_entry_id, v_tenant_id, '5135', 6000000, 0, 'Gasto operacional sintético'),
      (v_entry_id, v_tenant_id, '1110', 0, 6000000, 'Gasto operacional sintético');
  END IF;
END $$;

SELECT '✅ 0028 seed_client_tenants_and_shadow_gl complete' AS status;
