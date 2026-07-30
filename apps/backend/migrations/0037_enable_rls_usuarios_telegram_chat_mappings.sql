-- Migration: Enable RLS on `usuarios` and `telegram_chat_mappings`, with no policy.
-- Date: 2026-07-30
-- Purpose: Supabase advisory flagged both tables as fully exposed to anon/authenticated — RLS
-- was disabled entirely, so anyone with the project's anon key could read or write every row.
-- `usuarios` holds login credentials (password_hash) and business identifiers (nit);
-- `telegram_chat_mappings` links an external Telegram chat id to an internal company id.
--
-- This is safe to enable with ZERO policies (no anon/authenticated access at all) because every
-- current reader in the codebase was audited and migrated to the service-role client, which
-- bypasses RLS deliberately and explicitly (core/supabase_client.py::get_service_supabase):
--   - usuarios: infrastructure/repositories/usuario_repo.py (login fallback path, reachable
--     whenever DEMO_AUTH_ENABLED=False), core/identity_resolver.py, services/crm_service.py,
--     scripts/seed_demo_clients.py (all already on or migrated to service-role in this change).
--   - telegram_chat_mappings: presentation/telegram_endpoints.py's one query against this table
--     (migrated to service-role in this change; its separate `tenants` lookup is untouched and
--     keeps using the anon client, since `tenants` already has its own permissive policy).
--
-- Change: rls-hardening-usuarios-telegram (no OpenSpec change directory — a security remediation
-- of the same shape and size as the whatsapp_inbound_events RLS pattern in migration 0036).
-- Idempotent: Can be run multiple times safely.
-- Prerequisites: none — enables RLS on two existing tables, creates no new objects.

ALTER TABLE public.usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.telegram_chat_mappings ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE public.usuarios IS
    'RLS enabled, no policy (2026-07-30) — anon/authenticated have zero access. All reads go '
    'through the service-role client (see usuario_repo.py, identity_resolver.py, crm_service.py).';

COMMENT ON TABLE public.telegram_chat_mappings IS
    'RLS enabled, no policy (2026-07-30) — anon/authenticated have zero access. The one reader '
    '(telegram_endpoints.py) uses the service-role client.';
