-- Migration: Add source and metadata columns to leads table
-- For feria/event tracking (Rueda de Negocios Estud-IA)
-- Run this in Supabase SQL Editor

-- Add source column (e.g., "feria-estudia-2026-06-17")
ALTER TABLE leads ADD COLUMN IF NOT EXISTS source text;

-- Add metadata JSONB column for feria-specific data
-- (empresa, cargo, expectativa, servicio_interes, como_conociste, observaciones)
ALTER TABLE leads ADD COLUMN IF NOT EXISTS metadata jsonb;

-- Create index for filtering by source
CREATE INDEX IF NOT EXISTS idx_leads_source ON leads(source);
