# Design — pricing-catalog-and-operator-quote

## Decision 1 — the catalog lives in code, not in a table (deliberately unlike `uvt_values`)

The immediately preceding change put the UVT in a **database table** and argued hard that a code
constant would be wrong. Putting prices in code looks like a contradiction, so the difference is
worth stating precisely:

| | UVT | Price |
|---|---|---|
| Who changes it | DIAN, by resolution | The founder, by decision |
| When | Every December, on a legal calendar | Whenever the business decides |
| What happens if nobody touches the repo | It silently becomes **wrong** every 1 January | Nothing — it stays correct |
| Correct failure mode | Must be updatable without a deploy | *Should* require review before changing |

A price is not a fact about the world that drifts underneath us; it is a decision. Routing a
price change through a commit, a test run and a review is a feature, not friction — at 11 clients
the cost of a deploy is trivial next to the cost of a wrong published price. The UVT's rot risk
does not exist here.

The second reason is cohesion. `SERVICE_BANDS` already lives in `pricing_service.py` and
`PLAN_FEATURES` in `plan_features.py`. A table would split *what a band is* (code) from *what a
band costs* (database), and the two would drift. Keeping the price beside the key it belongs to
means a test can assert they cover exactly the same set — which is what task 1.4 does.

## Decision 2 — prices in minor units (`_cents`), unlike `uvt_values.value_cop`

Every monetary name in this codebase must carry its unit, and the unit is chosen by what the
value is *compared against*, not by aesthetics:

- `uvt_values.value_cop` is compared against annualised revenue converted to whole pesos, and is
  a legal figure published in whole pesos → whole COP.
- Catalog prices are compared against `b2b_clients.monthly_fee_cents` → **minor units**.

Forcing uniformity would put a conversion at the comparison site, which is exactly where a 100×
error becomes a wrong quote to a real client. The naming discipline (`_cop` vs `_cents`, never a
bare `price`) is the invariant, not the unit itself.

## Decision 3 — the operator route follows Approval Queue, not a tenant query param

`resolve_request_tenant_scope()` already returns `all_tenants=True` when the caller's membership
resolves to Cliente Cero — that is the Contexia-operator case, established in Decisión #14 and
implemented in `approval_queue_endpoints.py` as
`effective_tenant_id = tenant_id if scope.all_tenants else scope.tenant_id`.

This change reuses that contract rather than inventing one:

- New route `GET /api/v1/pricing/pre-cotizacion/cliente/{b2b_client_id}`.
- **Operator only.** `scope.all_tenants` false, or no scope at all → **404**, never 403
  (anti-enumeration, Decisión #17). A B2B client must not be able to discover the route's shape,
  let alone another client's numbers.
- The path takes the **`b2b_clients.id`**, not a raw tenant UUID. That is the identifier the
  Búnker already holds, and it keeps tenant UUIDs off the URL surface. The route resolves
  `b2b_clients.client_tenant_id` server-side; a roster row with no linked tenant yet returns an
  explicit `estado`, not a 500.
- Decisión #17's "no tenant query param" rule is untouched: the *self* route still has no
  parameter. Selecting a tenant is legitimate **only** for a scope that is already entitled to
  every tenant, which is precisely what Approval Queue established.

## Decision 4 — the cost-structure section exists because inference is moving on-prem

The founder asked for this to account for the migration to a sovereign local inference node. It
changes what the pricing doc must say, in two concrete ways:

**It removes a per-client variable cost.** Decisión #7 already forced the backend onto a
100%-free LLM cascade, and Decisión #21 moved Hermes' fallback to OmniRoute running locally,
alongside Hermes and GBrain (Decisiones #1 and #10). As inference consolidates onto owned
hardware, marginal cost per client tends toward electricity, not tokens. That is what makes a
$0 freemium tier and a $249.000 software tier structurally sound rather than a subsidy — and it
is the *reason* the numbers can be what they are.

**It forbids a pricing assumption.** The doc must state that these prices are **not** to be
re-derived from a paid-per-token vendor's rate card, because the architecture has deliberately
walked away from that dependency — twice, and once for a ToS reason (MiMo is excluded from the
backend outright). A future session that "recalculates margins" against OpenAI-style pricing
would be reasoning from a stack this project does not use.

The doc records this as **cost structure**, not as a margin model. Contexia has no measured
per-client infrastructure cost yet, and inventing one would repeat exactly the failure the
pre-quote engine was designed to avoid.

## Decision 5 — fee/band coherence is a warning, never a block

`monthly_fee_cents` outside its `service_band` range surfaces as a warning in the roster and in
the pre-quote response. It does not reject the write.

Micro is explicitly documented as an *exception* band, and Complejo is "cotizado" — i.e. by
construction there are legitimate fees outside any range. Blocking would force Tatiana to
mis-record the band to record the true fee, which destroys exactly the data this pair of columns
was added to capture. Surfacing beats enforcing.

`complejo` has an open-ended maximum (`max_cents = None`), so it can never be flagged as "too
high" — only as below its floor.

## Decision 6 — the doc points at the module; the module is the source

`docs/pricing.md` states the numbers **and** names `core/pricing_catalog.py` as authoritative.
Restating numbers in two places creates drift, but a doc that only says "read the code" is
useless to the founder, who is its primary reader. The resolution: the doc is the explanation and
the rationale; the module is the value. A test (`test_pricing_catalog.py`) asserts the module's
internal consistency, and the doc carries a visible "if these disagree, the module wins" line.

English body per `docs/documentation-standards.md`, with a bilingual founder summary at the top
under CLAUDE.md §2's explicit carve-out for founder-facing summaries.

## Out of scope (named, not silently dropped)

- **Taty's sales prompt.** It is currently instructed not to state prices because none existed.
  They exist now, so it *could* — but that is a live customer-facing sales agent on WhatsApp, and
  the same archived change documents the model inventing figures when ungrounded. Flagged for the
  founder as a separate decision.
- **Reconciling the drifted commercial names** in `TenantInfoCard.tsx` / `UpgradePlanBanner.tsx`.
  Those files carry another effort's uncommitted work; the catalog gives them a source to align
  to, but editing them here would collide with that session.
- **MRR projection from `monthly_fee_cents`.** Now finally possible, but it is reporting, not
  pricing.
