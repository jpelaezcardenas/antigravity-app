## Context

Change A shipped and archived the B2B half of the CRM cockpit (`crm-b2b-retainers-cockpit`):
`b2b_clients`/`b2b_payments` tables, `crm_service.py`/`crm_endpoints.py` behind `CRM_CANONICAL`,
and a `CrmVentasSection.tsx` tab shell where "B2C / Renta Natural" is currently a static
placeholder. This change fills that placeholder in with a real funnel.

Verified facts carried over from Change A (still true, re-confirmed where it matters):
- `tenants.is_cliente_cero` resolves the single owning tenant; `user_roles.role` is the live
  `role_type` enum (`admin | finance | marketing | growth | operator | viewer`) — RLS uses
  `role = 'admin'`, not the JWT `app_metadata` label set.
- Backend reads use `get_service_supabase()` (service-role), not `get_supabase()` (anon) — there is
  no per-request end-user Supabase session, so an anon-key query against admin-only RLS always
  returns zero rows regardless of caller identity.
- `contexia-wizard/`'s Wompi/leads/payments tables live in a **different** Supabase project
  (`wzqymuzpjbagnbgsiqig`) — reuse their column *shape* for `crm_wompi_transactions`, never FK
  across projects.
- No drag-and-drop library exists in this repo; `IdeasTab.tsx`'s click-to-advance Kanban idiom is
  the established pattern for board UIs here.

## Goals / Non-Goals

**Goals:**
- Give the B2C tab a real, live Kanban funnel: `NUEVOS → PROSPECTOS → POR_APROBAR →
  LISTOS_CONTADORA`, backed by real Supabase tables, on seeded data.
- Model a payment-approval HITL gate now, even though the underlying payment verification is
  simulated — so the *workflow* (Juan David clicks "Aprobar Pago") is real and testable before
  Wompi integration exists.
- Give Taty's future sales-router logic (Change D) a persistence target now (`crm_tax_profiles`)
  so that change doesn't also need a schema migration.
- Keep it small and independently deployable, same as Change A.

**Non-Goals:**
- Real Wompi payment link generation or webhook verification — gated on Wompi keys (Change C).
  `crm_wompi_transactions` rows in this change come only from the seed, never from a live payment.
- Taty/WhatsApp channel logic — a separate change (D) that will read/write `crm_tax_profiles` and
  `crm_leads` but isn't built here.
- Any Hermes/Manus/agentic automation — later changes (E–G).
- A second approval-queue integration: this change's `POST /crm/leads/{id}/approve-payment` is a
  dedicated, single-purpose endpoint (see Decision 3), not routed through the Supabase
  `approval_queue` table used elsewhere in the backend.

## Decisions

1. **Three tables, not one wide `crm_leads` table with jsonb blobs.** `crm_tax_profiles` and
   `crm_wompi_transactions` are separate tables with their own PKs/FKs to `crm_leads`, rather than
   nested jsonb columns on `crm_leads` itself. *Rationale*: `crm_tax_profiles` is explicitly Taty's
   memory (owned by a future, different subsystem — Change D) and `crm_wompi_transactions` will
   eventually be written by a webhook handler (Change C) independent of lead-stage writes;
   separate tables let those future changes touch their own table without contending on
   `crm_leads` row locks or schema. *Alternative considered*: a single denormalized `crm_leads`
   row with `tax_profile jsonb` and `wompi jsonb` columns. Rejected — couples three different
   future write-paths (Kanban advance, Taty intake, Wompi webhook) to one row, and loses the
   `UNIQUE(lead_id)` / `reference UNIQUE` constraints a proper table gives for free.

2. **`crm_leads.stage` is a plain `text` with a `CHECK` constraint, not a Postgres enum type.**
   Matches `b2b_clients.status`'s existing convention from Change A (`text` + `CHECK`), not a new
   enum type — consistent with this change reusing Change A's established patterns rather than
   introducing a new one. *Alternative considered*: a dedicated `lead_stage` enum type. Rejected —
   enum types are more painful to extend later (`ALTER TYPE ... ADD VALUE` has transaction
   restrictions in Postgres); a `CHECK` constraint is trivially replaced by a migration that also
   backfills, if a 5th stage is ever needed.

3. **The payment-approval HITL gate is a dedicated `POST /crm/leads/{id}/approve-payment`
   endpoint, not routed through the central Supabase `approval_queue`.** The central queue
   (`approval_queue_service.py`) is built around journal-entry-shaped drafts validated by the
   accounting `agent_critic` (`JOURNAL_ENTRY_DRAFT_TYPES`) — forcing a lead-payment approval
   through that shape adds indirection with no benefit yet, since there's no Critic/evaluator step
   for this domain and no other consumer of a `crm_payment_approval` draft type. *Alternative
   considered*: enqueue via `approval_queue_service.enqueue_draft(draft_type="crm_payment_approval")`
   for a unified audit trail across domains. Rejected for *now* — noted as an explicit fast-follow
   once the Sell Machine's agentic layer (Change F, Hermes→Manus bridge) needs a single audit
   surface to poll; a dedicated endpoint today is simpler and this change doesn't block that
   future unification (the dedicated endpoint can start writing to both places later without an
   API shape change).

4. **`crm_wompi_transactions` mirrors the wizard's `payments` table column names exactly**
   (`reference`, `wompi_transaction_id`, `wompi_raw_response`, `amount_cents`, `status`,
   `customer_email/phone/name`) even though it's a separate table in a separate project.
   *Rationale*: when Change C wires real Wompi webhook handling, the same verification/mapping
   logic (`SHA256(reference+amountInCents+currency+integritySecret)`) can be ported with minimal
   translation. *Alternative considered*: design a fresh, more "correct" shape for this table.
   Rejected — no benefit today, and diverging column names would double the translation work when
   Change C lands.

5. **Seed data is idempotent via `ON CONFLICT (tenant_id, whatsapp_phone) DO UPDATE`** on
   `crm_leads` (mirroring Change A's `ON CONFLICT` seed pattern), so re-running the seed migration
   is a safe no-op — same idempotency bar as Change A.

6. **Frontend: `B2cKanbanTab.tsx` clones `IdeasTab.tsx`'s exact idiom** — `COLUMNS` array of the 4
   stages, `useMemo` grouping by stage, a `move(leadId, stage)` handler that awaits
   `advanceCrmLead()` then reloads, and a stage-conditional "Aprobar Pago" button that only renders
   on `POR_APROBAR` cards. No drag-and-drop, no new libraries — matches the repo-wide convention
   already established by Change A and Social Ops.

## Risks / Trade-offs

- **[Risk] Same open-endpoint posture as Change A (accepted Risk R1 there).** These new endpoints
  add more surface with the same "no request-level auth beyond the Búnker edge-middleware gate +
  feature flag" posture. → **Mitigation**: no new risk introduced beyond what Change A already
  accepted; the follow-up recommendation from Change A's deployment report (add request-level auth
  before this surface grows further) applies more urgently now that a payment-approval action
  exists behind it — flag this explicitly in this change's own deployment report as a second,
  stronger nudge toward that follow-up.
- **[Risk] Two disjoint approval mechanisms** (Supabase `approval_queue` used elsewhere vs. this
  change's dedicated endpoint) could confuse future readers about "the" approval gate. →
  **Mitigation**: documented explicitly in Decision 3, with a called-out fast-follow path (mirror
  an audit row into `approval_queue` once Change F needs it) rather than silently diverging.
- **[Risk] Seeded `crm_wompi_transactions` rows could be mistaken for real payment activity** once
  this ships, since the table/columns look production-ready. → **Mitigation**: seed data uses
  obviously-fake `reference` values (e.g. `SEED-REF-...`) and this is called out in the deployment
  report and in a code comment on the seed migration.
- **[Trade-off] No tax-profile UI in this change** — `crm_tax_profiles` is seeded and readable via
  `GET /crm/leads/{id}/tax-profile` but the Kanban card itself doesn't render tax-profile detail in
  this pass; a lead card shows name/phone/stage/score only. Full profile display can be a
  fast-follow once Taty (Change D) is actually writing real profile data — building a rich UI
  against seed data now would likely need rework once real fields stabilize.

## Migration Plan

1. Apply `apps/backend/migrations/0022_crm_b2c_sell_machine.sql` (DDL: `crm_leads`,
   `crm_tax_profiles`, `crm_wompi_transactions`, indexes, RLS, triggers) via Supabase MCP
   `apply_migration`.
2. Apply `apps/backend/migrations/0023_seed_crm_b2c_leads.sql` (sample leads across all 4 stages,
   idempotent upsert).
3. Deploy backend (Railway) — new endpoints ship behind the already-live `CRM_CANONICAL` flag, so
   no new flag/dark-deploy step is needed; verify shape with the flag already on (Change A's
   deployment already flipped it in production).
4. Deploy frontend (Vercel) with `B2cKanbanTab.tsx` replacing the placeholder.
5. **Rollback**: the new tables are additive-only; if the B2C tab needs to be pulled, revert the
   frontend commit that swaps the placeholder back in (endpoints can stay live and unused — no
   flag to flip back, since `CRM_CANONICAL` also gates the already-shipped B2B tab and must stay
   on).

## Open Questions

- Exact wording for the "Aprobar Pago" button's confirmation UX (single click vs. a confirm step) —
  defaulting to single-click matching `IdeasTab.tsx`'s existing action buttons; revisit if this
  proves too easy to mis-click once real payments are at stake (Change C).
- Whether `crm_tax_profiles.topes` should have a more specific shape than `jsonb` — deferring to
  Change D (Taty) to define the exact fields it needs, since this change doesn't populate it with
  anything beyond a seed placeholder.
