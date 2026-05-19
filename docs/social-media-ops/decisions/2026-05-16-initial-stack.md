# Decision: Stack Inicial del Proyecto

- **Fecha:** 2026-05-16
- **Estado:** Aprobado
- **Decidido por:** Dirección Contexia + Antigravity

## Contexto
Necesitamos un stack que permita a una sola persona operar un sistema de contenidos orgánicos para Facebook en 7 días, con costo mínimo y máxima flexibilidad.

## Decisión
- **Orquestación:** n8n (self-hosted o cloud)
- **Base de datos MVP:** Google Sheets
- **Base de datos Fase 2:** Airtable
- **LLM:** Gemini 1.5 Pro
- **Almacenamiento:** Google Drive
- **Publicación:** Manual asistida (Meta API requiere App Review)
- **Aprobación:** Gmail notifications
- **Dashboard:** Google Sheets con fórmulas y formato condicional

## Alternativas consideradas
| Herramienta | Descartada por |
|:------------|:---------------|
| Make.com | Límites de ejecución en plan gratuito |
| Zapier | Costo alto para volumen de workflows |
| Airtable (MVP) | Agrega complejidad innecesaria para día 1; se migra en Fase 2 |
| Notion | No tiene API robusta para n8n ni vistas de calendario con automatización |
| Meta Graph API directa | Requiere App Review riguroso; workaround manual es más rápido para MVP |

## Consecuencias
- Google Sheets tiene límites de 10M celdas y no tiene relaciones nativas → migración a Airtable planificada
- Publicación manual agrega ~2 min por post → aceptable para 3 posts/semana
- Gmail no tiene botones de aprobación nativos → se usan enlaces en el correo

## Riesgos
- Si el volumen de datos crece rápido, Sheets puede ralentizarse → trigger de migración: >500 filas en cualquier tabla
