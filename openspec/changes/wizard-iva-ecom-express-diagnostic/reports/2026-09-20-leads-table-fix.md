# Report — `public.leads` Recreated

- Date: 2026-09-20
- Change: wizard-iva-ecom-express-diagnostic (§5b)
- Agent: Claude Sonnet 5 (Claude Code)
- Founder approval: explicit, per-migration ("go ahead, apply both migrations")

## What was applied

`contexia-wizard/supabase/migrations/20260920_recreate_leads_table.sql`, applied via
`mcp__supabase__apply_migration` to project `kpynymwghfwshvcvevxq`. Recreates `public.leads`
(15 columns) matching exactly what `app/api/leads/save/route.ts` and the surviving
`20260616_add_feria_lead_fields.sql` migration already expected. RLS enabled with an explicit
anon-deny policy (`leads_no_anon_access`).

## Verification

- `get_advisors(security)` post-migration: no new critical/error findings. One new WARN
  (`update_leads_updated_at` search_path mutable) — matches the same pre-existing pattern already
  present on this codebase's other trigger functions (`update_crm_b2b_updated_at`,
  `update_centinela_alerts_updated_at`); not a new class of risk, not fixed here to avoid
  inconsistent treatment of one function vs. the others.
- Direct SQL round-trip via `mcp__supabase__execute_sql` (bypasses RLS the same way a real
  service-role client does): insert with `ON CONFLICT (email) DO UPDATE` succeeded, returned the
  row, then deleted it. Table confirmed at 0 rows after cleanup.
- Local curl test against the actual Next.js dev server route returned
  `"new row violates row-level security policy for table 'leads'"`. Root cause: this repo's
  `contexia-wizard/.env.local` has no `SUPABASE_SERVICE_ROLE_KEY`, so `supabaseAdmin`
  (`lib/supabase.ts`) falls back to the anon key locally, and the anon-deny RLS policy correctly
  blocks it. Tried to confirm whether Vercel production has the real service-role key set via
  `filter_project_envs` — got a 403 (expected: env var values are permission-scoped, not
  something this session should be able to read). Did **not** loosen RLS to make the local test
  pass, since that would reopen exactly the anon-write gap the policy exists to close.

## Outcome

- Table structurally correct and matches all existing code paths that read/write it.
- Full end-to-end proof (real HTTP request through the deployed Next.js app, with a real
  service-role key) is still pending — recommend a quick production smoke test: submit Step 1 of
  either wizard flow for real and confirm a row appears in `leads`.
