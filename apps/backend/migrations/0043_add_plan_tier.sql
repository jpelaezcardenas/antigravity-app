-- Migration 0043: plan_tier on tenants and b2b_clients
-- Date: 2026-08-28
-- Adds an enforced plan tier column (text + CHECK, not a Postgres ENUM — see
-- openspec/changes/plan-tier-feature-gating/design.md D1) to tenants (canonical
-- enforcement point) and b2b_clients (mirrored for CRM listing). Defaults every
-- existing and new row to 'starter' so no currently-provisioned client loses
-- access when this ships — only an explicit future write can set 'freemium'.

ALTER TABLE tenants
  ADD COLUMN IF NOT EXISTS plan_tier text NOT NULL DEFAULT 'starter';

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_tenants_plan_tier'
  ) THEN
    ALTER TABLE tenants
      ADD CONSTRAINT chk_tenants_plan_tier
      CHECK (plan_tier IN ('freemium', 'starter', 'growth', 'enterprise'));
  END IF;
END $$;

ALTER TABLE b2b_clients
  ADD COLUMN IF NOT EXISTS plan_tier text NOT NULL DEFAULT 'starter';

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_b2b_clients_plan_tier'
  ) THEN
    ALTER TABLE b2b_clients
      ADD CONSTRAINT chk_b2b_clients_plan_tier
      CHECK (plan_tier IN ('freemium', 'starter', 'growth', 'enterprise'));
  END IF;
END $$;

COMMENT ON COLUMN tenants.plan_tier IS 'Enforced plan tier gating PWA feature access (core/plan_features.py). Not the same as the unrelated, best-effort usuarios.plan column.';
COMMENT ON COLUMN b2b_clients.plan_tier IS 'Mirrors tenants.plan_tier for CRM listing (see plan-tier-feature-gating design.md).';

SELECT '✅ 0043 add_plan_tier complete' AS status;
