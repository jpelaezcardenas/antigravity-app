# Contexia Content OS

Sistema operativo de contenidos orgánicos para la presencia de Contexia en Facebook. Diseñado para ser construido de forma híbrida con **n8n + FastAPI (Python)** e implementado y operado por una sola persona.

## Qué es este proyecto

Un motor de contenido end-to-end que cubre el ciclo completo de creación orgánico:

```
Idea → Investigación → Guión → Aprobación → Publicación → Métricas → Análisis → Retroalimentación → Siguiente ciclo
```

El sistema transforma los dolores reales del ICP de Contexia (miedo a la DIAN, sorpresa tributaria, desorden financiero) en contenido educativo y storytelling que posiciona a Contexia como la "amiga contadora" que explica con claridad y protege con criterio.

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTEXIA CONTENT OS                       │
├─────────────┬──────────────┬──────────────┬─────────────────┤
│  INGESTA    │  PRODUCCIÓN  │  DISTRIBUCIÓN│  INTELIGENCIA   │
│             │              │              │                 │
│ • Ideas     │ • Guiones    │ • Aprobación │ • Métricas      │
│ • Research  │ • Hooks      │ • Programar  │ • Scoring       │
│ • Backlog   │ • Copy + CTA │ • Publicar   │ • Patrones      │
│ • Calendario│ • Assets     │ • Logging    │ • Retroaliment. │
├─────────────┴──────────────┴──────────────┴─────────────────┤
│                      CAPA DE DATOS                          │
│                   Supabase (PostgreSQL)                     │
├─────────────────────────────────────────────────────────────┤
│             ORQUESTACIÓN E INFERENCIA HÍBRIDA               │
│                 n8n + FastAPI LLM Gateway                   │
├─────────────────────────────────────────────────────────────┤
│                    ALMACENAMIENTO                            │
│                     Supabase SQL                            │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack Real del Proyecto

| Capa | Herramienta | Rol |
|:-----|:------------|:----|
| **Orquestación** | **n8n** (Self-hosted local / Node.js) | Triggers semanales, cronjobs y ruteo visual del flujo editorial |
| **Capa de Inferencia** | **FastAPI LLM Gateway** (Python) | API de inferencia asíncrona tolerante a fallos expuesta en `POST /api/v1/llm/analyze` |
| **Base de datos** | **Supabase (PostgreSQL)** | Almacenamiento seguro, semillas de ideas, pipeline editorial y logging de métricas |
| **Motor de IA (LLM)** | **Cascada Failover de 5 proveedores** | **Groq** (Primario) ➔ **Cerebras** ➔ **Mistral AI** ➔ **Google Gemini (REST)** ➔ **OpenRouter** |
| **Aprobación** | **Gmail SMTP** (`jpelaezcardenas@gmail.com`) | Notificaciones y correos interactivos para revisión y aprobación manual-asistida |
| **Canal de Destino** | **Facebook Page** | Publicación asistida mediante copys listos y formateados |
| **Dashboard / Métricas** | **Supabase Table Editor + SQL Views** | Visualización de rendimiento de posts, scoring y feedback loop |

## Módulos clave

1. **Content Engine** — Generación de ideas, hooks, copies, CTA y guiones resilientes con IA y auto-curación de JSON.
2. **Editorial Calendar** — Planificación semanal estructurada con pilares de marca e ideas sembradas.
3. **Approval Pipeline** — Flujo de revisión humana mediante notificaciones automáticas por correo electrónico.
4. **Publish & Log** — Publicación manual asistida para el MVP y registro exacto del histórico de posts.
5. **Analytics Pulse** — Captura de métricas semanales (likes, shares, comments) y cálculo del Scoring de engagement.
6. **Feedback Loop** — Detección automática de "posts ganadores" e inyección de nuevas semillas al backlog de ideas.

## Estructura del repositorio

```
contexia-content-os/
├── .agents/rules/rules.md       ← Reglas canónicas de Contexia
├── docs/
│   ├── specs/                   ← Especificaciones técnicas del sistema
│   ├── decisions/               ← Registros de decisiones arquitectónicas
│   └── runbooks/                ← Guías de operación y troubleshooting
├── Base de conocimientos-Contexia.md  ← Ground truth de marca (202KB)
├── DISCOVERY_TEMPLATE.md        ← Preguntas de discovery cerradas
├── OUTPUT_FORMAT.md             ← Formatos obligatorios de salida
├── PROJECT_BRIEF.md             ← Scope y restricciones del proyecto
├── PLAN.md                      ← Plan vivo del proyecto y squad status
├── README.md                    ← Este archivo de arquitectura
├── rules.md                     ← Reglas del agente para lectura humana
└── workflows/                   ← Workflows JSON listos para importar a n8n
```

## Cómo configurar el proyecto

### Prerrequisitos
- **Python 3.11+** y gestor de paquetes `pip` instalados localmente.
- **Node.js** y **n8n** corriendo en local (`npx n8n start` en `http://localhost:5678`).
- Proyecto activo en **Supabase** (PostgreSQL) con las tablas inicializadas.
- Cuenta de **Gmail** y una Contraseña de Aplicación de 16 caracteres generada en Google.
- API Keys de tus proveedores de IA preferidos (Groq, Cerebras, Mistral, Gemini).

### Setup paso a paso

1. **Clonar el repositorio:**
   ```powershell
   git clone https://github.com/jpelaezcardenas/contexia-content-os.git
   ```

2. **Configurar variables de entorno (.env):**
   Crea un archivo `.env` en la raíz del backend (`antigravity-app/apps/backend/.env`) con tus credenciales de Supabase y API Keys de LLMs:
   ```env
   SUPABASE_URL=https://kpynymwghfwshvcvevxq.supabase.co
   SUPABASE_KEY=tu_anon_key_real
   GROQ_API_KEY=gsk_...
   CEREBRAS_API_KEY=csk-...
   ```

3. **Iniciar el Servidor Backend de FastAPI:**
   Instala las dependencias y arranca el servidor local de desarrollo:
   ```powershell
   cd c:\Users\contexia\Projects\antigravity-app\apps\backend
   pip install -r requirements.txt
   python -m uvicorn main:app --reload --port 8080
   ```
   *(El gateway de inferencia asíncrono con auto-curación estará expuesto en `http://localhost:8080/api/v1/llm/analyze`).*

4. **Importar Workflows a n8n:**
   Importa de manera masiva los 7 flujos de trabajo en tu base de datos local de n8n corriendo la siguiente línea en PowerShell:
   ```powershell
   Get-ChildItem -Path "workflows/*.json" | ForEach-Object { npx n8n import:workflow --input="$($_.FullName)" }
   ```

5. **Configurar Credenciales en n8n:**
   - Abre tu panel local de n8n: `http://localhost:5678/home/credentials`.
   - Crea/edita la credencial de tipo **SMTP** con el nombre **Gmail SMTP**, tu correo y tu Contraseña de Aplicación de 16 caracteres de Google.

## Cómo ejecutar QA

### Checklist de humanización (obligatorio en todo copy)
- [ ] ¿Suena como una amiga que sabe, no como un bot?
- [ ] ¿Evita jerga opaca (impuesto diferido, base gravable, causación)?
- [ ] ¿El CTA es claro y protector, no agresivo?
- [ ] ¿Un emprendedor de 25 años sin formación contable lo entendería?

### /audit Quality Gate
Todo feature pasa por el pipeline estricto: Environmental Check ➔ Functional Audit ➔ Trust Audit ➔ Score ≥9/10.

## Reglas de contribución
- Leer `.agents/rules/rules.md` antes de realizar cualquier cambio técnico.
- Toda decisión técnica debe documentarse en `docs/decisions/`.
- Todo bug recurrente o workaround manual se registra en `docs/runbooks/`.
- **CRÍTICO:** Nunca describir a Contexia como una firma contable regulada.

## Contexto de marca
- **Contexia** = AI Automation Agency (AAA) en Colombia, **NO** firma contable ni regulada.
- **Propuesta core** = Claridad Predictiva (separar la capa tecnológica de la regulada).
- **Tono** = Amiga contadora con criterio (empática, clara, protectora y directa).
- **Promesa** = "Sabe cuánto es tuyo antes de gastarlo".
