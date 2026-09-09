# Contexia — Official Pricing

> **Source of truth:** [`apps/backend/core/pricing_catalog.py`](../apps/backend/core/pricing_catalog.py).
> **If this document and that module disagree, the module wins.** This file exists to explain
> *why* the numbers are what they are; the module holds the values, and
> `apps/backend/tests/test_pricing_catalog.py` pins them so a silent edit fails a test instead of
> reaching a customer.

---

## Resumen para el fundador (2 minutos)

Contexia vende **dos cosas distintas, facturadas por dos entidades distintas**. Esto no es un
detalle contable: es la razón de que existan dos listas de precios y de que un cliente pueda
pagar lo mismo por el software y distinto por el servicio.

- **Entidad B** (Contexia S.A.S., empresa TIC) vende **licencia de software**. Precio fijo por
  plan. Es lo que el cliente abre en el navegador.
- **Entidad A** (práctica contable regulada, inscrita en la JCC) vende **servicio profesional**.
  Precio en **banda**, según la carga real de trabajo. No es un plan: es horas de contadora.

**Lo más importante de entender:** *Contexia Pro Micro* y *Contexia Pro Estándar* son **el mismo
software**, con exactamente las mismas funciones. Lo que cambia es cuánto trabajo humano requiere
ese cliente. Por eso el precio del servicio **no** vive en el plan (`core/plan_features.py`), sino
en la ficha del cliente (`b2b_clients.monthly_fee_cents` + `service_band`).

| Plan (cara al cliente) | `plan_tier` | Precio | ¿Incluye contadora? |
|---|---|---|---|
| **Pulso** | `freemium` | $0 | No |
| **GPS** | `starter` | **$249.000**/mes | No — el cliente conserva su contador |
| **Contexia Pro** | `growth` | **desde $1.490.000**/mes | Sí |
| **Contexia Total** | `enterprise` | Cotizado | Sí + revisoría fiscal |

| Banda de servicio (Entidad A) | `service_band` | Precio |
|---|---|---|
| **Micro** — excepción: movimiento mínimo, sin carga laboral | `micro` | **$890.000** (precio fijo) |
| **Estándar** — la mayoría de los casos | `estandar` | **$1.490.000 – $2.400.000** |
| **Complejo** | `complejo` | Cotizado caso por caso |

El "desde $1.490.000" de Contexia Pro **es** el piso de la banda Estándar — es el mismo número,
referenciado una sola vez en el código para que no puedan desincronizarse.

---

## How the two price lists relate

`plan_tier` governs **what the client can open** (`core/plan_features.py`). `service_band` governs
**what the accounting work costs** (`core/pricing_catalog.py`). They are independent on purpose:

- A `growth` client can be `micro` or `estandar` — same software, different human load.
- Changing a client's band must never change their feature access, and changing their tier must
  never silently re-price their professional service.

This is why `plan_features.py` is deliberately untouched by the pricing catalog. Conflating the
two would let a commercial decision alter a technical entitlement, or vice versa.

## Recording a quote

1. The pre-quote engine (`GET /api/v1/pricing/pre-cotizacion/cliente/{id}`) reads the client's
   Shadow GL and **suggests** a band.
2. Tatiana (the licensed accountant) confirms or overrides it.
3. The Búnker records the agreed `monthly_fee_cents` and `service_band` on the client.

The engine never sets a price and never writes a band. Its suggestion is **partial by
construction**: payroll/labour load does not exist in the data model and is roughly half the fee
criterion, so the engine always reports it as a missing driver and never claims high confidence.

### Fee/band coherence is advisory, never blocking

When a recorded fee falls outside its recorded band, the roster shows a warning. It does **not**
reject the write, because legitimate off-range fees exist by construction: Micro is explicitly an
exception, and Complejo is quoted case by case. Blocking would force an operator to mis-record the
band in order to record the true fee — destroying the very data these columns capture.

Complejo has **no** floor and **no** ceiling in the catalog. No published figure exists for it, and
inventing one (e.g. "starts where Estándar ends") would flag legitimate quotes as incoherent.

## Cost structure

Contexia's inference is being consolidated onto **owned, local hardware** — Hermes and GBrain
already run on-prem for data-sovereignty reasons (ARCHITECTURE.md Decisiones #1 and #10), the
backend's LLM path is a 100%-free provider cascade with no paid vendor in the default path
(Decisión #7), and Hermes' fallback moved to a locally-hosted OmniRoute gateway (Decisión #21).

Two consequences for pricing:

1. **Inference is not a per-client variable cost.** As it consolidates on hardware Contexia owns,
   the marginal cost of serving one more client tends toward electricity, not tokens. That is what
   makes a $0 freemium tier and a $249.000 software tier structurally sound rather than a
   subsidy — and it is why data sovereignty is a selling point for the tiers that handle
   regulated financial data, not just an architectural preference.

2. **These prices must not be re-derived from a paid-per-token vendor's rate card.** The
   architecture has deliberately walked away from that dependency — twice, and once for a
   contractual reason (MiMo is excluded from the backend outright by its ToS, Decisión #7). A
   future analysis that "recalculates margins" against OpenAI-style pricing would be reasoning
   from a stack this project does not use.

**No margin figure appears in this document.** Contexia has not measured a per-client
infrastructure cost, and inventing one would repeat exactly the failure mode the pre-quote engine
was designed to avoid: a confident number with nothing underneath it.

## A third revenue line: Renta Natural (persona natural)

Alongside Entidad B's software tiers and Entidad A's B2B service bands, Contexia sells Renta
Natural tax-filing through the WhatsApp sales funnel. Founder-given (2026-09-09): **desde
$350.000**, varying by cantidad de trámites, movimientos, and patrimonio — no ceiling, because
none exists; it is quoted case by case once an advisor reviews the client's information. Same
shape as the Complejo band: a real floor, deliberately no invented maximum.

## Taty's pricing skill (`taty-pricing-skill`, 2026-09-09)

Taty (the WhatsApp/Telegram/PWA conversational agent) previously refused to state any price,
because when `taty-whatsapp-renta-sales-capability` shipped, none were defined. Both gaps are
now closed by the founder's own commercial decision:

- **Every channel** states the B2B software tiers and service bands from this catalog (read live,
  never retyped as a prompt literal).
- **The Renta Natural WhatsApp funnel** states the $350.000 floor and its drivers, with an
  explicit instruction never to state a final exact number or an invented ceiling — the same
  discipline this whole catalog follows, applied to a live sales conversation.

Related: `TenantInfoCard.tsx` and `UpgradePlanBanner.tsx` carry hand-written commercial names that
drifted from the official ones. The catalog now gives them a source to align to (not yet done —
would collide with concurrent work on those files).

## References

- Values: `apps/backend/core/pricing_catalog.py` (authoritative)
- Pinned amounts: `apps/backend/tests/test_pricing_catalog.py`
- Entity split and legal limits: `.antigravity/GROUND_TRUTH.md` (governs identity)
- Feature access, deliberately separate: `apps/backend/core/plan_features.py`
- Pre-quote engine: `openspec/changes/archive/2026-09-09-pricing-quote-engine/`
