# Deployment report — fix-llm-engine-required-keys

Date: 2026-07-20

## Summary

Change deployed and verified live in production. The real JSON-mode LLM path (via
`get_ai_response_with_profile`'s custom-provider-order branch) now works end-to-end for the first
time — confirmed by a `POST /sell-machine/hooks/generate` call returning genuinely fresh,
LLM-generated hook content instead of the deterministic fallback set that appeared in every prior
Stage 11 this session.

## Commits deployed

- `1ae83fb` — fix(llm-engine): `_get_json_with_retry_custom_order` matched parse-then-validate pattern
- `ddb30bd` — fix(llm-engine): parse-failed check crashed on legitimate top-level JSON array responses

## Two bugs found and fixed in this change

1. **The originally-flagged bug**: `_get_json_with_retry_custom_order` called
   `self._parse_llm_response(raw_response, synonyms, list_keys, required_keys)` expecting a
   `(parsed, is_valid)` tuple back, but the real signature is
   `(self, response, synonyms=None, list_keys=None) -> Dict` — raised `TypeError` on every real
   call. Fixed by rewriting the function to mirror the already-correct sibling
   `_get_json_with_retry`'s pattern: parse via `_parse_llm_response`, then validate separately via
   the existing `_validate_required(parsed, required_keys)`.
2. **A second, deeper bug found live during this change's own Stage 11 smoke test** (not present
   in the original proposal — discovered while verifying fix #1's own success criterion):
   `parsed.get("parsing_error")` crashed with `AttributeError: 'list' object has no attribute
   'get'` whenever the LLM legitimately returns a top-level JSON array — exactly what Copywriter's
   system prompt explicitly requests ("Responde en JSON como una lista de objetos"). Present in
   **both** `_get_json_with_retry` and `_get_json_with_retry_custom_order` (identical line in
   both — fixed in both for consistency, matching design.md's own goal of byte-identical behavior
   between the two variants). Fixed via an `isinstance(parsed, dict)` guard.

## Stage 11 steps executed

1. Merged `feature/fix-llm-engine-required-keys` to `main` (fast-forward), pushed. Railway deploy
   `ed1279cc` (fix #1 only) reached `SUCCESS`.
2. **First live smoke test**: `POST /sell-machine/hooks/generate` → `200`, but still returned the
   deterministic fallback content. Railway logs confirmed the original `TypeError` was gone
   (fix #1 worked), but a **new** `AttributeError: 'list' object has no attribute 'get'` appeared
   instead — the second bug, discovered only because a real LLM call finally reached the
   parse/validate layer for the first time with a genuinely array-shaped response.
3. Fixed the second bug (commit `ddb30bd`), added 2 regression tests
   (`TestJsonRetryListShapedResponse`), re-ran the full suite (57/57 green), pushed, redeployed.
   Railway deploy `85e1246d` reached `SUCCESS`.
4. **Second, definitive live smoke test**: `POST /sell-machine/hooks/generate` with `{"count": 3}`
   → `200`, `5.119s`. Returned hooks were completely different from the known deterministic
   fallback set (fresh headlines like "¿Multas de la DIAN te están quitando el sueño?" instead of
   "¿Sabes si te toca declarar renta este año?") — **definitive proof the real LLM JSON path now
   works end-to-end**. Railway logs show zero `TypeError`/`AttributeError` anywhere in the
   request; the first Groq attempt returned malformed JSON (a real model-quality hiccup, not a
   bug) and the existing retry-with-re-prompt logic correctly retried and succeeded on the second
   attempt — the retry mechanism itself confirmed working as designed for the first time too.

## Impact confirmed

Both `copywriter_service.generate_hooks` and (per `activate-telemetry-loop`'s earlier Stage 11
logs showing the identical crash in `agents/content_evaluator.py`) the Content Critic's tone-check
should now both use real LLM output instead of always silently falling back to their documented
degradation behavior. This is the highest-reach fix of the session — it was silently degrading
every JSON-mode profile-routed LLM call in the Sell Machine.

## Verification evidence

- Railway deployment `85e1246d` (final): `SUCCESS`, confirmed responding.
- Live `POST /sell-machine/hooks/generate`: `200`, fresh LLM-generated content confirmed distinct
  from the deterministic fallback set, zero errors in Railway logs.
- Full regression suite: 57/57 green (1 pre-existing e2e-gated skip), zero regression.
