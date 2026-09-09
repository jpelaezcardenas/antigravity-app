## ADDED Requirements

### Requirement: Official Prices Have A Single Machine-Readable Source
The system SHALL define Contexia's official prices in exactly one module, covering both revenue
lines — Entidad B software tiers and Entidad A professional-service bands — and SHALL NOT restate
those amounts as literals anywhere else in the codebase.

#### Scenario: Every software tier has a defined commercial name and price
- **WHEN** the catalog is read
- **THEN** it covers exactly the tiers defined in `core/plan_features.py` and gives each a
  commercial name and either a fixed price in COP minor units or an explicit "quoted" marker

#### Scenario: Every service band has a defined price range
- **WHEN** the catalog is read
- **THEN** it covers exactly the bands defined in `services/pricing_service.py` and gives each a
  minimum price, and a maximum that may be explicitly open-ended for a quoted band

#### Scenario: The catalog cannot drift from the keys it prices
- **WHEN** a tier or band is added or removed anywhere in the codebase without updating the
  catalog
- **THEN** an automated test fails, naming the key that is missing or extra

#### Scenario: Monetary values carry their unit in their name
- **WHEN** any price is defined in the catalog
- **THEN** its identifier ends in `_cents`, matching `b2b_clients.monthly_fee_cents`, and no
  identifier holding an amount is named without a unit suffix

### Requirement: A Pre-Quote Reports What Its Suggested Band Costs
The system SHALL include the suggested band's price range in the pre-quote response, so the
output states a commercial consequence rather than only a label.

#### Scenario: A suggested band carries its price range
- **WHEN** a pre-quote returns a suggested band
- **THEN** the response includes that band's minimum and maximum price from the catalog, with the
  maximum null for a band that is quoted case by case

#### Scenario: An empty-state pre-quote reports no price
- **WHEN** a pre-quote returns `sin_historico_suficiente` or `uvt_no_disponible` and therefore no
  band
- **THEN** no price range is reported, rather than a zeroed or defaulted one

### Requirement: A Contexia Operator Can Pre-Quote A Specific Roster Client
The system SHALL expose an operator-only route that returns a pre-quote for a named B2B roster
client, resolving that client's own tenant server-side.

#### Scenario: An operator pre-quotes a roster client
- **WHEN** a caller whose resolved scope covers all tenants requests a pre-quote for a
  `b2b_clients` id
- **THEN** the response is computed exclusively from that client's own tenant's Shadow GL

#### Scenario: A non-operator is refused without confirming the route exists
- **WHEN** a caller whose scope is limited to a single tenant, or whose tenant cannot be
  resolved, requests the operator route
- **THEN** the system returns 404, never 403, and never another tenant's data

#### Scenario: An unauthenticated request is rejected
- **WHEN** a request without a valid session token calls the operator route
- **THEN** the system returns 401

#### Scenario: A roster client with no linked tenant is reported explicitly
- **WHEN** an operator pre-quotes a roster client whose `client_tenant_id` is null
- **THEN** the system returns an explicit state naming that cause, not a 500 and not an empty
  pre-quote that reads as "no activity"

#### Scenario: The self route keeps its no-parameter contract
- **WHEN** the caller's own pre-quote route is invoked
- **THEN** it still accepts no tenant or client identifier of any kind

### Requirement: A Recorded Fee Outside Its Recorded Band Is Surfaced
The system SHALL report when a client's stored `monthly_fee_cents` falls outside the range of its
stored `service_band`, and SHALL NOT reject the write.

#### Scenario: An off-band fee is flagged
- **WHEN** a client is stored with a band and a fee outside that band's range
- **THEN** the roster reports a coherence warning naming the band and the expected range

#### Scenario: A deliberate exception is still recordable
- **WHEN** an operator records an off-band fee
- **THEN** the write succeeds, because Micro is an exception band and Complejo is quoted case by
  case, so legitimate off-range fees exist by construction

#### Scenario: An open-ended band is never flagged as too high
- **WHEN** a client's band has no maximum
- **THEN** no upper-bound warning is produced for any fee

#### Scenario: An incomplete record produces no false warning
- **WHEN** a client has a fee but no band, or a band but no fee
- **THEN** no coherence warning is produced, since there is nothing to contradict

### Requirement: Pricing Documentation Names Its Own Source Of Truth
The system SHALL document the official prices for the founder, and that documentation SHALL name
the catalog module as authoritative over itself.

#### Scenario: The document defers to the module
- **WHEN** the pricing document states a price
- **THEN** it also states that `core/pricing_catalog.py` is authoritative if the two disagree

#### Scenario: Cost structure records the sovereign-inference position
- **WHEN** the pricing document describes cost structure
- **THEN** it records that inference is being consolidated onto owned local hardware and is
  therefore not a per-client variable cost, and states that these prices must not be re-derived
  from a paid-per-token vendor's rates

#### Scenario: No invented margin figure
- **WHEN** the pricing document describes cost structure
- **THEN** it contains no per-client infrastructure cost or margin percentage, because none has
  been measured
