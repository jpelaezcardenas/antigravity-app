## 1. Setup + schema verification

- [x] 1.1 Created branch `feature/taty-whatsapp-sales-router`.
- [x] 1.2 Re-confirmed live `crm_leads`/`crm_tax_profiles` columns via Supabase MCP (matches
      proposal exactly: `crm_leads(id, tenant_id, full_name, whatsapp_phone, email, stage, source,
      last_message, score, assigned_agent, ...)`, `crm_tax_profiles(id, tenant_id, lead_id,
      es_asalariado, topes, rut_status, extractos_status, obligado_declarar, notes, ...)`).
- [x] 1.3 Re-confirmed `CrmService.advance_lead(lead_id, stage)` /
      `get_tax_profile(lead_id)` / `update_tax_profile(lead_id, patch)` signatures by reading
      `crm_service.py` directly.
- [x] 1.4 Re-confirmed `meta_endpoints.py`'s hub.challenge verification code and
      `channels/telegram.py`'s normalizer shape / `telegram_endpoints.py`'s
      `send_telegram_message` outbound sender pattern by reading them directly.

## 2. WhatsApp channel — inbound normalizer — TDD

- [x] 2.1 Wrote `apps/backend/tests/test_whatsapp_channel.py`: a well-formed fabricated WhatsApp
      Cloud API text-message payload normalizes to the common event shape (`channel="whatsapp"`,
      correct `account_id`/`text`/`actor_name`); a status-only payload, a payload missing `entry`,
      and a malformed nested structure all normalize to an empty list without raising; sender
      tested both when unconfigured (`False`) and configured (mocked `httpx.AsyncClient`).
      Confirmed failing (module didn't exist).
- [x] 2.2 Authored `apps/backend/channels/whatsapp.py`: `normalize_whatsapp_webhook(payload) ->
      List[Dict]` (defensive `.get()` throughout, mirroring `channels/telegram.py`'s style) and
      `send_whatsapp_message(to, text) -> bool` (Graph API `POST /{phone_number_id}/messages` via
      httpx; returns `False`/logs a clear "not configured" case if `WHATSAPP_TOKEN`/
      `WHATSAPP_PHONE_NUMBER_ID` are unset — never calls out with empty credentials).
- [x] 2.3 6/6 tests green.

## 3. Lead-scoped router — TDD

- [x] 3.1 Wrote `apps/backend/tests/test_taty_lead_router.py`: `classify_lead_intent` (sales
      interest, payment-confirmation, unknown); `route_lead_message(lead_id, message)` — mocks
      `CrmService`/`get_service_supabase` directly (no Supabase credentials needed): advances
      `NUEVOS`→`PROSPECTOS` on sales intent; does NOT advance/regress a lead already past `NUEVOS`;
      persists persona fields via `update_tax_profile`, creating an empty tax-profile row first if
      missing; a payment-confirmation intent returns the graceful stub reply and never calls
      `advance_lead`; `find_or_create_lead` (existing-phone match, new-lead creation with
      `stage="NUEVOS"`). Confirmed failing (module didn't exist).
- [x] 3.2 Authored `apps/backend/services/taty_lead_router.py`: `classify_lead_intent(message) ->
      (intent, confidence)` (deterministic keywords, same pattern as `taty_intent_router.py`'s
      `classify_intent` but with sales/payment keyword sets, and NOT imported from/modifying that
      module), `find_or_create_lead(whatsapp_phone, full_name=None) -> lead_id`,
      `route_lead_message(lead_id, message) -> dict`. Reads/writes via `CrmService` (unmodified)
      and direct `get_service_supabase()` calls for lead-stage lookup/creation (isolated in
      `_get_lead_stage`/`_create_empty_tax_profile` for test patching).
- [x] 3.3 Authored the `generate_wompi_link`/`verify_wompi_transaction` stubs (raise
      `NotImplementedError` naming Change C) in the same module; `route_lead_message` never calls
      them — the payment-confirmation branch returns its own graceful reply directly.
- [x] 3.4 11/11 new tests green. Full targeted suite (89 tests: this change + Sell Machine +
      operator task + CRM) green, zero regression; `taty_intent_router.py` untouched.

## 4. Endpoints + flag — TDD

- [x] 4.1 Wrote `test_whatsapp_endpoints.py` (isolated FastAPI app + `httpx.AsyncClient` +
      `ASGITransport` + `pytest.mark.asyncio`, matching the established idiom): `GET /webhook`
      hub.challenge success/failure cases; `POST /webhook` with fabricated normalized events calls
      `find_or_create_lead` + `route_lead_message` and returns `{"ok": true, "events_processed": N}`;
      an empty-events payload does not route anything. Confirmed failing (routes/flag didn't
      exist).
- [x] 4.2 Added `WHATSAPP_CANONICAL: bool = False` to `config.py`. Created
      `apps/backend/presentation/whatsapp_endpoints.py` mounted at `/channels/whatsapp`, registered
      in `router.py` behind the new flag (mirrors `meta_endpoints.py`'s hub.challenge code exactly).
- [x] 4.3 6/6 new endpoint tests green. Full targeted suite (95 tests: this change + Sell Machine +
      operator task + CRM) green, zero regression.

## 5. Verify + DB state (MANDATORY before Stage 11)

- [x] 5.1 Ran the full targeted suite: 95/95 green (23 new + 72 pre-existing, zero regression).
      Confirmed via `git status --short` that no `contexia-app/` files were touched.
- [x] 5.2 Confirmed live in Supabase (via MCP, direct SQL simulation pre-deploy): created a
      disposable `NUEVOS` lead by `whatsapp_phone`, advanced it to `PROSPECTOS`, persisted
      `es_asalariado=true` to a new `crm_tax_profiles` row — all correct. Rows cleaned up.
- [x] 5.3 Wrote `openspec/changes/taty-whatsapp-sales-router/reports/2026-07-19-step5-verification.md`.

## 6. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [x] 6.1 Committed on `feature/taty-whatsapp-sales-router` (`5652f27`), referencing this change id.
- [x] 6.2 Fast-forward merged to `main` (no divergence) and pushed.
- [x] 6.3 Confirmed dark deploy: Railway deployment `9d4a5396` (commit `5652f27`) reached
      `SUCCESS`, and `GET /channels/whatsapp/webhook` returned **404** while
      `WHATSAPP_CANONICAL` was still unset/`false`.
- [x] 6.4 Confirmed no `contexia-app/` files touched — no sw.js bump/rebuild-sync needed.
- [x] 6.5 Verified the hub.challenge handshake 404s cleanly while dark (route not registered at
      all, per design — the flag gates route registration itself, not just its internals).
- [x] 6.6 Flipped `WHATSAPP_CANONICAL=true`. **Deployment instability note**: required 2 manual
      `railway_redeploy` triggers before the service responded reliably (~502 for extended periods
      with no crash signature in logs across 3 total deployments — see deployment report for full
      detail; confirmed via local import test this was not a code-level crash). Once up: hub.challenge
      returned `200`/`12345`; `POST /webhook` with a fabricated inbound message → `{"ok": true,
      "events_processed": 1}`; confirmed via direct Supabase SQL that a real `crm_leads` row was
      created (`whatsapp_phone="573000001111"`, `stage="PROSPECTOS"`, `source="whatsapp"`) through
      the actual deployed webhook → normalizer → router → CrmService path. Documented the
      simulated-payload limitation explicitly in the deployment report.
- [x] 6.7 Created deployment report at
      `openspec/changes/taty-whatsapp-sales-router/reports/2026-07-19-deployment.md`, including all
      accepted-risk notes from design.md plus the deployment-instability incident.

## 7. Archive

- [x] 7.1 Sync the `taty-whatsapp-sales-router` capability into `openspec/specs/` (using `git mv`
      for the archive move, per the process fix established after Change A's tree-drift incident)
      and archive this change once Stage 11 is confirmed complete and verified live.
