# Bloque 12: Roadmap de Implementación

---

## Datos confirmados post-discovery

| Campo | Valor confirmado |
|:------|:----------------|
| DB | **Airtable** |
| Frecuencia | **2 posts/semana** (8/mes) |
| Publicación | **Semiautomática** (programar tras aprobación) |
| Métricas | **Meta API** (integración directa) |
| Aprobación | **Gmail** (jpelaezcardenas@gmail.com) |
| Formatos | **CTA/interacción** + shadow audit temático |
| Autonomía | **Puede programar tras aprobación** |
| Dashboard | **Sí desde MVP** |
| Detección ganadores | **Sí desde MVP** |
| Contenido a evitar | Técnico, vendedor, genérico, informal |
| Voz | **Balanceado** (empático + estratégico + educativo) |

---

## Orden de implementación (7 días)

### Día 1: Infraestructura
- [ ] Crear base en Airtable con las 7 tablas (ver spec 02)
- [ ] Configurar vistas: Backlog, Kanban, Calendario, Dashboard
- [ ] Crear cuenta n8n (cloud o self-hosted)
- [ ] Obtener API key de Gemini 1.5 Pro
- [ ] Configurar credenciales en n8n: Airtable, Gmail, Gemini
- [ ] Verificar acceso a Facebook Page

### Día 2: Content Engine Core
- [ ] Implementar WF-01: Intake de Ideas (webhook + Airtable append)
- [ ] Implementar WF-04: Draft Creator (Airtable read → Gemini → Airtable write)
- [ ] Cargar prompts PRM-HOOK-01, PRM-COPY-01, PRM-STORY-01 en tabla PROMPTS
- [ ] Test: ingresar 3 ideas → generar 3 borradores

### Día 3: QA + Notificación
- [ ] Implementar WF-05: QA de Humanización (Gemini + PRM-QA-01)
- [ ] Implementar WF-06: Notificación Gmail
- [ ] Test end-to-end: idea → borrador → QA → email a jpelaezcardenas@gmail.com

### Día 4: Generación Inteligente
- [ ] Implementar WF-02: Generación Semanal de Ideas (Schedule + Gemini)
- [ ] Implementar WF-03: Enriquecimiento de Ideas
- [ ] Cargar prompts PRM-RESEARCH-01, PRM-CARRUSEL-01, PRM-VIDEO-01
- [ ] Test: generar 9 ideas → enriquecer → seleccionar top 2

### Día 5: Publicación + Logging
- [ ] Configurar Meta Graph API (si App Review disponible) o workaround con Creator Studio
- [ ] Implementar WF-07: Logging de Publicación
- [ ] Crear vista "Listos para Publicar" en Airtable
- [ ] Test: aprobar borrador → programar → registrar publicación

### Día 6: Métricas + Scoring
- [ ] Implementar WF-08: Captura de Métricas (Meta API o manual)
- [ ] Implementar WF-09: Scoring de Posts
- [ ] Configurar Dashboard en Airtable (vistas + fórmulas)
- [ ] Test: ingresar métricas → calcular score → clasificar ganador/perdedor

### Día 7: Análisis + Go-Live
- [ ] Implementar WF-10: Análisis Semanal + Retroalimentación
- [ ] Cargar prompt PRM-ANALYSIS-01, PRM-RECYCLE-01
- [ ] Poblar calendario editorial semana 1
- [ ] Test completo end-to-end
- [ ] QA de humanización en todos los borradores de semana 1
- [ ] **GO-LIVE: publicar primer post**

---

## Quick Wins (primeras 5 automatizaciones)

| # | Workflow | Tiempo | Valor |
|:--|:---------|:-------|:------|
| 1 | WF-01 Intake de Ideas | 30 min | Alimenta el sistema |
| 2 | WF-04 Draft Creator | 2h | Core del engine |
| 3 | WF-05 QA Humanización | 1h | Garantiza calidad |
| 4 | WF-06 Notificación | 30 min | Conecta IA con humano |
| 5 | WF-09 Scoring | 1h | Detecta ganadores |

---

## Credenciales necesarias

| Servicio | Qué se necesita | Cómo obtenerla |
|:---------|:----------------|:---------------|
| **Airtable** | API key + Base ID | Settings → API → Personal access token |
| **Gemini** | API key | Google AI Studio → API Keys |
| **Gmail** | OAuth2 credentials | n8n credential: Google OAuth2 |
| **Facebook** | Page Access Token | Meta Business Suite → Settings → Tokens |
| **n8n** | Instance URL + account | n8n.cloud signup o self-hosted |

---

## Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|:-------|:--------|:-----------|
| Meta App Review toma semanas | Alto | Workaround: usar Creator Studio para programar manualmente; n8n genera post listo |
| Gemini genera contenido genérico | Medio | Guardrails de marca en cada prompt + QA automático |
| Airtable free tier tiene 1000 registros | Bajo | Suficiente para 6+ meses; migrar a Pro si escala |
| Una persona se satura con 2 posts/semana | Bajo | Batch semanal: todo se genera el lunes, se publica L/J |

---

## Decisiones pendientes

| # | Decisión | Urgencia | Default si no se decide |
|:--|:---------|:---------|:-----------------------|
| 1 | ¿Facebook Page ya existe? | 🔴 Día 1 | Crear una nueva |
| 2 | ¿n8n cloud o self-hosted? | 🔴 Día 1 | Cloud (free tier) |
| 3 | ¿Tienes Airtable account? | 🔴 Día 1 | Crear free account |
| 4 | ¿Tienes Gemini API key? | 🔴 Día 2 | Crear en AI Studio (free) |
| 5 | ¿Auditoría Sombra como formato de contenido recurrente? | 🟡 Día 4 | Sí, 1 post/mes tipo shadow audit |

---

## Checklist de Go-Live

### Build
- [ ] 7 tablas creadas en Airtable
- [ ] 10 workflows activos en n8n
- [ ] 9 prompts cargados en tabla PROMPTS
- [ ] Credenciales configuradas y testeadas
- [ ] Calendario semana 1 poblado

### QA
- [ ] Cada borrador pasó checklist de humanización
- [ ] Ningún post usa palabras prohibidas
- [ ] Todos los hooks tienen <120 caracteres
- [ ] CTAs invitan a conversación, no a compra
- [ ] Tono verificado: cercano sin caricatura

### Go-Live
- [ ] Primer post publicado
- [ ] Logging registrado en Airtable
- [ ] Workflow de métricas programado
- [ ] Operador sabe cómo aprobar/rechazar borradores
- [ ] PLAN.md actualizado con status "🟢 Live"
