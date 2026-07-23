# Sesión activa

> El líder escribe aquí el plan vivo de la sesión. Los subagentes NO escriben aquí
> su detalle — eso va a `progress/impl_<id>.md` y `progress/review_<id>.md`.
> Al cerrar sesión: mover el resumen a `history.md` y dejar esta plantilla limpia.

**Change OpenSpec activo:** ninguno — `adopt-gbrain-second-brain` completado y archivado
(2026-07-05, `openspec/changes/archive/2026-07-05-adopt-gbrain-second-brain/`, 60/60 tareas).

**Resumen de lo logrado:**
- GBrain (github.com/jpelaezcardenas/garrytan-gbrain) corriendo en WSL junto a Hermes
  (`gbrain-autopilot.service`, systemd), conectado a un esquema dedicado `gbrain` en el
  Supabase existente — aislado de `knowledge_chunks`/Centinela, verificado.
- Repo separado `contexia-brain` (github.com/jpelaezcardenas/contexia-brain) para todo el
  contenido del cerebro — nunca dentro de `antigravity-app`.
- Conectado a Claude Code (`.mcp.json`), Codex (`config.toml`) y Hermes (perfil `contexia`) —
  verificado en vivo vía `hermes mcp test gbrain` (41 tools).
- Catálogo de 12 agentes Contexia proyectado desde `AGENTES.md` a skills de GBrain
  (`scripts/generate_gbrain_skills.py`, regenerable).
- De paso: se resolvió `reconcile-railway-antigravity-projects` (archivado el mismo día) —
  reconcilió los dos proyectos Railway duplicados y cerró una brecha de seguridad real
  (JWT_SECRET vacío en producción).

**Estado:** ninguna tarea en curso. Esperando siguiente dirección del fundador.
**Bloqueos:** —

---

## Sesión activa (2026-07-22)

Task in progress: chatwoot-hermes-taty-bridge — Task Groups 5-10 (bridge scaffold + webhook
filtering/HITL + Chatwoot client + Hermes client + backend client + orchestration)

Plan:
- Scaffold `apps/chatwoot-bridge/` (config.py, schemas.py, main.py, clients, tests/)
- TDD `POST /webhook` full HITL truth table (Task Group 6)
- TDD `chatwoot_client.py` (history/reply/contact attrs, respx-mocked) (Task Group 7)
- TDD `hermes_client.py` (OpenAI-compatible chat completions, fail-soft) (Task Group 8)
- TDD `backend_client.py` (HS256 JWT matching Hermes-operator contract, fail-soft) (Task Group 9)
- TDD orchestration `process_incoming_message` + health check (Task Group 10)
- Full suite `pytest apps/chatwoot-bridge/tests -v` green, report written, hand off to reviewer

---

## Sesión activa (2026-07-23)

Task in progress: hermes-task-queue-tenant-scoping — Tasks 1-6 (branch
`feature/hermes-task-queue-tenant-scoping`)

Plan:
- `core/tenant_context.py`: additive `tenant_exists(client, tenant_id)` helper (TDD)
- `operator_task_service.py`: optional `tenant_id` on `create_task`/`list_pending_tasks`,
  write-time tenant validation, derive tenant from `decision.tenant_id` in
  `dispatch_campaign_package` (TDD)
- `sell_machine_endpoints.py`: optional `HERMES_BRIDGE_TOKEN` bearer-auth dependency on the 5
  operator-task routes, `agent_operations` audit parity on the 4 mutating routes (TDD)
- Review/fix pre-existing tests broken by the signature/behavior changes (Task 5)
- Run targeted + full suite, write Step 6 verification report (Task 6)

Status: Tasks 1-6 done, handed to reviewer. Report:
`progress/impl_hermes-task-queue-tenant-scoping-1-6.md`. Tasks 0, 7-11 (curl testing, docs,
deploy, review gate, archive) intentionally out of scope for this session.
