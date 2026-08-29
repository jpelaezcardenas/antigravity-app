## 1. Apply vetted source changes

- [x] 1.1 Replace `apps/backend/agents/brand_rubric.py` with Manus's vetted
      `BRAND_RUBRIC_SYSTEM_PROMPT` (leads with "contadoras tituladas con licencia + tecnología",
      60/25/15 hook mix, DIAN as context not protagonist). `HARD_BAN_PHRASES` and Claim Ledger
      logic unchanged.
- [x] 1.2 Replace `apps/backend/agents/content_evaluator.py` with the fail-closed
      `evaluate_hook()` (LLM-unavailable path returns `approved: False`).
- [x] 1.3 Replace `apps/backend/services/copywriter_service.py` with the niche/value
      `_SYSTEM_PROMPT`, `_GENERIC_GROUNDING_QUERY`, and `_DETERMINISTIC_FALLBACK_HOOKS`.

## 2. Apply vetted test changes

- [x] 2.1 Replace `apps/backend/tests/test_content_evaluator.py` (fail-closed assertion).
- [x] 2.2 Replace `apps/backend/tests/test_copywriter_service.py` (niche-value grounding-query
      assertion).

## 3. Verify

- [x] 3.1 Run `pytest apps/backend/tests/test_brand_rubric.py
      apps/backend/tests/test_content_evaluator.py apps/backend/tests/test_copywriter_service.py
      -v` and confirm all pass. **41 passed.**
- [x] 3.2 Confirm no other test file in the repo depended on the old fail-open behavior or the
      old DIAN-default grounding query — grep found `evaluate_hook` used only in
      `sell_machine_service.py::evaluate_hooks()`, which already branches correctly on
      `result["approved"]` being `False` (rewrite-then-discard path), no dependency on the old
      fail-open default.

## 4. Stage 11 — Deploy to Production (MANDATORY, gated on founder confirmation)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [ ] 4.1 Commit locally (held per founder's standing instruction — no push without explicit
      go-ahead, since this changes live Content-Critic behavior).
- [ ] 4.2 On founder confirmation: `git push origin main`.
- [ ] 4.3 Railway build complete (green ✅) for `antigravity-app-production-175a`.
- [ ] 4.4 Production verification: a real `POST /api/v1/sell-machine/hooks/generate` call
      returns niche/value-leaning hooks; a real `POST /api/v1/sell-machine/hooks/evaluate` call
      with the LLM path disabled/mocked confirms fail-closed behavior (or is inferred from the
      passing test suite if a live LLM-outage simulation isn't practical against prod).
- [ ] 4.5 Deployment report:
      `openspec/changes/brand-rubric-niche-positioning-failclosed-fix/reports/YYYY-MM-DD-deployment.md`.

## 5. Close out

- [ ] 5.1 `openspec-sync-specs` to merge the MODIFIED requirements into
      `openspec/specs/sell-machine-creative-swarm/spec.md`.
- [ ] 5.2 Archive per `openspec-archive-change`.
