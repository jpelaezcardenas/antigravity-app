# Design — pwa-tenant-aware-screens

## Context

`GET /api/v1/financials` (`per-tenant-client-access`) is the only endpoint in the backend that
resolves the caller's own tenant today. Everything else — `/centinela/alerts/{company_id}`,
`/agents/*`, `/pulso/today` — is either unauthenticated, keyed by a free-text id the caller
supplies, or hardcoded to Cliente Cero. This change extracts the tenant-resolution policy
`/financials` already implements into a shared helper, and reuses it for two new endpoints instead
of inventing a second policy.

## Decisions

### D1 — Shared tenant resolver, not a copy-paste

`presentation/financials_endpoints.py` currently inlines this policy in `get_financials` (lines
64–71):
1. `user.get("resolved_tenant_id")` present → that tenant.
2. `user["id"] == _STAGING_USER["id"]` (i.e. `AUTH_ENFORCED=False`, no token — local
   dev/staging) → Cliente Cero.
3. Otherwise (authenticated, no resolved tenant) → `None`.

Extracted to `core/tenant_context.py::resolve_caller_tenant_id(user: dict) -> str | None`,
re-exporting the existing `resolve_cliente_cero_tenant_id()` helper it depends on.
`financials_endpoints.get_financials` is refactored to call it — behavior-preserving; the existing
`tests/test_financials_endpoint_tenant_scoping.py` suite is the regression guard (must stay green
unmodified).

**Why not duplicate the three lines into each new endpoint?** Three independent copies of "what
does an unresolved authenticated caller see" is exactly the kind of drift that produced the
Cliente-Cero-leak class of bug `per-tenant-client-access` closed. One helper, three call sites.

### D2 — New alerts route, existing route untouched

`GET /centinela/alerts/{company_id}` is consumed today by Hermes's `CentinelaAlertsTool`
(`wire-contexia-agents-to-hermes-workspace`) with a free-text `company_id` and a demo fallback when
Supabase has no rows for that id. Retrofitting auth onto it would break that integration contract.
Instead: `GET /centinela/alerts` (no path param) is a new, additive route on the same router,
tenant-scoped via D1, **no demo fallback** — an authenticated client with no rows gets an honest
empty list, not synthesized data. The PWA calls only the new route; Hermes keeps calling the old
one. Both read the same `centinela_alerts` table, just filtered differently (`company_id` vs
`tenant_id`).

### D3 — Liquidity bridge scope = account 1110 only

The mock's `LiquidityBridge` shape (`initialBalance`, `inflows`, `outflows`, `finalBalance`) maps
exactly onto what `_compute_caja_real_balance` already computes for account `1110` (Bancos):
- `initial_balance` = cumulative 1110 balance as of `month_start - 1 day` (reuses
  `_compute_caja_real_balance` with a different `as_of_date` — no new balance logic).
- `inflows` = sum of 1110 `debit_minor` within `[month_start, month_end]`.
- `outflows` = sum of 1110 `credit_minor` within the same range.
- `final_balance = initial_balance + inflows - outflows` (identically equals
  `_compute_caja_real_balance(month_end)` — asserted as a property in tests, not just computed
  independently, to catch drift between the two).

The mock's sibling card `FlowCompositionCard` (operación/inversión/financiación breakdown) is
**not** attempted — the Shadow GL has no classification dimension for that split. Per charter:
don't relabel data that doesn't have the promised granularity; that card stays mock.

### D4 — Rolling reseed via pg_cron, not an app-level scheduler

`erp_journal_entries.entry_date` for the `SYNTH-*-SALE` / `SYNTH-*-EXPENSE` rows (migration 0028)
was set to `CURRENT_DATE - 1` at seed time (2026-07-22) and is now static — `ventas_ayer` /
`gastos_ayer` read $0 for every client until the ledger receives real ingestion
(`shadow-gl-real-data-ingestion`, not yet started). Chosen fix: a Supabase `pg_cron` job,
re-running the same `UPDATE ... entry_date = CURRENT_DATE - 1` daily, scoped by the same
`external_reference_id`/`memo` tags migration 0028 established. This is a data-layer concern (lives
with the data, survives Railway restarts/redeploys, no new runtime dependency) rather than a
FastAPI background task or an external cron hitting an endpoint.

`SYNTH-*-OPEN` rows (opening balance, dated 180/30 days back) are excluded by filtering on the
`-SALE`/`-EXPENSE` suffix — re-dating the opening balance would corrupt the cumulative Caja Real
math.

**Precondition, verified before finalizing the migration:** `pg_cron` extension availability on
the Supabase project, checked via the Supabase MCP `list_extensions` during implementation. If
unavailable in this project tier, fall back to `create extension if not exists pg_cron` (documented
here as the primary path); if that also fails, the fallback is a Railway-side scheduled task
calling a new internal reseed function — not built speculatively, only if the primary path is
confirmed blocked.

### D5 — CashTodayCard error-state fix is a spec-compliance fix, not new scope

`openspec/specs/pulso-overview-live-data/spec.md` (already archived, already the ground truth)
requires: *"Error state falls back gracefully ... SHALL render an unobtrusive error/placeholder
state and SHALL NOT crash the screen or show a misleading mock value."* The current
`CashTodayCard.tsx` implementation catches the fetch error, `console.warn`s, and sets
`status: "ready"` with `pulsoMock.cash` — i.e. exactly the misleading-mock-value behavior the spec
forbids. This change adds an explicit `"error"` status branch (discrete inline message, e.g. "No
pudimos actualizar tu Caja Real"), removing the mock fallback. No spec text changes — the code
catches up to what's already required.

## Risks / trade-offs

- **New alerts route means two read paths into `centinela_alerts`.** Accepted: the alternative
  (retrofitting the Hermes-consumed route) risks breaking a live integration for a screen-scoped
  change. Revisit consolidation only when Hermes itself moves to tenant-scoped calls
  (`agent-endpoints-real-tenant-filtering`-shaped follow-up, not started).
- **`centinela_alerts` may have zero tenant-scoped rows for most clients** (writes still stamp
  Cliente Cero per `services/centinela_service.py::save_alerts`, unchanged by this change) — real
  clients will mostly see an honestly empty Alertas Activas section until alert-writing is also
  tenant-scoped. That's a known, separate gap (write-side), not silently patched over here.
- **pg_cron extension availability is unverified until implementation** — flagged as the one
  external unknown in this design; the fallback path is named, not deferred to "figure it out
  later."
- **Liquidity bridge is calendar-month, `/financials` daily-granularity is "yesterday only."**
  Different windows are intentional — the Flujo-detalle screen's mock is explicitly a *monthly*
  bridge ("Puente de Liquidez (Mensual)" in the component's own heading); matching that window
  is what keeps the label honest.
