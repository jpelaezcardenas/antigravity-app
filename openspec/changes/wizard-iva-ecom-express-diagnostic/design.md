## Context

`contexia-wizard/` is a real, deep Next.js app (Zustand store, Supabase-backed leads, Wompi payments, PDF audit reports) already serving one persona (formal incorporation / traditional tax diagnostic) at `contexia.online/wizard`, basePath-proxied via `vercel.json`. It already has precedent for a second, parallel flow variant: "Feria mode" (`lib/feriaConfig.ts`, env-var gated) swaps the entire site's hero/copy/branding for an event, but is a *global* toggle applied to the SAME 8-step flow — not a genuinely different, shorter flow. This proposal needs the opposite: a different flow with different steps, coexisting permanently alongside the 8-step one, not replacing it.

## Goals / Non-Goals

**Goals:**
- Ship a 3-step flow at `/wizard/iva-ecom` that a cold Instagram/TikTok visitor can complete in under a minute
- Compute an instant, client-side "IVA perdido" figure and a red/green verdict, with zero backend round-trip for the calculation
- Route qualified leads to WhatsApp with a pre-filled message referencing their specific finding
- Reuse the existing lead-capture endpoint and WhatsApp number — no new backend surface

**Non-Goals:**
- Does NOT touch the existing 8-step flow, its store, or its step components
- Does NOT change `POST /api/leads/save`'s contract — only adds a new `source` value and a new shape under the existing free-form metadata field
- Does NOT implement server-side tier scoring or persistence of the tier beyond what the lead-save call already captures
- Does NOT build the WhatsApp Community/Channel/Broadcast List infrastructure — that's the founder's operational setup (per the GTM plan), this only produces the CTA link into it

## Decisions

**D1 — New route + new store, not a mode flag on the existing `WizardStore`.**
The existing `WizardStore` (`lib/store.ts`) has `paso1`...`paso7` fields shaped for company incorporation (`Paso1Data`, `Paso2Data`, etc. from `lib/validations.ts`). The ecom flow's 3 steps (ventas mensuales, gasto en Meta Ads, margen bruto, tipo de persona, facturación electrónica) don't map onto that shape at all. Alternative considered: extend `WizardStore` with new optional fields — rejected, because it would force every consumer of the existing store to reason about fields that only apply to a different flow, and the existing store already persists to `localStorage` (a schema change there risks corrupting in-flight sessions of the 8-step flow for existing visitors). A separate `lib/ecomStore.ts` with its own small Zustand store and its own `localStorage` key avoids any interference.

**D2 — Math lives in a new `lib/ecomCalculations.ts`, with its own correctly-dated UVT constant — NOT reusing `lib/calculations.ts`'s `UVT_2026`.**
**Correction, found during founder review (2026-09-20) via the Contexia Knowledge Vault**
(`Ecosistema de comercio electrónico y comerciantes digitales... AMVA.pdf`, sourced from DIAN's
own normograma): `lib/calculations.ts`'s `UVT_2026` constant is mislabeled — it holds `49799`,
which is the **UVT 2025** value (Resolución DIAN 000193 de 2024), not UVT 2026 (`52374`,
Resolución DIAN 000238 de 2025). This is a pre-existing bug in the 8-step flow, not introduced by
this change, and the 8-step flow's own landing copy ("🎯 Basado en UVT 2026") is technically
inaccurate as a result. Fixing `lib/calculations.ts` is out of scope (Non-Goals — it's shared by
the 8-step flow) and tracked as a follow-up. This module instead defines its own `UVT_2026_REAL =
52374`, correctly sourced and named to avoid perpetuating the same ambiguity. This changes the
IVA-responsibility threshold from the originally-coded $174.296.500/año to the correct
**$183.309.000/año** (design.md's earlier draft used the wrong figure before this correction).

Formulas (per the founder's brief):
```
ivaPerdidoMensual = gastoMetaAdsMensual * 0.19
ventasAnualesProyectadas = ventasMensuales * 12
excedeTopeIVA = ventasAnualesProyectadas > (3500 * UVT_2026)
```

**D3 — The 3,500 UVT figure is the IVA-responsibility threshold (Art. 437 ET), NOT the 1,400 UVT renta-declarante threshold already used elsewhere in this codebase (`pricing_catalog.py`, `pricing-quote-engine`).**
These are two different legal obligations — being liable for VAT collection vs. being required to file an annual income return — and this codebase already tracks the 1,400 UVT figure for the second one. Using 3,500 UVT here for a *different* question is correct and not a contradiction, but the UI copy must say "responsable de IVA" and never "declarante de renta" for this number, to avoid the wizard silently contradicting the backend's own pricing/pre-cotización copy for the same visitor if they later go through both funnels.

**D4 — 19% flat rate on 100% of Meta Ads spend is a simplification, disclosed as such.**
Real IVA recovery depends on whether the business is IVA-responsible (D3) and files it correctly — a non-responsable persona natural cannot claim it at all, and the "loss" framing only truly applies to someone who COULD be claiming it but isn't. The tool's result screen must state this is an estimate ("si eres responsable de IVA y no lo estás reclamando"), never an unconditional "estás perdiendo $X" — per the GTM claims guardrails (CLAUDE.md §11: no unverified/absolute claims). This is a wording decision for Task 3 below, not a math change.

**D5 — Tier assignment (1/2/3) is a pure frontend classification for CTA routing, not a persisted CRM field.**
The brief calls for assigning Tier 1/2/3 to route the WhatsApp message tone/urgency (e.g., Tier 1 = high IVA loss + already over the UVT threshold = urgent; Tier 3 = small spend, informational). This tier is computed client-side from the same three inputs and is NOT written to `crm_leads`/HubSpot as a new field — it only shapes which pre-filled WhatsApp text the button uses. Persisting it as a structured CRM field is out of scope; the lead's raw numbers already travel to Supabase via the existing `metadata` JSONB pattern (D1/feria precedent), so the tier can always be recomputed later if needed.

**D6 — WhatsApp is the primary, ungated CTA; the wizard's own lead-save is optional and best-effort, not a gate.**
Two things surfaced together that change this from the original plan: (1) the founder's 3-step brief collects no email at all (ventas, gasto, margen, persona type, facturación — nothing else), but `POST /api/leads/save` returns 400 without `paso1.email`; (2) `contexia-wizard`'s lead-save endpoint queries a table (`public.leads`) that is NOT `crm_leads`, has no HubSpot sync, and Taty/Chatwoot never read it. **Correction made during implementation (2026-09-20):** an earlier draft of this document claimed this table lived in a wholly separate Supabase project. Live testing during Task 1 verification proved that wrong — `contexia-wizard/.env.local` points to the exact same Supabase project as `antigravity-app`'s backend (`kpynymwghfwshvcvevxq`, per `ARCHITECTURE.md`), and calling the endpoint returns a real error: `Could not find the table 'public.leads' in the schema cache... Perhaps you meant 'public.crm_leads'`. This is a genuinely separate, pre-existing production bug this change did not introduce and does not fix — see the Risks section. What doesn't change: regardless of which project the table lives in, that table is empty/broken right now, so **the wizard's lead-save call does not put the visitor in front of Taty or the CRM pipeline the rest of the GTM plan depends on.** Only the WhatsApp click does that, because it's the same production number Chatwoot's inbox 1 already watches.

Given that, gating the WhatsApp CTA behind a forced email field would add friction to the one action that actually matters, in service of writing to a table nothing downstream reads. Decision: Step 3 shows the result and the WhatsApp button as the primary, always-enabled CTA. Below it, an optional "te enviamos este resultado por email" field is offered; only if the visitor fills it does a `POST /api/leads/save` call fire (`source: "iva_ecom_express"`, the three steps' inputs nested under `metadata.iva_ecom_inputs`). If left blank, no call is made — the WhatsApp click is the funnel's real conversion event.

**D7 — `contexia-wizard`'s `POST /api/leads/save` is broken in the current schema (pre-existing, confirmed live 2026-09-20); this change does not fix it, only degrades gracefully around it.**
`app/api/leads/save/route.ts` queries `.from("leads")`, but the connected Supabase project (`kpynymwghfwshvcvevxq`, shared with `antigravity-app`) has no `public.leads` table — only `public.crm_leads`. Every call to this endpoint returns 500 today, which almost certainly means **the existing 8-step flow's lead capture is also silently failing in production right now**, not just this new 3-step flow's optional email field. This is a real, live, production-impacting bug, discovered as a side effect of Task 5 verification, not something this change introduces. Fixing it properly is a real decision (recreate `public.leads`? point the route at `crm_leads` with correct `tenant_id`/`source` mapping, which — since it's the SAME Supabase project — is now a much smaller lift than previously assumed, and would double as the crm bridge a prior draft of this document flagged as future work) and is explicitly OUT OF SCOPE for this change: it touches the existing 8-step flow's data path, which design.md's Non-Goals already excludes, and warrants its own OpenSpec change with the founder's input on which fix is correct. This change's own contract already tolerates it: Step 3's optional email save fails open (error state shown, WhatsApp CTA unaffected — see Risks), so nothing here depends on the endpoint working.

## Risks / Trade-offs

- **[Risk]** `contexia-wizard`'s production build was fully broken (Turbopack: "The PNG is not in RGBA format!" on `app/favicon.ico`, blocking EVERY route, not just this one) — discovered during Task 5 verification, confirmed pre-existing via `git log` (last touched 2026-09-12, unrelated commit) → **[Mitigation]** regenerated `app/favicon.ico` as a proper RGBA ICO from the existing `public/contexia-logo-transparent.png` (which was already valid RGBA) as a minimal, isolated fix — required to verify this change at all, and also unblocks any future deploy of the 8-step flow, which was equally broken by this.
- **[Risk]** Two independent `UVT_2026` constants (this app's `lib/calculations.ts`, and the backend's `uvt_values` table) could drift when DIAN republishes UVT for 2027 → **[Mitigation]** out of scope to unify (separate deployables by design), but flagged here explicitly so whoever updates one in December remembers to check the other; not blocking for this change since both already agree for 2026.
- **[Risk]** An unconditional-sounding "estás perdiendo $X en IVA" headline could read as the exact prohibited claim pattern (ROI/savings claim not measured on a real client) → **[Mitigation]** D4's disclosed-estimate wording is a hard requirement of Task 3, verified before Stage 11 deploy, not an optional nicety.
- **[Risk]** A visitor who already went through the 8-step flow could return via an ad and hit this different 3-step flow with a different lead record (no dedup by email/phone across the two `source` tags) → **[Mitigation]** `POST /api/leads/save` already upserts by email server-side, so a repeat visitor with the same email merges into one Supabase lead row regardless of which flow captured it — no duplicate-lead risk, just two different `source`/`metadata` histories on one row over time (acceptable, matches how Feria mode already coexists with the base flow).

## Correction (2026-09-20, post-deploy verification): `vercel.json` DID need a change

An earlier draft of this document (and Task 3.3) claimed no `vercel.json` change was needed
because `/wizard/:path*` already proxies every sub-path. That was wrong in a specific, real way:
the existing rewrite never matched **trailing-slash** paths at all — confirmed by testing
`/wizard/confirmacion/`, an existing page of the 8-step flow live for months, which also 404s
through `contexia.online`. Since `contexia-wizard`'s `next.config.ts` sets `trailingSlash: true`,
every single page of BOTH wizard flows redirects to add a trailing slash — meaning the entire
wizard has been effectively broken via the public domain for every page except the bare `/wizard`
root and the handful of paths with their own explicit redirect rule (`/wizard/login/`,
`/wizard/dashboard/`, `/wizard/`). This was a pre-existing, unrelated bug, not introduced by this
change, but it directly blocks this change's own purpose (the GTM campaign needs
`contexia.online/wizard/iva-ecom` to work), so fixing it is in scope here.

**Fix**: added one rewrite rule mirroring the existing wildcard pattern with a trailing slash:
```json
{ "source": "/wizard/:path*/", "destination": "https://contexia-wizard.vercel.app/wizard/:path*/" }
```
placed before the non-trailing-slash version. This is additive and minimal — no existing rule
removed or reordered otherwise.

## Migration Plan

1. Build `/wizard/iva-ecom` as new, additive files inside `contexia-wizard/` only
2. Deploy `contexia-wizard` to its own Vercel project (`contexia-wizard.vercel.app`) — separate deploy target from `contexia-app`/`antigravity-app`, no Stage 11 backend/Railway involvement
3. Verify `contexia.online/wizard/iva-ecom` resolves through the existing `vercel.json` rewrite (`/wizard/:path*` → `contexia-wizard.vercel.app/wizard/:path*`) without any `antigravity-app` deploy needed
4. Smoke test end-to-end: complete the 3 steps, confirm a lead lands in Supabase `leads` table with `source=iva_ecom_express`, confirm the WhatsApp link opens with the correct pre-filled text
5. Rollback: revert the `contexia-wizard` commit and redeploy — the existing 8-step flow is untouched throughout, so there is no combined-rollback risk

## Open Questions

- Founder to confirm the 3,500 UVT IVA-responsibility figure and the flat-19% simplification are acceptable to ship as "estimado" copy, or whether Tatiana (the accountant) should review the exact wording before this goes live to real ad traffic — this is a real-money claim about taxes, same review bar as any other Taty pricing/tax claim in this repo
- Exact WhatsApp CTA destination: does it link straight to `wa.me` (current `TatyFloat.tsx` pattern) or into the "50 Fundadores" broadcast list once that exists? For this change, default to the same `wa.me` number already live, since the broadcast list is founder-operational setup tracked outside this OpenSpec change
