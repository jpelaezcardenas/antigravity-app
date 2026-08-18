# Supabase & MCP Administration — Contexia

**Purpose:** single source of truth for Supabase project identity, which MCP path to use, known
data-integrity state, and the security backlog. Update this file whenever a session does Supabase
administration (new migration, new security finding, secret rotation) instead of leaving that
knowledge scattered across session memory.

**Last verified against live state:** 2026-08-18.

---

## 1. Canonical Supabase project

| Field | Value |
|---|---|
| Project ref | `kpynymwghfwshvcvevxq` |
| Name | `contexia-content-os` |
| Region | `us-west-2` |
| Status | `ACTIVE_HEALTHY` |
| Postgres | 17.6.1.121 |

**Do not use** `wzqymuzpjbagnbgsiqig` (name: `Contexia`, region `us-east-1`) — status `INACTIVE`.
It is a decommissioned project from before the canonical one was created (2026-05-17). If any tool,
script, or memory references it, that reference is stale.

## 2. Which MCP path to use

Two separate Supabase MCP integrations currently exist. Neither is wrong — pick based on where
you're working:

### Path A — Claude connector (claude.ai / desktop chats)
Account-level OAuth connection managed outside this repo (shows up as an internal connector ID,
not declared in any `.mcp.json`). Broad access — can see every Supabase project on the account.
**Use for:** ad hoc administration from a claude.ai/desktop chat (like this one). No local secret
to manage.

### Path B — Local `.mcp.json` (Claude Code CLI)
Declared in `C:\Users\contexia\Projects\.mcp.json`, using the official
`@supabase/mcp-server-supabase` package, correctly scoped to the canonical project via
`--project-ref=kpynymwghfwshvcvevxq`. **Use for:** Claude Code CLI sessions launched from
`C:\Users\contexia\Projects`.

**Known issue (being fixed 2026-08-18):** the `SUPABASE_ACCESS_TOKEN` for Path B was hardcoded in
plaintext in `.mcp.json`. That token is a Management API Personal Access Token — account-level,
distinct from `SUPABASE_ANON_KEY`/`SUPABASE_SERVICE_ROLE_KEY`/`DATABASE_URL` (which the production
backend uses and are unaffected by anything here). It is being moved to an environment variable
(`SUPABASE_MCP_TOKEN`) instead of a literal value in the file — see the repo-root `.mcp.json` for
current state, and rotate it periodically via the Supabase dashboard (Account → Access Tokens).

**Rule of thumb:** for one-off admin/maintenance work, either path is fine. For scripted/automated
work, prefer Path B once its token is environment-managed.

## 3. Shadow GL data-integrity status (Cliente Cero + all tenants)

Shadow GL (`erp_journal_entries`, `erp_journal_lines`, `dian_xml_documents`) is the canonical
ledger behind Contexia's "Caja Real" flow (see `ARCHITECTURE.md` → "Flujo estrella") — it is not a
side experiment, it is the mechanism the whole product's core promise depends on, live for the ~10
provisioned B2B tenants plus Cliente Cero (`ARCHITECTURE.md` Decision #13, #16).

**As of 2026-08-18 (updated same day, see incident note below):**

- `dian_xml_documents`: **0 rows.** Originally 4 (all synthetic — see incident note); the 3
  remaining fabricated-CUFE rows were removed as collateral of a pre-existing test-cleanup bug
  while implementing `shadow-gl-data-integrity-flag`.
- `erp_journal_entries`: **29 rows, all `source='manual'`** — the deliberate, still-active demo
  dataset (`SYNTH-*-SALE`/`SYNTH-*-EXPENSE` rows seeded by migration `0028` for the ~10 real
  per-tenant B2B clients so their Caja Real dashboards aren't empty, kept fresh by a daily
  `pg_cron` job — migration `0035`, `reseed-synth-shadow-gl`, runs 05:10 UTC — that re-dates them
  to "yesterday" every day). **Do not delete or "clean up" these** — the per-tenant `/financials`
  endpoint depends on them showing recent activity. `SYNTH-*-OPEN` rows (opening balance) are
  excluded from the reseed on purpose — re-dating those would corrupt the cumulative balance.
  These 29 rows were **unaffected** by the incident below (confirmed by direct query).
- No real Siigo/DIAN accounting data has been ingested through the ingestion pipeline yet.
- All rows now carry `is_verified_real` (added by `shadow-gl-data-integrity-flag`, see below) —
  currently all `false`, correctly, since none of the remaining data is a real Siigo/DIAN export.

**Incident, 2026-08-18 (disclosed, not hidden):** while running the regression test suite for
`shadow-gl-data-integrity-flag` (`RUN_SHADOW_GL=1 pytest test_shadow_gl_integration.py`), a
pre-existing, unrelated test class (`TestShadowGLIntegrationWithDB`) has an autouse cleanup
fixture that unconditionally deletes ALL `erp_journal_entries`/`erp_journal_lines`/
`dian_xml_documents` rows for the Cliente Cero tenant after every test — including rows it didn't
create — and pytest runs `yield`-based cleanup even when the test itself fails. That class's tests
were already failing for an unrelated pre-existing reason (stale English-header CSV fixture vs. the
now-Spanish-header parser — see `task_718da7b8` follow-up), but the cleanup still ran. Result: the
44 Cliente-Cero test/fixture rows previously documented here as "safe to eventually clean up" and
the 3 remaining `dian_xml_documents` fixture rows were deleted for real, earlier than planned and
without deliberate intent. Confirmed no impact on the 29 load-bearing SYNTH rows or on anything a
real client/dashboard reads. Founder was informed immediately and chose to accept the loss (synthetic
data, zero product dependency) rather than attempt a partial restore (an entries-only restore from
a partial snapshot would have left journal entries with no debit/credit lines — worse than absent).
**Lesson carried forward:** before running any `RUN_SHADOW_GL=1` test file against the live
project again, audit every class's cleanup fixture in that file first — finding one instance of
"deletes more than it created" doesn't mean it's the only one. (Both affected fixtures —
`test_shadow_gl_siigo_csv.py::TestIngestSiigoCSVPersistence` and
`test_shadow_gl_integration.py::TestShadowGLIntegrationWithDB` — were fixed in the same change to
snapshot-then-diff instead of delete-all, so this specific failure mode cannot recur.)

**`is_verified_real` is now live in production** (deployed 2026-08-18, commit `f984460`, verified
via curl against `https://antigravity-app-production-175a.up.railway.app` for all three ingestion
endpoints: omitting the flag persists `false`, `?is_verified_real=true` persists `true`). See
`openspec/changes/shadow-gl-data-integrity-flag/` for full artifacts and the deployment report.

**Why this matters:** a prior session's "Phase 5 COMPLETE — LIVE" reports declared this pipeline
production-ready with real data. It wasn't — confirmed independently by the 2026-08-13 tech-debt
audit, which found `shadow-gl-real-data-ingestion` 0% done and archived it as deferred, not
completed. Don't trust "done/deployed" status docs without checking the DB directly (see root
`CLAUDE.md`'s verification rule).

**Real data source going forward:** Siigo — Contexia already pays for the subscription; the
accountant exports XML DIAN / CSV Siigo manually. This is exactly what the existing manual-upload
endpoints were built for (`POST /api/v1/shadow-gl/dian-xml/ingest`,
`POST /api/v1/shadow-gl/siigo-csv/ingest`) — no new integration is planned, just real files instead
of fixtures.

**Data-integrity gate (OpenSpec change `shadow-gl-data-integrity-flag`, in progress):** an additive
`is_verified_real BOOLEAN DEFAULT false` column on both tables, backfilled `false` for all existing
rows, set `true` only through an explicit flag on ingestion once real Siigo/DIAN files are
uploaded. Any report treating Shadow GL as Contexia's "libro contable canónico" should filter
`WHERE is_verified_real = true`.

## 4. RLS status — documented, not "resolved"

- `usuarios` and `telegram_chat_mappings`: RLS is **enabled** but has **zero policies**.
- The production backend authenticates to Supabase with `SUPABASE_SERVICE_ROLE_KEY`, which
  **bypasses RLS entirely**. So RLS-enabled-with-no-policy is not adding real protection today for
  backend traffic — it only blocks direct `anon`/`authenticated`-key access from outside the
  backend, which isn't a path these two tables are exposed through today anyway.
- **This is documented as a neutral/no-op state, deliberately, not claimed as a fix.** If a future
  session wants real protection here, it needs policies designed against the actual auth model
  (JWT-based per-tenant resolution, see `ARCHITECTURE.md` Decision #13), not just "RLS on."

## 5. Security backlog — PARKED (founder decision, 2026-08-18)

Found during this audit, explicitly **not being touched right now** per founder instruction — kept
here only so it's not lost and isn't mistaken for "nobody knows":

- 4 `SECURITY DEFINER` functions executable by `anon`/`authenticated` without login:
  `set_hermes_tunnel(url, token)`, `refresh_shadow_gl_discrepancies()`, `rls_auto_enable()`,
  `handle_new_user_default_role()`. `set_hermes_tunnel` is the highest-risk one — it can reconfigure
  the Hermes tunnel URL/token via public REST API (`/rest/v1/rpc/set_hermes_tunnel`).
- 4 `SECURITY DEFINER` views: `contenido_por_aprobar`, `vista_rendimiento_contenido`,
  `dashboard_semanal`, `ideas_backlog`.
- `vector` extension installed in the `public` schema (should live in a dedicated schema).
- Materialized view `shadow_gl_discrepancies` selectable via the Data API by `anon`/`authenticated`.
- Leaked password protection disabled in Supabase Auth.
- RLS-enabled-no-policy on `usuarios`/`telegram_chat_mappings` (see §4 — documented, not a fix).

Run `get_advisors(type="security")` against `kpynymwghfwshvcvevxq` any time to re-check this list.

## 6. Other administration items discovered during this audit (informational only)

Not part of the security backlog above, but relevant "admin state" surfaced while investigating —
not acted on, just recorded so it isn't lost:

- **Migration `0034_rescope_centinela_alerts_tenant.sql`** (`ARCHITECTURE.md` Decision #15) is
  written but **not applied** — it would fix ~40 historical Centinela alerts mis-tagged with the
  wrong `tenant_id` due to a since-fixed bug in Pulso's filter. Needs founder approval before
  applying (per the decision's own note).
- **Migration numbering collision already happened once**: two parallel sessions both generated
  `0033_*.sql` for unrelated changes (approval_queue tenant scoping vs. Centinela rescoping) on
  2026-07-23; one was renamed to `0034` after the fact. Worth checking the next migration number
  against `apps/backend/migrations/` directly before creating a new one, not just against memory.
- Local Bitwarden master password rotated 2026-07-05 (`Lindafea0712*` → `Lindafea0712!`) per
  `ARCHITECTURE.md` Decision #11/#12 — the Supabase PAT rotation in §2 above follows the same
  pattern (Bitwarden-managed, not hardcoded).

## 7. Maintenance rule for this document

Whenever a session in this thread (or any future thread) does Supabase administration — applies a
migration, rotates a secret, finds a new security issue, changes which MCP path is preferred —
update this file in the same change, the same way `ARCHITECTURE.md`'s living-doc rule works for
product architecture. This file is the thing that stops knowledge from re-scattering into session
memory that the next thread has to rediscover from scratch.
