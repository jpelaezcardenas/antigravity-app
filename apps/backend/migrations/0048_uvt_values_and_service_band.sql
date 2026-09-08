-- Migration 0048: uvt_values reference table + b2b_clients.service_band
-- Date: 2026-09-08
-- Change: openspec/changes/pricing-quote-engine/
--
-- Two independent additions, shipped together because the pre-quote engine needs both:
--
--   1. `uvt_values` — Colombian UVT (Unidad de Valor Tributario) by tax year. The UVT
--      cannot live as a Python constant: it is re-published by DIAN resolution every
--      December, so a hardcoded value is wrong every 1 January and would silently
--      misclassify every lead arriving after that date. Every calculation takes the tax
--      year as a parameter and reads the value from here (design.md Decision #2).
--
--      Note that TWO UVT values are simultaneously in force during 2026 and apply to
--      DIFFERENT things: UVT 2025 governs the año-gravable-2025 filing-obligation
--      thresholds, while UVT 2026 governs sanctions and withholding accrued in 2026.
--      That is why this is a table keyed by year rather than a single "current" row.
--
--      `value_cop` is stored in WHOLE PESOS, not minor units — deliberately unlike the
--      Shadow GL's *_minor columns. The UVT is a legal figure published in whole pesos;
--      storing 4979900 to mean $49.799 would invite a 100x error in the dangerous
--      direction (a threshold 100x too high classifies everyone as a non-declarant).
--      The conversion from Shadow GL minor units happens exactly once, in
--      services/pricing_service.py, immediately before any UVT comparison.
--
--   2. `b2b_clients.service_band` — which band the agreed professional fee was quoted
--      under. `monthly_fee_cents` already exists (migration 0020) and records the amount;
--      it does not record the band, so a $1.490.000 fee is today indistinguishable from a
--      Micro exception and a bottom-of-Estándar quote. Entidad A's service is priced in a
--      band by real workload, not by a software tier — the tier map in
--      core/plan_features.py is deliberately NOT touched by this change.
--
-- Idempotent. NOT YET APPLIED to production: applying migrations requires the founder's
-- explicit approval (see openspec/changes/pricing-quote-engine/tasks.md, task 11.4b).

-- ---------------------------------------------------------------------------
-- 1. uvt_values
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.uvt_values (
    year        integer PRIMARY KEY,
    value_cop   bigint NOT NULL,
    resolution  text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT chk_uvt_values_year_plausible CHECK (year BETWEEN 2000 AND 2100),
    CONSTRAINT chk_uvt_values_positive CHECK (value_cop > 0)
);

COMMENT ON TABLE public.uvt_values IS
    'Colombian UVT by tax year. Public legal reference data, not tenant data. Read by '
    'services/uvt_service.py; never duplicated as a code constant.';
COMMENT ON COLUMN public.uvt_values.value_cop IS
    'UVT in WHOLE Colombian pesos (NOT minor units, unlike the Shadow GL *_minor columns).';
COMMENT ON COLUMN public.uvt_values.resolution IS
    'The DIAN resolution that set this value, so the figure is auditable to its source.';

-- Seed. ON CONFLICT DO NOTHING so re-running never overwrites a value that was later
-- corrected in place.
INSERT INTO public.uvt_values (year, value_cop, resolution) VALUES
    (2025, 49799, 'Resolución DIAN 000193 de 2024'),
    (2026, 52374, 'Resolución DIAN 000238 del 15 de diciembre de 2025')
ON CONFLICT (year) DO NOTHING;

-- RLS: this is public legal reference data — every authenticated caller may read it, and
-- only the service role may write it. Reads are deliberately unrestricted by tenant (the
-- UVT is the same figure for everyone); writes are not, which is why this is two policies
-- and not one permissive `USING (true)` FOR ALL — the shape the 2026-09-05 masterprompt
-- audit flags on erp_journal_* as providing no isolation at all.
ALTER TABLE public.uvt_values ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS uvt_values_read_all ON public.uvt_values;
CREATE POLICY uvt_values_read_all
    ON public.uvt_values
    FOR SELECT
    USING (true);

DROP POLICY IF EXISTS uvt_values_service_role_write ON public.uvt_values;
CREATE POLICY uvt_values_service_role_write
    ON public.uvt_values
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ---------------------------------------------------------------------------
-- 2. b2b_clients.service_band
-- ---------------------------------------------------------------------------

ALTER TABLE public.b2b_clients
    ADD COLUMN IF NOT EXISTS service_band text;

-- Nullable with no default: the existing roster has no recorded band, and inferring one
-- from the fee amount is exactly the guess this change exists to eliminate. An unquoted
-- client reads as NULL, not as a fabricated "estandar".
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_b2b_clients_service_band'
    ) THEN
        ALTER TABLE public.b2b_clients
            ADD CONSTRAINT chk_b2b_clients_service_band
            CHECK (service_band IS NULL OR service_band IN ('micro', 'estandar', 'complejo'));
    END IF;
END $$;

COMMENT ON COLUMN public.b2b_clients.service_band IS
    'Entidad A professional-service band the agreed monthly_fee_cents was quoted under: '
    'micro (exception, minimal movement without labour load) | estandar (the majority) | '
    'complejo (quoted case by case). NULL = not yet recorded; never inferred from the fee.';

SELECT '✅ 0048 uvt_values_and_service_band complete' AS status;
