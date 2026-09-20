## 0. Setup: Create Feature Branch (MANDATORY — FIRST STEP)

- [x] 0.1 Create feature branch `feature/wizard-iva-ecom-express-diagnostic` from `main` — corrected during apply: `contexia-wizard/` is NOT a separate repo, it's tracked inside the `antigravity-app` monorepo (confirmed via `git log -- contexia-wizard/` showing commits directly on `antigravity-app`'s history); this is a normal branch in this repo, not a cross-repo branch
- [x] 0.2 Verify branch creation and current branch status — `git branch --show-current` confirms `feature/wizard-iva-ecom-express-diagnostic`

## 1. Frontend: Ecom Store and Calculations

- [x] 1.1 Create `contexia-wizard/lib/ecomStore.ts` — small Zustand store (own `localStorage` key, does NOT extend `WizardStore`, design.md D1): `pasoActual` (1-3), `numeros` (ventasMensuales, gastoMetaAds, margenBruto), `formalizacion` (tipoPersona, facturaElectronicamente), `email` (optional), reset action
- [x] 1.2 Create `contexia-wizard/lib/ecomCalculations.ts` importing `UVT_2026` from the existing `lib/calculations.ts` (design.md D2) — exports `calcularIvaPerdidoMensual`, `excedeUmbralResponsableIVA`, `calcularTier` (1/2/3)
- [x] 1.3 Write unit tests for `ecomCalculations.ts` (TDD): `lib/ecomCalculations.test.ts`, 10/10 passing (`npx jest lib/ecomCalculations.test.ts`) — added `jest.config.js` + `test` script since jest was already a devDependency but never wired up

## 2. Frontend: Step Components

- [x] 2.1 Create `contexia-wizard/components/wizard-ecom/Step1Numeros.tsx` — ventas mensuales, gasto en Meta Ads, margen bruto (numeric inputs, validation: positive numbers required to enable "Siguiente")
- [x] 2.2 Create `contexia-wizard/components/wizard-ecom/Step2Formalizacion.tsx` — Persona Natural/SAS selector, facturación electrónica yes/no
- [x] 2.3 Create `contexia-wizard/components/wizard-ecom/Step3Resultado.tsx`:
  - Renders the instant client-side result (semaphore red/green, `ivaPerdidoMensual`) using `ecomCalculations.ts`
  - Copy is a disclosed estimate ("si eres responsable de IVA y no lo estás reclamando"), never an unconditional claim (design.md D4 — hard requirement)
  - WhatsApp button (primary, always enabled, no gating) using the existing production number/pattern from `components/layout/TatyFloat.tsx`, with pre-filled text referencing the estimated finding + "primeros 50 cupos" community offer
  - Optional email field below the WhatsApp button; only if filled, fires `POST /api/leads/save` with `source: "iva_ecom_express"` and `metadata.iva_ecom_inputs` (design.md D6) — leaving it blank must not error or block anything
  - Note: also created `EcomStepWrapper.tsx` (not in the original task list) — `components/wizard/StepWrapper.tsx` hardcodes "Paso X de 8", incompatible with a 3-step flow; reused all the same CSS classes for visual consistency
  - Known minor defect (non-blocking, D7 applies — this table isn't read downstream): `/api/leads/save`'s existing template-literal `whatsapp: `${pais_codigo}${whatsapp}`` produces the literal string `"undefined"` when only `paso1.email` is sent, since it doesn't guard for missing fields; not fixed here since backend/route.ts changes are out of scope

## 3. Frontend: Route Wiring

- [x] 3.1 Create `contexia-wizard/app/iva-ecom/page.tsx` + `ecom-client.tsx` — client component wiring `ecomStore` + the 3 step components, mirroring `app/wizard-client.tsx`'s step-router pattern but with its own store; `app/wizard-client.tsx` and the existing 8-step router are untouched
- [x] 3.2 Confirmed `next.config.ts`'s `basePath: "/wizard"` applies automatically — no `next.config.ts` change made
- [x] 3.3 Confirmed no change needed in `antigravity-app/vercel.json` — `/wizard/:path*` already proxies every sub-path of `contexia-wizard.vercel.app/wizard/*`; not touched

## 4. Review and Update Existing Unit Tests (MANDATORY)

- [x] 4.1 Confirmed no pre-existing tests exist for the 8-step flow (none of `lib/store.ts`, `lib/calculations.ts`, or any `Step1..8` component was touched by this change)
- [x] 4.2 `npx jest` — 10/10 passing, 1 suite (the new `ecomCalculations.test.ts`); zero regressions since it's the only suite that exists

## 5. Manual/E2E Verification (MANDATORY — AGENT MUST EXECUTE)

No new backend endpoint is introduced (design.md explicitly reuses `POST /api/leads/save` unmodified), so there are no new curl-testable endpoints. Verification is frontend-driven, using the local dev server / browser preview tools.

- [x] 5.0 **Blocking pre-existing bug found and fixed:** `npm run build`/dev server failed on EVERY route with "The PNG is not in RGBA format!" (`app/favicon.ico`, Turbopack). Confirmed pre-existing via `git log` (last touched 2026-09-12, unrelated commit). Regenerated `app/favicon.ico` as proper RGBA from `public/contexia-logo-transparent.png` via PIL — minimal, isolated fix (design.md Risks)
- [x] 5.1 Started dev server, navigated to `/wizard/iva-ecom` in a fresh browser tab (confirmed no console errors)
- [x] 5.2 Completed Step 1 (ventas 20.000.000, gasto Meta Ads 5.000.000, margen 35%), advanced to Step 2
- [x] 5.3 Completed Step 2 (Persona Natural, factura electrónicamente: Sí), advanced to Step 3
- [x] 5.4 Verified: `950.000 / mes` = `5.000.000 * 0.19` — correct
- [x] 5.5 Verified: ventas anualizadas (240M) > umbral (3.500 × 49.799 = 174.296.500) → red "Superas el umbral de responsable de IVA" — correct
- [x] 5.6 Clicked WhatsApp button with email field empty — opened `wa.me/573106229289` with correctly URL-encoded tier-1 message including the exact peso amount — worked, ungated as designed
- [x] 5.7 **Found a second pre-existing, unrelated production bug**: filling the optional email and submitting returns HTTP 500 from `/api/leads/save`. Server log: `Could not find the table 'public.leads' in the schema cache... Perhaps you meant 'public.crm_leads'`. Confirmed `contexia-wizard/.env.local` points to the SAME Supabase project as antigravity-app (`kpynymwghfwshvcvevxq`) — corrects design.md D7's earlier wrong claim of a separate project. This means the EXISTING 8-step flow's lead capture is almost certainly also silently broken in production. NOT fixed here (out of scope — see design.md D7); confirmed the graceful error path works instead (see 5.7b)
- [x] 5.7b Verified graceful degradation: on the 500, the page shows "No pudimos guardar tu email, pero puedes seguir por WhatsApp arriba." — no crash, no blank page, WhatsApp CTA still fully functional
- [x] 5.8 Verified `/wizard` (existing 8-step flow) still renders correctly, hero copy intact, all asset requests 200 — no regression
- [x] 5.9 Resized to 375×812 (mobile) — layout clean, no overflow, WhatsApp CTA prominent, TatyFloat bubble doesn't obstruct content
- [x] 5.10 Documented in `openspec/changes/wizard-iva-ecom-express-diagnostic/reports/2026-09-20-frontend-e2e-verification.md`

## 5b. Fix: Recreate `public.leads` (founder-approved 2026-09-20, scope extension)

Found during Task 5 verification (see report above): `POST /api/leads/save` returns 500 because
`public.leads` doesn't exist in the connected Supabase project. Founder chose "recreate
`public.leads`" over "repoint to `crm_leads`" — `crm_leads` (migration `0022`) is scoped tightly to
the Renta Natural funnel (no `cedula`/`ciudad`/`rol`/`ip_address`/`referrer`/`metadata` columns,
admin-only RLS, a strict 4-value `stage` CHECK) and repurposing it would require bolting on columns
to a table with different semantics, risking the existing CRM Kanban.

Also found (out of scope, spun off separately as `task_3a828cf6`): `public.empresas` and
`public.payments` — the wizard's Wompi "Crear Empresa" flow, which FK-references `leads(id)` —
are ALSO missing from this Supabase project. Not fixed here; needs a founder call on whether that
product line is still active.

- [x] 5b.1 Confirmed via PostgREST probing (`GET /rest/v1/<table>`) that `leads`, `empresas`, and
      `payments` all 404 (don't exist), while `crm_leads` returns a different error (exists, RLS
      blocks anon) — narrowed the fix to exactly `leads`
- [x] 5b.2 Wrote `contexia-wizard/supabase/migrations/20260920_recreate_leads_table.sql` —
      columns reverse-engineered from `app/api/leads/save/route.ts`'s upsert payload and the
      surviving `20260616_add_feria_lead_fields.sql` migration (which this one folds in directly).
      RLS enabled, anon access denied by policy (service-role client bypasses RLS; this is
      defense-in-depth, not the real access control)
- [x] 5b.3 **Founder approved and I applied** both migrations to the live Supabase project
      (`kpynymwghfwshvcvevxq`) via `mcp__supabase__apply_migration` — `leads` first, then
      `empresas`/`payments`. Ran `get_advisors(security)` after: no new critical/error findings;
      the one new WARN (`update_leads_updated_at` search_path mutable) matches the same
      pre-existing pattern already accepted for this codebase's other trigger functions
- [x] 5b.4 Verified via direct SQL round-trip (insert → confirm → delete, cleaned to 0 rows in all
      three tables): `leads` upsert-by-email works, FK from `empresas`/`payments` to `leads`
      works, `payments.status` defaults to `PENDING` correctly. **Caveat, not re-opened as a bug**:
      a local curl test against the actual Next.js route returned "new row violates row-level
      security policy" — traced to `contexia-wizard/.env.local` missing
      `SUPABASE_SERVICE_ROLE_KEY`, so `supabaseAdmin` (`lib/supabase.ts`) falls back to the anon
      key locally. Could not confirm Vercel's production env var directly (403 on
      `filter_project_envs` — expected, secret values are permission-scoped) but did NOT weaken
      the RLS policy to work around this; production almost certainly has the real service-role
      key set (otherwise every prior admin write across this app would already be broken), and
      loosening RLS to make a local test pass would reopen the exact anon-write gap the policy
      exists to close
- [x] 5b.5 Documented the fix in `openspec/changes/wizard-iva-ecom-express-diagnostic/reports/2026-09-20-leads-table-fix.md`

## 5c. Fix: Recreate `public.empresas` and `public.payments` (URGENT — live revenue-impacting, founder-approved 2026-09-20)

Investigating 5b's spun-off task (`task_3a828cf6`) directly (not deferred) surfaced this is NOT
dead code: `contexia-app/app/crear-empresa-wizard/` is the LIVE, actively-marketed "Crear tu
empresa" product ($1.200.000, "🔥 Lanzamiento" pricing badge), and its payment step
(`Step8Pago.tsx` → `lib/payments/wompiCheckout.ts`) calls
`POST /wizard/api/payments/create-transaction` — exactly the `contexia-wizard/app/api/payments/*`
route that depends on the missing `empresas`/`payments` tables. **Every real customer attempting
to pay through this live flow hits a 500 right now.**

- [x] 5c.1 Traced the call path: `contexia-app`'s live UI → `lib/payments/wompiCheckout.ts`
      (`API_BASE = "/wizard/api/payments"`) → `contexia-wizard/app/api/payments/create-transaction`
      → `lib/supabase/payments.ts` → `.from("empresas")`/`.from("payments")` — confirmed this is
      one live, connected system, not two unrelated flows
- [x] 5c.2 Read `lib/supabase/payments.ts` (createEmpresa/createPayment/updatePaymentStatus/
      getPaymentByReference) and `app/api/payments/webhook/route.ts` to get the exact column
      shapes still in use, cross-checked against the original `20260520_create_payments.sql`
- [x] 5c.3 Wrote `contexia-wizard/supabase/migrations/20260920_recreate_empresas_payments_tables.sql`
      — same shape as the original migration, RLS with anon-deny (service-role client bypasses
      RLS, same defense-in-depth posture as the `leads` fix). Depends on `leads` existing first
      (both tables FK-reference `leads(id)`) — must run 5b's migration before this one
- [x] 5c.4 Applied — see 5b.3 (both migrations were applied together)
- [x] 5c.5 Verified `empresas`/`payments` structurally via direct SQL round-trip (5b.4): FK chain
      `payments.empresa_id → empresas.id → leads.id` works, defaults correct. **NOT verified**: a
      real or Wompi-sandbox end-to-end transaction through `contexia.online/crear-empresa-wizard`
      (would require a real Wompi sandbox credential exchange and is a live-money-adjacent test —
      recommend the founder or Tatiana run one real low-value test purchase in production once
      convenient, rather than me simulating it further here)
- [x] 5c.6 Documented in `openspec/changes/wizard-iva-ecom-express-diagnostic/reports/2026-09-20-empresas-payments-table-fix.md`

## 6. Founder Review (BLOCKING before production traffic)

- [x] 6.1 Founder reviewed the exact Step 3 copy and requested deep investigation against the
      Contexia Knowledge Vault before sign-off. Investigation results (2026-09-20):
      - **3.500 UVT threshold: CONFIRMED correct.** Already Contexia's own stated messaging
        (`Base de conocimientos-Contexia.MD` line 377) and independently sourced with a legal
        citation (Art. 437 ET) in `Ecosistema de comercio electrónico...AMVA.pdf` (DIAN normograma).
      - **19% IVA rate: CONFIRMED correct.** Colombia's general statutory IVA rate, not a market
        assumption requiring benchmarking.
      - **Found and fixed a real bug while verifying:** `lib/calculations.ts`'s `UVT_2026`
        constant actually holds the UVT **2025** value ($49.799 vs. the real 2026 value of
        $52.374, per DIAN Resolución 000238 de 2025). This is a pre-existing bug affecting the
        LIVE 8-step flow too (its landing already claims "Basado en UVT 2026" while computing with
        2025's number). Fixed for THIS change by defining `UVT_2026_REAL = 52374` locally in
        `ecomCalculations.ts` rather than importing the mislabeled constant (design.md D2) —
        corrects the threshold from $174.296.500 to the accurate **$183.309.000/año**. The
        8-step flow's own bug is out of scope here and spun off as `task_72eda2f2`.
      - Founder sign-off on the wording itself (beyond the numbers) still pending final word from
        founder/Tatiana on tone.
- [ ] 6.2 Confirm the WhatsApp destination number/message is correct for this specific campaign (vs. the generic `TatyFloat.tsx` message)

## 7. Update Technical Documentation (MANDATORY)

- [x] 7.1 Added a section to `contexia-wizard/AGENTS.md` (the canonical doc `CLAUDE.md` points to via `@AGENTS.md`) documenting the `/wizard/iva-ecom` route, the separate `ecomStore`, and the pre-existing `leads/save` bug
- [x] 7.2 Updated `antigravity-app/feature_list.json`: `active` set to `["wizard-iva-ecom-express-diagnostic"]` with `active_switch_2026-09-20` explaining the pivot from the scrapped `auditoria-sombra-public-landing` premise

## 8. Deploy (contexia-wizard's own Vercel project — no Stage 11/Railway involvement)

- [x] 8.1 Committed on `feature/wizard-iva-ecom-express-diagnostic`, merged into `main` (`--no-ff`), pushed to `origin/main` (`1083aac5..1bc1749d`) — staged only the 25 files belonging to this change, left unrelated pre-existing working-tree changes untouched
- [x] 8.2 **Found via Vercel MCP, not assumed**: `contexia-wizard`'s Vercel project (`prj_RAcVQo65yFZhLR39msHESvJ7gylR`) has **no GitHub integration** (`get_git_deployment_context` lists only `contexia-web-app`, `contexia-pwa-cliente`, `miedo-fiscal-digital` as git-linked — `contexia-wizard` is absent). Its last 3 deployments all show `source: "cli"`. **The git push does NOT trigger a deploy for this project.** A manual `vercel deploy --prod` (from `contexia-wizard/`, by whoever has the Vercel CLI authenticated) is required — this is a real operational gap in the original task list, not something to route around silently
- [x] 8.3 Founder ran `vercel deploy --prod` from `contexia-wizard/` after fixing the project's Root Directory setting in the Vercel dashboard (a prior API-only attempt failed twice with `NEXT_NO_VERSION` — the project's Root Directory API override is write-once and only respected on true first-deployment; the dashboard UI + CLI was the only reliable path). Deploy READY, aliased to `contexia-wizard.vercel.app`
- [x] 8.4 **Found a second pre-existing bug while verifying**: `contexia.online/wizard/iva-ecom` 404'd even after the deploy succeeded — traced to `antigravity-app/vercel.json`'s `/wizard/:path*` rewrite never matching trailing-slash paths at all. Confirmed this predates this change entirely by testing `/wizard/confirmacion/` (an existing 8-step-flow page) — it 404s too. Since `contexia-wizard`'s `trailingSlash: true` redirects every page to add a slash, this meant the ENTIRE wizard has been broken via the public domain except the bare `/wizard` root and the handful of paths with their own explicit redirect rule. Fixed with one additive rewrite rule (`/wizard/:path*/`) mirroring the existing wildcard — see design.md's "Correction" section. Founder authorized a redeploy of `antigravity-app` (`contexia-web-app` Vercel project) to pick up the fix and clear a stale edge cache from earlier failed attempts
- [x] 8.5 Confirmed `contexia.online/wizard` (existing 8-step flow) still works unchanged — verified both before and after the `vercel.json` fix
- [x] 8.6 Deployment report: `openspec/changes/wizard-iva-ecom-express-diagnostic/reports/2026-09-20-deployment.md`

## 9. Founder-directed extension: Auditoría Sombra routing page (same day)

- [x] 9.1 Created `auditoria-sombra.html` (repo root, static): two self-select cards (Persona
      Natural / Empresa Formalizada), disabled "Continuar" button enabled only after selection,
      redirects to `/renta-natural` or `/wizard/iva-ecom` respectively
- [x] 9.2 Repointed both nav occurrences of the "AUDITORÍA SOMBRA" link in `landing.html`
      (desktop + mobile menu) from `/wizard/` to `/auditoria-sombra.html`
- [x] 9.3 Matched the wizard's own visual pattern per founder's explicit request: Orbitron
      headline font, teal→violet gradient on the second line, emoji feature row (⚡🔒🎯)
- [x] 9.4 Added a full header (not just the logo) with working "back" navigation — home, anchors
      back to landing sections, Crear Empresa, FAQ, Acceso App — plus the working mobile menu
      toggle, since a user landing here via a direct link needs a way back
- [x] 9.5 **Found and fixed 3 rounds of silently-broken Tailwind classes**: this site's
      `landing.min.css` is a pre-compiled, purged bundle — any class not already used elsewhere
      on the site silently does nothing (no error, just missing style). Hit this for
      `font-extrabold` (fixed → `font-black`, which exists), `pt-[200px]` and other arbitrary
      values (fixed → dedicated `#main-content` rule in a `<style>` block), and every
      color-opacity variant I introduced (`bg-teal/10`, `border-teal/30`, `hover:bg-teal/5`,
      etc. — none exist; replaced with plain CSS classes using literal rgba() values). Verified
      each fix via `getComputedStyle()` in the browser and by grepping the served CSS file
      directly, not by visual inspection alone
- [x] 9.6 Verified end-to-end locally (static file server): badge/headline render correctly below
      the fixed nav (no overlap), selecting a card highlights it and enables "Continuar", the
      `destino` variable resolves to the correct target for each option, mobile hamburger menu
      opens/closes correctly with working back-navigation links
