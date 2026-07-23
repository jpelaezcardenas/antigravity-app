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

---

## 2026-07-23 — hermes-task-queue-tenant-scoping (completo, Tasks 0-11, archivado)

Change OpenSpec `hermes-task-queue-tenant-scoping` — la cola `operator_tasks` que puentea el
backend con Hermes (local, siempre-hace-poll, Decisión #1) era ciega al tenant; se corrigió de
punta a punta:

- `create_task()`/`dispatch_campaign_package()` aceptan/derivan un `tenant_id` real (validado
  contra `tenants`), cayendo a Cliente Cero solo de forma explícita y con `logger.warning` — nunca
  un default mudo.
- `list_pending_tasks()` incluye `tenant_id` de forma contractual (proyección explícita de
  columnas, no un accidente de `select("*")`), más un filtro opcional por tenant.
- Governance del puente HTTP (5 rutas sin auth previa, riesgo aceptado documentado en
  `hermes-manus-execution-bridge` design.md R1): se evaluó y **rechazó** reutilizar
  `AgentAccessControl` completo (su check de membresía usuario↔tenant es vacuo para una máquina
  que sirve a TODOS los tenants); en su lugar: `HERMES_BRIDGE_TOKEN` env-gated (fail-open hasta que
  el fundador lo active — activación es tarea suya, no de este cambio), paridad de auditoría vía
  `agent_operations` (`agent_name="hermes-bridge"`), validación de tenant en escritura.
- `core/tenant_context.py` recibió solo una adición (`tenant_exists`) — coordinado sin tocar
  `resolve_cliente_cero_tenant_id`, propiedad del cambio activo concurrente
  `hermes-multi-tenant-wrapper` (commit `a07bb93`, Ground Truth Correction #3).
- Reviewer independiente: APROBADO — 47/47 tests dirigidos, suite completa sin regresiones (628
  pasan / 40 fallas pre-existentes idénticas antes/después). `RUN_TESTS=1 bash init.sh` no salió
  genuinely green por ~40 fallas pre-existentes no relacionadas + un bug de subprocesos pytest
  anidados en `test_shadow_gl_stage8_e2e.py` (ninguno de los dos introducido por este cambio) —
  documentado honestamente en vez de forzar el checkbox; se añadió una regla al self-improving
  loop de `CHECKPOINTS.md`.
- Stage 11: merge a `main` (`f944918..7b26638`), deploy Railway `production-175a` SUCCESS
  (`2c33acc2`), verificación en vivo con curl (200/404/tenant_id presente) + confirmación de la
  fila de auditoría vía Supabase MCP, estado de BD restaurado (sin endpoint DELETE en el puente —
  limpieza manual vía SQL).
- Specs sincronizadas en `openspec/specs/hermes-manus-execution-bridge/spec.md`; archivado en
  `openspec/changes/archive/2026-07-23-hermes-task-queue-tenant-scoping/`.
- **Pendiente del fundador (no bloquea el cierre):** activar `HERMES_BRIDGE_TOKEN` — actualizar
  primero el poller de Hermes (repo separado `hermes-workspace`) y su `.env` local con el header
  `Authorization: Bearer`, y solo después setear la env var en Railway (el orden inverso tumbaría
  el poller en vivo).
- Efecto secundario: se descubrieron y reportaron como tareas separadas (fuera de alcance) (1) el
  bug de subprocesos runaway en `test_shadow_gl_stage8_e2e.py`, y (2) que `DEPLOYMENT_STAGE/` no es
  en realidad un symlink a `ai-specs/openspec-deployment-standard/` como afirma `CLAUDE.md` §6/§8
  — ese directorio nunca existió en el repo.

**Estado:** ninguna tarea en curso. `feature_list.json.active = null`.

---

## taty-per-tenant-profiles — task 1 (2026-07-23)
Service profile resolver: DEFAULT_PROFILE + `_get_tenant_profile(tenant_id)` in taty_service.py,
replacing hardcoded AGENT_PROFILES. `_error_response` extended with optional `error_code`.
7 new tests green (test_taty_tenant_profiles.py). Reviewer: APPROVED.
Deviation: `_get_agent_profile` kept as transitional delegator — task 2 removes it when `ask()`
is rewired to take `tenant_id` directly.
## taty-per-tenant-profiles — task 2 (2026-07-23)
ask(company_id) -> ask(tenant_id) hard rename; _get_agent_profile deleted; _retrieve_chunks keys
off profile["kb_client_id"]; _build_prompt omits régimen clause when None (GROUND_TRUTH
compliance). 6 new tests green (test_taty_ask_tenant_scoping.py), task 1's 7 still green.
3 live callers now broken by design (fixed in tasks 3/4/5, same change). Reviewer: APPROVED.
Reviewer flagged unrelated pre-existing full-suite issue in test_shadow_gl_stage8_e2e.py for task 7.

## taty-per-tenant-profiles — task 3 (2026-07-23)
Closed the /api/v1/agents/ask auth hole: Depends(get_current_user) + canonical 3-way tenant
resolution (own tenant / staging->Cliente Cero / unresolved->in-band tenant_not_resolved error,
never Cliente Cero) on taty_endpoints.py. company_id in request body now fully ignored for
resolution (was previously used, unverified, to read any profile). GET delegates to POST's
single resolution path. 5 new tests, 18/18 green with tasks 1-2. Reviewer ran an adversarial
bypass trace by hand (missing/malformed auth, staging+spoofed body, resolved+spoofed body,
authenticated-unresolved) — no leak path found. APPROVED.

## taty-per-tenant-profiles — task 4 (2026-07-23)
Fixed the Telegram webhook's broken ask(company_id=...) call (task 2's regression). New
_resolve_tenant_for_company_id(company_id) translates telegram_chat_mappings.company_id ->
tenants.id before calling taty.ask(tenant_id=...); untranslatable id sends the existing "no
configurado" reply and never calls ask(). Social Ops onboarding branch (same mapping table)
untouched. 5 new tests, 23/23 green with tasks 1-3. Reviewer: APPROVED.

## taty-per-tenant-profiles — task 5 (2026-07-23)
Retirements: deleted deprecated POST /api/v1/agents/taty/ask route (AskRequest model kept,
shared with unrelated social_generate_content route); deleted taty_intent_router.py + its test
(dead code, zero live callers, per design D4). Grep-clean, 89/89 agents/taty tests pass,
23/23 tenant-scoping regression suite green. Reviewer: APPROVED. Flagged stale comment in
router.py for task 10.

## taty-per-tenant-profiles — task 6 (2026-07-23)
Mandatory existing-test audit: negative result, zero pre-existing tests affected by tasks 1-5's
ask() rename / AGENT_PROFILES deletion / taty_intent_router deletion. Reviewer independently
re-ran every grep + classification, confirmed genuine. Found 2 pre-existing unrelated
TestClient/httpx-starlette incompatibility failures (test_centinela_alerts_get.py,
test_secure_llm.py) for task 7 awareness.
