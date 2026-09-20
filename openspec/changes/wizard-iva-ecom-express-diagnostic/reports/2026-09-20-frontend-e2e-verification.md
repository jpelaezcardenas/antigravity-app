# Step 5 Report — Frontend E2E Verification

- Date: 2026-09-20
- Change: wizard-iva-ecom-express-diagnostic
- Agent: Claude Sonnet 5 (Claude Code)

## Environment

- `contexia-wizard` dev server (`npm run dev`, Turbopack, port 3000)
- Browser: built-in Claude Code browser pane

## Blocking Issue Found and Fixed

`npm run build` and the dev server both failed on **every route** (not just the new one) with:
```
./contexia-wizard/app/favicon.ico
Processing image failed
unable to decode image data
Caused by:
- Format error decoding Ico: The PNG is not in RGBA format!
```
Confirmed pre-existing via `git log --oneline -- contexia-wizard/app/favicon.ico` (last touched
2026-09-12, commit `f936b3cb`, unrelated to this change). Fixed by regenerating
`app/favicon.ico` as a proper RGBA ICO from `public/contexia-logo-transparent.png` (already valid
RGBA) using Python/PIL. This was necessary to verify this change at all, and also unblocks any
future Vercel/Turbopack build of the existing 8-step flow, which was equally broken.

## Test Steps and Results

| Step | Action | Result |
|---|---|---|
| 1 | Navigate to `/wizard/iva-ecom` | Renders clean, no console errors (fresh tab) |
| 2 | Step 1: ventas 20.000.000, gasto 5.000.000, margen 35% | Advances to Step 2 |
| 3 | Step 2: Persona Natural, factura electrónicamente: Sí | Advances to Step 3 |
| 4 | Step 3 math | `950.000/mes` = `5.000.000 × 0.19` — correct |
| 5 | Semaphore | Red, "Superas el umbral..." — 240M anualizado > 174.296.500 (3.500 × UVT 49.799) — correct |
| 6 | WhatsApp CTA (email empty) | Opens `wa.me/573106229289` with correctly encoded tier-1 message including the peso amount; ungated as designed |
| 7 | Optional email save | HTTP 500 — see "Second Bug Found" below |
| 7b | Graceful degradation | Page shows "No pudimos guardar tu email, pero puedes seguir por WhatsApp arriba." — no crash, WhatsApp CTA unaffected |
| 8 | Regression: `/wizard` (8-step flow) | Renders correctly, hero copy intact, all asset requests 200 |
| 9 | Mobile viewport (375×812) | Clean layout, no overflow, CTA prominent |

## Second Pre-Existing Bug Found (Not Fixed — Out of Scope)

`POST /wizard/api/leads/save` returns HTTP 500. Server log:
```
Supabase upsert error: {
  code: 'PGRST205',
  message: "Could not find the table 'public.leads' in the schema cache",
  hint: "Perhaps you meant the table 'public.crm_leads'"
}
```
`contexia-wizard/.env.local`'s `SUPABASE_URL` resolves to `kpynymwghfwshvcvevxq` — the SAME
Supabase project as `antigravity-app`'s backend, not a separate one as an earlier draft of
`design.md` assumed. That assumption is corrected in `design.md` D6/D7. Since this same endpoint
is what the EXISTING 8-step flow's Step 1 also calls, this strongly suggests the 8-step flow's
lead capture is also silently failing in production today. This is a real, pre-existing,
production-impacting bug, discovered as a side effect of this change's verification — NOT
introduced by this change, and NOT fixed here (fixing it means deciding whether to recreate
`public.leads` or repoint the route at `crm_leads` with correct `tenant_id`/`source` mapping,
which is a real architecture decision requiring founder input, and touches the existing 8-step
flow's data path which is explicitly out of this change's scope).

This change's own contract already tolerates the failure: the optional email save fails open,
and the primary conversion path (WhatsApp) never depends on this endpoint.

## Outcome

- Step 5 status: **PASS** (with two pre-existing, unrelated bugs found and documented — one fixed
  because it was fully blocking, one flagged for a separate future change)
- Blocking issues for THIS change: none — the 3-step flow works end-to-end, degrades gracefully
  around the broken lead-save endpoint, and does not regress the existing 8-step flow
