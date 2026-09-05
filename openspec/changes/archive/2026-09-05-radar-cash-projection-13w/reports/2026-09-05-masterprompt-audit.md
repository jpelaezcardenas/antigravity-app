# Audit — "MASTERPROMPT Pulso Diario v2 / Radar de Caja 13 Semanas" vs. what was delivered

**Date:** 2026-09-05
**Auditor:** Claude Opus 5 session (self-audit, requested by the founder)
**Subject:** OpenSpec change `radar-cash-projection-13w`, archived 2026-09-05
**Method:** every claim below is checked against the live system — production HTTP responses, the
production Supabase database, the repo, and the test suite. Nothing is asserted from memory.

---

## 1. Verdict

The module was **built, deployed and verified in production**. Of the masterprompt's 9
Definition-of-Done items, **6 are met, 2 are partial, 1 was not done**.

The more important output of this audit is not the checklist — it is that **two premises the
masterprompt states as fact are not true in production**, and one of them is a security finding.
Neither was caused by this change; both were found while verifying it.

---

## 2. Premises the masterprompt asserts — checked

| # | Premise (quoted) | Reality | Evidence |
|---|---|---|---|
| A1 | *"Supabase PostgreSQL con RLS estricto multi-tenant — cada cliente tiene su client_tenant_id, aislamiento total"* | **FALSE.** RLS is *enabled* but the policies are fully permissive. | `pg_policies`: `erp_journal_entries_anon_all`, `erp_journal_lines_anon_all`, `dian_xml_documents_anon_all` — each `cmd=ALL`, `USING (true)`, roles `{anon, authenticated, service_role}` |
| A2 | *"Shadow GL … es el motor de datos que YA calcula el Pulso Diario actual"* | **Structurally true, factually empty.** The wiring exists; the data does not. | Whole production DB: **30** `erp_journal_entries`, **60** `erp_journal_lines`, **0** `dian_xml_documents`, across 14 tenants. Cliente Cero has **0** entries. Best-populated tenant has 3 entries across 2 ISO weeks. |
| A3 | *"Pantalla actual (mock) del Radar Predictivo: /app/radar"* | TRUE (it was; it is now partly data-bound). | `contexia-app/CLAUDE.md`, tenth data-bound exception |
| A4 | *"Autenticación: JWT asimétrico ES256 + JWKS"* | TRUE and used unchanged. | `core/deps.py::_verify_supabase_token`; endpoint returns 401 without a token |

### A1 in detail — this is the finding that matters

Tenant isolation for the Shadow GL is enforced **only by application code** (`.eq("tenant_id", ...)`
in every query), **not by the database**. The `USING (true)` policies mean anyone holding the anon
key can read every tenant's ledger directly through PostgREST, bypassing the backend entirely.
Supabase's own linter separately flags that the `shadow_gl_discrepancies` materialized view is
selectable by `anon`/`authenticated`.

This is the same permissive-policy pattern `ARCHITECTURE.md` Decision #14 already records as an open
item for `approval_queue_anon_all` — it is broader than that note implies. Unrelated but found in
the same lint run and worth the founder's attention: `public.set_hermes_tunnel(p_url, p_token)` is a
`SECURITY DEFINER` function **executable by the `anon` role**.

None of this was introduced by this change. It is reported because the masterprompt's DoD asks the
endpoint to "respetar RLS", and the honest answer is that there is no RLS to respect on these tables.

---

## 3. Functional scope — line by line

| # | Requirement | Status | Evidence |
|---|---|---|---|
| B1 | New endpoint `GET /api/v1/radar/proyeccion-caja` | Met | Live: `401` without token on Railway and `contexia.online` |
| B2 | `client_tenant_id` from the JWT, **not** a query param | Met | `Depends(get_current_user)` + `resolve_request_tenant_scope()`; no query param |
| B3 | Project account `1110` week by week, 13 weeks | Met | `calculate_cash_projection_13w`; 13 weeks asserted in tests |
| B4 | Base rate from the last 8-12 weeks of history | Met | `PROJECTION_LOOKBACK_WEEKS = 12` |
| B5 | Use CxC/CxP **if they exist**, else declare `solo_historico` | Met | Verified none exist; `metodologia` always `"solo_historico"` |
| B6 | Reuse Impuesto Futuro Estimado **if it exists**, do not duplicate | Met | Verified it does not exist; returns `null`, never a fabricated number |
| B7 | Output shape | Met, 2 documented deviations | See section 4 |
| B8 | Confidence `alta` (1-4) / `media` (5-8) / `baja` (9-13) | **Deviated** | Ships `media` (1-4) / `baja` (5-13). See section 4 |
| B9 | 13-point line chart | Met | `CashProjection13wCard.tsx`, inline SVG |
| B10 | `alerta_narrativa` in large text, "amiga contadora" tone | Met | Rendered below the chart |
| B11 | Colour-code by confidence (optional) | Met | Two-band `linearGradient` (teal to grey) |
| B12 | Mobile-first | Met | Verified at 375x812, no horizontal scroll |
| B13 | Follow existing tokens; **no new chart library** if one exists | Met | No dependency added — reused `CashProjectionCard`'s inline-SVG technique |
| B14 | Out of scope respected (no multi-gateway, no Taty simulator, no execution) | Met | Read-only; nothing written to `approval_queue` |

---

## 4. Deviations, and why

**D-1 — Confidence bands: no `"alta"` tier.**
The masterprompt ties `"alta"` to weeks 1-4 *"basadas en CxC/CxP conocidas"*. Those tables do not
exist, so weeks 1-4 rest on the same trend extrapolation as the rest. Shipping `"alta"` would claim
a grounding the model does not have, to a PyME owner making cash decisions. Shipped `media` (1-4) /
`baja` (5-13); `"alta"` is reserved for a future `historico_mas_cxc_cxp` methodology. **This
deviation is deliberate and is the safer reading of the prompt's own stated intent** ("Esto es
honesto con el usuario y evita prometer precisión que el modelo no tiene").

**D-2 — `caja_proyectada` is in minor units (cents), not whole COP.**
The prompt's example shows `8200000` reading as whole pesos. The repo's hard convention is that the
backend returns COP in minor units and the frontend divides by 100 (`contexia-app/CLAUDE.md`,
"Unidades"). Followed the repo. Frontend and narrative both divide correctly.

**D-3 — `generado_en` is UTC (`...Z`), not Colombia time (`-05:00`).**
The prompt's example shows `-05:00`. Ships as UTC with an explicit `Z`, so it is unambiguous, but it
is not what the example showed. Cosmetic; listed for completeness, not fixed.

**D-4 — Endpoint mounted on its own PWA router.**
The prompt allowed *"o el nombre que siga la convención de rutas ya existente en el repo"*. The repo
splits the agent surface (`/agents/*`) from the PWA read surface (`/financials`, `/centinela`,
`/tenant`). The endpoint sits at `/radar` on a second router in `radar_endpoints.py` — satisfying
both the prompt's literal path and the repo's convention. This was not free: see section 6, P-1.

---

## 5. Definition of Done — scored

| # | DoD item | Status | Notes |
|---|---|---|---|
| C1 | OpenSpec proposal approved before touching code | **Met** | proposal → design → specs → tasks, then apply |
| C2 | Responds in < 2s | **Met** | Measured against real Supabase: **1.222s / 0.368s / 0.202s**. Caveat: near-empty tables, so this times the round-trip, not real volume |
| C3 | Respects RLS + explicit test that one tenant never sees another's data | **Partial** | `TestTenantIsolation` passes and is the *right* test — but it verifies **application-level** `.eq("tenant_id", ...)` scoping. Database RLS is `USING (true)` (section 2, A1), so the DoD's premise does not hold |
| C4 | Projection computed on **real Shadow GL data** of a test tenant, not a hardcoded mock | **Partial** | The service was executed against the real production DB for 3 tenants; all returned `sin_historico_suficiente` — correct, because no tenant has 4+ weeks of history. **The chart-with-numbers path has never run against real data anywhere**, because such data does not exist yet |
| C5 | `/app/radar` shows chart + narrative, responsive, reviewed copy | **Met** | Verified live and at mobile width |
| C6 | Honest empty state for a tenant without enough history | **Met** | And it is what **100% of tenants see today** |
| C7 | Health check + production deploy (Stage 11) | **Met** | Railway `SUCCESS` + `/api/v1/health` 200; Vercel serving the card; `sw.js` v18 |
| C8 | Analytics event to measure adoption (KPI >= 40% weekly) | **Not done** | Descoped mid-change: no analytics pattern existed in `contexia-app` to reuse. Closed now — see section 7 |

**Score: 6 met, 2 partial, 1 not done.**

---

## 6. Process failures in this change

| # | Failure | Consequence | Rule now in place |
|---|---|---|---|
| P-1 | Declared the endpoint "done" without checking where `presentation/router.py` mounts the radar router | **404 in production** on the documented path | `TestRouteRegistration` pins the mounted path against `api_router`; a direct call to the handler is not proof |
| P-2 | Synced the static export into `app/` without checking what Vercel actually serves | Endpoint live while `/app/radar` still served the old page | Sync target is the repo root; verify the file the rewrite resolves to (`app/radar.html`) |
| P-3 | Bumped `contexia-app/public/sw.js` and `app/sw.js`, not the live repo-root `sw.js` | Would have pinned viewers to the stale shell | Bump the one `curl https://contexia.online/sw.js` returns |
| P-4 | Answered pre-question #4 ("tenant de prueba") with "Cliente Cero" **without checking it had usable data** | DoD item C4 was unverifiable from the start; only discovered after deploying | Answering "which test tenant" means querying its row counts, not naming it |
| P-5 | Used a broad `git add openspec/` when committing the archive | Swept another session's in-flight OpenSpec edits into my commit | Stage explicit paths. *(Checked: no data lost — the deletions were the pending half of archives that session had already completed, and both archive copies exist)* |

P-1 through P-3 were each caught only by production, not by the test suite or by review. All three
are now covered by a test or a written rule.

---

## 7. What is still missing, and what happens to it

| Gap | Disposition |
|---|---|
| **C8 — adoption tracking event** | Closed now, as its own OpenSpec change (`radar-adoption-tracking`). It cannot be added to `radar-cash-projection-13w`, which is archived |
| **C4 — projection verified against real numbers** | **Cannot be closed by engineering.** Needs a tenant with 4+ weeks of real Shadow GL history. Blocked on ingestion (`real-data-ingestion-mvp`), not on this module |
| **C3 / A1 — permissive RLS on the Shadow GL** | **Founder decision required.** Tightening the `*_anon_all` policies to tenant-scoped ones is a security change affecting every reader of those tables, well beyond this module. Recommended as its own change, reviewing `set_hermes_tunnel`'s anon-executable `SECURITY DEFINER` grant in the same pass |
| **KPI "error medio < 15% en las primeras 2 semanas"** | Not measurable until C4 is unblocked — no projection has been produced yet to measure error against |

---

## 8. One-line summary for the founder

The Radar de Caja is live, correct, and honest about its own limits — and it **will show the "not
enough history yet" state to every client until the Shadow GL actually has data**. While auditing
it, the multi-tenant isolation on those same ledger tables turned out to be application-level only,
not enforced by the database.
