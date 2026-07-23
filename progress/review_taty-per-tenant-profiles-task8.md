# Review — task 8 (taty-per-tenant-profiles): Manual Endpoint Testing with curl

**Verdict:** APPROVED

## What I independently verified

1. **Traceback authenticity (8.2, HTTP 500).** The report's pasted traceback
   (`reports/2026-07-23-step-8-manual-curl.md:73-87`) shows a clean chain:
   `taty_endpoints.py:178 ask_taty -> _resolve_cliente_cero_tenant_id() (line 30) ->
   supabase.table("tenants") -> infrastructure/supabase_client.py:15 _ensure_initialized ->
   supabase/client.py:47 raise SupabaseException("supabase_url is required")`. This is a
   genuine "no Supabase configured locally" failure, not an unrelated crash. Confirmed by
   reading `apps/backend/presentation/taty_endpoints.py:26-36`: `_resolve_cliente_cero_tenant_id()`
   calls `get_supabase()` and `.table("tenants").select("id").eq("is_cliente_cero", True).single().execute()`
   with zero try/except around it — an unguarded raise is exactly what the traceback shows.

2. **Line-by-line comparison against `financials_endpoints.py`.** Its
   `_resolve_cliente_cero_tenant_id()` (`apps/backend/presentation/financials_endpoints.py:10-20`)
   is **byte-for-byte identical** to the taty copy (`taty_endpoints.py:26-36`): same body
   (`supabase.table("tenants").select("id").eq("is_cliente_cero", True).single().execute()` ->
   `return result.data["id"]`), same absence of any try/except. `financials_endpoints.py`'s
   caller (`get_pulso_daily`, lines 64-80) wraps the whole resolution+compute block in a
   `try/except Exception -> HTTPException(500, ...)` — the exact same outer-catch-to-generic-500
   shape as `taty_endpoints.py`'s `ask_taty` (lines 173-215). **Conclusion: this is a faithful,
   line-for-line replication of an already-shipped, already-accepted pattern, not a regression
   introduced by task 3.** Design D3 explicitly instructs this: "copy the `financials_endpoints.py`
   resolution block verbatim in spirit... same 10-line helper duplicated in
   `financials_endpoints.py` — matching existing convention beats inventing a shared module
   mid-change" (`design.md` D3, lines 40-46). Design nowhere asks for new error handling on this
   helper; it explicitly asks for parity with the existing pattern, and parity is what was
   delivered.

3. **8.6 (404) and 8.7 (422) claims.** Re-read the report's pasted output directly:
   - 8.6: `curl -X POST .../agents/taty/ask` -> `{"detail":"Not Found"}` / `HTTP_STATUS:404`
     (report lines 141-148) — matches task 5's route deletion, no DB dependency, credible.
   - 8.7a: `question` under min_length -> pydantic `string_too_short`, `HTTP_STATUS:422`
     (lines 162-167).
   - 8.7b: `question` missing -> pydantic `missing`, `HTTP_STATUS:422` (lines 177-181).
   Both are real, self-consistent Pydantic v2 error payloads (correct `type`/`loc`/`msg`/`ctx`
   shape, correct `errors.pydantic.dev/2.13` URL) — not fabricated boilerplate.

4. **8.3-8.5 deferral.** The report gives a specific, technical reason (no `SUPABASE_URL`/
   `SUPABASE_KEY` locally -> cannot mint a real ES256/JWKS-signed session JWT that would
   exercise `core/deps.py::_verify_supabase_token`'s real verification path per
   `ARCHITECTURE.md` decision #13) rather than a vague "skipped." This is consistent with task 7's
   documented precedent for the identical constraint, and the report is explicit that a
   locally-fabricated JWT would produce a false-positive result, which the task's own
   instructions forbid. This is a reasonable, honest deferral, not a silent skip — confirmed by
   direct comparison with the tasks.md text ("MANDATORY - AGENT MUST EXECUTE") which the report
   respects by executing everything that *is* executable and explicitly flagging what isn't,
   with a Stage 11 landing spot (11.6/11.7) named.

## Determination on the central question

`_resolve_cliente_cero_tenant_id()` in `taty_endpoints.py` behaves **identically** to
`financials_endpoints.py`'s version — both lack a try/except around the Supabase call, both
surface as a generic 500 via an outer catch-all when Supabase is unreachable. This is not a gap
introduced by task 3; it is a pre-existing, already-accepted convention that this change
faithfully replicated per an explicit design instruction (D3) to do exactly that. Production
Railway has Supabase configured, so this specific failure mode does not manifest in the Stage 11
deploy target under normal operation.

**Non-blocking observation for a separate follow-up (not this change):** both
`financials_endpoints.py` and `taty_endpoints.py` will 500 (rather than degrade gracefully) if
Supabase becomes transiently unreachable in production for the Cliente-Cero/staging resolution
path specifically. This is a pattern-wide robustness gap that predates this change and applies
equally to an already-shipped, already-reviewed endpoint (`GET /api/v1/financials`) — it should
not block task 8 or this OpenSpec change. Worth a small follow-up task (e.g. wrap both helpers'
Supabase call in a try/except that raises a clearly-labeled `HTTPException(503, "tenant
resolution unavailable")` instead of falling through to a generic try/except-500) if the founder
wants defense-in-depth against Supabase blips, but out of scope here.

## Checkpoints (Stage 8 — Manual curl testing)

- 8.1 Server boot: [x] — verified in report, clean boot with 60 routes, no crash despite missing
  Supabase credentials.
- 8.2 Unauthenticated GET (staging -> Cliente Cero): [x] as "code path confirmed, outcome
  blocked by environment" — accurately documented as partial, not falsely marked PASS. Root
  cause independently verified as a faithful replication of the existing
  `financials_endpoints.py` pattern (see above), not a regression.
- 8.3 Provisioned client JWT: [ ] deferred to Stage 11 (11.6) — reasonable, matches task 7
  precedent, no fabricated output.
- 8.4 Spoofed `company_id`: [ ] deferred to Stage 11 (11.6) — same reasoning as 8.3.
- 8.5 Unresolved-tenant JWT: [ ] deferred — flagged as having no dedicated Stage 11 item
  (11.6/11.7 don't exactly cover the authenticated-but-unresolved case); implementer correctly
  surfaced this gap for the leader rather than silently letting it fall through. Recommend the
  leader add an explicit Stage 11 item for this before archiving, but it does not block
  approving task 8 itself (task 8's job was testing + honest reporting, which it did).
- 8.7 Malformed body (422 x2): [x] — verified real, correctly-shaped Pydantic errors.
- 8.6 Deleted route (404): [x] — verified.
- No source files modified (testing-only task, confirmed via implementer report and by this
  review not finding any diff outside `progress/` and the report file).
- No fabricated curl output — every response traced to a real, internally-consistent
  request/response/traceback triple.

## Required changes

None. Task 8 is complete and honestly reported. Recommend (non-blocking, for the leader before
Stage 12 archive):
1. Add a Stage 11 verification item covering the authenticated-but-unresolved-tenant case
   (8.5's production equivalent), since 11.6/11.7 don't currently cover it — the implementer
   already flagged this gap in both the impl report and the curl report.
