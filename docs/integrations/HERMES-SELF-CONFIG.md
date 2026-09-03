# Hermes Self-Configuration — Instrucción Maestra para Contexia

**Versión:** 2026-08-30  
**Estado:** REFERENCIA OFICIAL — cargar al inicio de cada sesión de configuración de Hermes  
**Propósito:** Llevar a Hermes a estado SOTA para Contexia — todos los sistemas activos, autenticados y documentados.

---

## 1. Contexto: qué es Hermes en Contexia

Hermes es el **orquestador local de agentes** de Contexia. Corre en WSL/Ubuntu (`localhost:8642` gateway, `localhost:9119` dashboard) con Hermes Desktop v0.21.0 como GUI nativa de Windows. Es la única pieza que corre local por soberanía de datos — nunca sube a Railway/Vercel/cloud.

**Stack confirmado en vivo (2026-08-29):**
- Gateway: `localhost:8642` → UP, responde 200
- Desktop: Hermes Desktop v0.21.0 (native Windows app, replaced Workspace SPA)
- Dashboard: `localhost:9119` → UP, responde 200
- OmniRoute: `localhost:20128` → UP via systemd `omniroute.service`
- GBrain: `localhost:gbrain-autopilot.service` → UP, indexa `contexia-brain/`
- Chatwoot bridge: `localhost:8090` → UP (PID 25924, watchdog cada 1 min)
- HubSpot poller: scheduled task cada 5 min → 13 días sin interrupción

**Modelos:**
- Primary: `mimo-v2.5-pro` (externo, `token-plan-sgp.xiaomimimo.com`)
- Fallback: OmniRoute (`localhost:20128/v1`, MIT, ~58k estrellas GitHub)
- Modelo local disponible: Ollama (no usado como fallback — si OmniRoute cae, la solicitud falla)

---

## 2. Verificación inicial (ejecutar antes de cualquier configuración)

```bash
# Gateway Hermes
curl -s http://localhost:8642/health

# OmniRoute
curl -s http://localhost:20128/health

# GBrain
systemctl --user status gbrain-autopilot.service

# Chatwoot bridge (Windows → WSL no alcanza, verificar desde Windows)
# Scheduled Task: ContexiaChatwootBridge debe estar Ready

# OmniRoute systemd service
systemctl --user status omniroute.service
```

---

## 3. Deuda técnica activa — resolver en orden

### 3.1 HERMES_BRIDGE_TOKEN (BLOQUEANTE — resolver PRIMERO)

**Problema:** El backend de Railway (`antigravity-app-production-175a`) requiere `Authorization: Bearer <token>` en las 5 rutas de tareas de Hermes. El token NO existe en Railway hoy — `HERMES_BRIDGE_TOKEN` no aparece en las variables del servicio.

**Efecto:** Los scripts de cron de Pulso Diario fallan con error `401 Unauthorized` o `Method Not Allowed` al llamar al backend.

**Pasos para resolverlo:**

```bash
# 1. Generar un token seguro (128 bits)
python3 -c "import secrets; print(secrets.token_hex(32))"

# 2. Guardar en Railway via CLI (necesita login previo)
railway login
railway variables set HERMES_BRIDGE_TOKEN=<token-generado> --service antigravity-app

# 3. Guardar en el .env local de Hermes
echo "HERMES_BRIDGE_TOKEN=<token-generado>" >> ~/.hermes/.env.local

# 4. Actualizar los scripts de cron en ~/.hermes/scripts/
# Agregar el header a los curl calls:
# curl -H "Authorization: Bearer $HERMES_BRIDGE_TOKEN" ...

# 5. Verificar que Railway auto-redeploy corrió (puede tomar ~80s)
# Test: curl -s -o /dev/null -w "%{http_code}" https://antigravity-app-production-175a.up.railway.app/api/v1/tasks/pending
# Esperado sin token: 401
# Esperado con token: 200 o 204
```

**IMPORTANTE:** El valor del token NO va en ningún archivo del repo (`antigravity-app`). Solo en Railway env vars + Bitwarden vault + `.hermes/.env.local` (local, no versionado).

---

### 3.2 Railway CLI Login (prerrequisito de 3.1)

Railway CLI ya está instalado (`v5.45.10`). Falta el login:

```bash
# En WSL, ejecutar:
railway login
# Abrirá browser → autenticar con cuenta Railway de Contexia
# Una vez logueado, persistir en:
railway variables list --service antigravity-app  # verificar acceso
```

---

### 3.3 Bitwarden CLI (BAJA PRIORIDAD — no bloquea operación diaria)

Bitwarden CLI (`bw`) no está instalado en WSL. Sin él, los secrets no se resuelven automáticamente desde el vault de Bitwarden.

```bash
# Instalar en WSL
npm install -g @bitwarden/cli

# Login
bw login jpelaezcardenas@gmail.com

# Obtener BWS_ACCESS_TOKEN desde Railway o vault de Bitwarden
# Agregar a ~/.hermes/.env.local:
echo "BWS_ACCESS_TOKEN=<token>" >> ~/.hermes/.env.local
```

---

### 3.4 Repo antigravity-app (REQUIERE APROBACIÓN §12)

El clon WSL en `~/antigravity-app` (o el path equivalente) tiene 946 archivos modificados sin commit/push. **Regla §12 de HARNESS.md:** Hermes NUNCA commitea/pushea a `antigravity-app` sin aprobación explícita del fundador.

**Acción pendiente para Claude Code (no para Hermes):**
1. Verificar el contenido de esas modificaciones
2. Decidir qué commitear, qué descartar
3. Ejecutar push

---

## 4. Jobs del Workspace — arreglar todos los 8

Los 8 jobs están rojos/overdue desde julio 2026. Causas identificadas:
1. `delivery: origin` — no funciona con API server (solo con Workspace UI)
2. Endpoints del backend cambiaron (ahora requieren auth)
3. `company_id` hardcodeado y posiblemente stale

### 4.1 Decisiones de diseño adoptadas

| Decisión | Valor |
|---|---|
| **delivery** | `bot-chat` (para briefings) / `local` (para tareas nocturnas) |
| **company_id** | Multi-tenant — iterar sobre tenants activos, no hardcodear un UUID |
| **auth** | Bearer token via `HERMES_BRIDGE_TOKEN` env var |
| **skill vs script** | Scripts para jobs operativos (deterministas, 0 costo LLM) / Skills para jobs de razonamiento (`maestro`, `morning-brief`) |

### 4.2 Template de script corregido

```bash
#!/usr/bin/env bash
# Template: job de Pulso Diario para todos los tenants activos

set -euo pipefail

BACKEND="https://antigravity-app-production-175a.up.railway.app"
TOKEN="${HERMES_BRIDGE_TOKEN:-}"

if [ -z "$TOKEN" ]; then
  echo "ERROR: HERMES_BRIDGE_TOKEN no está seteado" >&2
  exit 1
fi

# Obtener tenants activos (devuelve lista de tenant_ids)
TENANTS=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "$BACKEND/api/v1/tenants/active" | python3 -c "
import sys, json
tenants = json.load(sys.stdin)
for t in tenants:
    print(t['tenant_id'])
")

for TENANT_ID in $TENANTS; do
  echo "Procesando tenant: $TENANT_ID"
  curl -s -H "Authorization: Bearer $TOKEN" \
       -H "X-Tenant-ID: $TENANT_ID" \
       "$BACKEND/api/v1/pulso-diario/run" || echo "WARN: falló para $TENANT_ID"
done

echo "Pulso Diario completado: $(date)"
```

### 4.3 Matriz de jobs: estado deseado

| Job | Delivery | Tipo | Skill | Horario |
|---|---|---|---|---|
| `radar-predictivo-6am` | `bot-chat` (Taty/Chatwoot) | Script | `contexia-radar-predictivo` | `0 6 * * 1-5` |
| `morning-brief` | `bot-chat` (Taty/Chatwoot) | Skill | `contexia-morning-brief` | `0 8 * * *` |
| `pulso-diario-9am` | `bot-chat` (Taty/Chatwoot) | Script | `contexia-pulso-diario` | `0 9 * * 1-5` |
| `maestro-orchestration-10am` | `bot-chat` (Taty/Chatwoot) | Skill | `contexia-orchestration` | `0 10 * * 1-5` |
| `centinela-compliance-monitor-noon` | `bot-chat` (Taty/Chatwoot) | Script | `contexia-centinela-fiscal` | `0 12 * * 1-5` |
| `social-ops-briefing-8am` | `bot-chat` (Taty/Chatwoot) | Script | `contexia-social-ops` | `0 8 * * 1-5` |
| `auditoria-sombra-noche-2am` | `local` | Script | `contexia-shadow-gl` | `0 2 * * *` |
| `contexia-hola-mundo-test` | `bot-chat` | Skill | `contexia-hola-mundo` | `0 8 * * *` |

### 4.4 Endpoint correcto para cada job

Verificar contra el backend real antes de actualizar los jobs:

```bash
# Verificar qué endpoints existen (requiere auth)
curl -s -H "Authorization: Bearer $HERMES_BRIDGE_TOKEN" \
  https://antigravity-app-production-175a.up.railway.app/api/v1/ | python3 -m json.tool

# Endpoints confirmados activos:
# GET  /api/v1/financials           → Caja Real (requiere JWT de usuario, no bearer)
# GET  /api/v1/centinela/alerts     → Alertas Centinela (requiere JWT)
# GET  /api/v1/tasks/pending        → Cola Hermes (requiere HERMES_BRIDGE_TOKEN)
# POST /api/v1/tasks/               → Crear tarea (requiere HERMES_BRIDGE_TOKEN)
# GET  /api/v1/approval-queue/      → Cola de aprobación (requiere JWT)
# POST /api/v1/pulso-diario/latest  → Insight Bridge (requiere JWT)
```

---

## 5. OmniRoute — estado SOTA

### 5.1 Estado actual (confirmado 2026-08-29)
- ✅ Corre via systemd `omniroute.service` (no se apaga al reiniciar WSL)
- ✅ 7 combos configurados y activos
- ✅ 5 API keys por servicio (Hermes, backend, n8n, Claude Code, admin)
- ⚠️ API key auth: bug de encriptación CLI/server (local-only, riesgo bajo, documentado)

### 5.2 Combos canónicos de Contexia

| Combo | Uso | Fallback chain |
|---|---|---|
| `contexia-fast-free` | Clasificación, FAQ, borradores | `mimo-v2.5 → deepseek-v4 → big-pickle` |
| `contexia-docs-free` | Extracción, JSON, documentos | `deepseek-v4 → mimo-v2.5 → hy3 → big-pickle` |
| `contexia-tools-free` | Tool calling, multi-step | `mimo-v2.5 → nemotron-3 → deepseek-v4` |
| `contexia-dev-free` | Código, pruebas, docs | `deepseek-v4 → mimo-v2.5 → north-mini-code` |
| `contexia-private-local` | Datos confidenciales | `mimo-v2.5 (local primero)` |
| `contexia-critical-review` | Revisión supervisada | `deepseek-v4 → mimo-v2.5` |

### 5.3 Política de datos (NUNCA violar)

| Clasificación | ¿Routing libre? | Política |
|---|---|---|
| PÚBLICO | ✅ Sí | Cualquier combo free |
| INTERNO | ✅ Con validación | Combo free |
| CONFIDENCIAL | ⚠️ Solo anonimizado | `contexia-private-local` |
| RESTRINGIDO | ❌ NO | Modelo local + aprobación humana |

---

## 6. Integración Hermes ↔ Claude Code (el gap que cerrar)

### 6.1 Estado actual de la integración

```
Claude Code Desktop ──MCP──► OmniRoute (localhost:20128)
                                  │
Claude Code Desktop ──MCP──► GBrain (contexia-brain/)
                                  │
Hermes Desktop ──────────► GBrain (lectura/escritura)
Hermes Desktop ──────────► Chatwoot bridge (bot-chat delivery)
Hermes Desktop ──────────► Railway (via CLI instalado)
```

**Gap confirmado:** No existe un canal directo bidireccional Hermes ↔ Claude Code. La coordinación hoy es:
- Hermes escribe en GBrain → Claude Code lee GBrain
- Claude Code escribe en GBrain → Hermes lee GBrain
- Canal de coordinación manual: `COORDINATION-LOG.md` en WSL

### 6.2 Puente MCP confirmado operativo

4 tools MCP de Hermes → Claude Code (`contexia_agents/server.py`):
- `pulso_status` → `GET /api/v1/pulso/{usuario_id}`
- `centinela_alerts` → `GET /api/v1/centinela/alerts`
- `auditoria_report` → `GET /api/v1/auditoria/...`
- `approval_queue_list` → `GET /api/v1/approval-queue/`

Todos apuntan al backend canónico `-175a`. ✅ Verificado sin errores de import.

### 6.3 Reglas de coordinación (no negociables)

1. **Hermes NUNCA commitea/pushea a `antigravity-app`** sin aprobación explícita del fundador (§12 de HARNESS.md).
2. **Hermes NUNCA auto-aprueba** acciones financieras, pauta o declaraciones (Regla "Nous Never Approves" del GROUND_TRUTH.md).
3. **Claude Code es el coordinador principal del repo**. Hermes orquesta tareas locales y conversaciones.
4. **GBrain es el canal de memoria compartida** entre ambos agentes. Actualizar GBrain después de cualquier decisión importante.

---

## 7. Personalities de Hermes — catálogo Contexia

7 personalities configuradas en `~/.hermes/config.yaml` (verificadas 2026-08-29):

| Personality ID | Propósito | Modelo |
|---|---|---|
| `taty-v1` | Sales router + Asistente Fiscal WhatsApp | mimo-v2.5 + OmniRoute fallback |
| `centinela-v1` | Auditoría fiscal ex-ante | mimo-v2.5 |
| `pulso-v1` | Análisis financiero diario | mimo-v2.5 |
| `radar-v1` | Predicción de riesgos tributarios | mimo-v2.5 |
| `auditoria-v1` | Auditoría Sombra (Shadow GL) | mimo-v2.5 |
| `kb-v1` | Knowledge Base / normograma DIAN | mimo-v2.5 |
| `social-ops-v1` | Operaciones de contenido y marketing | mimo-v2.5 |

---

## 8. Skills de Hermes — catálogo Contexia (21 activos)

Verificados en `~/.hermes/skills/` (2026-08-29):

**En `contexia/` (10 skills):**
- `contexia-hola-mundo`, `contexia-orchestration`, `contexia-morning-brief`
- `contexia-approval-queue`, `contexia-audit`, `contexia-kb`
- `contexia-llm-failover` (extra, no estaba en handoff original)
- `contexia-omniroute` (gestión de OmniRoute)
- `contexia-pulso-diario`, `contexia-shadow-gl` ← NUEVOS 2026-08-29

**En raíz (11 skills):**
- `contexia-centinela-fiscal`, `contexia-renta-natural` ← NUEVOS 2026-08-29
- `contexia-social-ops`, `contexia-radar-predictivo`
- Y 7 más de uso general

---

## 9. MCP Servers activos (9 configurados)

| Server | Propósito |
|---|---|
| `gbrain` | Segundo cerebro — memoria persistente |
| `context7` | Contexto de código / docs |
| `supabase` | Acceso directo a DB (staging/admin) |
| `vercel` | Deploy y logs de Vercel |
| `railway` | Variables, deployments, logs (requiere login) |
| `calendly` | Agendamiento |
| `cloudflare` | Túnel cloudflared |
| `gamma` | Generación de presentaciones |
| `prisma-postgres` | Gestión de schema |

**railway:** requiere `railway login` antes de usarlo (auth OAuth, no API key estática).

---

## 10. Checklist de estado SOTA — validar antes de dar por listo

```
[ ] HERMES_BRIDGE_TOKEN seteado en Railway
[ ] HERMES_BRIDGE_TOKEN en ~/.hermes/.env.local
[ ] Scripts de cron actualizados con Bearer auth
[ ] Pulso Diario script probado y retorna 200 (no 401/405)
[ ] 8 Jobs del Workspace actualizados (delivery: bot-chat, auth, endpoints)
[ ] railway login ejecutado y persistido
[ ] Al menos 1 job del Workspace ejecutado exitosamente (sin rojo)
[ ] OmniRoute systemd service activo (no se apaga al reiniciar)
[ ] GBrain sincronizado con el estado final de esta sesión
[ ] COORDINATION-LOG.md actualizado con cambios de esta sesión
[ ] Deuda documentada: Bitwarden CLI, OmniRoute API key bug, repo push
```

---

## 11. Comandos de diagnóstico rápido (para cualquier sesión futura)

```bash
# Estado general de todos los servicios locales
echo "=== HERMES ===" && curl -s http://localhost:8642/health
echo "=== OMNIROUTE ===" && curl -s http://localhost:20128/health
echo "=== GBRAIN ===" && systemctl --user is-active gbrain-autopilot.service
echo "=== OMNIROUTE SERVICE ===" && systemctl --user is-active omniroute.service

# Cron jobs activos
hermes cronjob list

# Skills activos
ls ~/.hermes/skills/ | wc -l && ls ~/.hermes/skills/contexia/

# Memoria actual
wc -c ~/.hermes/profiles/contexia/memories/MEMORY.md

# Estado de Railway (requiere login)
railway status 2>/dev/null || echo "Railway: no logueado"

# Último sync de HubSpot
tail -5 /path/to/hermes-hubspot-poller/logs/poller.log 2>/dev/null || echo "Log no alcanzable desde WSL"
```

---

## 12. Flujo de arranque recomendado para nuevas sesiones de Hermes

1. **Leer este documento** → entender estado actual
2. **Verificar servicios** → sección 2 (health checks)
3. **Cargar contexto de GBrain** → `hermes gbrain query "estado actual Contexia"`
4. **Revisar COORDINATION-LOG.md** → qué hizo Claude Code desde la última sesión
5. **Ejecutar checklist §10** → identificar qué falta
6. **Priorizar por impacto** → 3.1 (token) siempre primero si falta

---

*Documento canónico en: `antigravity-app/docs/integrations/HERMES-SELF-CONFIG.md`*  
*Última actualización: 2026-08-30*  
*Mantenedor: Claude Code + Hermes (actualizar conjuntamente)*
