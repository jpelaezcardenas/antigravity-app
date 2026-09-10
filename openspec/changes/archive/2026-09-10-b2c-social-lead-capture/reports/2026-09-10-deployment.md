# Deployment report — b2c-social-lead-capture (2026-09-10)

## Summary

All 6 content tasks (1–6) implemented via the leader/implementer/reviewer harness, running in
parallel with `taty-document-collection-wiring` by explicit founder decision. Deployed to
production and verified live, with one real bug found and fixed during verification.

## What shipped

- `POST /api/v1/crm/social-capture/partial` — public, unauthenticated, IP+phone throttled,
  resolves to Cliente Cero, stamps `crm_leads.source` via `CrmService.whatsapp_intake`'s new
  additive `source` param.
- Landing page at `contexia.online/renta-natural` (URL confirmed by the founder 2026-09-10),
  built in `contexia-app/` (`app/renta-natural/`, `components/renta-natural/`). Partial capture
  fires the first time the WhatsApp number becomes valid; full capture fires on submit — the
  backend's phone throttle makes the second call a safe no-op.
- First-contact WhatsApp message reuses the existing Chatwoot/Taty text-delivery path — no new
  send mechanism.
- Migration `0052_crm_leads_source.sql` (nullable `source` text column, additive, no backfill).

## Deploy steps taken

1. Migration `0052` applied to Supabase (`kpynymwghfwshvcvevxq`) 2026-09-09 with explicit
   founder confirmation. Verified live: `crm_leads.source` is `text`, `is_nullable = 'YES'`.
2. `npm run build` in `contexia-app/` — clean, `/renta-natural` present in the route list.
3. Static export synced per the documented mapping (`out/app/* -> app/`, everything else ->
   repo root, copy-overwrite, no deletion) — same convention as every prior PWA deploy this
   repo has done. `CACHE_VERSION` bumped `v20-2026-09-09` -> `v21-2026-09-10` in both
   `contexia-app/public/sw.js` and the synced root `sw.js`.
4. Commit `1ec9d2b` pushed to `main`. Vercel auto-deployed (`dpl_FFQieg1PM663DqVB1Zp3pXy2xFbW`,
   `READY`, `production`). Railway auto-deployed the backend; `/api/v1/health` returned 200.

## Real bug found during verification (and fixed)

`contexia.online/renta-natural` returned **404** immediately after the Vercel deploy went
`READY`. Root cause: `vercel.json`'s `rewrites` array never got a
`{"source": "/renta-natural", "destination": "/renta-natural.html"}` entry — every other clean
URL this repo serves (`/flujo-detalle`, `/crear-empresa-wizard`, `/app/*`) has one, but this
change's own `tasks.md` never called out `vercel.json` as a file that needed touching, so it was
never in scope for any implementer or reviewer to check. Neither the Next.js build nor the
backend test suite would have caught this — it's purely a static-hosting routing gap, invisible
to both.

Fixed in commit `77f47b9`: added the missing rewrite plus the same `no-store` cache headers
`/flujo-detalle` already uses (this page captures real leads and must never serve a stale
cached version). Re-verified after the fix: `contexia.online/renta-natural` returns 200 with the
real form content (confirmed via `grep` for "Renta Natural"/"WhatsApp" in the response body, not
just the status code).

**Process note for future landing-page-style changes in this repo:** a new public route under
the repo root (not under `/app/`) needs an explicit `vercel.json` rewrite entry, and no artifact
in this session's harness (design.md, tasks.md, the reviewer's checklist) currently prompts for
that. Worth adding to `DEPLOYMENT_STAGE/checklist-vercel.md` per the self-improving-loop rule in
CLAUDE.md §8, so the next similar change catches this before deploy, not after.

## What was verified live

- `GET /api/v1/health` — 200, `{"status":"healthy",...}`.
- `POST /api/v1/crm/social-capture/partial` against the live Railway backend, body
  `{"whatsapp_phone":"573000000000","source":"deploy-smoke-test"}` — 200,
  `{"lead_id":"9385dd0a-...","is_new":true,"stage":"NUEVOS"}`. The row was deleted immediately
  after confirming the shape (`DELETE FROM crm_leads WHERE id = '9385dd0a-...'`) — this was a
  smoke test of the endpoint contract, not a real lead.
- `contexia.online/renta-natural` — 200, real form content present (post-fix).

## Real WhatsApp delivery — verified

The founder authorized a real end-to-end test against his own number (`573504187902`). That
number already had a real `crm_leads` row (`business_interest`, `PROSPECTOS`, created during
this session's earlier Twilio testing) — the first-contact trigger only fires on the `is_new:
True` create path (design.md Decision 4), so with founder's explicit, informed authorization
that row was deleted first. `POST /api/v1/crm/social-capture/partial` was called against the
live Railway backend with that phone number, returned `is_new: true`, and the founder confirmed
the real WhatsApp message ("¡Hola! Soy Taty, la asistente de Contexia...") actually arrived.
Immediately after, the resulting lead's `stage`/`lead_type` were restored to
`PROSPECTOS`/`business_interest` to preserve the founder's real lead record — only those two
fields were overwritten; the row itself is a new id (`6e717c21-...`), not the original
(`2c7f8911-...`).

## Restrictions respected

- `taty-voice-outbound-calls` Tasks 7–9 untouched.
- No migration applied without explicit founder confirmation (0052 was confirmed 2026-09-09).
- No fabricated verification — the WhatsApp-delivery gap above is stated plainly, not glossed
  over.
