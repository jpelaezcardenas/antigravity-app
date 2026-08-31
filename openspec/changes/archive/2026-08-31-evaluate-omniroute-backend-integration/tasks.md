# Tasks: evaluate-omniroute-backend-integration

This is a research change — tasks are investigation steps, not code. No Stage 11 applies unless
the investigation concludes with a go decision and a follow-up implementation change is opened.

## 1. Provider-by-provider review

- [x] 1.1 AI Horde — reliability disqualifier documented (design.md, volunteer/crowdsourced
      compute, no SLA).
- [x] 1.2 OpenCode Free — ToS prohibits proxy/resale/third-party access (OmniRoute FREE_TIERS.md
      categorizes it as "Avoid"). Disqualified.
- [x] 1.3 Felo — no public API for backend use; enterprise-only negotiated access; ToS unclear
      for application backend use. Not usable.
- [x] 1.4 DVA — not identified as a distinct provider in OmniRoute's FREE_TIERS.md; unknown ToS.
      Cannot assume safe — excluded by default under the bar set by Finding #2.
- [x] 1.5 Short-coded providers (`aug`, `cxa`, `tllm`, `cfp`, `zc`, `no-think`, `ddgw`, `unc`,
      `veo-free`, `veoaifree-web`, `pepper`) — `ddgw` = DuckDuckGo Web (Avoid), `unc` =
      UncloseAI (prohibits competing ML services), `veo-free`/`veoaifree-web` (prohibit automated
      use). Remaining 5 (`aug`, `cxa`, `tllm`, `cfp`, `zc`, `no-think`, `pepper`) unidentified —
      unknown ToS, excluded by default.

## 2. OmniRoute gateway-level review

- [x] 2.1 OmniRoute is MIT-licensed (software use is fine) but MIT does not shield upstream
      provider ToS. OmniRoute's own FREE_TIERS.md acknowledges upstream terms apply to every
      routed call. No ToS protection from routing through the gateway.

## 3. Reliability benchmark

- [x] 3.1 Skipped — the ToS review (tasks 1–2) disqualifies all reviewed providers for backend
      production use before a reliability benchmark is meaningful. A benchmark of providers you
      cannot legally use for the backend is wasted work.

## 4. Cost/benefit quantification

- [x] 4.1 Backend cascade (Groq → OpenRouter free → NVIDIA NIM) is already $0/month with 3 real
      fallback hops. No cost problem exists for the backend. The "cost savings" cited in earlier
      notes were for Hermes/Houston usage, not the backend. OmniRoute adds no value here.

## 5. Recommendation

- [x] 5.1 **NO-GO** — final recommendation documented in design.md. OmniRoute must not be
      integrated into the antigravity-app backend. Hermes continues to use it per Decision #21
      (local, non-customer-facing). No code changes warranted. Change archived as documented no-go.
