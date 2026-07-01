# Production Deployment Guide - Render/Railway

**Status:** Stage 1 ✅ Passed. Ready for immediate deployment.

---

## OPCIÓN A: Render.com (Recomendado)

### Paso 1: Preparar código en GitHub

```bash
# En tu máquina, en la raíz del proyecto
cd C:\Users\contexia\Projects\antigravity-app\.claude\worktrees\angry-sutherland-976d5d

# Verificar que Dockerfile existe
ls -la apps/backend/Dockerfile
ls -la apps/backend/requirements.txt

# Stagear cambios
git add .

# Commit final
git commit -m "feat: Production deployment - Stage 1 monitoring passed, all metrics approved"

# Push a GitHub
git push origin claude/angry-sutherland-976d5d
```

### Paso 2: Crear Web Service en Render

1. Ve a https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Selecciona **"Deploy an existing repository"**
4. Busca y selecciona: `antigravity-app`
5. **Settings:**
   - **Name:** `contexia-backend`
   - **Root Directory:** `apps/backend`
   - **Runtime:** `Docker`
   - **Build Command:** (dejar vacío - Render auto-detecta)
   - **Start Command:** (dejar vacío - Render usa CMD del Dockerfile)

### Paso 3: Agregar Variables de Entorno en Render

En el panel de Render, sección **"Environment"**:

```
SUPABASE_URL=[YOUR_SUPABASE_URL]
SUPABASE_KEY=[YOUR_SUPABASE_SECRET_KEY]
DATABASE_URL=[YOUR_DATABASE_URL]
OPENROUTER_API_KEY=[YOUR_OPENROUTER_API_KEY]
GROQ_API_KEY=[YOUR_GROQ_API_KEY]
JWT_SECRET=[YOUR_JWT_SECRET_32_CHARS_MIN]
ENVIRONMENT=production
DEBUG=False
ALLOWED_ORIGINS=https://contexia.online,https://app.contexia.online
PREFER_FREE_MODELS=True
LLM_TIMEOUT=30
LOG_LLM_CALLS=True
```

**⚠️ NOTE**: Replace `[YOUR_*]` placeholders with actual values from your Supabase project and API keys.

### Paso 4: Deploy

Click **"Create Web Service"** → Render automáticamente:
- Clona el código
- Construye la imagen Docker
- Inicia el servidor
- Te da una URL: `https://contexia-backend.onrender.com`

**Esperar 3-5 minutos** hasta que diga "Live"

### Paso 5: Verificar que está live

```bash
# Health check
curl https://contexia-backend.onrender.com/api/v1/health

# Debería responder:
# {"status":"healthy","timestamp":"...","service":"Contexia API"}
```

---

## OPCIÓN B: Railway.app

### Paso 1: GitHub (igual que Render)

```bash
git add .
git commit -m "feat: Production deployment - Stage 1 monitoring passed"
git push origin claude/angry-sutherland-976d5d
```

### Paso 2: Crear proyecto en Railway

1. Ve a https://railway.app
2. Click **"New Project"**
3. Selecciona **"Deploy from GitHub repo"**
4. Conecta tu GitHub (first time solo)
5. Selecciona `antigravity-app`
6. Click **"Deploy now"**

### Paso 3: Variables de Entorno en Railway

En **"Variables"** tab, pegar todo el bloque .env:

```
SUPABASE_URL=[YOUR_SUPABASE_URL]
SUPABASE_KEY=[YOUR_SUPABASE_SECRET_KEY]
DATABASE_URL=[YOUR_DATABASE_URL]
OPENROUTER_API_KEY=[YOUR_OPENROUTER_API_KEY]
GROQ_API_KEY=[YOUR_GROQ_API_KEY]
JWT_SECRET=[YOUR_JWT_SECRET_32_CHARS_MIN]
ENVIRONMENT=production
DEBUG=False
```

**⚠️ NOTE**: Replace `[YOUR_*]` placeholders with actual values from your Supabase project and API keys.

### Paso 4: Configurar puerto

En **"Settings"**:
- **Start Command:** `python main.py` (si no auto-detecta)
- **Port:** `8080` (debe coincidir con tu Dockerfile EXPOSE)

### Paso 5: Deploy

Click **"Deploy"** → Railway construye y deploya automáticamente  
URL pública: `https://contexia-backend-prod.railway.app` (similar)

---

## Paso Final: Conectar Frontend a Backend

Una vez tengas la URL pública (ej: `https://contexia-backend.onrender.com`):

1. Ve al proyecto React (frontend)
2. Abre `src/api/axios.ts` o similar
3. Busca `baseURL`
4. Reemplaza:
   ```
   // OLD
   baseURL: 'http://localhost:8000'
   
   // NEW
   baseURL: 'https://contexia-backend.onrender.com'
   ```
5. Rebuild y deploy frontend a tu hosting

---

## Health Check Post-Deploy

```bash
# Verify backend is live
curl https://contexia-backend.onrender.com/api/v1/health

# Verify LLM is working
curl -X POST https://contexia-backend.onrender.com/api/v1/agents/task-info/taty_faq

# Verify Swagger docs
curl https://contexia-backend.onrender.com/openapi.json | head -10
```

---

## Troubleshooting

**Error: "Application startup complete" but 502 Bad Gateway**
- Railway/Render esperaba puerto diferente
- Chequea el Dockerfile: `EXPOSE 8080` debe coincidir
- Configura Port en la plataforma a `8080`

**Error: "Invalid API key"**
- Verifica que copiaste correctamente OPENROUTER_API_KEY y GROQ_API_KEY
- Recuerda: estas keys se cancelan después (son de staging)
- Genera keys nuevas para producción si quieres

**Backend deploy exitoso pero endpoints retornan 500**
- Chequea logs en Render/Railway
- Probablemente Supabase credentials
- Verifica que DATABASE_URL es correcta

---

## Resumen

| Paso | Acción | Tiempo |
|------|--------|--------|
| 1 | git push | 30s |
| 2 | Crear Web Service | 1m |
| 3 | Agregar vars de entorno | 2m |
| 4 | Deploy (build + startup) | 3-5m |
| 5 | Health check | 1m |
| **Total** | | **~10-15 minutos** |

**Estado:** Todo listo. Puedes deployar AHORA MISMO.
