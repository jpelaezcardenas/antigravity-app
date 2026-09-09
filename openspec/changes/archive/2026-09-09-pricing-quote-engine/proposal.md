# Pricing quote engine + agreed per-client price

## Why

Contexia sells two things billed by two distinct entities (`.antigravity/GROUND_TRUTH.md`):
**Entidad B** (Contexia S.A.S., TIC company) sells a software licence with fixed tiers, and
**Entidad A** (the regulated accounting practice, JCC-registered) sells a professional service
priced in a **band** according to real workload — not a tier.

Three concrete gaps block that model today:

1. **There is nowhere to record the agreed professional fee's band.** `b2b_clients` already has
   `monthly_fee_cents` (migration 0020 — the original handoff for this change assumed it was
   missing; verified live against Supabase, it exists and is nullable), but nothing records
   *which band* that fee was quoted under. Without the band, a $1.490.000 fee is
   indistinguishable from a Micro exception or a bottom-of-Estándar quote, so we cannot audit
   pricing consistency, detect a short payment against the right expectation, or project MRR by
   service band.

2. **Nothing sizes a lead's workload.** A freemium tenant already has a Shadow GL. Nobody reads it
   to answer "roughly how much work is this client?" before Tatiana quotes, so every quote starts
   from zero.

3. **The UVT would rot the moment it is written down.** Colombian filing thresholds are expressed
   in UVT, and two UVT values are simultaneously live during 2026 (UVT 2025 = $49.799 for año
   gravable 2025 obligation thresholds; UVT 2026 = $52.374 for 2026 sanctions and withholding).
   A constant in Python is wrong every 1 January and would silently misclassify every lead that
   arrives after it.

## What changes

1. **`uvt_values` table** (new migration) — `year` PK, `value_cop`, `resolution`, `created_at`.
   Seeded with UVT 2025 (Res. 000193 de 2024) and UVT 2026 (Res. 000238 del 15-dic-2025). Every
   calculation takes the tax year as a parameter and reads the value from this table.

2. **`b2b_clients.service_band`** (same migration) — `text` with `CHECK (service_band IN
   ('micro','estandar','complejo'))`, nullable. Exposed together with the existing
   `monthly_fee_cents` in the Búnker's B2B/Retainers tab, using the same write pattern the tab
   already uses for alta/baja/pago.

3. **`GET /api/v1/pricing/pre-cotizacion`** (new, tenant-scoped) — reads the caller's own Shadow
   GL and returns annualised revenue (COP and its UVT equivalent for the requested tax year),
   average monthly journal-line count, whether the revenue criterion crosses 1.400 UVT, a
   suggested band, a confidence level, and the drivers it could not observe.

## Non-goals

- **Not setting a price.** The endpoint suggests a band; Tatiana (the licensed accountant)
  confirms or overrides it. Nothing here writes a fee or a band automatically.
- **Not touching `core/plan_features.py`.** Pro Micro and Pro Estándar have *identical* software
  features — what differs is human workload. The service price lives on `b2b_clients`, never in
  the tier map. The pre-quote endpoint is therefore not plan-gated.
- **Not estimating payroll/labour load.** It does not exist in the data model. It is reported as a
  missing driver, never inferred.
- **Not computing a full declarant determination.** Four of the five quantitative obligation
  criteria and the qualitative IVA criterion are unobservable from the Shadow GL; the endpoint
  reports only the revenue criterion and names the rest as unevaluated.
- **Not applying the migration to production.** The SQL ships ready; applying it requires the
  founder's explicit approval.
- **No frontend surface for the pre-quote endpoint.** This change ships the backend contract and
  the Búnker's band/fee capture only. Rendering the pre-quote inside the CRM is a separate change.
