-- Migration 0029: Provision Supabase Auth logins for B2B clients with a known email
-- Date: 2026-07-20
-- Creates one auth.users + auth.identities per client with an email (9 existing + CÓDIGO 520),
-- wires user_tenants/user_roles/usuarios to each client's OWN tenant (client_tenant_id from
-- migration 0028), and backfills b2b_clients.login_user_id/provision_status.
--
-- Nia Cano has no email in the source ledger and is intentionally skipped (provision_status
-- stays 'pending_email' from migration 0028).
--
-- SECURITY: no emails are sent. Each user gets a random temporary password (never a hardcoded
-- literal) which is surfaced ONCE via the final SELECT of this migration for the founder to
-- distribute manually; it is not stored anywhere in plaintext. Clients reset via the existing
-- reset-password.html flow. Idempotent: re-running skips clients that already have login_user_id.

CREATE TEMP TABLE IF NOT EXISTS provisioned_creds (name text, email text, temp_password text);

DO $$
DECLARE
  v_client record;
  v_user_id uuid;
  v_temp_password text;
BEGIN
  FOR v_client IN
    SELECT c.id AS client_id, c.name AS name, c.email AS email,
           c.client_tenant_id AS client_tenant_id, t.nit AS nit
    FROM b2b_clients c
    JOIN tenants t ON t.id = c.client_tenant_id
    WHERE c.email IS NOT NULL
      AND c.login_user_id IS NULL
  LOOP
    v_temp_password := 'Cx-' || substr(md5(random()::text || clock_timestamp()::text), 1, 10);
    v_user_id := gen_random_uuid();

    INSERT INTO auth.users (
      instance_id, id, aud, role, email, encrypted_password, email_confirmed_at,
      raw_app_meta_data, raw_user_meta_data, created_at, updated_at,
      confirmation_token, recovery_token, email_change_token_new, email_change,
      phone_change, phone_change_token, reauthentication_token, is_sso_user, is_anonymous
    ) VALUES (
      '00000000-0000-0000-0000-000000000000', v_user_id, 'authenticated', 'authenticated',
      v_client.email, crypt(v_temp_password, gen_salt('bf')), now(),
      jsonb_build_object('role', 'cliente', 'roles', jsonb_build_array('cliente'), 'provider', 'email', 'providers', jsonb_build_array('email')),
      jsonb_build_object('email', v_client.email, 'email_verified', true, 'phone_verified', false),
      now(), now(), '', '', '', '', '', '', '', false, false
    );

    -- `email` is a GENERATED column on auth.identities (derived from identity_data->>'email'),
    -- so it must not appear in the insert column list.
    INSERT INTO auth.identities (id, user_id, provider_id, provider, identity_data, created_at, updated_at)
    VALUES (
      gen_random_uuid(), v_user_id, v_user_id::text, 'email',
      jsonb_build_object('sub', v_user_id::text, 'email', v_client.email, 'email_verified', true),
      now(), now()
    );

    -- Legacy backend `usuarios` table: seeded for identity_resolver consistency only. This client
    -- never logs in via the demo/backend auth path; password_hash is an unrevealed random hash.
    INSERT INTO usuarios (id, email, nombre_empresa, nit, plan, password_hash)
    VALUES (v_user_id, v_client.email, v_client.name, v_client.nit, 'starter',
            crypt(gen_random_uuid()::text, gen_salt('bf')))
    ON CONFLICT (id) DO NOTHING;

    INSERT INTO user_tenants (user_id, tenant_id, is_owner, is_active)
    VALUES (v_user_id, v_client.client_tenant_id, true, true);

    INSERT INTO user_roles (user_id, tenant_id, role)
    VALUES (v_user_id, v_client.client_tenant_id, 'viewer');

    UPDATE b2b_clients
    SET login_user_id = v_user_id, provision_status = 'provisioned'
    WHERE id = v_client.client_id;

    INSERT INTO provisioned_creds (name, email, temp_password)
    VALUES (v_client.name, v_client.email, v_temp_password);
  END LOOP;
END $$;

SELECT * FROM provisioned_creds ORDER BY name;
