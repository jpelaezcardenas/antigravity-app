## Context

Verified live (Supabase MCP `information_schema.columns` query, and direct file reads — not just
subagent summaries) before writing this document:

- `tenants` (no `CREATE TABLE` exists anywhere in `apps/backend/migrations/` — it predates that
  folder) currently has exactly: `id uuid`, `nit text`, `legal_name text`,
  `is_cliente_cero boolean`, `created_at timestamptz`, `company_id text`. No `plan_tier`, no
  `updated_at`.
  - Since no tracked migration ever created this table, the new migration in this change is also
    the first to formally document `tenants`' schema in-repo (via a defensive
    `ADD COLUMN IF NOT EXISTS`, not a `CREATE TABLE`).
- `b2b_clients` (created `0020_crm_b2b_retainers.sql`, altered `0027`, `0041`) has:
  `id, tenant_id, name, nit, status, monthly_fee_cents, notes, created_at, updated_at, email,
  phone, contact_name, client_tenant_id, login_user_id, provision_status, hubspot_company_id,
  last_synced_at`. Confirmed live via the same Supabase query — matches the migration-derived list
  exactly.
- The `plan_type` Postgres ENUM (`'starter','pro','enterprise'`, migration `0010`) types a column
  on a **different, unrelated table** (`customer_invites.plan`) — not `usuarios`, not `tenants`.
  It is not reused here: its vocabulary (`pro`, no `freemium`) doesn't match this repo's actual
  pricing tiers (Freemium/Starter/Growth/Enterprise, per the master plan), and the master plan
  explicitly calls for `text + CHECK`, not a second dead enum.
- `usuarios.plan` is a live `text` column (confirmed via `information_schema.columns`, not the
  `plan_type` enum as the master plan assumed) defaulting to `'starter'::text`. It is written by
  `CrmService._provision_b2b_client_login` (`crm_service.py:272-281`) — not
  `create_b2b_client` as earlier investigation assumed — conditionally (only when an email was
  supplied at alta) and best-effort (swallowed on exception). It is **not** touched by this
  change; `plan_tier` lives on `tenants`/`b2b_clients`, a separate concern from this legacy
  per-user column.
- `core/rbac.py` is confirmed dead code (`from main import db` — `main` defines no `db` symbol;
  its only callers, `mission_endpoints.py`/`mission_rbac.py`, are never mounted by `main.py` or
  `presentation/router.py`). Its `is_role_allowed_for_plan` starter/pro/enterprise vocabulary is
  not reused, for the same reason `plan_type` isn't.
- Next available migration number is `0043` (confirmed: highest existing file is `0042`, no
  `0043_*.sql` exists yet, and the `0031`→`0033` gap in the sequence is a pre-existing, harmless
  gap — confirmed via `git log --diff-filter=D` that no `0032` file was ever created and deleted;
  not a hidden collision like the real one documented in ARCHITECTURE.md Decision #15).
- The 3 real, data-bound PWA components each already have a distinct, working state-handling
  idiom (verified by direct reading of all three files):
  - `CashTodayCard.tsx`: `useState<"loading"|"ready"|"empty"|"error">`, 4 named branches.
  - `ActiveAlerts.tsx`: `useState<"loading"|"ready">` only — a fetch error or a truly empty result
    both collapse to `status="ready"` with `alerts=[]`, and the component renders `null` (nothing)
    whenever `alerts.length === 0`. Deliberately minimal — "Honest empty-on-error."
  - `MonthlyLiquidityBridgeCard.tsx`: `useState<CardStatus>` where
    `CardStatus = "loading"|"ready"|"unavailable"` — backend `status:"empty"` and any fetch
    failure both collapse into `"unavailable"`.
- Backend insertion points (verified by direct reading, not just subagent summary):
  - `GET /api/v1/financials` (`financials_endpoints.py:85-126`) and
    `GET /api/v1/financials/liquidity-bridge` (`:129-165`) both use a **local**
    `_resolve_caller_tenant_id`, deliberately kept separate from the canonical
    `resolve_request_tenant_scope` per the module's own docstring (predates the Stage-4
    consolidation; changing that resolver is explicitly out of scope for this change — see
    Non-Goals). Insertion point in both: immediately after the `if tenant_id is None: return
    _empty_*()` guard, before the `compute_*` call.
  - `GET /api/v1/centinela/alerts` (`centinela_endpoints.py:282-...`, `get_my_alerts`) uses the
    **shared** `resolve_request_tenant_scope`. Insertion point: after `tenant_id =
    scope.tenant_id if scope else None` and its `if tenant_id is None` guard, before the
    `centinela_alerts` query.
  - None of the three handlers currently fetch a `tenants` row with more than `id` — a plan-tier
    check always requires one new query. This change adds it as a single new helper function in
    `core/plan_features.py`, not a change to either existing tenant-resolution mechanism.

## Goals / Non-Goals

**Goals:**
- A real, enforced `plan_tier` on every tenant, defaulting existing clients to unchanged behavior.
- The 3 real PWA endpoints/components each gain an explicit `not_in_plan` state, expressed as one
  more branch in their *existing* state machine — never a new UI pattern, never a silent 200 with
  wrong data.
- A `GET /api/v1/tenant/me` endpoint so Config shows the tenant's real name/tier.
- An "upgrade your plan" nudge on the 3 mock screens for a `freemium` tenant.

**Non-Goals:**
- No pricing numbers anywhere in code (per master plan — 3 contradictory figures exist in the
  real world; the founder sets real tariffs later).
- Not migrating `financials_endpoints.py`'s local `_resolve_caller_tenant_id` onto the shared
  `resolve_request_tenant_scope` — that's a separate, higher-risk refactor of an
  already-reviewed, tenant-security-relevant endpoint (flagged as deliberate in its own
  docstring); this change adds a plan-tier check without touching which resolver either endpoint
  uses.
- Not wiring a tier selector into the B2B "Alta" form or `create_b2b_client`/
  `_provision_b2b_client_login` — Subdomain 4's scope, which depends on this change's
  `plan_tier` column existing.
- Not touching `usuarios.plan` (a separate, pre-existing, best-effort column unrelated to this
  change's `tenants.plan_tier`).
- Not reusing or cleaning up the dead `plan_type` enum or `core/rbac.py` — out of scope, noted
  only as "don't collide with," not "go fix."

## Decisions

**D1 — `plan_tier` is `text + CHECK`, values `'freemium'|'starter'|'growth'|'enterprise'`, default
`'starter'`.** Not a Postgres ENUM (avoids an `ALTER TYPE` migration every time a tier name
changes — the master plan's own stated preference) and not a reuse of the existing dead
`plan_type` enum (wrong vocabulary: no `freemium`, has `pro` instead of `growth`). Default
`'starter'` for every existing and new row — **not** `'freemium'` — so this migration cannot
silently downgrade an existing paying client's access the moment it ships; a tenant only becomes
`freemium` via an explicit future write (Subdomain 4's onboarding flow). Alternative considered:
default to `NULL` and treat `NULL` as "full access" in the helper — rejected, because an
undocumented implicit default is exactly the kind of silent-assumption bug this codebase's own
incident history (ARCHITECTURE.md §CLAUDE.md "Incidente 2026-06-29") warns against; an explicit
`'starter'` default is self-documenting in the schema itself.

**D2 — `core/plan_features.py` is a plain dict + one function, not a class/service.** Matches the
size of the problem (4 tiers, 3 features today) and the codebase's existing preference for small,
explicit maps over abstractions (`CLAUDE.md` "Detect and highlight repeated code patterns," not
"invent a framework"). An unrecognized/missing `plan_tier` value **fails open** (full access) —
alternative considered was fail-closed (restrict to nothing), rejected because the only realistic
way to hit an unrecognized value is a data problem (a row written before this migration's default
applied, or a future tier name added to the CHECK constraint but not yet to this map), and the
established pattern across this repo's tenant-scoping decisions (#13-#17) is "never let an
internal inconsistency silently break an existing paying client's access" — the failure mode this
change must avoid is "a `starter` client suddenly can't see their own Centinela alerts because of
a typo," not "a hypothetical malicious tier value gets more access than it should" (there is no
security boundary here — `plan_tier` is a product gate, not an auth gate; auth/tenant-isolation
are unchanged and remain governed by Decisions #13-#17).

**D3 — Feature-gate all 3 endpoints uniformly, even though `freemium` currently passes all 3
checks for `financials`.** `GET /api/v1/financials` maps to feature `pulso_diario`, which
`freemium` *does* include — so today, gating this endpoint is a no-op for `freemium`. Applying the
same check to all 3 anyway (rather than special-casing `financials` as "never gated") means a
future 5th tier that excludes `pulso_diario` doesn't require touching this endpoint's code again.

**D4 — Per-component `not_in_plan` UI treatment follows each component's own existing idiom, not
a shared new one:**
- `CashTodayCard`: no visible change — `freemium` includes `pulso_diario`, so this component never
  actually renders a `not_in_plan` state today (see D3). The branch is still added in code for
  forward-compatibility, but no tier reachable by this change exercises it.
- `MonthlyLiquidityBridgeCard`: adds a **new**, distinct `"not_in_plan"` value to `CardStatus`
  (`"loading"|"ready"|"unavailable"|"not_in_plan"`), rendering "Esta función no está incluida en tu
  plan." Alternative considered: collapse into the existing `"unavailable"` state — rejected,
  because `"unavailable"` already means "we tried, no data" and collapsing a plan restriction into
  it would look identical to a data outage, defeating the point of telling a freemium user this
  exists behind a paid tier.
- `ActiveAlerts`: adds a new optional `status: "not_in_plan"` field to
  `CentinelaAlertsScopedResponse` (additive — existing tiers never see it, so no existing
  behavior changes). The component adds exactly one new branch: `status === "not_in_plan"` renders
  a single muted line ("Centinela Fiscal no está en tu plan actual.") instead of `null`. This
  deliberately breaks from the component's "renders nothing when empty" idiom for this one case,
  because "genuinely nothing to show" and "there's a feature you don't have" are not the same
  thing, and only the latter deserves an upsell surface — the existing empty/error paths (`alerts
  = []`, no explicit status) are untouched and still render `null`.

**D5 — `GET /api/v1/tenant/me` uses the canonical `resolve_request_tenant_scope`, not a new local
resolver.** Unlike `financials_endpoints.py`, this is a brand-new endpoint with no prior reviewed
behavior to preserve, so there's no reason to duplicate the resolution ladder — it follows the
same pattern as `centinela_endpoints.py`'s `get_my_alerts`. An unresolved tenant returns
`{legal_name: null, plan_tier: null, status: "empty"}`, mirroring `_empty_snapshot()`'s existing
explicit-empty pattern rather than a 404/403 (this is a read endpoint about the caller's own
identity, not a queue/ownership check, so the anti-enumeration 404 policy of Decisions #14/#17
doesn't apply here).

## Risks / Trade-offs

- [Risk] A tenant row somehow written without going through the new migration's default (e.g. a
  raw insert bypassing Postgres defaults is not realistically possible, but a *future* migration
  that recreates `tenants` without preserving the default could silently regress this). →
  Mitigation: D2's fail-open helper means even a NULL/missing `plan_tier` degrades to full access,
  never to an unexpected lockout.
- [Risk] Adding a `not_in_plan` field to `CentinelaAlertsScopedResponse` changes its shape. →
  Mitigation: additive-only (new optional field), and D2 means every currently-provisioned tenant
  (`starter` default) never triggers it — verified no existing consumer of this response
  (`ActiveAlerts.tsx`, the only frontend caller found in this repo) breaks on an unexpected extra
  field.
- [Risk] The mock screens' "upgrade your plan" prompt could be confused for real gating (the
  screens themselves stay mock either way). → Mitigation: the prompt is purely presentational,
  gated only by `GET /api/v1/tenant/me`'s `plan_tier`, and does not claim or imply the underlying
  screen has real data — explicitly noted as a task to keep the copy honest.

## Migration Plan

1. Apply `0043_add_plan_tier.sql` (defensive `ADD COLUMN IF NOT EXISTS` on both `tenants` and
   `b2b_clients`, `CHECK` constraint, default `'starter'`) — additive, backward-compatible, no
   backfill script needed since the column default handles existing rows.
2. Ship `core/plan_features.py` and the 3 endpoint changes together (they're one deploy unit —
   the helper has no callers until the endpoints reference it).
3. Ship `GET /api/v1/tenant/me`.
4. Ship the 4 frontend changes (3 real components' new branch + Config page) together, since they
   depend on the backend responses existing in production first.
5. Ship the 3 mock-screen upgrade prompts last — purely additive, no dependency risk.
6. Rollback: the migration is additive-only (no data destroyed by rolling back — a rollback would
   just drop the column); reverting the endpoint/frontend commits is a standard git revert with no
   migration-down step required since nothing downstream depends on `plan_tier` existing yet
   outside this change.

## Open Questions

- [FOUNDER ACTION] Confirm the 4 tier names (`freemium`/`starter`/`growth`/`enterprise`) match the
  eventual real pricing tiers — this change only commits to the names and feature membership, not
  prices (per master plan's explicit "no pricing numbers in code").
- [ENGINEERING, deferred to Subdomain 4] `usuarios.plan` (the separate, best-effort, per-user
  `text` column written by `_provision_b2b_client_login`) has no relationship to `tenants.plan_tier`
  after this change — worth deciding in Subdomain 4 whether `usuarios.plan` should be
  deprecated/reconciled once a real per-tenant tier exists, since it's a second, less reliable
  source of "what tier is this" today.
