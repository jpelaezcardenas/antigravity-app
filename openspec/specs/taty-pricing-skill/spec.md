## ADDED Requirements

### Requirement: Renta Natural Pricing Is Catalogued With No Invented Ceiling
The system SHALL record the Renta Natural persona-natural filing price in
`core/pricing_catalog.py` as a floor with no maximum, marked quoted, and SHALL NOT invent a
ceiling.

#### Scenario: The floor matches the founder's figure
- **WHEN** the catalog is read
- **THEN** `RENTA_NATURAL_PRICING.min_cents` equals $350.000 in COP minor units and `max_cents`
  is `None`

#### Scenario: The pricing drivers are named data, not prose
- **WHEN** the catalog is read
- **THEN** `RENTA_NATURAL_PRICING.price_drivers` names cantidad de trámites, movimientos, and
  patrimonio

### Requirement: Taty States Real B2B Prices On Every Channel
The system SHALL make Contexia's official software-tier and service-band prices available to
Taty's system prompt regardless of channel, sourced from `core/pricing_catalog.py`.

#### Scenario: The B2B catalog appears in the base prompt
- **WHEN** Taty's system prompt is built, with or without `lead_context`
- **THEN** the prompt states the software tiers and service bands from the catalog

#### Scenario: No price is duplicated as a literal
- **WHEN** the prompt-building code is inspected
- **THEN** no B2B tier or band price appears as a hardcoded number in `taty_service.py`

### Requirement: Taty States The Real Renta Natural Floor Instead Of Refusing
The system SHALL instruct Taty to state the Renta Natural floor price and that it varies by
case, and SHALL NOT instruct her to invent an exact final number or a ceiling.

#### Scenario: The refusal instruction is gone
- **WHEN** `lead_context.offer.precio_confirmado` is true
- **THEN** the system prompt does not instruct Taty to avoid mentioning a price

#### Scenario: The floor and its drivers are stated
- **WHEN** the Renta Natural offer's price is confirmed
- **THEN** the prompt states the floor price and the named drivers that make it vary

#### Scenario: No ceiling or false-final-number instruction is given
- **WHEN** the Renta Natural offer's price is confirmed
- **THEN** the prompt explicitly instructs Taty never to state a final exact price or an upper
  bound, since neither exists

### Requirement: The Pricing Skill Does Not Touch Feature Gating Or Payment Flow
The system SHALL NOT alter `core/plan_features.py`, tenant resolution, or the Wompi HITL
payment-link flow as part of stating prices.

#### Scenario: No plan-gating file is modified
- **WHEN** this change's diff is inspected
- **THEN** `core/plan_features.py` is unchanged

#### Scenario: Payment-link generation is unaffected
- **WHEN** a lead advances to payment after this change
- **THEN** the existing Wompi HITL approval flow behaves exactly as before
