# Tasks — taty-pricing-skill

## Stage 1. Catalog (TDD)

- [x] 1.1 Failing tests: `RENTA_NATURAL_PRICING.min_cents == 35_000_000`, `max_cents is None`,
      `is_quoted is True`, `price_drivers` names the three founder-given drivers
- [x] 1.2 Implement in `core/pricing_catalog.py`

## Stage 2. Always-on B2B pricing block in Taty's base prompt (TDD)

- [x] 2.1 Failing tests: `_build_system_prompt(profile, lead_context=None)` (Telegram/PWA shape)
      includes GPS/Pro/Total tier names and Micro/Estándar/Complejo band labels
- [x] 2.2 Failing test: no B2B price appears as a hardcoded literal in `taty_service.py`
- [x] 2.3 Implement, reading `SOFTWARE_TIERS` / `SERVICE_BAND_PRICING` from the catalog

## Stage 3. Renta Natural floor replaces the refusal (TDD)

- [x] 3.1 Failing test: `RENTA_OFFER_CONTEXT["precio_confirmado"]` is `True`, sourced from the
      catalog constant (not a bare literal)
- [x] 3.2 Failing tests: with `precio_confirmado=True`, the prompt states "$350.000" and the
      three drivers, and does NOT contain the old refusal instruction
- [x] 3.3 Failing test: the prompt explicitly instructs never to state a final exact number or a
      ceiling
- [x] 3.4 Implement in `taty_lead_router.py` (`RENTA_OFFER_CONTEXT`) and
      `taty_service.py` (`_build_system_prompt`'s `lead_context` branch)

## Stage 4. Persona framing

- [x] 4.1 Add the "vendedora estrella" skill line to Taty's base persona, next to the existing
      "Fintech Centrado en el Ser Humano" framing

## Stage 5. Verification

- [x] 5.1 Full backend suite, compared against `main` for zero regressions
- [x] 5.2 Confirm `core/plan_features.py` untouched
- [x] 5.3 Confirm the Wompi HITL flow's own tests are unaffected

## Stage 6. Documentation

- [x] 6.1 `docs/pricing.md` — add Renta Natural as the third revenue line, remove the "known
      follow-up" note about Taty refusing to quote (resolved)
- [x] 6.2 ARCHITECTURE.md settled decision

## Stage 11. Deploy to Production

- [x] 11.0 Rebuild + sync the static export if any frontend file changed (it should not — this
      change is backend prompt content only); confirm no `contexia-app/` diff before skipping
- [x] 11.1 git commit + push to main
- [x] 11.2 Vercel build complete (unaffected, but confirm green)
- [x] 11.3 Railway deploy active
- [x] 11.4 Production: confirm `/api/v1/agents/ask` and the WhatsApp reply path still return
      401/200 as before (prompt content is not independently visible via HTTP status, so this
      verifies the deploy shipped without confirming prompt text live — see report for the
      honest limit of this check)
- [x] 11.5 Deployment report

**No migration in this change.**
