# Design — taty-pricing-skill

## Decision 1 — Renta Natural is a floor-only entry, structurally like `complejo`

The founder's own words: "desde 350.000 pesos teniendo en cuenta cantidad de trámites,
movimientos, patrimonio... según el caso." No ceiling was given, because none exists — it is
quoted case by case. `RENTA_NATURAL_PRICING` therefore uses `min_cents=35_000_000`,
`max_cents=None`, `is_quoted=True`, mirroring `SERVICE_BAND_PRICING["complejo"]` exactly. The
drivers are recorded as data (`price_drivers` tuple), not prose, so the prompt-building code
states them rather than re-typing them.

## Decision 2 — the pricing skill is always-on, not gated to the Renta Natural funnel

The existing `precio_confirmado` gate lives inside `lead_context`, which only WhatsApp Renta
Natural leads receive (`_build_lead_context`). That correctly scopes the *Renta Natural* number
to that funnel. But it means Taty has never been able to state the B2B numbers on Telegram, the
PWA channel, or a WhatsApp conversation that isn't in the Renta Natural funnel — those numbers
are public and official regardless of channel.

So this change adds a second, independent block to `_build_system_prompt`'s `base` (always
built, every channel), stating the B2B catalog. It does not touch the `lead_context` gate at all
— that remains the Renta-Natural-specific mechanism, now simply pointed at a real price instead
of a refusal.

## Decision 3 — the model is told the shape of the number, not a script

Following the same rule Decisión #19 established for fiscal figures: an LLM given a precise
script still drifts under paraphrase. The instruction states the **facts** (floor, currency,
that it varies, the three drivers) and an explicit prohibition (no exact final number, no
ceiling), rather than a sentence to reproduce verbatim. This mirrors how the fiscal-figure and
contact-info rules already in this prompt are worded — the intro-line rule is the one exception,
and it is exempted because A/B testing showed the model drops the self-intro when not scripted
verbatim; there is no equivalent evidence here that a price needs scripting.

## Decision 4 — one source, read at prompt-build time, never restated as a literal

Both new prompt blocks read `core/pricing_catalog.py` directly (`SOFTWARE_TIERS`,
`SERVICE_BAND_PRICING`, `RENTA_NATURAL_PRICING`) and format them at call time. No price is
retyped as a string literal in `taty_service.py` or `taty_lead_router.py`. A future catalog edit
changes what Taty says on the next request, with nothing else to update.

## Decision 5 — "skill" is prompt framing, not a new subsystem

The founder asked for this to read as one of Taty's skills, alongside her existing persona
("Fintech Centrado en el Ser Humano", "copiloto fiscal 24/7"). No Hermes skill-file mechanism
was found wired to Taty anywhere in this repo (`AGENTES.md`'s agent catalog describes her as a
conversational operator with an LLM system prompt, not a skill-loader). Building one would be
new infrastructure unrelated to fixing a price refusal, so this change adds a persona line
naming the capability ("también es la vendedora estrella de Contexia: conoce los precios reales
y sabe guiar a un prospecto hacia el plan o la banda correcta") and leaves any real skill-file
architecture as a separate, explicitly future decision — consistent with the founder's own
framing that lead qualification is "más adelante", not now.

## Out of scope

- Lead qualification (explicitly future, per the founder).
- A Hermes-native skill/profile artifact for Taty.
- Changing which channels receive `lead_context` at all — Telegram/PWA still get no
  `lead_context`, so they rely solely on the new always-on catalog block, not the Renta Natural
  gate.
