## Context

Three OpenSpec changes already carry the exact code needed for a real Renta Natural sale, opened
independently by different sessions with no shared closing criterion:

| Change | Verified state (2026-09-10, read from `tasks.md`) | Owns |
|---|---|---|
| `taty-channel-consolidation` | Tasks 1-3, 5 done (signature verification, bridge rewiring, dead-code removal). Task 4 blocked. Tasks 6-9 (E2E, Stage 11, archive) not started. | single live WhatsApp webhook |
| `whatsapp-durable-inbox` | Tasks 1-3 done (inbound event table, ingestion, pull/ack API). Tasks 4-8 not started. | durable inbound queue |
| `taty-wompi-entidad-a-remittance` | 0% — every task from 0.1 (confirm with Wompi support) onward is unstarted. | Entidad A payout leg |
| `taty-document-collection-wiring` (reference only) | Deployed to production, Stage 11 closed (`reports/2026-09-10-deployment.md`). Only task 6 (synthetic-doc verification) open. | document intake — not reopened here |

A fourth, unrelated system already exists at ~70% completion: `apps/hermes-manus-poller` plus the
`hermes-manus-poller`/`hermes-manus-execution-bridge` OpenSpec capabilities, which drive paid
Meta/Instagram acquisition via Manus. Two founder-supplied playbooks
(`Informe final — Preparación de Manus...` and `Playbook de Ejecución de Campaña — Manus AI`)
describe that circuit's remaining gaps (webhook registration, three ready-to-integrate patches).
That system feeds leads *into* the WhatsApp channel this change consolidates, but its own gaps are
tracked under its own capability and are explicitly not re-scoped here — conflating "get someone to
message Taty" with "close the sale once they do" would blur two independently-failing systems into
one change with no clear owner for either failure mode.

Per CLAUDE.md §7 (post-apply changes are spec updates, not quick fixes) and the founder's explicit
instruction (2026-09-10), this change absorbs the three blocking changes' remaining task scope
rather than editing their directories directly — they stay as historical record; this change is
where the work actually happens and where Stage 11 closes.

## Goals / Non-Goals

**Goals:**
- One live, signed WhatsApp webhook that Meta can point at without ambiguity.
- No inbound WhatsApp message lost to a bridge crash or restart.
- A working Entidad A payout rail, verified with one real transaction.
- A single, explicit go/no-go checklist for "first sale complete" that spans all three legs.

**Non-Goals:**
- Rebuilding or re-scoping the Manus paid-acquisition circuit (`hermes-manus-poller`).
- Any B2B tier, `plan_features.py`, Pulso, GPS, or Agentic OS change.
- A second or third Renta Natural sale, or any volume/scale guarantee — the closing criterion is
  exactly one verified transaction end to end, matching the founder's framing ("primera venta de
  ciclo completo, no más construcción").
- Reopening `taty-document-collection-wiring` — its remaining task 6 is a pre-flight check this
  change references but does not own.

## Decisions

**Decision 1 — Absorb, don't merge directories.** The three source changes'
`openspec/changes/<name>/` directories are left untouched (per the founder's answer to the
absorption question: "Absorber los 3 changes completos"). This change's `tasks.md` restates their
remaining tasks under its own numbering, with a back-reference to the source task ID so the
original context (why a decision was made, what tests already exist) isn't lost. When this change
archives, the sync step (Stage 9/archive) closes all four specs together, not just this one's new
capability.

**Decision 2 — Founder-dependent blockers are tracked tasks, not assumptions.** Two inputs cannot
be produced by an agent:
- The Meta App Secret (Meta App Dashboard → Settings → Basic) and the `phone_number_id` decision
  that `taty-channel-consolidation` task 4 needs. Without it, no webhook can be pointed anywhere,
  and this change cannot proceed past channel consolidation.
- Confirmation from Wompi support on whether "Pagos a Terceros" is the right product for remitting
  to Entidad A, and Entidad A's real payout beneficiary details (bank account, account type,
  document). `taty-wompi-entidad-a-remittance` tasks 0.1-0.6 depend on this.

Both are modeled as blocking tasks owned by the founder, not defaulted or guessed — consistent with
CLAUDE.md's "question assumptions" principle and the repo's standing rule that a missing input
means STOP, not fabricate (ARCHITECTURE.md §9, the 2026-06-29 incident).

**Decision 3 — SUPERSEDED 2026-09-10, see Decision 3b.** Original text (kept for history): "Merchant
of record is Entidad A, unconditionally. Wompi already collects payment under Entidad B credentials
(existing `wompi-payment-integration` capability, live in production). Renta Natural is an Entidad A
service. This change does not touch how money is *collected* — it adds the *remittance* leg: after
a Renta Natural transaction settles, Entidad A must receive the net proceeds via a tracked payout,
not a manual bank transfer with no audit trail." This decision assumed Wompi collection was the
payment path for the first sale; the founder has since deprioritized that assumption (see 3b).

**Decision 3b — First sale is cash/QR in person, not a Wompi flow (founder decision, 2026-09-10).**
Most Renta Natural clients meet Tatiana in person and pay cash, or a direct transfer via a key/QR
she hands them — not through Wompi's checkout. The Wompi Entidad A remittance rail (Decision 3) is
therefore deferred, not built for this change: it solved a problem ("how does Entidad A get paid
once Wompi collects for it") that doesn't arise on the actual first-sale path. This is a
simplification, not a downgrade — it removes this change's dependency on Bloqueo 2 (Wompi support
confirmation, Entidad A payout beneficiary details) entirely. `wompi-payment-integration` (existing,
live, Entidad B-credentialed) is untouched and keeps working for whichever future clients do pay by
card/PSE through Wompi; this change simply stops requiring the remittance leg on top of it to close.
If cash-first turns out to need its own tracking (e.g. Tatiana needs a system record of a cash sale
beyond her own bookkeeping), that is new, smaller scope for a future change — not assumed here.

**Decision 4 — Stage 11 for this change means a verified sale, not just green deploys (REVISED
2026-09-10 per Decision 3b).** Per the founder's explicit framing, "terminado" for this change
requires: (a) the channel-consolidation and durable-inbox code deployed and passing their own task
gates, and (b) one real, human-approved Renta Natural sale observed end to end (WhatsApp intake →
Taty triage → Tatiana's quote → in-person meeting → cash/QR payment received by Tatiana → service
delivered). The Wompi remittance leg is no longer part of (b) — a Wompi transaction is not required
for the closing verification. Code-complete without (b) is documented as "not done," matching
CLAUDE.md §8's "Without Stage 11: Change is incomplete, even if all tasks say done."

## Risks / Trade-offs

- **[Risk] The Meta App Secret / `phone_number_id` blocker could stall indefinitely** since it's
  outside agent control → **Mitigation**: task is flagged Day 1 as the critical path item; every
  other absorbed task (durable inbox, Wompi payout) can proceed in parallel since none of them
  depend on the webhook being live yet — only the final E2E verification does.
- **[Risk] Wompi Pagos a Terceros may not exist or may not fit Entidad A's payout shape** (task 0.1
  is explicitly a confirmation step, not an assumption) → **Mitigation**: design defers the payout
  service's exact API contract to task 0's findings; if Pagos a Terceros doesn't apply, the
  fallback (manual reconciled transfer with the same `remittance_status` tracking table) is
  designed to require no schema change, only a different `wompi_payout_service.py` implementation.
- **[Risk] Absorbing three changes' remaining scope into one could make `tasks.md` hard to track**
  → **Mitigation**: tasks.md groups tasks by absorbed-change origin with explicit back-references,
  so progress against each original change remains individually auditable.
- **[Trade-off] Real-money smoke test (task under Decision 4) is inherently risky** — it moves
  actual funds → **Mitigation**: requires explicit founder approval before execution, sandbox test
  first, and is the last task before Stage 11 sign-off, not an early validation step.

## Migration Plan

1. Land channel consolidation (Meta secret + phone_number_id resolution) — founder-blocked, first.
2. Land durable inbox (poller, Taty Bot user, migration `0036` — founder-approved before applying).
3. Land Wompi remittance rail (Wompi-support-confirmed, migration for `remittance_status` —
   founder-approved before applying).
4. Run sandbox smoke test for the payout rail.
5. Run the one real-money verification transaction, founder-approved.
6. Stage 11: commit, deploy, verify production, write the deployment report referencing all three
   absorbed changes.
7. Sync specs for all four capabilities (three absorbed + `renta-natural-sale-verification`) and
   archive this change plus the three source changes together.

Rollback: each absorbed piece (webhook, poller, payout service) ships behind its own existing
feature-flag/env-gate pattern already established in the source changes' designs (e.g.
`INTERNAL_API_KEY` fail-closed for internal endpoints); no new rollback mechanism is introduced.

## Open Questions

- **RESUELTA 2026-09-10:** Meta App Secret obtenido, `phone_number_id` (`1296858506837233`)
  confirmado canónico, env vars en Railway. Pendiente solo la acción manual 1.3b (Verify Token en
  Meta Dashboard) y el drill local 1.5 (requiere el laptop del fundador).
- **RESUELTA / REENCUADRADA 2026-09-10 (Decision 3b):** ya no es un bloqueo de este change — Wompi
  Pagos a Terceros queda diferido, el primer cierre se hace en efectivo/QR en persona.
- **DECISIÓN PENDIENTE DEL FUNDADOR:** approve applying migration `0036` (whatsapp inbound events)
  to Supabase production — not auto-applied. The remittance-tracking migration (`0053`) stays
  unapplied indefinitely per Decision 3b, not pending founder action right now.
- Whether the Manus paid-acquisition circuit's remaining gaps (webhook registration, B3/B4/B5
  patches) should be scheduled in a follow-up change once this one closes — noted, not decided
  here, since it's out of scope per Non-Goals.
- Whether a cash/QR sale needs any system-of-record trace beyond Tatiana's own bookkeeping — not
  assumed here per Decision 3b; raise as its own small change if it turns out to matter.
