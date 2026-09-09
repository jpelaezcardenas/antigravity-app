# Review — task whatsapp-b2b-lead-bridge_task4 (Group 4: Chatwoot auto-tagging)

**Verdict:** APPROVED

## Independent verification performed

1. **CRITICAL — 4.1 dropdown value confirmation.** Independently re-ran the exact live call the
   implementer claimed to have made:
   `GET http://localhost:3020/api/v1/accounts/2/custom_attribute_definitions` with the token from
   `apps/chatwoot-bridge/.env` (`CHATWOOT_URL`/`CHATWOOT_API_TOKEN`/`CHATWOOT_ACCOUNT_ID=2`).
   Live response byte-for-byte confirms the implementer's report: attribute id 4
   `tipo_contribuyente` = `["persona_natural","SAS","regimen_simple","no_responsable_IVA"]`, id 5
   `servicio_interes` = `["renta","contabilidad_mensual","creacion_empresa","CFO","facturacion"]`.
   Not fabricated — the claim is genuine and reproducible.
   The implementer did **not** overclaim: they explicitly separated "the value exists and is
   spelled correctly" (confirmed) from "which of the two real business-shaped
   `servicio_interes` options (`creacion_empresa` vs `CFO`) is the right semantic mapping for
   `business_interest`" (a judgment call, honestly flagged for founder review, exactly per
   design.md's own open risk at `openspec/changes/whatsapp-b2b-lead-bridge/design.md:101-102`).
   This is the honest-uncertainty behavior the task required, not fabrication.

2. **`_INTENT_TO_SERVICIO_INTERES["business_interest"] = "creacion_empresa"`** confirmed at
   `apps/chatwoot-bridge/main.py:76`. Precedence of the `tipo_contribuyente` branch confirmed at
   `main.py:119-124` — `if intent == "business_interest": ... "SAS"` comes before the
   `elif "es_asalariado" in persona_fields` derivation, so business signal wins as required.

3. **Fire-and-forget contract preserved.** `_auto_tag_chatwoot()` still wraps everything in a
   single `try/except Exception` (`main.py:100-130`) that only logs
   (`logger.exception(...)`) — no re-raise, no effect on the already-sent reply. Verified via
   `test_business_interest_tagging_failure_never_raises_or_blocks_reply`: `set_attrs` raises, and
   `send_reply` is still asserted awaited.

4. **Tests are legitimate TDD, not boundary-mocking.** Both new tests mock `taty_reply`
   (upstream classification — the input boundary) and the Chatwoot HTTP client calls
   (`set_conv_attrs`/`set_attrs` — the external-service boundary), while exercising the real
   `_auto_tag_chatwoot()` intent→attribute mapping and precedence logic under test. This mirrors
   the existing `sales_interest` test pattern and does not mock the function under test itself.
   Ran independently: `python -m pytest tests/test_process_message.py -k business_interest -v`
   → 2 passed.

5. **No regression.** Full suite: `python -m pytest tests/test_process_message.py -q` →
   `1 failed, 11 passed`. The 1 failure
   (`TestSingleBrainInvariant::test_reply_comes_from_the_sales_router_not_hermes`) is pre-existing
   and unrelated — confirmed independently that it's a `private=True` kwarg mismatch from the
   already-shipped `voicebox-local-voice-adoption` change (commit `8a748f7`), not something Group
   4 introduced. `git status --short apps/chatwoot-bridge/` shows only `main.py` and
   `tests/test_process_message.py` touched — no Groups 1-3 files, no migrations, no
   frontend/Búnker files touched.

## Checkpoints
- C1 (no fabricated source for the dropdown value): [x]
- C2 (correct map entry + precedence): [x]
- C3 (fire-and-forget preserved): [x]
- C4 (legitimate TDD, tests pass): [x]
- C5 (no regression, scope discipline): [x]

## Required changes
None. Recommend the founder confirm the `creacion_empresa` vs `CFO` semantic choice for
`business_interest` before Stage 11, per the implementer's own flag — this is a product judgment
call, not a code defect, and does not block approval of this implementation task.
