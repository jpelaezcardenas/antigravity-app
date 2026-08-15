# Deployment Report — wompi-production-go-live

**Date:** 2026-08-13
**Status:** Config flipped to production, deployed, and stable. Real-money verification NOT
performed — this is a founder-only action, deliberately never simulated by an agent.

## What is done

Sections 1-4 (config-flip work) were completed and verified prior to this triage session:

- Railway env vars flipped: `WOMPI_ENV=production`, production public/private keys, production
  integrity/events secrets.
- `WOMPI_BASE_URL` confirmed as dead config (unreferenced anywhere except its own declaration) —
  left untouched, no functional impact.
- Railway deployment reached `SUCCESS`; `validate_wompi_config()` passed with the new production
  values (confirmed via a live 200 response and absence of any `ValueError` traceback from that
  function in deployment logs).
- Webhook registered in Wompi's production dashboard, confirmed saved by the founder before the
  config flip proceeded (design.md's own risk-ordering).

## What is explicitly NOT done

**Section 5 (real-money verification) was never executed, simulated, or fabricated.** Per this
change's own `tasks.md`, task 5.1 states: *"STOP. The agent does not execute, simulate, or
fabricate this step."* That instruction is honored here. No payment was made, no
`crm_wompi_transactions` row was checked (6.1 requires 5.1/5.2 first), and the `WOMPI_BASE_URL`
dead-config note and rollback plan for 6.2 are captured here instead, since the report itself
can still be useful before the real-payment step happens.

**Rollback plan** (unchanged from design.md): revert the 5 Railway env vars to their sandbox
values (`WOMPI_ENV=sandbox`, `pub_test_...`, `prv_test_...`, `test_integrity_...`,
`test_events_...`).

## Archival decision (2026-08-13 tech-debt triage)

This change's own task 7.1 ties archiving to real-payment verification being complete. As part of
the broader triage restoring the "one change at a time" invariant across 11 accumulated changes,
this change is archived now with that verification **explicitly left open**, not silently marked
done. The config-flip engineering work is genuinely finished and stable; only a founder action
remains. See `openspec/FOUNDER_ACTIONS_2026-08-13.md` — "Do a real Wompi payment test" (MEDIUM
priority) captures 5.1/5.2/6.1 as the outstanding follow-up. If a real payment is later performed,
whoever verifies it should update this report with the confirmed transaction reference.
