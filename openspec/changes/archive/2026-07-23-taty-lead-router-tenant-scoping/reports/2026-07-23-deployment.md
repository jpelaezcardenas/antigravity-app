# Deployment Report

- Date: 2026-07-23
- Change: taty-lead-router-tenant-scoping

## Deploy target

This change does not deploy independently. Its branch (`feature/taty-lead-router-tenant-scoping`)
is based on and merges into `feature/chatwoot-hermes-taty-bridge`, which has not yet merged to
`main`. Production deploy (Railway `-175a` for the backend) happens only when the parent branch's
own Stage 11 runs — see `openspec/changes/chatwoot-hermes-taty-bridge/tasks.md` Task Group 14.

Neither `CRM_CANONICAL` nor `WHATSAPP_CANONICAL` (the two feature flags gating the code paths this
change touches) is enabled in production today, so this fix carries zero production behavior
change on its own until both the parent branch merges and those flags are flipped on.

## What ships when the parent branch reaches production

- `CrmService.whatsapp_intake` accepts an optional `full_name` (backward compatible).
- `taty_lead_router.find_or_create_lead` is tenant-scoped (via delegation) instead of the prior
  phone-only lookup — closes a latent cross-tenant correctness gap before `per-tenant-client-access`
  goes live.

## Verification already performed (see Steps 4-5 reports in this same `reports/` directory)

- Automated suite: 58/58 targeted tests passing; full-suite regression independently confirmed
  clean (40 pre-existing, unrelated failures verified byte-identical before/after).
- Manual curl against the live `/api/v1/channels/whatsapp/webhook` endpoint confirmed the corrected
  tenant-scoped delegation path is genuinely reached (traceback-verified), blocked only by a known,
  pre-existing local `SUPABASE_SERVICE_ROLE_KEY` gap unrelated to this change.
