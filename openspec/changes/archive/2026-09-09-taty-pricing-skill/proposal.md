# Taty's pricing skill — real figures replace the price refusal

## Why

Taty's system prompt (`TatyAgentService._build_system_prompt`) currently instructs her to
**refuse to state a price** on the WhatsApp Renta Natural funnel: "el precio para este caso
todavía no está definido en el sistema... NO inventes ni menciones un número." That instruction
existed because, until now, no price existed anywhere to state — founder decision, deferred
2026-08-11.

Two things have changed:

1. `core/pricing_catalog.py` (from `pricing-catalog-and-operator-quote`) already holds Contexia's
   B2B software tiers and professional-service bands, but it does not exist anywhere in Taty's
   prompt at all — she cannot quote GPS, Pro, or the service bands on any channel, even though
   those numbers are official and public.
2. The founder has now given the Renta Natural persona-natural price: **desde $350.000**, varying
   by trámites, movimientos y patrimonio — the founder's own words, explicitly declining to give
   a ceiling because none exists (it is genuinely quoted case by case).

This is a live customer-facing sales agent, so the same discipline applies as everywhere else
prices touch this repo: one source of truth, no fabricated bound, and the model told explicitly
what it may and may not say.

## What changes

1. **`core/pricing_catalog.py` gains a third revenue line**: `RENTA_NATURAL_PRICING` — floor
   $350.000, no ceiling, `is_quoted=True`, with the three named drivers the founder gave
   (cantidad de trámites, movimientos, patrimonio). Structurally identical to the `complejo`
   service band: a floor with no invented ceiling.

2. **Taty gains a standing pricing skill**, available on every channel (Telegram, PWA, WhatsApp),
   not only the Renta Natural funnel: she can state the B2B software tiers (GPS $249.000, Pro
   desde $1.490.000, Total cotizado) and the professional-service bands (Micro $890.000, Estándar
   $1.490.000–$2.400.000, Complejo cotizado) when asked, sourced from the catalog, never
   hardcoded in the prompt string.

3. **`RENTA_OFFER_CONTEXT.precio_confirmado` flips to `True`**, sourced from the new catalog
   entry. Taty may now say "desde $350.000, varía según [drivers]" — and is explicitly instructed
   never to state an exact final number or a ceiling that does not exist.

4. **Framed as one of Taty's skills**, consistent with her existing persona block ("Fintech
   Centrado en el Ser Humano", "copiloto fiscal 24/7"): a "vendedora estrella" capability that
   knows Contexia's real prices and can guide a prospect toward the right tier or band.

## Non-goals

- **Not lead qualification.** The founder named this as a future step. This change gives Taty
  pricing knowledge; it does not add scoring, routing, or qualification logic.
- **Not a Hermes agent-profile file.** "Skill" here means a described capability inside Taty's
  existing system-prompt construction (`taty_service.py`), not a new Hermes orchestration
  artifact — no such mechanism was found wired to Taty in this repo, and inventing one is out of
  scope for a pricing fix.
- **Not touching `core/plan_features.py`** or any tenant/feature-gating logic — this is prompt
  content only.
- **Not changing Wompi checkout or payment-link generation.** Taty states the Renta Natural
  price; the existing HITL-gated Wompi link flow (`taty-wompi-link-hitl-gate`) is unchanged.
