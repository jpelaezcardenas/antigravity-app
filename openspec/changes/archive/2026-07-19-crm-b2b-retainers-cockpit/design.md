## Context

The Búnker (`/app/bunker`, admin-only via Vercel edge middleware) reserves a "CRM / Ventas" sidebar
slot rendering `contexia-app/components/bunker/CrmVentasSection.tsx`, currently a static mock (5
hardcoded fake clients, no fetch, no props). Contexia's real B2B retainer data lives in a manual
Excel. There is a proven live-data pattern already in the Búnker to clone: **Social Content Ops**
(`social_ops_service.py` + `social_ops_endpoints.py` + `contexia-app/lib/social-ops-api.ts` +
`components/bunker/social-ops/IdeasTab.tsx`), which is Supabase-preferred with a demo-fallback, gated
behind a feature flag (`SOCIAL_OPS_CANONICAL`), and documented as a data-bound exception to the
"mock-first" Búnker charter.

Verified live-schema facts that shape this design:
- `tenants(id, nit, legal_name, is_cliente_cero boolean, ...)` exists; Cliente Cero is resolved via
  `WHERE is_cliente_cero = true`, matching `financials_endpoints.py`/`financials_service.py`.
- `user_roles.role` is a Postgres **enum** column (`role_type`: `admin | finance | marketing | growth
  | operator | viewer` — verified live via `pg_enum`), not `role_name` text as in migration `0019`,
  not `role_id`+`roles` FK as in migration `0013`. This is distinct from the Vercel edge middleware's
  JWT `app_metadata.role` labels (`admin | superadmin | contexia_admin`), which is a separate
  frontend-route-gating concept. RLS policies on `b2b_clients`/`b2b_payments` use `role = 'admin'`
  against this Postgres enum. Cliente Cero tenant id verified live:
  `e2d30d09-6b96-4ebe-a79a-c6aff7a5df34` (Contexia SAS, NIT 900000000).
- Live check confirms `ingestion_batches` (migration `0019`) has **zero** RLS policies despite the
  migration defining one — `CREATE POLICY IF NOT EXISTS` silently no-ops when the policy doesn't
  exist yet in some Postgres versions/contexts here, confirming this migration must use
  `DROP POLICY IF EXISTS ... ; CREATE POLICY ...` instead.
- A generic `clients` table (uuid `company_id` PK) already exists — the new B2B table must be named
  `b2b_clients` to avoid collision.
- There is no automated migration runner in this repo; migrations are raw idempotent `.sql` files
  applied manually (or via the Supabase MCP `apply_migration` tool) from `apps/backend/migrations/`.
- Backend money convention is minor units (`amount_cents`), matching Caja Real and `erp_journal_lines`.

## Goals / Non-Goals

**Goals:**
- Give Contexia a live, queryable, correct source of truth for B2B retainer clients and their monthly
  payment history, replacing the Excel and the mock UI.
- Ship read-only endpoints + a live grid, following existing conventions exactly (Supabase-preferred/
  demo-fallback, feature flag, RLS, `@theme` tokens, no new frontend libraries).
- Keep the change small and independently deployable — this is Change A of a longer staged plan.

**Non-Goals:**
- B2C lead Kanban funnel, `crm_leads`/`crm_tax_profiles`/`crm_wompi_transactions` — a later change.
- Wompi payment integration, Taty/WhatsApp, Hermes/Manus agentic layer — later changes, fully out of
  scope here.
- Write endpoints for editing payments/client status — optional stretch, not required for this
  change to be complete and useful (read-only grid delivers the core value: visibility).
- Multi-tenant B2B CRM for external customers — this is Contexia's own retainer book (Cliente Cero),
  not a product feature for other tenants.

## Decisions

1. **Tenant-scope the new tables via `tenant_id → tenants(id)` (Cliente Cero), not schema-less
   single-tenant.** Every existing financial/governance table in this repo (`missions`,
   `ingestion_batches`, `erp_journal_*`) is tenant-scoped with RLS. Diverging here would make B2B
   retainer data the only ungoverned financial table, and would force a painful retrofit if Contexia
   ever manages a second accounting entity. Cost is one resolved-once column; consistency wins.
   *Alternative considered*: no tenant column, since there's only one real tenant today. Rejected —
   breaks the uniform RLS story for no real savings.

2. **Payment grain: a normalized ledger, one row per `(client, period)` — not a wide 6-column table.**
   The Excel's natural grain *is* the (client × month) cell. A normalized `b2b_payments` table lets
   the grid be a trivial server-side pivot, doesn't require an `ALTER TABLE` every new month, and
   supports `UNIQUE(client_id, period)` for idempotent re-seeding (critical since there's no migration
   runner). *Alternative considered*: `ene, feb, ..., jun bigint` columns on `b2b_clients`. Rejected —
   rigid at year boundaries, can't represent partial/adjusted payments, breaks idempotent upsert.

3. **Money stored as `amount_cents bigint` (minor units).** Matches the platform-wide convention
   (Caja Real, `erp_journal_lines.*_cents`); frontend divides by 100 via the existing `formatCop`
   helper. *Alternative considered*: whole-COP integer columns (as the sibling `contexia-wizard`
   project does). Rejected — this repo, not the wizard, is the convention to match; consistency with
   the codebase we're actually shipping into.

4. **RLS admin predicate uses the live `role_type` enum directly (`role = 'admin'`)**, not migration
   `0019`'s `role_name IN (...)` (a column that does not exist on the live table) nor migration
   `0013`'s `role_id`+`roles` join, and not the edge middleware's JWT label set
   (`admin|superadmin|contexia_admin`, a separate frontend-only concept). Verified live: the enum's
   only values are `admin | finance | marketing | growth | operator | viewer` — `admin` is the sole
   qualifying value for this admin-only gate.

5. **Idempotent DDL throughout**: `CREATE TABLE/INDEX IF NOT EXISTS`; for RLS policies,
   `DROP POLICY IF EXISTS ...; CREATE POLICY ...` (not `CREATE POLICY IF NOT EXISTS`, which is not
   valid Postgres syntax — migration `0019` uses it and is latently broken on re-run). Seed data uses
   `ON CONFLICT (...) DO UPDATE` so re-applying the seed migration is a safe no-op.

6. **Ship behind a new `CRM_CANONICAL` feature flag**, default `false`, following the exact
   `SOCIAL_OPS_CANONICAL` playbook: deploy dark, smoke-test in prod, then flip. Read endpoints only in
   this change reduces the blast radius of flipping the flag.

7. **Frontend clones the `IdeasTab.tsx`/`social-ops-api.ts` idiom exactly**: a private typed
   `api<T>(path, init?)` wrapper over `fetch` against `${API_BASE_URL}/api/v1` (no auth/tenant
   headers — matching the existing open-endpoint pattern), `useState` + `useEffect(...,[])` load with
   explicit `loading`/`error`/`source` states, `@theme` tokens only, no new libraries. `CrmVentasSection.tsx`
   becomes a tab shell (`"B2B / Retainers"` live, `"B2C / Renta Natural"` a placeholder) rather than a
   full page rewrite, so the sidebar/composition in `app/app/bunker/page.tsx` needs no changes.

8. **`crm_service.py` reads via `get_service_supabase()` (service-role), not `get_supabase()`
   (anon).** The backend has no per-request end-user Supabase session — API calls from the FastAPI
   service to Supabase carry an API key, not a user JWT, so `auth.uid()` is `NULL` inside the RLS
   policy and an anon-key query would always be denied zero rows regardless of the caller's actual
   role. Since there is no session to evaluate the policy against, the admin-only RLS is enforced at
   the *application* layer (Vercel edge middleware gating the Búnker route + the `CRM_CANONICAL`
   flag), and the database RLS is defense-in-depth against direct anon-key table access from any
   other context. This is the same posture already accepted for Social Ops and is called out as
   Risk R1 below — not a new gap introduced by this design.

## Risks / Trade-offs

- **[Risk] The CRM read endpoints attach no per-request auth** (consistent with Social Ops today) —
  only the Vercel edge middleware on the Búnker route and the `CRM_CANONICAL` flag gate access, and
  the backend reads via the service-role Supabase client (see Decision 8), so RLS is defense-in-depth
  rather than the live gate. B2B revenue data is more sensitive than social-ops demo data.
  → **Mitigation**: flag this explicitly at Stage 11 before flipping `CRM_CANONICAL` in prod; note in
  the deployment report as an accepted risk consistent with the rest of the Búnker's current auth
  posture (fixing platform-wide API auth is out of scope for this change).
- **[Risk] `tenants` has no committed `CREATE TABLE` migration** — it exists live but was applied
  out-of-band, same situation `0013`/`0019` already depend on. → **Mitigation**: verify via `list_tables`
  before writing the FK; document, don't attempt to backfill the missing migration (out of scope).
- **[Risk] Re-seeding must not double-count.** → **Mitigation**: `UNIQUE(client_id, period)` +
  `ON CONFLICT DO UPDATE`; re-apply the seed migration once in Task 2 to prove idempotency before
  moving on.
- **[Trade-off] Read-only in this change.** Editing a payment or toggling client status from the UI
  is deferred; visibility (the main pain point — "no system view of who pays what") is delivered
  first, writes can follow as a fast-follow if needed.

## Migration Plan

1. Apply `apps/backend/migrations/0020_crm_b2b_retainers.sql` (DDL: `b2b_clients`, `b2b_payments`,
   indexes, RLS, triggers) via Supabase MCP `apply_migration`.
2. Apply `apps/backend/migrations/0021_seed_b2b_retainers.sql` (10 clients, 60 payment rows,
   idempotent upsert).
3. Deploy backend (Railway) with `CRM_CANONICAL=false` by default; verify endpoints respond with
   `source=supabase` once the flag is manually flipped in a test call.
4. Deploy frontend (Vercel) with the new tab shell; the B2C tab is a placeholder so nothing breaks.
5. Flip `CRM_CANONICAL=true` in Railway prod once smoke-tested.
6. **Rollback**: flip `CRM_CANONICAL=false` (endpoints 404 again, frontend falls back gracefully to
   its error/empty state); the migrations are additive-only (new tables) so no destructive rollback
   is needed at the DB layer.

## Open Questions

- Should `b2b_clients.monthly_fee_cents` (the nominal contracted retainer) be populated at seed time,
  or left null until Juan David confirms nominal fees per client separately from actual payments?
  Defaulting to null; the grid works from actual `b2b_payments` regardless.
- Exact wording/placement of the "third data-bound screen" entry in `contexia-app/CLAUDE.md` — will
  follow the existing Social Content Ops entry's structure.
