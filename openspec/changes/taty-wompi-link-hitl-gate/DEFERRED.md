# taty-wompi-link-hitl-gate — DEFERRED

**Date deferred:** 2026-08-13 (pre-GTM tech-debt triage)
**Status:** 0/16 tasks started. Not archived — left in `changes/` as a tracked, intentional
deferral.

## Why deferred

Restoring the "one change at a time" invariant (HARNESS.md) required triaging 11 accumulated
active changes down to a small number before the GTM integration push. This change has zero
engineering investment yet.

## What already exists (do not duplicate)

`taty-whatsapp-renta-sales-capability` (archived 2026-08-13) task 4.7 verified live that a
`sales_interest`-triggered Wompi HITL gate already exists in production — commit `0839eda` — and
confirmed it is untouched by that change: no automatic link is sent in the reply text, and exactly
one `approval_queue` row lands with `draft_type="wompi_payment_link"`. This change
(`taty-wompi-link-hitl-gate`) appears to formalize/complete that existing gate with proper TDD
coverage (Sections 1-2), not build it from scratch — re-read `proposal.md`/`design.md` against the
current state of `taty_lead_router.py` and `ApprovalQueueService.approve_draft` before resuming,
since the baseline may have shifted since this change was proposed.

## Dependency

Section 5 (founder action: merchant-of-record fix for Entidad A's Wompi account) is out of this
change's scope but tracked as a prerequisite for the gate to matter in production — see
`openspec/FOUNDER_ACTIONS_2026-08-13.md`. `wompi-production-go-live` (archived 2026-08-13) flipped
Wompi to production credentials but real-money verification is still pending a founder-performed
payment — this change's own manual smoke test (3.2) depends on that being resolved first.

## Resume trigger

Pick this back up once Wompi's production real-payment verification (`wompi-production-go-live`'s
open item) is confirmed working, so this gate has a live payment path to test against.
