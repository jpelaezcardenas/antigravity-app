-- Migration 0027: b2b_clients contact + per-client tenant linkage
-- Date: 2026-07-20
-- Adds contact fields (email/phone/contact_name) and the linkage to each client's
-- OWN tenant (client_tenant_id) + login user (login_user_id) + provisioning state.
-- This enables per-client PWA logins that resolve to per-client Shadow GL data.
-- `tenant_id` stays = Cliente Cero (roster owner); `client_tenant_id` = the client's
-- own business tenant. Idempotent.

ALTER TABLE b2b_clients
  ADD COLUMN IF NOT EXISTS email text,
  ADD COLUMN IF NOT EXISTS phone text,
  ADD COLUMN IF NOT EXISTS contact_name text,
  ADD COLUMN IF NOT EXISTS client_tenant_id uuid REFERENCES tenants(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS login_user_id uuid,
  ADD COLUMN IF NOT EXISTS provision_status text NOT NULL DEFAULT 'not_provisioned';

ALTER TABLE b2b_clients DROP CONSTRAINT IF EXISTS chk_b2b_clients_provision_status;
ALTER TABLE b2b_clients
  ADD CONSTRAINT chk_b2b_clients_provision_status
  CHECK (provision_status IN ('not_provisioned', 'provisioned', 'pending_email'));

CREATE INDEX IF NOT EXISTS idx_b2b_clients_client_tenant ON b2b_clients (client_tenant_id);

COMMENT ON COLUMN b2b_clients.client_tenant_id IS 'The client''s OWN tenant (their business), distinct from tenant_id which is Cliente Cero (roster owner).';
COMMENT ON COLUMN b2b_clients.login_user_id IS 'auth.users.id of the provisioned end-user login for this client (null until provisioned).';
COMMENT ON COLUMN b2b_clients.provision_status IS 'not_provisioned | provisioned | pending_email (no email to create a login).';

SELECT '✅ 0027 b2b_clients_contact_and_tenant complete' AS status;
