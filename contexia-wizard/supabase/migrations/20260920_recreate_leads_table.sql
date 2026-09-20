-- Migration: Recreate public.leads
-- Date: 2026-09-20
--
-- Restores the table app/api/leads/save/route.ts has always queried.
-- Confirmed missing 2026-09-20 (openspec/changes/wizard-iva-ecom-express-diagnostic):
-- every call to POST /wizard/api/leads/save returns 500 with
-- "Could not find the table 'public.leads' in the schema cache". This affects
-- BOTH the existing 8-step Shadow Audit flow's lead capture (Step 1 auto-save,
-- every subsequent step's re-save) and the new 3-step iva-ecom flow's optional
-- email field.
--
-- Column shape reverse-engineered from the only two sources of truth that
-- still reference it: route.ts's upsert payload, and the one surviving
-- migration that ALTERed it (20260616_add_feria_lead_fields.sql, which this
-- migration folds in directly rather than relying on running after this one).
--
-- Deliberately NOT touching crm_leads (different table, different funnel,
-- different RLS/Kanban semantics -- see design.md D7 in the change above for
-- why bridging the two was considered and rejected for this fix).

CREATE TABLE IF NOT EXISTS leads (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre text,
  cedula text,
  email text NOT NULL,
  whatsapp text,
  ciudad text,
  rol text,
  ip_address text,
  user_agent text,
  referrer text,
  status text DEFAULT 'contacted',
  source text,
  metadata jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_leads_email UNIQUE (email)
);

CREATE INDEX IF NOT EXISTS idx_leads_source ON leads (source);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads (created_at);

-- updated_at trigger, same pattern as antigravity-app's crm tables.
CREATE OR REPLACE FUNCTION update_leads_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_leads_updated_at ON leads;
CREATE TRIGGER trg_leads_updated_at
  BEFORE UPDATE ON leads
  FOR EACH ROW
  EXECUTE FUNCTION update_leads_updated_at();

-- RLS: this table is written by the wizard's server-side route using the
-- service-role client (supabaseAdmin in lib/supabase.ts), which bypasses RLS
-- entirely -- so RLS here is a defense-in-depth backstop against the anon key
-- (used client-side elsewhere in this app) ever being able to read or write
-- real leads directly, not the primary access control.
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS leads_no_anon_access ON leads;
CREATE POLICY leads_no_anon_access ON leads
  FOR ALL
  USING (false)
  WITH CHECK (false);

COMMENT ON TABLE leads IS 'contexia-wizard lead capture (both the 8-step Shadow Audit flow and the 3-step iva-ecom flow). Written exclusively via the service-role client in app/api/leads/save/route.ts. Recreated 2026-09-20 after being found missing in production -- see openspec/changes/wizard-iva-ecom-express-diagnostic.';

SELECT '✅ 20260920_recreate_leads_table complete' AS status;
