# Official price catalog + operator pre-quote

## Why

`pricing-quote-engine` (archived 2026-09-09) shipped the engine. It is deployed and reachable,
but it is **not usable for its actual purpose**, and the prices it exists to support are written
down nowhere.

**1. The engine cannot quote a client.** `GET /api/v1/pricing/pre-cotizacion` resolves the tenant
of *the caller*. In the Búnker the caller is a Contexia operator (their membership resolves to
Cliente Cero), so today the endpoint returns **Contexia's own** pre-quote, not the prospect's.
Tatiana cannot use it to size the client she is about to quote — which is the one workflow the
engine was built for.

**2. The official prices exist nowhere in the repo.** Verified by grep: no file contains
`249.000`, `1.490.000`, or `890.000`. They live only in the founder's head and in chat. The
consequence is already visible in the codebase:

- `TenantInfoCard.tsx` and `UpgradePlanBanner.tsx` carry hand-written commercial names that
  drifted from the official ones, edited ad hoc in an unrelated effort.
- `taty-whatsapp-renta-sales-capability` had to instruct Taty's system prompt to **refuse to
  state a price**, because "las tarifas están sin definir" — and that same change documents the
  model confidently inventing tax figures and contact details when it lacked grounding. An
  undefined price is not a neutral gap; it is an invitation for an LLM to fabricate one.
- The engine suggests a band (`micro`/`estandar`/`complejo`) but cannot say what that band costs,
  so its output still needs a human who happens to remember the numbers.

**3. Nothing enforces that a recorded fee matches its band.** `service_band` and
`monthly_fee_cents` are independent columns. A client can be stored as `micro` with a
$2.400.000 fee and nothing notices.

## What changes

1. **`core/pricing_catalog.py`** — the single machine-readable source of truth for both revenue
   lines: Entidad B software tiers (fixed) and Entidad A service bands (ranges). Prices in COP
   minor units, named `_cents`, matching `b2b_clients.monthly_fee_cents`. A test asserts the
   catalog covers exactly the tiers in `plan_features.PLAN_FEATURES` and exactly the bands in
   `pricing_service.SERVICE_BANDS`, so the three cannot drift apart.

2. **`docs/pricing.md`** — the canonical human reference, pointing at the module rather than
   restating the numbers, plus the cost-structure section the sovereign-local-inference migration
   makes necessary (see design.md Decision 4).

3. **Pre-quote reports what the band costs** — the response gains the suggested band's price
   range, so the output is actionable rather than a label.

4. **Operator route** `GET /api/v1/pricing/pre-cotizacion/cliente/{b2b_client_id}` — lets a
   Contexia operator pre-quote a specific roster client, following Approval Queue's
   operator-scope precedent (ARCHITECTURE.md Decisión #14). Non-operators get 404.

5. **Búnker integration** — a per-client "Pre-cotizar" action in the B2B/Retainers tab that shows
   the suggested band, its price range, the confidence, and the drivers the engine could not
   observe, next to the band selector that records the decision.

6. **Fee/band coherence warning** — when a recorded `monthly_fee_cents` falls outside its
   recorded `service_band` range, the roster says so. A warning, not a block: a deliberate
   exception is legitimate, silently losing track of it is not.

## Non-goals

- **Not enforcing price.** The catalog informs; Tatiana still decides. Nothing rejects a fee for
  being off-band, and nothing writes a band automatically.
- **Not changing `core/plan_features.py`.** Feature access and price remain separate concerns —
  Pro Micro and Pro Estándar are the same software.
- **Not wiring prices into Taty's sales prompt.** Now that prices exist, Taty *could* state them
  on WhatsApp. That is a customer-facing change to a live sales agent and is flagged for the
  founder, not made here.
- **Not billing.** No invoicing, no Wompi link generation, no MRR projection.
