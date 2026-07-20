-- Migration 0026: crm-tax-documents Storage bucket + crm_tax_profiles storage-path columns
-- (taty-document-collection, Change I)
-- Date: 2026-07-20
-- First Storage-bucket migration in this repo. Private bucket for RUT/extractos documents
-- collected by Taty via WhatsApp; admin-only RLS on storage.objects, matching the same
-- role='admin' pattern used by every table RLS policy in this repo. Single-tenant simplification:
-- unlike table RLS (which joins on tenant_id), storage.objects has no tenant_id column, so this
-- policy checks admin role without a tenant join — acceptable since only Cliente Cero uses this
-- bucket today.

ALTER TABLE crm_tax_profiles ADD COLUMN IF NOT EXISTS rut_storage_path text;
ALTER TABLE crm_tax_profiles ADD COLUMN IF NOT EXISTS extractos_storage_path text;

-- The live rut_status/extractos_status CHECK constraints only allowed ('pending','collected')
-- (discovered live during Stage 8 DB verification — not visible from information_schema.columns
-- alone). Extended here to add 'requested' as the collection-in-progress state, keeping
-- 'collected' as the terminal state (reusing existing seeded-data vocabulary rather than
-- inventing 'received').
ALTER TABLE crm_tax_profiles DROP CONSTRAINT IF EXISTS chk_crm_tax_profiles_rut_status;
ALTER TABLE crm_tax_profiles ADD CONSTRAINT chk_crm_tax_profiles_rut_status
  CHECK (rut_status = ANY (ARRAY['pending'::text, 'requested'::text, 'collected'::text]));

ALTER TABLE crm_tax_profiles DROP CONSTRAINT IF EXISTS chk_crm_tax_profiles_extractos_status;
ALTER TABLE crm_tax_profiles ADD CONSTRAINT chk_crm_tax_profiles_extractos_status
  CHECK (extractos_status = ANY (ARRAY['pending'::text, 'requested'::text, 'collected'::text]));

INSERT INTO storage.buckets (id, name, public)
VALUES ('crm-tax-documents', 'crm-tax-documents', false)
ON CONFLICT (id) DO NOTHING;

DROP POLICY IF EXISTS crm_tax_documents_admin_only ON storage.objects;
CREATE POLICY crm_tax_documents_admin_only ON storage.objects
  FOR ALL
  USING (
    bucket_id = 'crm-tax-documents'
    AND auth.uid() IN (SELECT user_id FROM user_roles WHERE role = 'admin')
  )
  WITH CHECK (
    bucket_id = 'crm-tax-documents'
    AND auth.uid() IN (SELECT user_id FROM user_roles WHERE role = 'admin')
  );

COMMENT ON COLUMN crm_tax_profiles.rut_storage_path IS 'Supabase Storage object path in the crm-tax-documents bucket, e.g. {lead_id}/rut.pdf. Never a URL — signed URLs are generated on demand, never persisted.';
COMMENT ON COLUMN crm_tax_profiles.extractos_storage_path IS 'Same as rut_storage_path, for the extractos bancarios document.';

SELECT '✅ 0026 crm_tax_documents complete' AS status;
