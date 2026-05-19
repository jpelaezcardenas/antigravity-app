# Contexia — GPS Financiero para PyMEs

Plataforma de Inteligencia Financiera que ayuda a las PyMEs en Latinoamérica a gestionar su flujo de caja, impuestos y riesgo regulatorio.

**Versión: 2.0 (Monolito Unificado)**

## 📦 Estructura del Monolito

```
antigravity-app/
├── frontend/                     # Frontend unificado (Vite + Next.js)
│   ├── dashboard/               # Portal cliente (Vite + React 19)
│   ├── wizard/                  # Auditoría DIAN + Crear Empresa (Next.js 14)
│   ├── public/                  # Assets estáticos (imágenes, favicons, JS)
│   └── shared/                  # (Futuro) Componentes compartidos
│
├── backend/                      # FastAPI + Python
│   ├── main.py                  # Punto de entrada
│   ├── config.py                # Configuración centralizada
│   ├── application/              # Casos de uso
│   ├── domain/                   # Lógica de negocio
│   ├── infrastructure/           # Adaptadores (BD, APIs externas)
│   ├── presentation/             # Routers y endpoints
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env (ignored)
│
├── .agents/                      # Content OS (n8n + reglas)
│   ├── workflows/               # 7 JSONs n8n (WF-01 a WF-10)
│   └── rules/                   # Reglas operativas + knowledge base
│
├── docs/                         # Documentación
│   ├── social-media-ops/        # Content OS specs y runbooks
│   ├── api/                      # (Futuro) OpenAPI docs
│   └── shadow-audit-knowledge-base.md
│
├── .config/                      # Configuración y deployment
│   ├── docker-compose.yml
│   ├── .env.example
│   └── deploy/
│
├── scripts/                      # Automatización
│   ├── setup.sh                  # Instalar dependencias
│   ├── dev.sh                    # Arrancar ambiente local
│   └── build.sh                  # Build para producción
│
├── Makefile                      # Orquestación de desarrollo
├── vercel.json                   # Configuración Vercel
└── .gitignore
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- Git
- Docker (opcional)

### Setup Completo (5 min)

```bash
# 1. Clonar y setup
git clone <repo>
cd antigravity-app
make setup

# 2. Configurar credenciales
cp .config/.env.example backend/.env
# Editar backend/.env con tus credenciales (Supabase, Gemini, etc.)

# 3. Arrancar desarrollo
make dev
```

Los servicios estarán disponibles en:
- **Dashboard**: http://localhost:5173 (Vite + React)
- **Wizard**: http://localhost:3000 (Next.js)
- **Backend API**: http://localhost:8080 (FastAPI)

## 📊 Tech Stack

### Frontend
- **Dashboard**: Vite 6.2, React 19, TypeScript 5.8, TailwindCSS 4.1, shadcn/ui
- **Wizard**: Next.js 14, TypeScript, TailwindCSS, shadcn/ui, Supabase Auth
- **Shared**: React Router, Gemini AI SDK, Supabase Client

### Backend
- **FastAPI** con OpenAPI (Swagger)
- **Supabase** (PostgreSQL) para datos + Auth
- **Python 3.10+** con Clean Architecture (layers)
- **uvicorn** servidor ASGI

### Infrastructure
- **Vercel**: Frontend (dashboard deploy)
- **Railway** (antes) / **Docker**: Backend
- **Supabase**: DB + Auth + Real-time
- **n8n**: Orquestación de workflows (local + producción)
- **Gmail + Resend**: Email transactional

### Content OS
- **n8n**: 7 workflows parametrizados (ingesta, generación, scoring, análisis)
- **Supabase**: Almacenamiento de ideas, borradores, métricas, posts
- **Claude API**: Generación de contenido
- **Meta / Facebook Graph API**: Publicación y métricas orgánicas

## 🏗️ Arquitectura de Desarrollo

### Monorepo sin workspace
Es un **monolito compartido** (no es un monorepo de paquetes tipo Turbo/Yarn Workspaces). Los 3 servicios (dashboard, wizard, backend) son **independientes y desacoplados**:

- **Dashboard** y **Wizard** se compilan por separado → frontend/dashboard/dist y frontend/wizard/.next
- **Backend** corre como API en 8080 con CORS abierto (dev) o restringido (prod)
- Los frontends consumen la API mediante HTTPS desde el navegador

**Ventaja**: Facilita trabajo paralelo, deploys independientes, sin conflictos de versiones compartidas.

## 🎯 Comandos Frecuentes

```bash
# Instalar dependencias
make install          # O: make setup

# Desarrollo
make dev              # Arranca todos los servicios en paralelo

# Específicos
make run-backend      # Solo backend (puerto 8080)
make run-dashboard    # Solo dashboard (puerto 5173)
make run-wizard       # Solo wizard (puerto 3000)

# Build
make build            # Compila ambos frontends + verifica backend

# Testing
make test             # Pytest (backend) + Jest (frontends, si existen)

# Docker
make docker-build     # Construye imagen Docker del backend
make docker-up        # Levanta docker-compose (.config/docker-compose.yml)
make docker-down      # Detiene containers

# Limpieza
make clean            # Elimina node_modules, dist, __pycache__, etc.
```

Ver `make help` para más comandos.

## 🔐 Secretos y Configuración

### Backend (.env)
```
SUPABASE_URL=https://...
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
DATABASE_URL=postgresql://...
GEMINI_API_KEY=...
RESEND_API_KEY=...
```

### Frontend (environment variables)
Las variables de frontend van en `frontend/{dashboard,wizard}/.env.local` y deben ser públicas (prefijo `VITE_` o `REACT_APP_`):

```
VITE_SUPABASE_URL=https://...
VITE_SUPABASE_ANON_KEY=eyJ...
REACT_APP_GEMINI_API_KEY=...
```

**Nunca** incluir `SERVICE_ROLE_KEY` en frontend.

## 📚 Documentación

- **[docs/social-media-ops/](./docs/social-media-ops/)** — Content OS specs, workflows, reglas
- **[DEPLOY_INSTRUCTIONS.md](./DEPLOY_INSTRUCTIONS.md)** — Cómo desplegar a producción
- **[SUPABASE_SETUP.md](./SUPABASE_SETUP.md)** — Setup y migraciones de BD
- **[.agents/README.md](./.agents/README.md)** — Sobre workflows y reglas automáticas

## 🧠 Content OS (n8n + Reglas)

El sistema tiene un **subsistema automático** de generación y publicación de contenido en Facebook:

1. **Ingesta** (`WF-01`) — Ideas desde formulario / fuentes externas
2. **Generación** (`WF-02`) — LLM genera ideas masivas
3. **Creación** (`WF-04`) — Pasa idea → guión/borrador con IA
4. **Publicación** (`WF-07`) — Logging automático en Supabase
5. **Métricas** (`WF-08`) — Captura datos desde Facebook/Meta
6. **Scoring** (`WF-09`) — Calcula engagement y ROI
7. **Análisis** (`WF-10`) — Resumen semanal automático

Toda la **inteligencia** está en:
- `.agents/rules/rules.md` — Reglas globales
- `.agents/rules/OUTPUT_FORMAT.md` — Estructura esperada de prompts
- `.agents/rules/Base de conocimientos-Contexia.md` — ICP, dolores, voz

## 🎬 Deploy

### Frontend (Vercel)
```bash
# Vercel detecta automáticamente el cambio
git push origin main
# Vercel construye frontend/dashboard y lo deploya
```

### Backend (Docker / Railway)
```bash
# Desde la raíz
docker build -t contexia-backend:latest ./backend
docker run -p 8080:8080 --env-file backend/.env contexia-backend:latest
```

Ver [DEPLOY_INSTRUCTIONS.md](./DEPLOY_INSTRUCTIONS.md) para más detalles.

## 🤝 Contributing

1. Crear rama: `git checkout -b feature/tu-feature`
2. Hacer cambios, commitear
3. Abrir PR a `main`
4. Asegurar que `make test` y `make build` pasen
5. Merge cuando esté aprobado

## 📝 Licencia

Propietaria Contexia SAS.

## 🆘 Soporte

- **Issues**: GitHub Issues en este repo
- **Docs**: Ver carpeta `docs/`
- **Team**: Equipo de Contexia

---

**Última actualización:** 2026-05-19  
**Rama de reorganización:** `feature/reorganize-monolith` (merged a `main`)
