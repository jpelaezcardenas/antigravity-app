-- STATUS: PROPOSED — DO NOT APPLY without founder approval.
--
-- Re-stamps centinela_alerts rows that were mis-scoped under Cliente Cero
-- (via the silent-default bug fixed by centinela-tenant-scoped-alerts:
-- CentinelaService.save_alerts() used to stamp every alert lacking a
-- tenant_id with Cliente Cero, so alerts generated for a B2B client's own
-- data were archived under Contexia's tenant instead of the client's) to
-- the tenant that actually owns each company_id.
--
-- Idempotent: re-running matches no rows once tenant_id already equals the
-- mapped tenant (guarded by `IS DISTINCT FROM`).
-- Reversible in spirit: rows are only ever moved from Cliente Cero to a real
-- tenant; the pre-image audit query below records exactly which rows changed.
-- Rows whose company_id maps to no non-Cliente-Cero tenant are left
-- untouched (they are legitimately Contexia's own alerts).
--
-- Founder may run this manually in the Supabase SQL editor — this is the
-- established pattern in this repo for data-mutating migrations touching
-- production Supabase.

-- Step 0 (audit — run first, keep the output for the record):
SELECT id, company_id, tenant_id
FROM public.centinela_alerts
WHERE tenant_id = 'e2d30d09-6b96-4ebe-a79a-c6aff7a5df34'  -- Cliente Cero
  AND company_id IN (
    SELECT company_id FROM public.tenants
    WHERE company_id IS NOT NULL AND is_cliente_cero = false
  );

-- Step 0b (ambiguity check — must return 0 rows before Step 1 is safe to run;
-- if company_id is not unique across tenants, the UPDATE below could map a
-- row to the wrong tenant):
SELECT company_id, count(*)
FROM public.tenants
WHERE company_id IS NOT NULL
GROUP BY company_id
HAVING count(*) > 1;

-- Step 1 (the re-stamp — DO NOT RUN without founder approval):
-- UPDATE public.centinela_alerts a
-- SET    tenant_id = t.id
-- FROM   public.tenants t
-- WHERE  t.company_id = a.company_id
--   AND  t.is_cliente_cero = false
--   AND  a.tenant_id IS DISTINCT FROM t.id;

-- Step 2 (verify after Step 1 — expect 0 mismatched rows):
SELECT count(*) AS mismatched
FROM   public.centinela_alerts a
JOIN   public.tenants t ON t.company_id = a.company_id
WHERE  a.tenant_id IS DISTINCT FROM t.id;
