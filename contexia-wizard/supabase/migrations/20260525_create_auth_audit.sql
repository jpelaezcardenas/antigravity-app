-- Auth audit trail — every login attempt (success and failure) lands here.
-- Required by CLAUDE.md §2 (auditabilidad de operaciones que tocan acceso a datos fiscales).
-- Created 2026-05-25 as part of audit-login-2026-05-25 spec, T6.

CREATE TABLE IF NOT EXISTS auth_audit (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  email TEXT,                       -- normalized lowercase; null if request had no email field
  outcome TEXT NOT NULL,            -- 'success' | 'invalid_credentials' | 'not_authorized' | 'unknown_email' | 'rate_limited' | 'error'
  error_code TEXT,                  -- Supabase error code or our own (e.g. 'no_role_match')
  error_message TEXT,
  method TEXT NOT NULL,             -- 'password' | 'oauth_google' | 'oauth_microsoft'
  requested_role TEXT,              -- 'admin' | 'cliente' — what the toggle was set to (dual-role accounts)
  resolved_role TEXT,               -- role actually granted (null if outcome != 'success')
  destination TEXT,                 -- redirect target on success
  ip INET,                          -- caller IP (set from x-forwarded-for at endpoint)
  user_agent TEXT,
  CONSTRAINT auth_audit_outcome_check CHECK (outcome IN (
    'success', 'invalid_credentials', 'not_authorized', 'unknown_email', 'rate_limited', 'error'
  ))
);

CREATE INDEX IF NOT EXISTS idx_auth_audit_email_time ON auth_audit (email, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_auth_audit_outcome_time ON auth_audit (outcome, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_auth_audit_occurred_at ON auth_audit (occurred_at DESC);

-- Row-Level Security: nobody reads this from client. Only service_role (server-side endpoints)
-- can INSERT/SELECT. Frontend POSTs through an API route that uses service_role internally.
ALTER TABLE auth_audit ENABLE ROW LEVEL SECURITY;

-- No policies = no client access. service_role bypasses RLS by design.

COMMENT ON TABLE auth_audit IS
  'Login attempt audit trail. Inserted by /api/auth/audit-login (service_role). Never reads from anon/authenticated clients.';
