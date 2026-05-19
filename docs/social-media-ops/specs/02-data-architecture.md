# Bloque 5: Arquitectura de Datos

## Convenciones

| Regla | Valor |
|:------|:------|
| **Naming** | snake_case, prefijo por módulo |
| **IDs** | Auto-incremento numérico (Google Sheets row number) |
| **Fechas** | ISO 8601: `YYYY-MM-DD` |
| **Estados** | Siempre en MAYÚSCULAS: `IDEA`, `DRAFT`, `REVIEW`, `APPROVED`, `PUBLISHED`, `ARCHIVED` |
| **Booleanos** | `TRUE` / `FALSE` |

---

## Tabla 1: `IDEAS` — Banco de ideas y backlog

| Campo | Tipo | Ejemplo | Notas |
|:------|:-----|:--------|:------|
| `idea_id` | Number (auto) | 1 | Row number |
| `fecha_ingreso` | Date | 2026-05-16 | Fecha de captura |
| `fuente` | Single Select | `ICP_DOLOR`, `NOTICIA`, `TRENDING`, `RECICLAJE`, `MANUAL` | Origen de la idea |
| `tema_raw` | Text | "Qué pasa si no declaro renta" | Idea cruda sin procesar |
| `pilar` | Single Select | `CLARIDAD`, `PROTECCION`, `ACCION`, `COMUNIDAD` | Pilar editorial |
| `angulo` | Text | "El mito de la zona gris para freelancers" | Ángulo específico sugerido por IA |
| `formato_sugerido` | Single Select | `TEXTO_IMAGEN`, `CARRUSEL`, `VIDEO_CORTO`, `STORYTELLING` | Formato recomendado |
| `dolor_icp` | Single Select | `MIEDO_DIAN`, `SORPRESA_TRIBUTARIA`, `DESORDEN`, `JERGA_OPACA`, `CEGUERA_CAJA`, `FORMALIZACION` | Dolor que ataca |
| `score_potencial` | Number (1-10) | 8 | Score de potencial estimado por IA |
| `status` | Single Select | `NUEVA`, `SELECCIONADA`, `DESCARTADA`, `USADA` | Estado |
| `notas` | Text | "Podría ser carrusel con 5 mitos" | Notas libres |

**Vistas sugeridas:**
- `Backlog` — Todas las ideas con status NUEVA, ordenadas por score_potencial desc
- `Por Pilar` — Agrupadas por pilar editorial
- `Por Dolor` — Agrupadas por dolor_icp

---

## Tabla 2: `CALENDARIO` — Calendario editorial semanal

| Campo | Tipo | Ejemplo | Notas |
|:------|:-----|:--------|:------|
| `cal_id` | Number (auto) | 1 | Row number |
| `semana` | Number | 1 | Semana del mes (1-4) |
| `fecha_publicacion` | Date | 2026-05-19 | Fecha planificada |
| `dia_semana` | Text | Lunes | Calculado |
| `idea_id` | Number | 5 | Referencia a tabla IDEAS |
| `pilar` | Single Select | `CLARIDAD` | Heredado de idea |
| `formato` | Single Select | `CARRUSEL` | Formato final decidido |
| `titulo_trabajo` | Text | "5 mitos de la zona gris online" | Título interno de trabajo |
| `status` | Single Select | `PLANIFICADO`, `EN_PRODUCCION`, `DRAFT`, `REVIEW`, `APPROVED`, `PUBLISHED` | Estado del contenido |
| `responsable` | Text | "Operador" | Quién lo ejecuta |
| `notas_editoriales` | Text | "Incluir dato del 70% de mortalidad empresarial" | Notas para producción |

**Vistas sugeridas:**
- `Semana Actual` — Filtro por semana actual
- `Kanban` — Agrupado por status
- `Calendario` — Vista de calendario por fecha_publicacion

---

## Tabla 3: `CONTENIDO` — Pipeline de producción

| Campo | Tipo | Ejemplo | Notas |
|:------|:-----|:--------|:------|
| `content_id` | Number (auto) | 1 | Row number |
| `cal_id` | Number | 3 | Referencia a CALENDARIO |
| `hook` | Text | "¿Sabías que la DIAN ya sabe cuánto vendes por Instagram?" | Gancho generado |
| `hook_alt_1` | Text | "El 70% de los negocios digitales quiebra por esto..." | Alternativa 1 |
| `hook_alt_2` | Text | "Tu contador no te va a decir esto, pero..." | Alternativa 2 |
| `hook_seleccionado` | Single Select | `PRINCIPAL`, `ALT_1`, `ALT_2` | Cuál se eligió |
| `copy_body` | Long Text | (Cuerpo del post completo) | Copy principal |
| `cta` | Text | "¿Cuánto de tu plata es realmente tuya? Escríbenos 'CLARIDAD'" | Call to action |
| `hashtags` | Text | "#ContabilidadDigital #DIAN #Contexia" | Hashtags sugeridos |
| `guion_video` | Long Text | (Guión completo si es video) | Solo si formato = VIDEO |
| `notas_visual` | Text | "Usar paleta azul oscuro + datos grandes" | Indicaciones para diseño |
| `asset_url` | URL | https://drive.google.com/... | Link al asset en Drive |
| `version` | Number | 2 | Número de versión del contenido |
| `status` | Single Select | `BORRADOR_IA`, `EDITADO_HUMANO`, `APROBADO`, `LISTO_PUBLICAR` | Estado |
| `fecha_aprobacion` | Date | 2026-05-18 | Cuándo se aprobó |
| `aprobado_por` | Text | "Operador" | Quién aprobó |
| `qa_humanizacion` | Boolean | TRUE | ¿Pasó checklist de humanización? |

**Vistas sugeridas:**
- `Por Aprobar` — status = BORRADOR_IA o EDITADO_HUMANO
- `Listos para Publicar` — status = APROBADO o LISTO_PUBLICAR
- `Historial` — Todo el contenido con versión

---

## Tabla 4: `PUBLICACIONES` — Registro de posts publicados

| Campo | Tipo | Ejemplo | Notas |
|:------|:-----|:--------|:------|
| `pub_id` | Number (auto) | 1 | Row number |
| `content_id` | Number | 3 | Referencia a CONTENIDO |
| `fecha_publicacion_real` | DateTime | 2026-05-19 10:00 | Fecha y hora real |
| `plataforma` | Single Select | `FACEBOOK` | Siempre FB en MVP |
| `url_post` | URL | https://facebook.com/... | Link directo al post |
| `tipo_publicacion` | Single Select | `TEXTO_IMAGEN`, `CARRUSEL`, `VIDEO`, `LINK` | Tipo real publicado |
| `notas_publicacion` | Text | "Se publicó con ligera edición del CTA" | Notas del operador |

---

## Tabla 5: `METRICAS` — Métricas por publicación

| Campo | Tipo | Ejemplo | Notas |
|:------|:-----|:--------|:------|
| `metric_id` | Number (auto) | 1 | Row number |
| `pub_id` | Number | 1 | Referencia a PUBLICACIONES |
| `fecha_captura` | Date | 2026-05-21 | Fecha de recolección (48h post publicación) |
| `alcance` | Number | 1250 | Personas alcanzadas |
| `impresiones` | Number | 2100 | Veces mostrado |
| `reacciones` | Number | 45 | Likes, loves, etc. |
| `comentarios` | Number | 12 | Comentarios totales |
| `compartidos` | Number | 8 | Shares |
| `clics_link` | Number | 23 | Clics en enlaces (si aplica) |
| `guardados` | Number | 15 | Saves |
| `engagement_rate` | Number (%) | 4.8 | Fórmula: (reacciones+comentarios+compartidos+guardados)/alcance*100 |
| `score` | Number (1-100) | 72 | Score compuesto calculado |
| `clasificacion` | Single Select | `GANADOR`, `PROMEDIO`, `PERDEDOR` | Basado en score |
| `insight_ia` | Text | "El hook con pregunta directa tuvo 3x más engagement" | Análisis generado por IA |

**Fórmula del Score:**
```
score = (engagement_rate * 30) + (alcance_normalizado * 25) + (compartidos_normalizado * 25) + (comentarios_normalizado * 20)
```

**Clasificación:**
- **GANADOR**: score ≥ 70
- **PROMEDIO**: score 40-69
- **PERDEDOR**: score < 40

---

## Tabla 6: `PROMPTS` — Biblioteca de prompts versionados

| Campo | Tipo | Ejemplo | Notas |
|:------|:-----|:--------|:------|
| `prompt_id` | Text | `PRM-HOOK-01` | ID manual con prefijo |
| `nombre` | Text | "Generador de Hooks Empáticos" | Nombre descriptivo |
| `categoria` | Single Select | `HOOK`, `COPY`, `CTA`, `GUION`, `ANALISIS`, `REESCRITURA`, `INVESTIGACION` | Tipo de prompt |
| `version` | Number | 3 | Versión actual |
| `prompt_text` | Long Text | (Texto completo del prompt) | El prompt |
| `variables` | Text | "{{tema}}, {{dolor_icp}}, {{pilar}}" | Variables que recibe |
| `modelo_recomendado` | Text | "Gemini 1.5 Pro" | LLM recomendado |
| `temperatura` | Number | 0.7 | Temperatura sugerida |
| `ultima_edicion` | Date | 2026-05-16 | Fecha de última edición |
| `performance_notes` | Text | "v3 mejoró tono empático 40%" | Notas sobre rendimiento |

---

## Tabla 7: `INSIGHTS` — Análisis semanales

| Campo | Tipo | Ejemplo | Notas |
|:------|:-----|:--------|:------|
| `insight_id` | Number (auto) | 1 | Row number |
| `semana` | Number | 1 | Semana analizada |
| `fecha_analisis` | Date | 2026-05-23 | Fecha del análisis |
| `top_post_id` | Number | 3 | pub_id del mejor post |
| `top_hook_tipo` | Text | "Pregunta directa con dato" | Patrón del mejor hook |
| `top_pilar` | Text | CLARIDAD | Pilar que mejor funcionó |
| `top_formato` | Text | CARRUSEL | Formato que mejor funcionó |
| `top_dolor` | Text | MIEDO_DIAN | Dolor con más resonancia |
| `resumen_ia` | Long Text | (Análisis completo generado por IA) | Resumen semanal |
| `recomendacion_siguiente` | Long Text | "Duplicar carruseles sobre DIAN, probar storytelling de caso real" | Recomendación para próxima semana |
| `accion_tomada` | Text | "Se agregaron 3 ideas de carrusel DIAN al backlog" | Qué se hizo con la recomendación |

---

## Relaciones entre tablas

```
IDEAS ──(idea_id)──→ CALENDARIO
CALENDARIO ──(cal_id)──→ CONTENIDO
CONTENIDO ──(content_id)──→ PUBLICACIONES
PUBLICACIONES ──(pub_id)──→ METRICAS
METRICAS ──(análisis)──→ INSIGHTS
INSIGHTS ──(recomendación)──→ IDEAS (ciclo cerrado)
```

## Estructura en Google Sheets (MVP)

Cada tabla = 1 pestaña (tab) en el mismo Google Sheet:
1. `IDEAS`
2. `CALENDARIO`
3. `CONTENIDO`
4. `PUBLICACIONES`
5. `METRICAS`
6. `PROMPTS`
7. `INSIGHTS`
8. `DASHBOARD` (pestaña con fórmulas y gráficos)
