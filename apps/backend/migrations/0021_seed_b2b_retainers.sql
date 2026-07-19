-- Migration 0021: Seed B2B retainer clients + Jan-Jun 2026 payment ledger
-- Date: 2026-07-19
-- Idempotent: re-running upserts clients and payments without duplicating rows.
-- Note: Repuestos Don Alvaro's March amount is 1,200,000 COP (a source-data typo of
-- 12,000,000 has been corrected here — every other month for this client is 1,200,000).

DO $$
DECLARE
  v_tenant_id uuid;
BEGIN
  SELECT id INTO v_tenant_id FROM tenants WHERE is_cliente_cero = true LIMIT 1;

  IF v_tenant_id IS NULL THEN
    RAISE EXCEPTION 'No Cliente Cero tenant found; cannot seed b2b_clients/b2b_payments';
  END IF;

  INSERT INTO b2b_clients (tenant_id, name, status)
  VALUES
    (v_tenant_id, 'Repuestos Don Álvaro', 'activo'),
    (v_tenant_id, 'Medic', 'activo'),
    (v_tenant_id, 'Nia Cano', 'activo'),
    (v_tenant_id, 'Lavadero de Carros', 'activo'),
    (v_tenant_id, 'Carnicería Los López', 'activo'),
    (v_tenant_id, 'Ferez', 'activo'),
    (v_tenant_id, 'Variedades Carlos', 'activo'),
    (v_tenant_id, 'Surge', 'activo'),
    (v_tenant_id, 'Clinic Estetic', 'activo'),
    (v_tenant_id, 'Maderas y Maderas', 'activo')
  ON CONFLICT (tenant_id, name) DO UPDATE SET status = EXCLUDED.status;

  INSERT INTO b2b_payments (tenant_id, client_id, period, amount_cents)
  SELECT v_tenant_id, c.id, p.period::date, p.amount_cents
  FROM (VALUES
    ('Repuestos Don Álvaro', '2026-01-01', 120000000),
    ('Repuestos Don Álvaro', '2026-02-01', 120000000),
    ('Repuestos Don Álvaro', '2026-03-01', 120000000),
    ('Repuestos Don Álvaro', '2026-04-01', 120000000),
    ('Repuestos Don Álvaro', '2026-05-01', 120000000),
    ('Repuestos Don Álvaro', '2026-06-01', 0),

    ('Medic', '2026-01-01', 200000000),
    ('Medic', '2026-02-01', 200000000),
    ('Medic', '2026-03-01', 200000000),
    ('Medic', '2026-04-01', 200000000),
    ('Medic', '2026-05-01', 200000000),
    ('Medic', '2026-06-01', 200000000),

    ('Nia Cano', '2026-01-01', 0),
    ('Nia Cano', '2026-02-01', 0),
    ('Nia Cano', '2026-03-01', 60000000),
    ('Nia Cano', '2026-04-01', 0),
    ('Nia Cano', '2026-05-01', 0),
    ('Nia Cano', '2026-06-01', 0),

    ('Lavadero de Carros', '2026-01-01', 60000000),
    ('Lavadero de Carros', '2026-02-01', 60000000),
    ('Lavadero de Carros', '2026-03-01', 60000000),
    ('Lavadero de Carros', '2026-04-01', 60000000),
    ('Lavadero de Carros', '2026-05-01', 60000000),
    ('Lavadero de Carros', '2026-06-01', 60000000),

    ('Carnicería Los López', '2026-01-01', 0),
    ('Carnicería Los López', '2026-02-01', 0),
    ('Carnicería Los López', '2026-03-01', 200000000),
    ('Carnicería Los López', '2026-04-01', 200000000),
    ('Carnicería Los López', '2026-05-01', 200000000),
    ('Carnicería Los López', '2026-06-01', 0),

    ('Ferez', '2026-01-01', 0),
    ('Ferez', '2026-02-01', 0),
    ('Ferez', '2026-03-01', 89000000),
    ('Ferez', '2026-04-01', 89000000),
    ('Ferez', '2026-05-01', 89000000),
    ('Ferez', '2026-06-01', 89000000),

    ('Variedades Carlos', '2026-01-01', 0),
    ('Variedades Carlos', '2026-02-01', 0),
    ('Variedades Carlos', '2026-03-01', 89000000),
    ('Variedades Carlos', '2026-04-01', 89000000),
    ('Variedades Carlos', '2026-05-01', 89000000),
    ('Variedades Carlos', '2026-06-01', 89000000),

    ('Surge', '2026-01-01', 0),
    ('Surge', '2026-02-01', 0),
    ('Surge', '2026-03-01', 0),
    ('Surge', '2026-04-01', 0),
    ('Surge', '2026-05-01', 40000000),
    ('Surge', '2026-06-01', 0),

    ('Clinic Estetic', '2026-01-01', 0),
    ('Clinic Estetic', '2026-02-01', 0),
    ('Clinic Estetic', '2026-03-01', 0),
    ('Clinic Estetic', '2026-04-01', 0),
    ('Clinic Estetic', '2026-05-01', 40000000),
    ('Clinic Estetic', '2026-06-01', 0),

    ('Maderas y Maderas', '2026-01-01', 0),
    ('Maderas y Maderas', '2026-02-01', 0),
    ('Maderas y Maderas', '2026-03-01', 0),
    ('Maderas y Maderas', '2026-04-01', 0),
    ('Maderas y Maderas', '2026-05-01', 120000000),
    ('Maderas y Maderas', '2026-06-01', 0)
  ) AS p(client_name, period, amount_cents)
  JOIN b2b_clients c ON c.tenant_id = v_tenant_id AND c.name = p.client_name
  ON CONFLICT (client_id, period) DO UPDATE SET amount_cents = EXCLUDED.amount_cents;
END $$;

SELECT '✅ 0021 seed_b2b_retainers complete' AS status;
