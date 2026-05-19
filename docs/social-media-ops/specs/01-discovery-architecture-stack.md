# Contexia Content OS — System Blueprint

## BLOQUE 1: DISCOVERY + CONFIRMADOS + DEFAULTS

### 1A. Lo ya confirmado (datos duros)

| # | Dato | Fuente |
|:--|:-----|:-------|
| 1 | Canal: Facebook Page (orgánico) | PROJECT_BRIEF |
| 2 | Operador: 1 persona | PROJECT_BRIEF |
| 3 | Contenido: educativo + storytelling | PROJECT_BRIEF |
| 4 | Stack: n8n + Sheets/Airtable + Drive + LLM | PROJECT_BRIEF |
| 5 | Tono: amiga contadora con criterio | rules.md |
| 6 | Contexia = AAA, NO firma contable | rules.md |
| 7 | Propuesta core: Claridad Predictiva | Base de conocimientos |
| 8 | ICP: PyMEs, dropshippers, creadores, freelancers, nómadas digitales | Base de conocimientos |
| 9 | Dolores: miedo DIAN, sorpresa tributaria, jerga opaca, ceguera de caja | Base de conocimientos |
| 10 | Plazo MVP: 7 días | PROJECT_BRIEF |
| 11 | Repo: github.com/jpelaezcardenas/contexia-content-os | Confirmado por usuario |

### 1B. Defaults aplicados (asunciones inteligentes)

| # | Decisión | Default | Razón |
|:--|:---------|:--------|:------|
| 1 | DB del MVP | Google Sheets | Cero costo, migra a Airtable en Fase 2 |
| 2 | Frecuencia semana 1 | 3 posts/semana | Sostenible para 1 persona |
| 3 | Publicación | Manual asistida | Meta API requiere App Review; n8n genera post listo, humano copia y publica |
| 4 | Aprobación | Gmail notification | Ya se usa, mínima fricción |
| 5 | LLM | Gemini 1.5 Pro | Costo/token competitivo, API estable |
| 6 | Formatos prioritarios | Texto+imagen, Carrusel, Caso/storytelling | Viables sin equipo creativo |
| 7 | Métricas | Export manual (MVP) | Meta API para métricas requiere permisos adicionales |
| 8 | Dashboard | Google Sheets con formato condicional | Cero setup extra |
| 9 | Autonomía del sistema | Genera borradores, humano aprueba y publica | Human-in-the-loop |

### 1C. Preguntas de discovery pendientes (no bloquean MVP)

| # | Pregunta | Impacto | Bloqueante? |
|:--|:---------|:--------|:------------|
| 1 | ¿La Facebook Page ya existe o hay que crearla? | Setup | No — se puede crear día 1 |
| 2 | ¿Tienes cuenta de n8n activa? Cloud o self-hosted? | Infra | Sí — necesario para workflows |
| 3 | ¿Tienes API key de Gemini o prefieres otro LLM? | Content engine | Sí — necesario para generación |
| 4 | ¿Tienes Google Workspace o Gmail personal? | Sheets/Drive | No — funciona con ambos |
| 5 | ¿Horario preferido de publicación? | Calendario | No — default: 10am COT |

---

## BLOQUE 2: SUPUESTOS Y DECISIONES

### Decisiones tomadas (no requieren aprobación per rules §7)

1. **Google Sheets como DB del MVP** — migración a Airtable cuando haya >500 filas
2. **Publicación manual asistida** — n8n genera post completo (copy + imagen + hashtags), operador hace copy-paste a Facebook
3. **Batch semanal** — el sistema genera contenido de toda la semana en un solo batch (lunes), no diario
4. **3 posts/semana** — L/Mi/V como default
5. **Sin pauta pagada** — todo orgánico en Fase 1

### Decisiones que requieren confirmación

| # | Decisión | Opciones | Recomendación |
|:--|:---------|:---------|:--------------|
| 1 | ¿La persona que opera también graba videos? | A) Sí, videos sencillos B) Solo texto+imagen | **A** — Reels de 30-60s con guión generado |
| 2 | ¿Publicar como "Contexia" o como persona real? | A) Marca B) Persona C) Mix | **C** — Marca con cara humana |

---

## BLOQUE 3: ARQUITECTURA GENERAL

### Flujo completo de una pieza de contenido

```
LUNES (Batch semanal)
  │
  ▼
[1. INGESTA] ──── Ideas del backlog + noticias + dolores ICP
  │
  ▼
[2. ENRIQUECIMIENTO] ──── LLM analiza idea → ángulo + pilar + formato
  │
  ▼
[3. PRODUCCIÓN] ──── LLM genera: Hook + Copy + CTA + Guión (si video)
  │
  ▼
[4. QA HUMANIZACIÓN] ──── Prompt de reescritura empática si suena robótico
  │
  ▼
[5. NOTIFICACIÓN] ──── Gmail envía borrador al operador para revisión
  │
  ▼
MARTES-JUEVES (Humano)
  │
  ▼
[6. REVISIÓN] ──── Operador edita, ajusta tono, prepara visual
  │
  ▼
[7. APROBACIÓN] ──── Operador marca "Aprobado" en Sheets
  │
  ▼
[8. PUBLICACIÓN] ──── Operador copia post a Facebook (manual asistida)
  │
  ▼
[9. LOGGING] ──── Operador registra URL + fecha + hora en Sheets
  │
  ▼
VIERNES (Automático)
  │
  ▼
[10. MÉTRICAS] ──── Operador ingresa métricas del post (manual MVP)
  │
  ▼
[11. SCORING] ──── n8n calcula score por post
  │
  ▼
[12. ANÁLISIS] ──── LLM detecta patrones ganadores/perdedores
  │
  ▼
[13. RETROALIMENTACIÓN] ──── Sistema propone ajustes para siguiente semana
```

### Qué es automático vs manual

| Paso | Automático | Manual |
|:-----|:-----------|:-------|
| Generar ideas | ✅ | |
| Escribir hooks/copy/CTA | ✅ | |
| QA de humanización | ✅ | |
| Notificar borrador | ✅ | |
| Revisar y editar | | ✅ |
| Aprobar | | ✅ (checkbox en Sheets) |
| Publicar en Facebook | | ✅ (copy-paste) |
| Registrar publicación | | ✅ (URL + fecha en Sheets) |
| Ingresar métricas | | ✅ (MVP) |
| Calcular score | ✅ | |
| Detectar ganadores | ✅ | |
| Recomendar siguiente ciclo | ✅ | |

---

## BLOQUE 4: STACK RECOMENDADO

### Stack MVP (7 días)

| Capa | Herramienta | Costo | Para qué |
|:-----|:------------|:------|:---------|
| Orquestación | n8n Cloud (free tier) o self-hosted | $0 | Ejecutar workflows |
| Base de datos | Google Sheets | $0 | Calendario, pipeline, métricas |
| Almacenamiento | Google Drive | $0 | Assets, versiones, backups |
| LLM | Gemini 1.5 Pro API | ~$0.01-0.05/post | Generación de contenido |
| Notificación | Gmail | $0 | Enviar borradores para aprobación |
| Canal | Facebook Page | $0 | Publicación orgánica |
| Dashboard | Google Sheets (pestañas) | $0 | Métricas y scores |

**Costo total MVP: ~$0-2 USD/mes** (solo tokens LLM)

### Stack 30 días (Fase 2)

| Migración | De → A | Trigger de migración |
|:----------|:-------|:---------------------|
| Base de datos | Sheets → Airtable | >500 filas o necesidad de formularios |
| Aprobación | Gmail → Telegram bot | Necesidad de aprobación con un tap |
| Dashboard | Sheets → Looker Studio | Necesidad de visualización avanzada |
| Métricas | Manual → Meta API (parcial) | App Review aprobado |
| Publicación | Manual → Meta Graph API | App Review aprobado |

### Qué NO usar todavía
- ❌ Hootsuite / Buffer / Metricool — agrega costo sin valor para 3 posts/semana
- ❌ Notion — API limitada para automatización con n8n
- ❌ Canva API — MVP usa templates manuales
- ❌ Make.com — n8n cubre todo sin límite de ejecuciones
