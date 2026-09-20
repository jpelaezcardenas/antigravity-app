## Why

`contexia.online/wizard` already exists as a live, working 8-step "Shadow Audit" diagnostic (Régimen Simple vs Ordinario, `contexia-wizard/` — confirmed live 2026-09-20, not 404 as initially suspected). But it was built for company incorporation / formal tax diagnostic, and 8 steps is too long for the GTM campaign's actual target: a dropshipper or e-commerce seller arriving cold from an Instagram/TikTok ad. That audience needs an answer in under a minute or they bounce — an 8-step form against that traffic source produces the 70-80% drop-off the founder flagged. The agency's Month 1 content (Reel 14: "recupera el IVA de tus pautas") needs a fast, ecom-specific hook: show the prospect the exact peso amount of IVA they're losing on Meta Ads spend, then route them straight to WhatsApp.

**Correction of an earlier proposal in this thread**: an earlier draft of this change built a brand-new, separate landing page (`contexia-app/app/auditoria/`) duplicating this functionality. That was based on an incorrect premise (that no B2B freemium landing existed) and is scrapped. This proposal instead extends the EXISTING `contexia-wizard/` app — no new app, no duplicate lead-capture surface.

## What Changes

- Add a new route `contexia-wizard/app/iva-ecom/page.tsx` (served at `contexia.online/wizard/iva-ecom` via the existing basePath) alongside the current `/wizard` (8-step) flow — additive, the 8-step flow is untouched
- New 3-step flow, purpose-built for the ecom/dropshipper persona:
  1. **Números**: ventas mensuales, gasto en Meta Ads, margen bruto aproximado
  2. **Formalización**: ¿Persona Natural o SAS?, ¿factura electrónicamente?
  3. **Resultado + WhatsApp**: instant verdict (red/green semaphore) showing estimated monthly IVA left on the table + a tier assignment (1/2/3) + a WhatsApp CTA to join "los primeros 50 cupos" of the VIP community
- All math computed client-side, instantly, no backend round-trip for the calculation itself (same "instant" promise the existing wizard already makes for its own diagnóstico step)
- Lead capture reuses the existing `POST /api/leads/save` endpoint (same one the 8-step flow and Feria mode already use), tagged with `source=iva_ecom_express` — no new endpoint, no schema change (the endpoint already supports an arbitrary `source` string and a `feria_data`-style metadata JSONB payload, which this flow reuses for its own step data under a differently-named key)
- WhatsApp CTA reuses the existing production number and `wa.me` link pattern already live in `TatyFloat.tsx`, with new prefilled text referencing the IVA finding and the "Comunidad VIP" / "50 Fundadores" program

**Not BREAKING** — purely additive: new route, new step components, new `source` tag value. The existing 8-step flow, its store, and its API contract are untouched.

## Capabilities

### New Capabilities
- `wizard-iva-ecom-express-diagnostic`: the 3-step express IVA diagnostic flow for e-commerce/dropshipper leads, its client-side math, its tier assignment, and its WhatsApp handoff

### Modified Capabilities
(none — the existing 8-step wizard capability, its store, and `POST /api/leads/save` are reused unmodified; a `source` tag is a pre-existing, unconstrained field, not a contract change)

## Scope Extension (2026-09-20, founder-approved)

Verification of the 3-step flow surfaced that `public.leads` — the table `app/api/leads/save/route.ts`
has always queried, used by both the existing 8-step flow and this change's optional email
field — does not exist in the connected Supabase project. Founder chose to recreate it (over
repointing to `crm_leads`, a differently-scoped table). This is documented as an extension of this
change rather than a new one, per the one-change-at-a-time invariant, since it was discovered as a
direct consequence of this change's own verification work. See `design.md` D6/D7 and
`tasks.md` §5b for the full investigation and fix.

**Second, more urgent extension (same day):** following the `leads` fix, `empresas` and `payments`
(same Supabase project, FK-chained to `leads`) were also found missing. Investigation showed these
are NOT dead tables — they back `contexia-app/app/crear-empresa-wizard/`, a LIVE, actively-priced
product ($1.200.000) whose Wompi payment flow is currently broken for every real customer. See
`tasks.md` §5c.

**Third extension (same day, founder-directed):** the founder requested an intermediate routing
page — `contexia.online`'s "🔍 AUDITORÍA SOMBRA" header link previously pointed straight to the
8-step flow. New file `auditoria-sombra.html` (root static site) lets a visitor self-select
Persona Natural (→ `/renta-natural`) or Empresa Formalizada (→ `/wizard/iva-ecom`) before landing
on the right diagnostic. `landing.html`'s two nav links (desktop + mobile) were repointed to it —
2-line diff, no other change. Styled to match the wizard's own hero pattern (Orbitron headline,
teal→violet gradient, emoji feature row) per the founder's explicit ask to keep visual consistency
across every new page in this funnel. See `tasks.md` §9 for the build/verification log, including
several Tailwind utility classes that silently don't exist in this site's pre-compiled
`landing.min.css` (arbitrary values and color-opacity variants are purged if unused elsewhere) —
worth remembering for any future static page in this same site.

## Impact

- **New files** (all inside `contexia-wizard/`, never in `contexia-app/`):
  - `app/iva-ecom/page.tsx`
  - `components/wizard-ecom/Step1Numeros.tsx`, `Step2Formalizacion.tsx`, `Step3Resultado.tsx`
  - `lib/ecomCalculations.ts` (IVA-lost and UVT-threshold math, mirroring the existing `lib/calculations.ts` pattern)
  - `lib/ecomStore.ts` (a separate, small Zustand store — NOT extending the existing 8-step `WizardStore`, since the data shapes don't overlap)
- **No changes** to `contexia-app/`, the antigravity-app backend, or any Supabase migration
- **No changes** to `vercel.json` rewrites — `/wizard/:path*` already proxies every sub-path of `contexia-wizard.vercel.app/wizard/*`, so `/wizard/iva-ecom` works automatically once the route exists in `contexia-wizard`
- **Feature-list impact**: replaces `auditoria-sombra-public-landing` (scrapped, wrong premise) as the active change in `feature_list.json`, still pausing `hermes-jarvis-contexia`
