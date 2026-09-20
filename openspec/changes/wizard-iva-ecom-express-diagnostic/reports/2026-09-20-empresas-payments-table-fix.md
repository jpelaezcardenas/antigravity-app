# Report — `public.empresas` and `public.payments` Recreated

- Date: 2026-09-20
- Change: wizard-iva-ecom-express-diagnostic (§5c)
- Agent: Claude Sonnet 5 (Claude Code)
- Founder approval: explicit, per-migration ("go ahead, apply both migrations")

## Why this was urgent

Traced the live call path before touching anything: `contexia-app/app/crear-empresa-wizard/`
(the current, actively-marketed "Crear tu empresa" product, $1.200.000, "Lanzamiento" pricing) →
`lib/payments/wompiCheckout.ts` (`API_BASE = "/wizard/api/payments"`) →
`contexia-wizard/app/api/payments/create-transaction` → `lib/supabase/payments.ts` →
`.from("empresas")` / `.from("payments")`. Both tables were missing (confirmed via PostgREST
probing, 404). Every real customer attempting to pay through this live flow was hitting a 500.

## What was applied

`contexia-wizard/supabase/migrations/20260920_recreate_empresas_payments_tables.sql`, applied via
`mcp__supabase__apply_migration` to project `kpynymwghfwshvcvevxq`, immediately after the `leads`
migration (FK dependency: both tables reference `leads(id)`). Column shapes matched against
`lib/supabase/payments.ts` (createEmpresa/createPayment/updatePaymentStatus/getPaymentByReference)
and `app/api/payments/webhook/route.ts`'s reads. RLS enabled with anon-deny policies on both
tables.

## Verification

- `get_advisors(security)` post-migration: no new critical/error findings (see leads report for
  the one pre-existing-pattern WARN, shared across this migration set).
- `information_schema.tables` confirms both tables exist: `empresas` (15 columns), `payments`
  (20 columns).
- Direct SQL round-trip: inserted an `empresas` row, then a `payments` row referencing it via
  `empresa_id` (which itself references `leads` via `lead_id`, left null here since no lead was
  created in this test) — confirmed `payments.status` defaults to `'PENDING'` correctly, and the
  FK chain resolves. Deleted both test rows; all three tables (`leads`, `empresas`, `payments`)
  confirmed back at 0 rows.

## What was NOT verified (explicit, not silently skipped)

A real or Wompi-sandbox end-to-end transaction through `contexia.online/crear-empresa-wizard` —
submit the real 8-step form, open the real Wompi checkout widget, complete a test payment, confirm
the webhook fires and flips `payments.status` to `APPROVED`, confirm the confirmation email sends.
This requires a live Wompi sandbox/test credential exchange and touches the app's actual payment
UI, which is closer to a live-money test than something to simulate further from here.

**Recommendation:** the founder or Tatiana run one real low-value test purchase (or use Wompi's
sandbox mode if configured) through the production flow to close this loop. The database layer is
now structurally sound and matches every column the application code reads and writes — the
remaining risk is entirely in things this investigation couldn't reach: the real
`SUPABASE_SERVICE_ROLE_KEY` in Vercel's environment (see leads report) and the real Wompi
credentials/webhook signature configuration in production.

## Outcome

Tables recreated, verified structurally sound, zero regressions to `crm_leads` or any other table.
The urgent, revenue-impacting gap (missing tables) is closed. Full production confirmation with
real credentials is a follow-up the founder should own.
