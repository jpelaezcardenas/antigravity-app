# Tasks: evaluate-omniroute-backend-integration

This is a research change — tasks are investigation steps, not code. No Stage 11 applies unless
the investigation concludes with a go decision and a follow-up implementation change is opened.

## 1. Provider-by-provider review

- [x] 1.1 AI Horde — reliability disqualifier documented (design.md, volunteer/crowdsourced
      compute, no SLA).
- [ ] 1.2 OpenCode Free — ToS + reliability check.
- [ ] 1.3 Felo — ToS + reliability check.
- [ ] 1.4 DVA — ToS + reliability check.
- [ ] 1.5 Remaining short-coded providers (`aug`, `cxa`, `tllm`, `cfp`, `zc`, `no-think`,
      `ddgw`, `unc`, `veo-free`, `veoaifree-web`, `pepper`) — identify what each actually is
      before reviewing ToS (names are not self-explanatory).

## 2. OmniRoute gateway-level review

- [ ] 2.1 Read OmniRoute's own ToS/license terms for redistributing third-party free-tier APIs
      to a commercial application backend — separate question from each underlying provider.

## 3. Reliability benchmark

- [ ] 3.1 Measure p50/p95 latency and failure rate of the OmniRoute combos already in use, under
      backend-realistic request patterns (not just Hermes' own interactive use).

## 4. Cost/benefit quantification

- [ ] 4.1 Quantify what cost problem this would actually solve for the BACKEND specifically
      (not Hermes) — the backend's existing Groq/Cerebras/OpenRouter/NVIDIA NIM cascade is
      already 100% free; clarify what OmniRoute would add beyond redundancy.

## 5. Recommendation

- [ ] 5.1 Final go/no-go recommendation to the founder, once 1-4 are complete. Update design.md
      accordingly. Archive this change regardless of outcome (a documented no-go is a valid
      completion).
