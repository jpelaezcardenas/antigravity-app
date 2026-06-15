# Checklist Railway — Deploy Backend a Producción

**Aplica a:** Proyectos que usan Railway para backend (antigravity-app, Centinela, Taty, etc.)

---

## Pre-Deploy (en tu laptop)

- [ ] Backend compilable / sin errores de sintaxis
- [ ] Tests pasan: `npm test` o `pytest` (según stack)
- [ ] Linting pasa: `npm run lint` o `ruff check .`
- [ ] Migrations creadas y documentadas (si hay cambios de DB)
- [ ] `.env` values están en Railway secrets, no hardcoded

---

## Push a Remoto

```bash
# Verifica rama
git branch --show-current
# Debería ser: main, develop, o feature/[CHANGE-ID]

# Push
git push origin [current-branch]

# Verifica
git log --oneline -1
```

Checklist:
- [ ] `git push` sin errores
- [ ] Rama remota actualizada
- [ ] GitHub muestra el nuevo commit

---

## Railway: Espera el Deploy

**URL:** https://railway.app/[project]/deployments

1. Abre esa URL
2. Busca el deploy más reciente (debería estar arriba)
3. Status debe ser "Deploying" → "Success" ✅

Estados posibles:
```
Deploying → Skipping tests → Active ✅     (éxito)
Deploying → Build failed ❌                 (falla)
Deploying → Runtime error ❌               (error en startup)
```

Checklist:
- [ ] Deploy aparece en Railway (dentro de 1-2 min)
- [ ] Status no está "Failed" o "Cancelled"
- [ ] Tiempo transcurrido: < 5 minutos (normal es 2-3)

---

## Railway: Verifica el Log

Haz click en el deployment para ver logs:

```
[timestamp] Building docker image...
[timestamp] Pushing to registry...
[timestamp] Starting service...
[timestamp] Service is live
```

Busca:
- [ ] No hay líneas rojas que digan "ERROR" o "FATAL"
- [ ] Ves "Service is live" o "Started successfully"
- [ ] Si hay warnings (amarillo), está OK (pero nota cuáles)

**Si ves errores:**
- [ ] Nota el error exacto (copiar la línea)
- [ ] Compara con spec.md y requirements
- [ ] Si es un dependency missing, agrega a `requirements.txt` (Python) o `package.json` (Node)

---

## Live Backend: Verifica Endpoint

Una vez que Railway dice ✅ **Active**, prueba el backend:

```bash
# Reemplaza con tu endpoint real
curl -s https://antigravity-app-production-175a.up.railway.app/api/v1/health | jq .

# O para un endpoint específico:
curl -s -X POST https://antigravity-app-production-175a.up.railway.app/api/v1/social-ops/ideas \
  -H "Content-Type: application/json" \
  -d '{"idea": "test"}' | jq .
```

Checklist:
- [ ] Endpoint responde (status 200, 201, 400, etc. — no 502/503)
- [ ] Response es JSON (o esperado format)
- [ ] No ves "Internal Server Error"

---

## Verificación Funcional

**Para cada cambio, verifica:**

Si fue **API nueva:**
- [ ] GET/POST/PUT/DELETE responden según spec.md
- [ ] Input validation funciona (envía data inválida, debería fallar)
- [ ] Errores retornan status correcto (400, 401, 404, 500, etc.)
- [ ] Response headers correctos (Content-Type, CORS si aplica)

Si fue **DB migration:**
- [ ] Nueva tabla existe (query en Railway Postgres console)
- [ ] Columnas tienen tipos correctos
- [ ] Constraints funcionan (unique, foreign key, etc.)

Si fue **servicio background:**
- [ ] Servicio está en "Running" en Railway
- [ ] Logs no muestran errores repetidos
- [ ] Si procesa jobs, verifica que está procesando

---

## Railway Postgres: Verifica DB (Si Aplica)

Si tu cambio incluye migrations:

```bash
# Abre Railway console
https://railway.app/[project]/postgres/browser

# Verifica tabla nueva
SELECT * FROM [table_name] LIMIT 1;

# Verifica schema
\d [table_name]
```

Checklist:
- [ ] Tabla existe
- [ ] Columnas match spec.md
- [ ] No hay errores al query
- [ ] Foreign keys apuntan a tablas correctas

---

## Rollback (Si Algo Salió Mal)

Si el cambio rompió el backend:

```bash
# 1. Identifica commit bueno
git log --oneline -10
# Busca el anterior a tu cambio

# 2. Revert
git revert [commit-hash]
# (crea commit que deshace tu cambio)

# 3. Push
git push origin [branch]

# 4. Railway detectará nuevo commit y desplegará
# Espera a que status sea ✅ Active
```

Checklist:
- [ ] `git revert` creó nuevo commit
- [ ] Push fue exitoso
- [ ] Railway detectó nuevo commit
- [ ] Deploy status: ✅ Active
- [ ] Backend endpoint responde de nuevo

---

## Reporte

```markdown
## Railway Deployment — [CHANGE-ID]

- Commit: `[git rev-parse --short HEAD]`
- Railway URL: https://railway.app/[project]/deployments/[deployment-id]
- Deploy time: [X minutos]
- Status: ✅ ACTIVE

### Verificación en Vivo
- Endpoint: https://[railway-url]/api/v1/[endpoint]
- Responde: ✅ Sí (HTTP 200)
- Response format: ✅ Correcto

### DB Changes (si aplica)
- Tabla nueva: [table_name]
- Verificada: ✅ Sí
```

Copia esto a:
```
openspec/changes/[CHANGE-ID]/reports/YYYY-MM-DD-railway-deployment.md
```

---

## Troubleshooting Rápido

| Problema | Causa | Solución |
|----------|-------|----------|
| "Build failed" | Dependencies missing | Añade a requirements.txt / package.json |
| "Runtime error" | Import error, env var missing | Verifica .env en Railway |
| "503 Service Unavailable" | Servicio en restart | Espera 30 seg, retry |
| "Connection refused" | Puerto incorrecto | Verifica PORT en código |
| Endpoint 404 | Ruta no existe | Compara con spec.md |
| DB migration failed | SQL syntax error | Verifica migrations/ folder |

---

## Referencias

- Railway docs: https://docs.railway.app/
- antigravity-app Railway: https://railway.app/[project]
- Postgres console: https://railway.app/[project]/postgres
