-- Migration 0054: Drop legacy clients table
-- Date: 2026-09-23
--
-- Description:
-- Cleans up the obsolete 'clients' table which previously stored 3 synthetic demo clients
-- from May 2026 (TechStart, Consultoria Fiscal Lopez, Importaciones Martinez).
-- The active production client registry is public.b2b_clients (with public.b2b_payments).
-- Backup of the 3 legacy rows is archived at docs/archive/legacy_clients_backup.json.
--
-- Note on public.payments:
-- public.payments is NOT obsolete test data; it backs the live Wompi checkout for
-- "Crear tu empresa" ($1.200.000 COP) at contexia-wizard/lib/supabase/payments.ts.

-- Drop FK constraints from empty legacy tables that referenced clients(company_id)
ALTER TABLE IF EXISTS public.campaigns DROP CONSTRAINT IF EXISTS campaigns_company_id_fkey;
ALTER TABLE IF EXISTS public.alerts DROP CONSTRAINT IF EXISTS alerts_company_id_fkey;
ALTER TABLE IF EXISTS public.snapshots DROP CONSTRAINT IF EXISTS snapshots_company_id_fkey;

-- Drop the obsolete clients table
DROP TABLE IF EXISTS public.clients CASCADE;

SELECT '✅ 0054 drop_legacy_clients_table complete' AS status;
