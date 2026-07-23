# Review — Stage 11 live-fix, commit 89c7774

**Verdict:** APPROVED

## Scope

Commit `89c7774` — `fix(pwa-tenant-aware-screens): unique React keys for ActiveAlerts`,
made directly by the leader during Stage 11 live E2E testing (not via the normal
implementer flow — flagged explicitly in `tasks.md` Stage 11.1 and reviewed here
per that flag).

## Checkpoints

- C1 (reasoning sound / genuine uniqueness within one render): [x] — `git show 89c7774`
  changes `id: alert.rule_id || \`alert-${index}\`` to
  `id: \`${alert.rule_id || "alert"}-${index}\`` (`ActiveAlerts.tsx:24`). Old logic only
  used `index` when `rule_id` was falsy (`""`/`null`/`undefined`); when `rule_id` was
  present but repeated across rows (confirmed live: 20 real `SHADOW_GL_DISCREPANCY`
  alerts all sharing one `rule_id`), every row got the identical key
  `"SHADOW_GL_DISCREPANCY"`, hence the observed React duplicate-key warning. The fix
  always appends `index`, and `index` is the array position from `.map((alert) => ...)`
  at `ActiveAlerts.tsx:79` (via `alerts.map(toActiveAlert)` upstream at line 51) — a
  single `Array.prototype.map` pass assigns each element a distinct position exactly
  once, so `${prefix}-${index}` is guaranteed unique within one render regardless of
  what `alert.rule_id` is, including the all-falsy case (`"alert-0"`, `"alert-1"`, ...
  never collide either). Reasoning holds.
- C2 (no regression vs. Stage 8-reviewed behavior): [x] — `git show --stat 89c7774`
  confirms 1 file, 5 insertions / 1 deletion, all inside `toActiveAlert`'s `id` field
  plus a 4-line comment. Diffed the rest of `ActiveAlerts.tsx` against the Stage 8
  version (`d8d6747`) mentally via the full current read: `toSeverity` (lines 13-15),
  `message` composition (line 27), loading skeleton (`AlertsSkeleton`, lines 31-39),
  empty/error → `null` (line 72), and the `useEffect`/`cancelled`-guard fetch flow
  (lines 45-66) are byte-for-byte what Stage 8's review (`progress/review_stage8.md`)
  approved — untouched by this commit. Surgical, single-concern change confirmed.
- C3 (typecheck): [x] — ran `cd contexia-app && npx tsc --noEmit` myself: exit code 0,
  clean.
- C4 (diff scope): [x] — `git show --stat 89c7774` output: only
  `contexia-app/components/pulso/ActiveAlerts.tsx` touched (6 lines changed). No
  encroachment on any other Stage 7-10 file.
- C5 (comparable risk elsewhere in this change's diff): [x], none found —
  - `MonthlyLiquidityBridgeCard.tsx` (Stage 9, read in full): renders a single
    `LiquidityBridgeSnapshot` object, not a list — no `.map()`, no React `key` prop
    anywhere in the component. Not exposed to this class of bug.
  - Backend `centinela_endpoints.py` (Stage 2, `GET /api/v1/centinela/alerts` /
    `get_my_alerts`, lines 236-303): `rule_id` is used only as a plain response field
    inside `CentinelaAlert` Pydantic models built via list comprehension
    (`alert_models = [CentinelaAlert(...) for a in raw_alerts]`, lines 276-287) — never
    as a dict/map key, dedup key, or any place where non-uniqueness could silently drop
    or overwrite a row server-side. `saved_alert_ids` (evaluate endpoint) comes from
    `centinela.save_alerts(alerts)`, a different code path unrelated to this change. No
    comparable bug surfaced on spot-check.

## Notes

- The commit message and inline comment both correctly identify the invariant
  (`rule_id` is a many-to-one rule→document label, not a row identity) rather than
  just patching the symptom, which is the right level of documentation for future
  readers who might be tempted to "clean up" the key expression back to `rule_id`
  alone.
- This is a legitimate live-testing catch, not scope creep — it was found and fixed
  within the same screen (`ActiveAlerts`) already in scope for Stage 8/11, and
  `tasks.md` Stage 11.1 documents it transparently rather than silently folding it in.

No required changes.
