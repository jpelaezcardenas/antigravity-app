-- Migration 0030: Remove Nia Cano — never an actual Contexia client
-- Date: 2026-07-20
-- Nia Cano was present in the original manual-Excel-derived seed (migration 0021) and
-- received a per-client tenant + synthetic Shadow GL in migration 0028, but the founder
-- confirmed she was never actually a Contexia client. Removes her roster row, her own
-- tenant, her synthetic Shadow GL, and her payment history. She was never provisioned a
-- login (provision_status stayed 'pending_email', no email in the source ledger), so
-- there is no auth.users/user_tenants/user_roles/usuarios row to clean up.
-- Idempotent: safe to re-run (no-ops once she's gone).

DO $$
DECLARE
  v_client_id uuid;
  v_client_tenant_id uuid;
BEGIN
  SELECT id, client_tenant_id INTO v_client_id, v_client_tenant_id
  FROM b2b_clients WHERE name = 'Nia Cano';

  IF v_client_id IS NULL THEN
    RAISE NOTICE 'Nia Cano already removed, nothing to do.';
    RETURN;
  END IF;

  DELETE FROM erp_journal_lines WHERE tenant_id = v_client_tenant_id;
  DELETE FROM erp_journal_entries WHERE tenant_id = v_client_tenant_id;
  DELETE FROM b2b_payments WHERE client_id = v_client_id;
  DELETE FROM b2b_clients WHERE id = v_client_id;

  IF v_client_tenant_id IS NOT NULL THEN
    DELETE FROM tenants WHERE id = v_client_tenant_id;
  END IF;
END $$;

SELECT '✅ 0030 remove_nia_cano complete' AS status;
