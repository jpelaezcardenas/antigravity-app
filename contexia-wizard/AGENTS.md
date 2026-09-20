<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.

## Routes: the 8-step flow (`/`) vs. the 3-step express flow (`/iva-ecom`)

`app/page.tsx` + `app/wizard-client.tsx` is the original 8-step Shadow Audit flow (company
incorporation / traditional tax diagnostic), served at `contexia.online/wizard` via the
`basePath: "/wizard"` in `next.config.ts`. `app/iva-ecom/page.tsx` + `app/iva-ecom/ecom-client.tsx`
is a separate, parallel 3-step express diagnostic for the e-commerce/dropshipper persona (GTM
campaign, `openspec/changes/wizard-iva-ecom-express-diagnostic/`), served at
`contexia.online/wizard/iva-ecom` through the same basePath — no routing change was needed.

They deliberately do NOT share a store: `lib/store.ts`'s `WizardStore` is shaped for the 8-step
flow's `Paso1..7` data and persists to its own `localStorage` key; the 3-step flow has its own
`lib/ecomStore.ts` with its own key. Extending `WizardStore` would risk corrupting in-flight
8-step sessions for existing visitors on a schema change. Same reasoning for
`components/wizard-ecom/EcomStepWrapper.tsx` — it's a near-duplicate of
`components/wizard/StepWrapper.tsx`, kept separate only because the original hardcodes
"Paso X de 8".

## Known pre-existing bug: `POST /api/leads/save` returns 500

`app/api/leads/save/route.ts` queries `public.leads`, which does not exist in the connected
Supabase project (`kpynymwghfwshvcvevxq` — the SAME project `antigravity-app`'s backend uses, only
`public.crm_leads` exists there). Confirmed live 2026-09-20. This affects BOTH the 8-step flow's
lead capture and the 3-step flow's optional email field — the 3-step flow degrades gracefully
around it (WhatsApp CTA never depends on it), but the 8-step flow's leads are likely being lost
silently in production. Not fixed as part of `wizard-iva-ecom-express-diagnostic` (out of scope —
fixing it is a real schema decision, tracked separately). See that change's `design.md` D6/D7 and
`reports/2026-09-20-frontend-e2e-verification.md` for the full investigation.
<!-- END:nextjs-agent-rules -->
