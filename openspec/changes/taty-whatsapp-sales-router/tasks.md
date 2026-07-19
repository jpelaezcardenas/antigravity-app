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

- [ ] 6.1 Commit backend changes in scoped commits referencing this change id.
- [ ] 6.2 Merge to `main` (check for conflicts) and push.
- [ ] 6.3 Confirm Railway backend deploy completes green with `WHATSAPP_CANONICAL=false` (dark
      deploy — new flag, needs this step like Change E, unlike Change F's flag reuse).
- [ ] 6.4 No frontend touched — no sw.js bump/rebuild-sync for this change; confirm via `git diff`
      at merge time.
- [ ] 6.5 Verify the `GET /channels/whatsapp/webhook` hub.challenge handshake responds correctly
      live even while the flag is dark (a handshake echo carries no data risk) — or confirm it
      404s cleanly if gated entirely behind the flag; document which.
- [ ] 6.6 Flip `WHATSAPP_CANONICAL=true` on Railway. POST a fabricated inbound WhatsApp payload via
      curl; confirm a `crm_leads` row is created/advanced and `crm_tax_profiles` persona fields
      land correctly via direct Supabase SQL. Explicitly note in the deployment report that this is
      a simulated payload, not a real inbound WhatsApp message — true end-to-end verification is
      gated on a real WhatsApp Business number/token that does not exist yet.
- [ ] 6.7 Create deployment report at
      `openspec/changes/taty-whatsapp-sales-router/reports/YYYY-MM-DD-deployment.md`, including the
      accepted-risk notes from design.md (unverifiable end-to-end without a real number; keyword
      classification coarseness, consistent with existing Taty precedent; defensive payload
      parsing).

## 7. Archive

- [ ] 7.1 Sync the `taty-whatsapp-sales-router` capability into `openspec/specs/` (using `git mv`
      for the archive move, per the process fix established after Change A's tree-drift incident)
      and archive this change once Stage 11 is confirmed complete and verified live.
