# Stage 11 deployment report — crm-alta-tiered-provisioning

- Date: 2026-08-28
- Commit: `2c9aff1` (`feat: add plan-tier selection + invite-link provisioning to B2B alta`)

## Backend (Railway `production-175a`)

- Pushed to `main` → Railway auto-deployed. Deployment `355a7764-f9d6-47b6-858f-be91c4bd9efa`:
  `SUCCESS`.
- Post-deploy `POST /api/v1/crm/b2b/clients` briefly returned `502` (documented cold-start
  window). Re-checked with a bounded polling loop (5s interval, capped at 20 attempts): healthy
  after ~35s.
- Verified live: `POST /api/v1/crm/b2b/clients` with no auth header returns `401`, not `500` —
  confirms the new `plan_tier` field and the `generate_link`-based provisioning path didn't
  introduce a crash on the request-validation path, and auth is still enforced correctly.

## Frontend (Vercel)

- Deployment `dpl_ADaej58jWdG4Xpa7xnBg6JUAibCB` (commit `2c9aff1`): `state: "READY"`, aliased to
  `contexia.online`/`www.contexia.online`.

## What was NOT verified live (founder action, same deferred pattern as Subdomains 1-4)

An actual end-to-end alta submission through the Búnker UI (selecting a tier, confirming the
invite link appears and is copyable, confirming the linked account can log in) requires an
authenticated admin session — this agent does not handle plaintext credentials. Covered instead
by 35 passing pytest cases (independently re-verified by the reviewer, including direct
inspection of the installed `gotrue` package to confirm the `generate_link` API shape matches
what's called in production).

**FOUNDER ACTION (not blocking):** create one throwaway B2B client from the Búnker with a tier
other than the default and a real email you control, confirm the invite link appears and is
copyable, click it, and confirm you land in a working login flow for that tenant. Delete the
throwaway client afterward.

## Conclusion

All 13 changed/added files committed and pushed. Both deploy targets green. Auth wiring on the
touched endpoint verified consistent with pre-existing behavior. Ready to archive.
