# Task 4 — Chatwoot auto-tagging: extend `_auto_tag_chatwoot()`

**Change:** whatsapp-b2b-lead-bridge
**Task:** Group 4 (4.1-4.4)

## 4.1 — Dropdown value confirmation (READ THIS FIRST)

**CONFIRMED live against the actual Chatwoot instance** — not guessed, not taken from the
archived investigation's paraphrase. The bridge already has `CHATWOOT_URL`/`CHATWOOT_API_TOKEN`/
`CHATWOOT_ACCOUNT_ID` in `apps/chatwoot-bridge/.env` and the instance was reachable
(`curl localhost:3020/api` → 200). I called the Chatwoot API directly:

```
GET {CHATWOOT_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/custom_attribute_definitions
Header: api_access_token: <token from .env>
```

Live response (2026-09-09) for the two relevant attribute definitions:

- `tipo_contribuyente` (id 4, contact_attribute, list): `["persona_natural", "SAS",
  "regimen_simple", "no_responsable_IVA"]`
- `servicio_interes` (id 5, contact_attribute, list): `["renta", "contabilidad_mensual",
  "creacion_empresa", "CFO", "facturacion"]`

**`tipo_contribuyente: "SAS"` is unambiguous** — it is the only business-shaped option on that
attribute, confirmed as the exact string (not a display label, the raw `attribute_values` entry).

**`servicio_interes` has two real, distinct business-shaped options: `"creacion_empresa"` and
`"CFO"`.** Both exist live; the API confirms the *set* of valid values, not which one Taty's new
`business_interest` intent should map to — that's a semantic choice design.md left open
("to confirm against the exact dropdown option string during implementation, per the original
finding's mention of both"). I chose **`"creacion_empresa"`**, because the keyword list driving
`business_interest` (`empresa`, `sas`, `negocio`, `sociedad`, `compañía` — company-formation /
continuous-operations language, per design.md Decision 1) matches "someone is forming or running
a company" more directly than `"CFO"` (which reads as an ongoing outsourced-CFO service request,
a narrower and more advanced signal than the general B2B keyword match this task classifies).

**Explicit flag for the founder, per the task's own instruction:** the *value itself*
(`"creacion_empresa"`) is confirmed to exist and be spelled correctly on the live instance — that
part needs no further verification. What is **not** confirmed, and would benefit from founder
review before Stage 11, is the **semantic mapping choice** between `"creacion_empresa"` and
`"CFO"` for the `business_interest` intent specifically. If a real B2B conversation later shows
the "CFO" label fits better in practice, changing the map entry
(`_INTENT_TO_SERVICIO_INTERES["business_interest"]` in `apps/chatwoot-bridge/main.py`) is a
one-line change, no schema/migration involved.

## 4.2/4.3 — Implementation

Files touched:
- `apps/chatwoot-bridge/tests/test_process_message.py` — added two tests to
  `TestAutoTagChatwoot`:
  - `test_business_interest_tags_conversation_and_contact` — asserts `servicio_interes ==
    "creacion_empresa"` and `tipo_contribuyente == "SAS"` when intent is `business_interest`,
    even when `persona_fields` is present (`{"es_asalariado": False}`) — proving precedence over
    the existing `persona_natural`/`regimen_simple` derivation (design.md Decision 3).
  - `test_business_interest_tagging_failure_never_raises_or_blocks_reply` — `set_attrs` raises;
    asserts the reply is still sent (same fire-and-forget contract as the existing
    `test_tagging_failure_never_raises_or_blocks_reply` for `sales_interest`).
- `apps/chatwoot-bridge/main.py`:
  - Added `"business_interest": "creacion_empresa"` to `_INTENT_TO_SERVICIO_INTERES`, with an
    inline comment recording the live-confirmation source and the CFO alternative.
  - Added a `business_interest` branch in `_auto_tag_chatwoot()` that sets
    `contact_attrs["tipo_contribuyente"] = "SAS"` **before** (elif) the existing
    `persona_fields`/`es_asalariado` derivation, so it takes precedence as required.
  - No change to the fire-and-forget `try/except` wrapper or to `set_conversation_attributes`/
    `set_contact_attributes` call shape — both stay untouched.

## 4.4 — Test results

Ran TDD sequence: new tests failed first against pre-implementation code
(`KeyError: 'servicio_interes'`), then passed after the `main.py` change.

Full-file run after implementation:

```
$ python -m pytest tests/test_process_message.py -q
...
FAILED tests/test_process_message.py::TestSingleBrainInvariant::test_reply_comes_from_the_sales_router_not_hermes
1 failed, 11 passed, 1 warning in 6.15s
```

**The 1 failure is pre-existing and unrelated to this task.** Confirmed by `git stash` (removing
all of my Group 4 changes plus every other uncommitted change in the tree, i.e. reverting to the
committed state at `8a748f7` which already contains Groups 1-3 applied and approved) and
re-running just that test:

```
$ python -m pytest tests/test_process_message.py -k test_reply_comes_from_the_sales_router_not_hermes -q
...
E           AssertionError: expected await not found.
E           Expected: mock(42, 'Respuesta de Taty')
E             Actual: mock(42, 'Respuesta de Taty', private=True)
1 failed, 9 deselected, 1 warning in 5.88s
```

Identical failure, identical mismatch (`send_reply` is called with `private=True` — a
`voicebox-local-voice-adoption` change, unrelated to auto-tagging), with none of my changes
present. `git stash pop` restored my work afterward; no other files were touched by the
stash/pop round-trip.

My two new tests (`test_business_interest_tags_conversation_and_contact`,
`test_business_interest_tagging_failure_never_raises_or_blocks_reply`) are both green, and no
existing `TestAutoTagChatwoot` test (sales_interest, unknown-intent, sales_interest-tagging-
failure) regressed.

## Scope discipline

Did not touch: Groups 1-3 (backend classifier, migration, `route_lead_message` wiring — already
approved), `tasks.md`, any migration file, the Búnker/frontend, or `hermes-hubspot-poller`.
