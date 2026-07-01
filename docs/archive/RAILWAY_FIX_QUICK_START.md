# 🚀 RAILWAY FIX - Quick Start

**Situación**: 3 routers no cargan en Railway (Pulso, Taty, Agents)  
**Solución**: Force redeploy O revisar logs

---

## ⚡ OPCIÓN 1: Force Redeploy (30 segundos)

### Paso 1: Abrir Railway
```
https://railway.com/project/27f4a1b4-1e46-4ad7-b08e-15e92817ffdd
```

### Paso 2: En el dashboard
1. **Click en "Backend"** (el servicio que dice Python/FastAPI)
2. **Click en "Deployments"** (arriba)
3. **Verás un listado de deploys**

### Paso 3: Forzar redeploy
**Click en el deploy ACTUAL** (el más reciente, probablemente con un checkmark ✓)

Debería abrir panel con:
- Status: "Success" o "Failed"  
- Build logs
- **Un botón "Redeploy" o "Rebuild" (arriba a la derecha)**

**Click en Redeploy**

### Paso 4: Esperar
- Verás: "Building..." → "Deploying..." → "Running"
- Toma ~2-3 minutos

### Paso 5: Verificar
Después que diga "Running", ejecuta:
```bash
curl -X GET "https://antigravity-app-production-175a.up.railway.app/api/v1/pulso/today?company_id=ff1a8b7c-b0a1-422e-bc48-fac6242be027"
```

Si retorna `200` → ✅ FIXED  
Si retorna `404` → continúa a OPCIÓN 2

---

## 🔍 OPCIÓN 2: Revisar Logs (si Redeploy no funcionó)

### Paso 1: En el mismo panel de Deployment
**Click en "Logs"** (tab/sección)

### Paso 2: Buscar errores
En los logs, busca (Ctrl+F):
```
ImportError
ModuleNotFoundError
ERROR
pulso
taty
agents
```

### Paso 3: Lee qué dice el error
Busca algo como:
```
[ERROR] Unable to load pulso_endpoints: ModuleNotFoundError: ...
[ERROR] pulso_service not found
[ERROR] Failed to import agents.llm_engine
```

### Paso 4: Reporta el error exacto
Si ves un error, **copia TODO el mensaje** y **enviámelo**.

Formato:
```
[TIMESTAMP] Error: xxxxxxx
```

---

## 💡 Qué podría estar fallando

| Síntoma | Causa | Solución |
|---------|-------|----------|
| Build Success pero 404 en endpoints | Routers no se registraron | Redeploy |
| Build Failed | Error en código o deps | Ver logs, arreglar |
| ImportError: pulso_service | Archivo falta | Commit & push |
| ImportError: llm_engine | Archivo falta | Commit & push |
| ModuleNotFoundError: groq | Dependencia no instalada | Agregar a requirements.txt |

---

## ✅ Checklist de Verification

Después de arreglar, verifica TODOS:

```bash
# 1. Health Check
curl https://antigravity-app-production-175a.up.railway.app/api/v1/health
# Esperado: 200

# 2. Centinela (ya funciona)
curl https://antigravity-app-production-175a.up.railway.app/api/v1/centinela/alerts?company_id=ff1a8b7c-b0a1-422e-bc48-fac6242be027
# Esperado: 200 + array

# 3. Pulso (era 404)
curl -X POST https://antigravity-app-production-175a.up.railway.app/api/v1/pulso/today \
  -H "Content-Type: application/json" \
  -d '{"company_id":"ff1a8b7c-b0a1-422e-bc48-fac6242be027"}'
# Esperado: 200 + JSON con KPIs

# 4. Taty (era 404)
curl -X POST https://antigravity-app-production-175a.up.railway.app/api/v1/taty/ask \
  -H "Content-Type: application/json" \
  -d '{"company_id":"ff1a8b7c-b0a1-422e-bc48-fac6242be027","question":"test"}'
# Esperado: 200 + JSON con respuesta

# 5. Full Pipeline (era 404)
curl -X POST https://antigravity-app-production-175a.up.railway.app/api/v1/agents/orchestrator/full-pipeline \
  -H "Content-Type: application/json" \
  -d '{"company_id":"ff1a8b7c-b0a1-422e-bc48-fac6242be027","company_url":"https://test.com","campaign_objective":"test","budget":5000}'
# Esperado: 200 + JSON con 7 stages
```

Si TODOS retornan 200 → ✅ MVP FUNCIONA

---

## 🆘 Si nada funciona

1. **Copia los últimos 50 logs** de Railway
2. **Pégamelos aquí con formato:**
```
[TIMESTAMP] log line 1
[TIMESTAMP] log line 2
[TIMESTAMP] ERROR: ...
```
3. **Yo buscaré exactamente qué está roto**

---

## ⏱️ Tiempo estimado

- **Redeploy solamente**: 3-5 minutos
- **Revisar logs + arreglar**: 10-15 minutos
- **Verification**: 2 minutos

**Total**: 5-20 min para tener MVP 100% funcional

---

**Empezá con OPCIÓN 1 (Redeploy), después reporta resultados** 👇
