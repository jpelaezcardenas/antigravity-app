# Bitácora (append-only)

> Una entrada por sesión cerrada. El líder añade al final; nunca se reescribe lo anterior.
> Esto reemplaza el hábito de volcar reportes sueltos a la raíz del repo.

---

## 2026-06-30 — Bootstrap del harness + canon vivo

- Creados: `ARCHITECTURE.md` (producto) + `../ARCHITECTURE.md` (workspace) + `HARNESS.md`.
- Harness: `.claude/agents/{leader,implementer,reviewer}.md`, `progress/`, `feature_list.json`, `init.sh`, hooks.
- Cableado: `CLAUDE.md` (imports + mapa + carve-out English-only), `openspec/config.yaml`, `CHECKPOINTS.md`.
- Limpieza: archivados los `.md` de sesión/fase de la raíz → `docs/archive/`.
- Patrón de referencia: `jpelaezcardenas/ejemplo-harness-subagentes`.

---

## 2026-07-01 — Restauración PWA + wiring Caja Real + arranque MVP Cliente Cero + limpieza OpenSpec

**PWA / producción:**
- Restaurada la PWA completa del cliente (commit `b6fcb81`) tras la degradación Haiku (`4433c5b`).
- Caja Real en vivo cableada vía `<script>` en `app/overview.html` (`f91d9da`); logout mojibake real corregido (`8559ca1`). Verificado live: $3.520.000 desde `GET /api/v1/financials`.
- Canon: documentada la EXCEPCIÓN "hand-edit en app/" en CLAUDE.md §9 + ARCHITECTURE.md (`cd5c095`) para que una sesión nueva NO regenere `app/` y borre la Caja Real.

**Arranque MVP Cliente Cero:**
- Creado el change OpenSpec activo `reconcile-contexia-app-source-live-pwa` (proposal/design/specs/tasks válidos, `d95ce65`). Puntero del harness cableado (`feature_list.json.active` + `progress/current.md`); `init.sh` EXIT=0.

**Limpieza `openspec/changes/` (reconciliación):**
- Archivados (completos/superseded): `wire-contexia-agents-to-hermes-workspace` (168/0, sincronizó spec `mcp-agents-invocation`), `shadow-gl-hitl-workflows` (69/0), `hermes-profile-based-llm-routing` (Stage 1 GLM 5.2 shipped, Stage 2 superseded), `hermes-user-sync-and-onboarding` (closed-for-scope), `wire-pulso-overview-live-shadow-gl` (capabilities live; sincronizó specs `pulso-financials-api` + `pulso-overview-live-data`; corregida la contradicción del reporte que citaba el commit revertido `4433c5b`).
- Dejados EN ACTIVO a propósito (con nota de reconciliación donde aplica): `reconcile-contexia-app-source-live-pwa` (activo), `keeper-migration-2026-06-15` (hold intencional hasta 2026-07-04), `hermes-multi-tenant-wrapper` (in-progress, ventana hasta Jul 25; checkboxes drift), `automated-approval-rules` (deployed; falta cerrar checklist DoD), `shadow-gl-real-data-ingestion` (0/101, pending redeploy — requiere verificación), `metrics-dashboard-phase9` (0/108, propuesta sin empezar).
- Pendiente menor (no bloquea): `openspec/MVP_COMPLETE.md` afirma "MVP COMPLETE 2026-06-26" — cubre ingesta Shadow GL, no el PWA de datos en vivo; conviene aclarar la redacción en una vuelta futura.

---

## 2026-07-01 — Prueba en vivo del harness (leader→implementer→reviewer)

- **Feature 1** `harness_selftest_cents_to_cop`: **done** (aprobada por reviewer, `progress/review_1.md`).
- Confirmado: los subagentes personalizados (`.claude/agents/*.md`) se registran al ARRANCAR Claude Code, no a mitad de sesión — esta sesión de chat predata su creación, así que `subagent_type: "implementer"/"reviewer"` no resolvió. Se usó `general-purpose` con el protocolo exacto de cada rol como *workaround* documentado; el mecanismo de archivos (progress/, feature_list.json, TDD, gate) funcionó end-to-end igual.
- Implementer: TDD real (rojo→verde con output verbatim), confinado a `harness_selftest/`, no se autoaprobó.
- Reviewer: re-verificación **independiente** (no confió en el reporte del implementer, re-corrió los tests él mismo), detectó y correctamente descartó un diff no relacionado en `app/overview.html` como ruido preexistente de otra sesión.
- `init.sh` verde tras el cierre.
- `harness_selftest/` es desechable (demo de bootstrap) — pendiente decisión del usuario: conservar como ejemplo vivo o `git rm`.
