## Context

`_detect_persona_fields(message)` in `taty_lead_router.py` already exists and is called from
`route_lead_message` on every inbound WhatsApp message; it currently only fills `es_asalariado`
via two keyword tuples (`_ASALARIADO_KEYWORDS`, `_INDEPENDIENTE_KEYWORDS`), and its docstring
already (incorrectly) claims to extract `topes` too. `crm_tax_profiles.topes` (jsonb, default
`'{}'`) and `.obligado_declarar` (boolean, nullable) are live columns nobody writes to.
`core/constants.py` already defines `UVT_2026 = 49799`, `UMBRAL_RENTA_UVT = 1400`, and
`UMBRAL_RENTA_COP = UMBRAL_RENTA_UVT * UVT_2026` (~$69.7M COP) — the renta-declarant threshold this
change reuses rather than reinvents. (`centinela_service.py` has its own separate `UVT_2026 =
52.374` + `REGIMEN_SIMPLE_LIMIT_UVT = 160` for a different rule — RUT/Régimen Simple, not the renta
threshold — left untouched, not reused here.)

## Goals / Non-Goals

**Goals:**
- Detect a peso amount tied to a qualifying category (`consignaciones`, `ingresos`, `compras`,
  `patrimonio`) mentioned in a lead's WhatsApp message and accumulate it into `topes` (merge, not
  overwrite — a lead may mention different categories across several messages).
- Once at least one `topes` category is known, compute a **preliminary** `obligado_declarar`
  signal against `UMBRAL_RENTA_COP`.
- Keep detection in the same deterministic-keyword style as the existing `_detect_persona_fields`
  — no new dependency, no LLM call, consistent with gap #3 (ReAct) being explicitly out of scope
  for this change.

**Non-Goals:**
- Not a legally authoritative renta-declarant determination. Per `.antigravity/GROUND_TRUTH.md`,
  Contexia is the Entidad B (tech), not a regulated accounting firm — `obligado_declarar` is a
  **preliminary signal** for Taty/the human contadora to confirm, never presented to the lead as a
  final ruling. This change does not change any user-facing copy that states a determination as
  fact.
- Not implementing the full DIAN topes checklist (compras/patrimonio have their own distinct UVT
  thresholds in real DIAN rules) — only the `ingresos`/`consignaciones` category is checked against
  `UMBRAL_RENTA_COP` for now, since that's the only threshold already computed in this repo. Adding
  the other category-specific thresholds is a follow-up if the founder wants Taty to be more
  precise; flagged as an Open Question below, not silently assumed.
- No new WhatsApp-side qualifying questions (e.g. Taty doesn't yet proactively ask "cuánto te
  consignaron el año pasado?") — this change only reacts to whatever the lead volunteers. Adding
  proactive qualifying questions is a UX/conversation-design decision for a later change (would also
  interact with gap #3's ReAct rework), not bundled here.

## Decisions

1. **Peso-amount extraction stays regex/keyword-based, not LLM-based** — matches the existing
   `_detect_persona_fields` style and this change's narrow scope. A category keyword
   (`consign(?:é|acion)|ingres|compr|patrimonio`) followed within the same message by a peso amount
   (`\d[\d.,]*\s*(?:millones?|mill|k)?`) is parsed into COP. Supports plain numbers
   ("70000000"), "millones" suffix ("70 millones" → 70,000,000), and "k" suffix as thousands ("70k"
   → 70,000) — the three shapes a WhatsApp lead is realistically going to type.
2. **`topes` merges, never overwrites.** `service.update_tax_profile(lead_id, {"topes": {**existing,
   **new}})` — reading the current `topes` first (already fetched via `get_tax_profile` in the
   existing `route_lead_message` flow) before merging, so a lead mentioning `consignaciones` in one
   message and `ingresos` in another doesn't lose the earlier one.
3. **`obligado_declarar` is computed, not detected directly.** Once `topes` contains any of
   `ingresos`/`consignaciones`, compare the max of those two against `UMBRAL_RENTA_COP`; set
   `obligado_declarar = amount >= UMBRAL_RENTA_COP`. Recomputed every time `topes` changes (cheap,
   deterministic), not cached separately from the trigger.
4. **Reuse `core/constants.py`, not `centinela_service.py`'s constants** — different named
   constants with the same name (`UVT_2026`) but different values/purposes in this repo already
   (confirmed via grep); `core/constants.py`'s `UMBRAL_RENTA_COP` is the one actually meant for the
   personal renta-declarant threshold, `centinela_service.py`'s is for a B2B Régimen Simple rule.
   Do not conflate them.
5. **All existing tenant_id/TDD/Stage-11 lessons from Changes H/I carry over unchanged** — no new
   profile-creation code path is introduced here (reuses the existing `_create_empty_tax_profile`
   already fixed in Change I), so no new tenant_id risk.

## Risks / Trade-offs

- **[Risk] A naive regex could misparse an unrelated number as a topes amount** (e.g. a phone
  number or a date near a keyword) → **Mitigation**: require the peso-amount pattern to appear
  within the same message as the category keyword, not just anywhere in the conversation; keep the
  regex narrow (must include a currency-shaped suffix or be a clearly large bare number, e.g. 6+
  digits) rather than matching any digit sequence.
- **[Risk] Presenting `obligado_declarar` as if it were a determination could mislead a lead into
  under/over-preparing, or expose Contexia to being perceived as giving tax advice it's not
  licensed for** → **Mitigation**: this change only writes the field to `crm_tax_profiles` for
  internal/contadora use; it does not add or change any lead-facing message. Any future change that
  surfaces this to the lead directly must route through the human contadora review, per
  GROUND_TRUTH's Entidad B framing.
- **[Trade-off] Only `ingresos`/`consignaciones` are checked against a threshold** (not
  compras/patrimonio) — accepted for now since those thresholds aren't in this repo yet; documented
  as an Open Question rather than fabricating threshold values that could be legally wrong.

## Migration Plan

No migration — both target columns already exist live (confirmed via
`information_schema.columns`). Pure logic change to `taty_lead_router.py`. Stage 11 is a live
smoke test only (send a fabricated WhatsApp message mentioning consignaciones, confirm `topes` and
`obligado_declarar` populate correctly via Supabase SQL), same "no real WhatsApp number" accepted
limitation as Changes D/I.

## Open Questions

- Should Taty eventually ask proactive qualifying questions to fill `topes` faster, rather than
  waiting for the lead to volunteer amounts? Recommend **not now** — bundling this into the
  ReAct/KB rework (gaps #3/#4) makes more sense than adding ad-hoc proactive prompts to the
  current deterministic router twice.
- Should `compras`/`patrimonio` get their own UVT thresholds computed and added to
  `core/constants.py`? Recommend deferring until the founder confirms the exact DIAN 2026 UVT
  multipliers for those two categories — not guessing at legally-sensitive thresholds in this
  change.
