# Bloque 6: Workflows n8n

## Mapa de workflows

| ID | Nombre | Trigger | Frecuencia |
|:---|:-------|:--------|:-----------|
| WF-01 | Intake de Ideas | Manual / Webhook | Ad-hoc |
| WF-02 | Generación Semanal de Ideas | Schedule (Lunes 7am) | Semanal |
| WF-03 | Enriquecimiento de Ideas | Automático post WF-02 | Semanal |
| WF-04 | Creación de Borrador | Schedule (Lunes 9am) | Semanal |
| WF-05 | QA de Humanización | Automático post WF-04 | Por borrador |
| WF-06 | Notificación para Revisión | Automático post WF-05 | Por borrador |
| WF-07 | Logging de Publicación | Manual trigger | Por post |
| WF-08 | Captura de Métricas | Schedule (Viernes 10am) | Semanal |
| WF-09 | Scoring de Posts | Automático post WF-08 | Semanal |
| WF-10 | Análisis Semanal + Retroalimentación | Schedule (Viernes 3pm) | Semanal |

---

## WF-01: Intake de Ideas

- **Nombre:** `ctx-intake-ideas`
- **Objetivo:** Capturar ideas rápidas desde cualquier fuente y agregarlas al backlog
- **Trigger:** Webhook (para integraciones externas) o Manual
- **Inputs:** `tema_raw` (obligatorio), `fuente` (opcional), `notas` (opcional)

**Nodos:**
1. `Webhook/Manual Trigger` — Recibe idea
2. `Set` — Normaliza datos: agrega fecha_ingreso, status=NUEVA, fuente default=MANUAL
3. `Google Sheets (Append)` — Escribe nueva fila en pestaña IDEAS
4. `Respond` — Confirma "Idea #X registrada"

**Validaciones:**
- `tema_raw` no puede estar vacío → si vacío, retorna error
- Deduplicación: buscar si el tema ya existe (fuzzy match opcional en Fase 2)

**Errores comunes:**
- Google Sheets API rate limit → retry con backoff
- Campo vacío → respuesta de error clara

**Cambios en DB:** Agrega 1 fila a `IDEAS`
**Acción humana:** Ninguna

---

## WF-02: Generación Semanal de Ideas

- **Nombre:** `ctx-idea-generator`
- **Objetivo:** Generar 6-9 ideas nuevas basadas en dolores del ICP y tendencias
- **Trigger:** Schedule — Lunes 7:00 AM COT

**Nodos:**
1. `Schedule Trigger` — Lunes 7am
2. `Google Sheets (Read)` — Leer últimos INSIGHTS (recomendaciones de la semana anterior)
3. `Google Sheets (Read)` — Leer IDEAS con status=USADA y score alto (patrones ganadores)
4. `Gemini (Chat)` — Prompt: "Genera 9 ideas de contenido para Contexia..."
   - Variables: `{{dolores_icp}}`, `{{pilares}}`, `{{patrones_ganadores}}`, `{{recomendaciones_previas}}`
   - Output: JSON array con 9 objetos {tema, pilar, formato_sugerido, dolor_icp, score_potencial}
5. `Code (JSON Parse)` — Parsear respuesta del LLM
6. `SplitInBatches` — Procesar cada idea
7. `Google Sheets (Append)` — Escribir cada idea en pestaña IDEAS

**Validaciones:**
- Verificar que el LLM devolvió JSON válido
- Verificar que hay al menos 6 ideas
- Verificar que hay diversidad de pilares (no todos del mismo pilar)

**Errores comunes:**
- LLM devuelve texto libre en vez de JSON → prompt con instrucción estricta de formato
- API timeout → retry x3

**Cambios en DB:** Agrega 6-9 filas a `IDEAS`
**Acción humana:** Ninguna (las ideas se revisan en WF-03 o manualmente)

---

## WF-03: Enriquecimiento de Ideas

- **Nombre:** `ctx-idea-enrichment`
- **Objetivo:** Tomar ideas con status NUEVA y agregarles ángulo + score
- **Trigger:** Automático — se ejecuta después de WF-02

**Nodos:**
1. `Google Sheets (Read)` — Leer IDEAS con status=NUEVA y sin ángulo
2. `SplitInBatches` — Procesar cada idea
3. `Gemini (Chat)` — Prompt de enriquecimiento:
   - Input: `{{tema_raw}}`, `{{dolor_icp}}`
   - Output: `{angulo, score_potencial, formato_sugerido, hook_preview}`
4. `Google Sheets (Update)` — Actualizar la fila con ángulo y score
5. `IF` — Si score ≥ 7, marcar status=SELECCIONADA

**Cambios en DB:** Actualiza campos angulo, score_potencial, formato_sugerido en `IDEAS`
**Acción humana:** Revisar ideas SELECCIONADAS y confirmar cuáles van al calendario

---

## WF-04: Creación de Borrador

- **Nombre:** `ctx-draft-creator`
- **Objetivo:** Generar hook + copy + CTA + guión para cada post de la semana
- **Trigger:** Schedule — Lunes 9:00 AM COT (después de que ideas estén seleccionadas)

**Nodos:**
1. `Schedule Trigger` — Lunes 9am
2. `Google Sheets (Read)` — Leer CALENDARIO: posts de la semana actual con status=PLANIFICADO
3. `SplitInBatches` — Procesar cada post
4. `Google Sheets (Read)` — Leer idea asociada (idea_id)
5. `Switch` — Según formato: TEXTO_IMAGEN, CARRUSEL, VIDEO_CORTO, STORYTELLING
6. `Gemini (Chat)` — Prompt específico por formato:
   - Variables: `{{tema}}`, `{{angulo}}`, `{{dolor_icp}}`, `{{pilar}}`, `{{formato}}`
   - Output: `{hook, hook_alt_1, hook_alt_2, copy_body, cta, hashtags, guion_video (si aplica), notas_visual}`
7. `Code (Parse)` — Parsear respuesta
8. `Google Sheets (Append)` — Escribir en pestaña CONTENIDO
9. `Google Sheets (Update)` — Actualizar CALENDARIO: status=DRAFT

**Validaciones:**
- Copy body entre 100-500 caracteres para FB
- Hook máximo 120 caracteres
- CTA presente y no vacío
- Si formato=VIDEO, guion_video no puede estar vacío

**Errores comunes:**
- LLM genera copy demasiado largo → instrucción de límite en prompt
- LLM genera contenido genérico → guardrails de marca en prompt

**Cambios en DB:** Agrega filas a `CONTENIDO`, actualiza status en `CALENDARIO`
**Acción humana:** Ninguna (la revisión viene en WF-06)

---

## WF-05: QA de Humanización

- **Nombre:** `ctx-humanization-qa`
- **Objetivo:** Verificar que el contenido NO suena robótico y cumple la voz Contexia
- **Trigger:** Automático — se ejecuta después de WF-04 por cada borrador

**Nodos:**
1. `Google Sheets (Read)` — Leer CONTENIDO con status=BORRADOR_IA
2. `SplitInBatches` — Procesar cada borrador
3. `Gemini (Chat)` — Prompt de QA:
   - Input: `{{copy_body}}`, `{{hook}}`, `{{cta}}`
   - Output: `{es_humano: bool, problemas: string[], version_reescrita: string (si no es humano)}`
4. `IF` — Si es_humano=false:
   - `Google Sheets (Update)` — Reemplazar copy con version_reescrita, incrementar version
5. `Google Sheets (Update)` — Marcar qa_humanizacion=TRUE

**Checklist interno del prompt QA:**
- ¿Suena como amiga o como bot?
- ¿Tiene jerga opaca (base gravable, causación, impuesto diferido)?
- ¿El CTA es protector o agresivo?
- ¿Un emprendedor de 25 años lo entendería?
- ¿Suena colombiano sin ser caricatura?

**Cambios en DB:** Actualiza copy_body (si reescrito), qa_humanizacion en `CONTENIDO`
**Acción humana:** Ninguna

---

## WF-06: Notificación para Revisión

- **Nombre:** `ctx-review-notify`
- **Objetivo:** Enviar borradores listos al operador para revisión humana
- **Trigger:** Automático — después de WF-05

**Nodos:**
1. `Google Sheets (Read)` — Leer CONTENIDO con qa_humanizacion=TRUE y status=BORRADOR_IA
2. `Code` — Formatear email con todos los borradores de la semana
3. `Gmail (Send)` — Enviar email con:
   - Asunto: "📝 Contexia Content OS — 3 borradores listos para revisar (Semana X)"
   - Cuerpo: tabla con hook, copy preview, formato, link a Sheets
4. `Google Sheets (Update)` — status de cada borrador → REVIEW

**Cambios en DB:** Actualiza status a REVIEW en `CONTENIDO`
**Acción humana:** Operador revisa email, va a Sheets, edita si necesario, cambia status a APROBADO

---

## WF-07: Logging de Publicación

- **Nombre:** `ctx-publish-log`
- **Objetivo:** Registrar un post como publicado con su URL
- **Trigger:** Manual (el operador lo activa después de publicar)

**Nodos:**
1. `Manual Trigger` o `Webhook`
2. `Input` — content_id, url_post, fecha_publicacion_real
3. `Google Sheets (Append)` — Agregar fila a PUBLICACIONES
4. `Google Sheets (Update)` — CONTENIDO: status=LISTO_PUBLICAR → (no cambia, ya publicado)
5. `Google Sheets (Update)` — CALENDARIO: status=PUBLISHED

**Cambios en DB:** Agrega fila a `PUBLICACIONES`, actualiza `CALENDARIO` y `CONTENIDO`
**Acción humana:** Operador provee URL del post y activa el workflow

---

## WF-08: Captura de Métricas

- **Nombre:** `ctx-metrics-capture`
- **Objetivo:** Registrar métricas de los posts publicados en la semana
- **Trigger:** Schedule — Viernes 10:00 AM COT

**Nodos (MVP — manual asistido):**
1. `Schedule Trigger` — Viernes 10am
2. `Google Sheets (Read)` — Leer PUBLICACIONES de la semana sin métricas
3. `Gmail (Send)` — Enviar recordatorio al operador:
   - "📊 Es viernes — hora de capturar métricas de los 3 posts de esta semana"
   - Incluir links directos a cada post de Facebook
   - Incluir link a la pestaña METRICAS del Sheet
4. *(Operador ingresa métricas manualmente en Sheets)*

**Nodos (Fase 2 — Meta API):**
1. `Schedule Trigger`
2. `HTTP Request` — Llamar Meta Graph API por cada post_id
3. `Code` — Parsear métricas
4. `Google Sheets (Append)` — Escribir métricas

**Cambios en DB:** Agrega filas a `METRICAS` (manual en MVP)
**Acción humana:** Operador ingresa alcance, reacciones, comentarios, compartidos, guardados

---

## WF-09: Scoring de Posts

- **Nombre:** `ctx-post-scoring`
- **Objetivo:** Calcular score compuesto y clasificar cada post
- **Trigger:** Automático — cuando se detectan métricas nuevas (o Schedule Viernes 11am)

**Nodos:**
1. `Google Sheets (Read)` — Leer METRICAS sin score calculado
2. `Code` — Calcular por cada post:
   ```
   engagement_rate = (reacciones + comentarios + compartidos + guardados) / alcance * 100
   score = (engagement_rate * 30) + (alcance_norm * 25) + (compartidos_norm * 25) + (comentarios_norm * 20)
   clasificacion = score >= 70 ? "GANADOR" : score >= 40 ? "PROMEDIO" : "PERDEDOR"
   ```
3. `Google Sheets (Update)` — Escribir engagement_rate, score, clasificacion en METRICAS

**Cambios en DB:** Actualiza engagement_rate, score, clasificacion en `METRICAS`
**Acción humana:** Ninguna

---

## WF-10: Análisis Semanal + Retroalimentación

- **Nombre:** `ctx-weekly-analysis`
- **Objetivo:** Generar análisis semanal e inyectar recomendaciones al siguiente ciclo
- **Trigger:** Schedule — Viernes 3:00 PM COT

**Nodos:**
1. `Schedule Trigger` — Viernes 3pm
2. `Google Sheets (Read)` — Leer METRICAS de la semana con scores
3. `Google Sheets (Read)` — Leer CONTENIDO asociado (hooks, pilares, formatos)
4. `Gemini (Chat)` — Prompt de análisis:
   - Input: `{{metricas_semana}}`, `{{contenido_semana}}`, `{{pilares}}`, `{{formatos}}`
   - Output: `{resumen, top_hook_tipo, top_pilar, top_formato, top_dolor, recomendacion_siguiente}`
5. `Google Sheets (Append)` — Escribir en INSIGHTS
6. `Gmail (Send)` — Enviar resumen semanal al operador:
   - "📈 Resumen Semana X — Tu mejor post fue [título] con score [X]"
   - Incluir recomendaciones para la próxima semana
7. `Google Sheets (Append)` — Agregar 3 ideas nuevas a IDEAS basadas en la recomendación (cierre del ciclo)

**Cambios en DB:** Agrega fila a `INSIGHTS`, agrega ideas a `IDEAS`
**Acción humana:** Operador lee resumen y decide qué ajustar

---

## Orden de implementación (primeras 5)

| Prioridad | Workflow | Razón |
|:----------|:---------|:------|
| 1 | WF-01 Intake | Base para alimentar el sistema |
| 2 | WF-04 Draft Creator | Core del Content Engine |
| 3 | WF-05 QA Humanización | Garantiza calidad de marca |
| 4 | WF-06 Notificación | Conecta IA con humano |
| 5 | WF-02 Idea Generator | Automatiza la investigación |
