# Design: evaluate-omniroute-backend-integration

**Status: IN PROGRESS — preliminary findings only, not a final recommendation.**

## Context

`docs/integrations/OMNIRROUTE_SETUP.md` lists the providers actually wired into Contexia's
OmniRoute combos (not the full 476+ catalog OmniRoute exposes in general — only what's
configured): OpenCode Free, Felo, AI Horde, DVA, plus several unnamed short-coded providers
(`aug`, `cxa`, `tllm`, `cfp`, `zc`, `no-think`, `ddgw`, `unc`, `veo-free`, `veoaifree-web`,
`pepper`). A full per-provider ToS + reliability review of all of these was not completed in
this pass — this design.md documents what was checked and flags what remains open.

## Preliminary finding #1 — AI Horde: reliability disqualifies it for backend production traffic,
independent of ToS

Verified directly (`stablehorde.net/mission/`, `aihorde.net`): AI Horde is a **crowdsourced,
volunteer-powered compute network** — image/text generation capacity comes from community
members donating GPU time, not a hosted service with an SLA. The project is explicitly
community-first, not opposed to commercial use, but capacity and latency are inherently
unpredictable (volunteer nodes join/leave at will).

**Conclusion**: even if AI Horde's ToS technically permits commercial/application use, it is
**not suitable** for any backend path that serves real customer requests (`/financials`, Taty
responses, Centinela alerts) — those need bounded, predictable latency. This is a reliability
disqualifier, not a ToS one. AI Horde may still be fine for Hermes' own internal/non-customer-
facing reasoning (where it already lives, per Decision #21) — that distinction matters: Hermes
using it for its own local automation is a different risk profile than the backend using it for
paying-customer traffic.

## Preliminary finding #2 — the backend's existing MiMo exclusion (Decision #7) sets the bar

The backend already excluded MiMo specifically because its ToS prohibits "application backend"
use, even though it's a paid, presumably more reliable service than most of OmniRoute's free
tier. Any OmniRoute-routed provider considered for the backend needs to clear a **higher** bar
than MiMo failed to clear, not a lower one — free-tier ToS for aggregated third-party APIs
tends to be more restrictive about redistribution/backend use, not less.

## Open — not yet investigated

- OpenCode Free, Felo, DVA, and the 11 short-coded providers: no ToS review done yet for any of
  them individually. Do not assume any are backend-safe without checking.
- Whether OmniRoute's own gateway ToS (as the aggregator/redistributor) imposes its own
  restriction on backend/application use, separate from each underlying provider's terms.
- Actual measured latency/failure rate of the OmniRoute combos already in Hermes use — no
  benchmark has been run against backend-realistic traffic patterns.
- Whether it's worth pursuing at all given the backend's existing free cascade (Groq/Cerebras/
  OpenRouter/NVIDIA NIM) already covers 3-4 real hops with acceptable reliability — the actual
  cost problem this would solve for the backend (as opposed to Hermes' own usage) hasn't been
  quantified.

## Preliminary recommendation (subject to revision once the above is investigated)

**Lean no-go for now, pending the remaining research.** The one provider checked in detail (AI
Horde) is disqualified on reliability grounds for customer-facing traffic, and the backend's
existing cascade isn't obviously under-served by comparison. This isn't a final answer — it's
the honest state of a partial evaluation. Do not treat this as closing the question; the
remaining 13+ providers and the OmniRoute gateway's own terms are still unverified.
