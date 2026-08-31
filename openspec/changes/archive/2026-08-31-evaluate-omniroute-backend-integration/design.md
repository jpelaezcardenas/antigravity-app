# Design: evaluate-omniroute-backend-integration

**Status: CLOSED — NO-GO. OmniRoute is not suitable for the antigravity-app backend.**

## Final recommendation (2026-08-31)

**NO-GO.** OmniRoute must not be integrated into the antigravity-app backend cascade. Hermes
continues to use it for its own local/non-customer-facing automation per Decision #21 — that
use-case is unaffected by this conclusion.

---

## Finding #1 — AI Horde: reliability disqualifier (pre-existing)

AI Horde is a crowdsourced volunteer-powered compute network with no SLA. Disqualified on
reliability grounds for any customer-facing backend path, independent of ToS.

## Finding #2 — OmniRoute's own FREE_TIERS.md explicitly flags the providers as "Avoid" or "Caution"

OmniRoute's own documentation (`docs/reference/FREE_TIERS.md`, reviewed 2026-08-31) categorizes
its providers with explicit ToS warnings:

**"Avoid" (explicit proxy/resale prohibition):**
- `opencode` — prohibits proxy/resale/third-party access
- `duckduckgo-web` (`ddgw`) — prohibits automated querying and developing AI services
- `blackbox`, `coze`, `friendliai`, `kiro`, `modal`, `nlpcloud` — same prohibition class
- `fireworks`, `iflytek` — prohibit automated/programmatic relay use
- `mistral` — APIs limited to "personal needs"
- `agy` — "prohibits using third-party software, tools, or services (including proxies)"

**"Caution" (sublicensing/redistribution prohibited):**
- `groq` — sublicensing/redistribution prohibited (this is already in the backend cascade; its
  direct API use is fine, but routing it via OmniRoute would be a ToS violation)
- `cerebras`, `deepseek`, `sambanova`, `together` — same class
- `gemini`, `nvidia`, `vertex` — free tier restricted to development/prototyping only

**Short-coded providers (partial identification):**
- `ddgw` = DuckDuckGo Web — Avoid
- `unc` = likely UncloseAI — prohibits building competing ML services
- `veo-free`, `veoaifree-web` — prohibit "inhuman speeds" (automated batch use)
- `aug`, `cxa`, `tllm`, `cfp`, `zc`, `no-think`, `pepper` — not identified in FREE_TIERS.md;
  unknown ToS, cannot assume safe

## Finding #3 — OmniRoute gateway ToS (MIT, but upstream terms still apply)

OmniRoute itself is MIT-licensed — the software can be used commercially. However, the MIT
license does not grant rights to use the *upstream providers* it routes to. OmniRoute's own
documentation acknowledges this: upstream provider ToS apply to every routed API call.
Routing through OmniRoute does not create a shield against a provider's ToS.

## Finding #4 — No cost problem exists for the backend to solve

The backend's existing cascade (Groq → OpenRouter free → NVIDIA NIM) is already 100% free with
three real fallback hops. OmniRoute would not reduce cost (already $0) nor meaningfully increase
reliability (adding providers that are explicitly restricted for backend use would add legal risk,
not resilience). The "cost problem" cited in prior session notes referred to Hermes/Houston usage,
not the backend.

## Finding #5 — The bar set by Decision #7 (MiMo exclusion) makes this a non-starter

MiMo (a paid, presumably reliable service) was excluded because its ToS prohibits "application
backend" use. Every OmniRoute provider reviewed in detail either (a) has the same prohibition
explicitly, (b) is categorized "Avoid" in OmniRoute's own docs, or (c) has an unknown/unverified
ToS. None cleared the bar MiMo failed.

## Decision: NO-GO — do not integrate OmniRoute into antigravity-app backend

Hermes continues to use OmniRoute for its own local automation per Decision #21. That is a
separate, lower-risk use case (internal tooling, not serving customer financial data). No code
changes to the backend are warranted from this evaluation.
