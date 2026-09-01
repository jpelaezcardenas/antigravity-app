# GTM-HANDOFF — Estado real del sistema · 2026-09-01

> **Uso:** este archivo es el punto de arranque del hilo "GTM". Léelo completo antes de
> proponer nada. No confíes en documentos de planeación sin verificar contra el repo real.

---

## §1 Resumen ejecutivo — Día 0 como objetivo

El sistema está operativo con 11 clientes activos. Dos motores comerciales corren en paralelo:

- **Campaña 1 — Renta Natural 2026 (B2C):** pipeline Manus completo (Content Critic → Approval Queue → poller → Manus publica), HubSpot live, Chatwoot/Taty por WhatsApp. **Bloqueante pendiente:** el poller de Manus nunca se ejecutó en modo real (`DRY_RUN=true` desde la última verificación — confirmar en el hilo nuevo si ya se activó).
- **Campaña 2 — Freemium B2B SaaS:** tier gating, provisioning desde el Búnker, invite link real, seed de saldo freemium, insight bridge de Hermes operativo. **Bloqueante pendiente:** nunca se lanzó comercialmente — faltaba el pricing. Ya está definido (ver §2 del plan original en el txt fuente).

### Lo ya cerrado — no repetir investigación

| Fecha | Qué se cerró | Evidencia |
|---|---|---|
| 2026-08-28/29 | Constraint `operator_tasks.task_type` (bloqueaba insight bridge de Pulso Diario) | Archivado: `openspec/changes/archive/2026-08-28-operator-tasks-pulso-insight-constraint-fix` |
| 2026-08-29 | `HERMES_BRIDGE_TOKEN` confirmado seteado en Railway prod | Verificado en vivo |
| 2026-08-29 | Manus redirigido fuera de n8n (violaba AGENTES.md Regla 4); 0 JWT service_role inline confirmado | Reporte de Manus verificado |
| 2026-08-29/30 | Positioning "contadoras tituladas + tecnología"; brand_rubric.py/content_evaluator.py/copywriter_service.py actualizados; bug fail-open de Content Critic → fail-closed | Archivado: `2026-08-30-brand-rubric-niche-positioning-failclosed-fix`, 41/41 tests |
| 2026-08-29 | Fixture freemium reusable creado (tenant `9a28eac7-...`, "Demo Envigado — Cliente Freemium") con saldo sembrado + login vía Edge Function | Verificado en Supabase |
| 2026-08-30 | Gate HITL de Wompi implementado | Archivado: `taty-wompi-link-hitl-gate` |
| 2026-08-30/31 | Endpoints internos multi-tenant para Hermes (`/internal/*`) | Archivado: `hermes-multi-tenant-endpoints` |
| 2026-08-30/31 | OmniRoute evaluado y cerrado como NO-GO para el backend (violaciones ToS de proveedores detrás) | Archivado: `evaluate-omniroute-backend-integration`; ARCHITECTURE.md Decisión #21 |
| 2026-08-31/2026-09-01 | Dashboard de métricas Fase 9 completo, cron nocturno corriendo, verificado E2E en 11 tenants | Change `metrics-dashboard-phase9` — completo, solo falta archivar formalmente |

---

## §2 Corrección crítica de fuente de verdad

**NO confiar en `contexia-mcp-servers/HANDOFF-RADAR-SHADOW-GL.md` para el estado de Shadow GL/Radar.** Ese documento (25-ago-2026) afirma que Shadow GL está "0% implementado" y que las clases `RadarRiskTool`/`ShadowGLIngestTool` "no existen en ningún lado" — esto es parcialmente falso y estaba desactualizado el día en que se escribió.

**La verdad verificada contra el repo real:**
- Shadow GL está en producción desde julio 2026 (migraciones, servicios, tests, flag `is_verified_real`)
- `RadarRiskTool`/`ShadowGLIngestTool` — esto sí es cierto: esas clases MCP **fueron borradas**, no están desactivadas. Si se quiere exponer Shadow GL/Radar vía MCP para Hermes, es trabajo nuevo, no una "reactivación"

---

## §3 Estado real de Shadow GL (verificado contra repo)

### Migraciones aplicadas (en producción)

| Migración | Qué hace |
|---|---|
| `0016` | Crea `erp_journal_entries`, `erp_journal_lines` |
| `0019` | Crea `dian_xml_documents` |
| `0028` | Índices y RLS para Shadow GL |
| `0035` | Ajustes de schema |
| `0042_shadow_gl_is_verified_real.sql` | Agrega `is_verified_real BOOLEAN NOT NULL DEFAULT false` a ambas tablas de journal |

El repo va actualmente en migración `0045`.

### Servicios en producción

| Archivo | Función |
|---|---|
| `apps/backend/services/shadow_gl_service.py` | `parse_siigo_csv()` (línea 127), `ingest_siigo_csv()` (línea 408), `ingest_dian_xml()` |
| `apps/backend/services/shadow_gl_seed_service.py` | Datos sintéticos para demos/fixtures |
| `apps/backend/presentation/shadow_gl_endpoints.py` | Endpoints HTTP de ingesta; `?is_verified_real=true` para marcar dato real |
| `apps/backend/services/radar_service.py` | Scoring determinista 0-100 por reglas (discrepancia 40pts, monto 30pts, frecuencia 20pts, días vencido 10pts) — no es un modelo predictivo |

### Ingesta hoy = 100% manual

`parse_siigo_csv()` procesa texto CSV que Taty exporta y sube manualmente por NIT. Cero código de API REST de Siigo en ningún lado del backend (búsqueda confirmada: cero hits para `SiigoApiClient`, `api.siigo.com`).

### Flag `is_verified_real`

- `false` = dato sintético (seed/demo, fixture freemium)
- `true` = dato real cargado por un cliente o por un job verificado
- Controla qué datos se muestran en producción vs. demos

### OpenSpec relacionado (archivado)

`openspec/changes/archive/2026-08-13-shadow-gl-real-data-ingestion/` — dejó Siigo API live sync **explícitamente fuera de alcance**: "deferred pending commercial negotiation + SyncManager". Esta decisión se revierte parcialmente en la tarea descrita en §4.

---

## §4 La tarea Siigo a implementar (ver handoff detallado)

La implementación completa de Siigo API live sync está documentada en:

**`GTM-HANDOFF-siigo-api-sync.md`** (mismo directorio que este archivo)

**Resumen de lo que hay que hacer:**
- Construir `SiigoApiClient` que autentica contra `api.siigo.com` y mapea respuestas al shape de `parse_siigo_csv()`
- Job programado nocturno
- Marcar filas ingeridas con `is_verified_real=true`
- Requiere un OpenSpec change propio antes de tocar código

**Primer paso antes de abrir el change:** confirmar con Siigo si una cuenta = todos los NITs de Taty, o si cada NIT necesita sus propias credenciales.

---

## §5 Cabos sueltos priorizados

| # | Cabo suelto | Prioridad | Dueño |
|---|---|---|---|
| 1 | **`SUPABASE_SERVICE_ROLE_KEY` sin rotar** — confirmado por el informe del Hub (v4, 29-ago): "vencida, prioridad alta". Es parte de un problema más amplio: credenciales de la auditoría de junio siguen sin rotar en su totalidad | 🔴 ALTA | Fundador (acción de seguridad) |
| 2 | Tres PRs de seguridad de junio sin fusionar a producción | 🔴 ALTA | Fundador (revisar + merge) |
| 3 | Política RLS permisiva — acceso anónimo residual sobre la cola de aprobación (`approval_queue_anon_all`) | 🟡 MEDIA | Implementer + PR |
| 4 | Gating fino Growth/Enterprise vs Starter en `plan_features.py` — hoy idénticas | 🟡 MEDIA | Implementer |
| 5 | Migración de re-etiquetado de ~40 alertas históricas de Centinela mal asociadas (`0034_rescope_centinela_alerts_tenant.sql`) — escrita, **no aplicada**, requiere aprobación explícita | 🟡 MEDIA | Fundador (aprueba) + aplicar |
| 6 | Backend secundario Railway (`enthusiastic-youthfulness`/`-dc78`) sin tráfico real — pendiente decomisionar | 🟢 BAJA | Fundador (decision) |
| 7 | Decisión estructural: cobro de servicios contables debe salir de Entidad A (firma regulada), no de Entidad B (Contexia tech) | 🟢 BAJA | Fundador (legal) |
| 8 | Ciclo E2E de Campaña 1 — confirmar si el poller de Manus ya se activó en modo real (`DRY_RUN=false`) o sigue en dry-run | 🔴 ALTA | Fundador (acción operativa) |
| 9 | Un checkbox sin commitear en `metrics-dashboard-phase9/tasks.md` (verificación visual ya hecha, falta commit + archivar el change) | 🟢 BAJA | Cualquier agente |

---

## §6 Restricciones heredadas (no negociables)

- **Nous Never Approves:** cualquier write-back hacia sistemas externos requiere Approval Queue humano
- **Secretos:** API keys, tokens y contraseñas van a Bitwarden/Railway env vars, **nunca a git ni a archivos del repo**
- **Stage 11 obligatorio:** ningún change OpenSpec se archiva sin deploy verificado en Railway/Vercel (CLAUDE.md §8)
- **No volver a n8n legacy:** Manus no usa n8n de Contexia (AGENTES.md Regla 4, verificado y corregido 2026-08-29)
- **Un change activo a la vez:** el repo tiene la regla de una sola carpeta activa en `openspec/changes/active/`
- **ARCHITECTURE.md vivo:** cualquier cambio de contenedor o dependencia externa se actualiza en ARCHITECTURE.md en el mismo change

---

## §7 Primer paso recomendado para este hilo

**Dos opciones — elegir una:**

**Opción A (seguridad primero, bloqueante):** rotar `SUPABASE_SERVICE_ROLE_KEY` + revisar/merge los 3 PRs de seguridad de junio. Sin esto, escalar el número de clientes reales aumenta la superficie expuesta.

**Opción B (producto primero):** confirmar con Siigo el modelo de cuentas → abrir OpenSpec proposal `siigo-api-live-sync` → implementar `SiigoApiClient`. Desbloquea datos reales para los primeros clientes.

El informe del Hub clasifica la rotación de secretos como "prioridad alta" — si hay tiempo, hacer A antes de B.

---

## §8 Referencias

| Recurso | Ruta / URL |
|---|---|
| Estado de Shadow GL (detallado) | `GTM-HANDOFF-siigo-api-sync.md` (este mismo directorio) |
| Change que dejó Siigo API fuera de alcance | `openspec/changes/archive/2026-08-13-shadow-gl-real-data-ingestion/proposal.md` |
| Spec del flag `is_verified_real` | `openspec/specs/shadow-gl-data-integrity/spec.md` |
| Spec del CSV parser actual | `openspec/specs/shadow-gl-siigo-csv-ingestion/spec.md` |
| Decisión #21 OmniRoute NO-GO | `ARCHITECTURE.md` línea ~181 |
| Decisión #20 Houston read-only | `ARCHITECTURE.md` — Houston no genera outreach por el Sell Machine |
| Handoff previo desactualizado (NO usar para Shadow GL/Radar) | `contexia-mcp-servers/HANDOFF-RADAR-SHADOW-GL.md` |
| Informe técnico Hub (snapshot de negocio 29-ago) | Compartido por el fundador fuera del repo |
| Canon del repo | `ARCHITECTURE.md`, `HARNESS.md`, `AGENTES.md`, `.antigravity/GROUND_TRUTH.md` |
| Concepto "Hermes personal / SO agéntico" | `../contexia-brain/concepts/hermes-personal-agentic-os.md` |
| OpenSpec proposal Hermes Jarvis | `openspec/changes/active/hermes-jarvis-contexia/proposal.md` |
