# Bloque 10: Métricas y Analítica + Bloque 11: Dashboard

---

## Métricas por Post

| Métrica | Valor | Unidad | Fuente | Cuándo capturar |
|:--------|:------|:-------|:-------|:----------------|
| `alcance` | Número | personas | Facebook Insights | 48h post publicación |
| `impresiones` | Número | veces mostrado | Facebook Insights | 48h post publicación |
| `reacciones` | Número | likes+loves+etc | Facebook Insights | 48h post publicación |
| `comentarios` | Número | comentarios | Facebook Insights | 48h post publicación |
| `compartidos` | Número | shares | Facebook Insights | 48h post publicación |
| `guardados` | Número | saves | Facebook Insights | 48h post publicación |
| `clics_link` | Número | clics | Facebook Insights | 48h post publicación |
| `engagement_rate` | % | porcentaje | Calculado | Automático |
| `score` | 1-100 | puntos | Calculado | Automático |

## Fórmula del Score Compuesto

```
engagement_rate = (reacciones + comentarios + compartidos + guardados) / alcance × 100

score = (engagement_rate × 30) + (alcance_normalizado × 25) + (compartidos_normalizado × 25) + (comentarios_normalizado × 20)
```

**Normalización:** cada métrica se normaliza contra el máximo del mes → valor / max_del_mes × 100

## Clasificación

| Clasificación | Score | Acción |
|:-------------|:------|:-------|
| **GANADOR** | ≥ 70 | Reciclar: crear variaciones. Analizar qué funcionó |
| **PROMEDIO** | 40-69 | Mantener: ajustar hook o formato y reprobar |
| **PERDEDOR** | < 40 | Matar: no repetir este ángulo/formato |

## Métricas Semanales

| Métrica | Cálculo |
|:--------|:--------|
| `posts_publicados` | Count de posts con status=PUBLISHED en la semana |
| `alcance_total_semana` | Sum(alcance) de la semana |
| `engagement_promedio` | Avg(engagement_rate) de la semana |
| `mejor_post` | Post con score más alto |
| `peor_post` | Post con score más bajo |
| `pilar_ganador` | Pilar con mejor score promedio |
| `formato_ganador` | Formato con mejor score promedio |

## KPIs del Mes

| KPI | Meta Mes 1 | Unidad | Fecha evaluación |
|:----|:-----------|:-------|:-----------------|
| Seguidores nuevos | +100 | seguidores | Fin de mes |
| Alcance total | 5,000 | personas | Fin de mes |
| Engagement rate promedio | ≥ 3% | porcentaje | Fin de mes |
| Posts publicados | 12 | posts | Fin de mes |
| Posts ganadores | ≥ 3 | posts (score≥70) | Fin de mes |
| Tasa de cumplimiento calendario | ≥ 90% | porcentaje | Fin de mes |

## Métricas que NO valen la pena todavía
- ❌ CPM / CPC (no hay pauta)
- ❌ Conversiones a lead (no hay funnel aún)
- ❌ Brand lift (necesita baseline)
- ❌ Sentiment analysis (volumen muy bajo)

## Detección de Falsos Positivos
- Un post con muchas reacciones pero 0 compartidos puede ser "entretenido pero no valioso"
- Un post con pocos likes pero muchos saves es "contenido de referencia" → valioso
- Ponderación de `compartidos` y `guardados` más alta para compensar

---

# Dashboard Mínimo (Pestaña DASHBOARD en Google Sheets)

## Sección 1: Resumen Ejecutivo
| Campo | Valor (fórmula) |
|:------|:----------------|
| Semana actual | =WEEKNUM(TODAY()) |
| Posts publicados esta semana | =COUNTIFS(...) |
| Engagement promedio semana | =AVERAGEIFS(...) |
| Mejor post semana | =INDEX(MATCH(MAX(...))) |
| Score promedio mes | =AVERAGE(METRICAS!score) |

## Sección 2: Ranking por Post (Top 5)
Tabla ordenada por score descendente con: título, pilar, formato, score, clasificación

## Sección 3: Ranking por Pilar
| Pilar | Posts | Score Promedio | Engagement Promedio |
|:------|:------|:---------------|:--------------------|
| CLARIDAD | =COUNTIF | =AVERAGEIF | =AVERAGEIF |
| PROTECCIÓN | ... | ... | ... |
| ACCIÓN | ... | ... | ... |
| COMUNIDAD | ... | ... | ... |

## Sección 4: Ranking por Formato
Misma estructura que pilares pero agrupado por formato

## Sección 5: Tendencia Semanal
Gráfico de línea (sparkline en Sheets): engagement_rate por semana

## Sección 6: Alertas
- 🔴 Si engagement < 2% → "Revisar hooks y formatos"
- 🟡 Si 0 posts publicados en la semana → "Calendario atrasado"
- 🟢 Si hay post GANADOR → "¡Reciclar este contenido!"

## Sección 7: Insights Accionables
- "Repetir: [pilar ganador] + [formato ganador]"
- "Mejorar: [pilar perdedor] necesita nuevo ángulo"
- "Matar: [formato con peor engagement] no está funcionando"
