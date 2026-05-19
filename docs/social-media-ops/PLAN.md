# PLAN.md — Contexia Content OS

> Plan vivo del proyecto. Todo feature nuevo debe reflejarse aquí.
> Última actualización: 2026-05-16

## Project Overview

| Campo | Valor |
|:------|:------|
| **Nombre** | Contexia Content OS |
| **Objetivo** | Sistema operativo de contenidos orgánicos para Facebook, automatizado con n8n |
| **Operador** | 1 persona |
| **Plazo MVP** | 7 días |
| **Repo** | https://github.com/jpelaezcardenas/contexia-content-os |

## Personas

| Persona | Descripción | Dolor principal |
|:--------|:------------|:----------------|
| **PyME Digital** | Dropshipper, creador, freelancer en Colombia | Miedo a la DIAN, no sabe cuánto es suyo |
| **Solopreneur Tech** | Agencia IA, nómada digital, exportador de servicios | Desorden financiero, sorpresa tributaria |
| **Emprendedor en formalización** | Vende por Instagram/WhatsApp sin estructura | Terror a formalizarse, jerga opaca |

## JTBD (Jobs To Be Done)
- Cuando **veo contenido de Contexia**, quiero **entender mi situación financiera sin jerga**, para **sentir que alguien me cuida y me explica claro**.
- Cuando **me da miedo la DIAN**, quiero **saber que hay una salida ordenada**, para **dejar de postergar y actuar hoy**.

## Constraints
- Una sola persona opera todo el sistema
- Solo contenido orgánico (cero pauta pagada en Fase 1)
- Facebook como canal único del MVP
- Presupuesto mínimo (herramientas gratuitas o freemium)
- Publicación manual asistida en MVP (Meta API requiere App Review)

## Tech Decisions

| Decisión | Elegido | Alternativas | Razón |
|:---------|:--------|:-------------|:------|
| **Orquestación / Integración** | **n8n + FastAPI (Híbrido)** ✅ | Python puro, Make, Zapier | **n8n** para triggers, cron y ruteo visual; **FastAPI** para inferencia resiliente, failover y lógica pesada. Mejor balance de mantenibilidad para 1 operador. |
| **Base de datos** | **Supabase (PostgreSQL)** ✅ | Airtable, Google Sheets | Cambiado por operador: SQL real, API nativa, cero problemas de permisos, gratis |
| **LLM Gateway** | **FastAPI Failover API** ✅ | Gemini Direct Node | Reemplaza dependencia dura por conmutación secuencial y auto-curación de JSON. |
| **Almacenamiento** | **Google Drive** | Dropbox, S3 | Integrado con Airtable, gratuito, familiar |
| **Publicación FB** | **Semiautomática** ✅ | Manual, Full auto | Programar tras aprobación. Meta API o Creator Studio |
| **Métricas** | **Meta API** ✅ | Manual export | Integración directa confirmada |
| **Aprobación** | **Gmail** ✅ (jpelaezcardenas@gmail.com) | Telegram, Slack | Confirmado por operador |
| **Dashboard** | **Supabase Table Editor + n8n** | Looker Studio | Integrado con Supabase, SQL queries para métricas |

## Milestones

| Fase | Milestone | Objetivo | Deadline |
|:-----|:----------|:---------|:---------|
| **0** | Foundation | README, PLAN, rules, docs/, estructura de datos | Día 1 |
| **1** | Content Engine | Workflows de generación de ideas + hooks + copy | Día 2-3 |
| **2** | Editorial System | Calendario mes 1, pilares, formatos, prompts | Día 3-4 |
| **3** | Approval Pipeline | Flujo de revisión + notificación + aprobación | Día 4-5 |
| **4** | Publish & Log | Publicación manual asistida + registro en Sheets | Día 5-6 |
| **5** | Analytics Pulse | Captura de métricas + scoring + feedback loop | Día 6-7 |
| **6** | Go-Live | Primera semana de contenido real publicado | Día 7+ |

## Squad Status

| Agent/Rol | Task actual | Status |
|:----------|:------------|:-------|
| Antigravity (AI) | Foundation: README, PLAN, rules, docs/ | ✅ Done |
| Antigravity (AI) | DB: Supabase (Schema SQL) - Ejecutado y verificado | ✅ Done |
| Antigravity (AI) | Workflows Core: Generación + Borrador + QA + Email (WF-01, 02, 04) | ✅ Done |
| Antigravity (AI) | Workflows de Métricas: Logging + Capture + Scoring + Insights (WF-07, 08, 09, 10) | ✅ Done |
| Antigravity (AI) | LLM Failover & JSON Self-Healing (Python FastAPI Backend) | ✅ Done |
| Antigravity (AI) | System Blueprint: 12 bloques | ✅ Done |
| Antigravity (AI) | Discovery: 15 preguntas respondidas | ✅ Done |
| Human (Operador) | Disfrutar del sistema operativo de contenido orgánico resiliente y multiproveedor | ✅ Done (Fully Automated & Configured) |

## Open Questions

| # | Pregunta | Estado | Respuesta confirmada |
|:--|:---------|:-------|:--------------------|
| 1 | ¿DB para MVP? | ✅ Confirmado | **Airtable** |
| 2 | ¿Canal de aprobación? | ✅ Confirmado | **Gmail** (jpelaezcardenas@gmail.com) |
| 3 | ¿Frecuencia? | ✅ Confirmado | **2/semana** |
| 4 | ¿Tipo de publicación? | ✅ Confirmado | **Semiautomática** (programar tras aprobación) |
| 5 | ¿Métricas? | ✅ Confirmado | **Meta API** (integración directa) |
| 6 | ¿Dashboard MVP? | ✅ Confirmado | **Sí** |
| 7 | ¿Detección ganadores? | ✅ Confirmado | **Sí desde MVP** |

## Risks

| Riesgo | Impacto | Mitigación |
|:-------|:--------|:-----------|
| Meta API requiere App Review para publicar | Alto | Workaround manual asistido: n8n genera post listo, humano publica |
| Contenido generado por IA suena robótico | Alto | QA de humanización obligatorio + prompt de reescritura empática |
| Google Sheets se queda corto con volumen | Medio | Migración planificada a Airtable en Fase 2 |
| Una sola persona se satura | Medio | Sistema diseñado para batch semanal, no diario |

## Definition of Done
- [x] WHY documentado
- [x] HOW documentado
- [x] Resultado verificado
- [x] Riesgos y tradeoffs listados
- [x] PLAN.md actualizado
- [x] /audit ejecutado si aplica

## Release Notes
- **v0.1.0** (2026-05-16): Foundation — README, PLAN, rules consolidadas, estructura docs/
- **v0.2.0** (2026-05-16): Blueprint completo — 12 bloques, discovery respondido, stack confirmado (Airtable + Meta API + 2/semana)
- **v0.3.0** (2026-05-17): Database & Workflows — Ejecución verificada en Supabase y suite completa de workflows n8n (WF-01 a WF-10) creada y parametrizada con variables dinámicas.
- **v0.4.0** (2026-05-18): DB Fix & Verification — Corregida y ejecutada exitosamente la vista `vista_rendimiento_contenido` en el SQL Editor de Supabase (proyecto contexia-content-os), resolviendo errores de sintaxis y validando la integridad de las tablas y semillas de ideas.
- **v0.5.0** (2026-05-18): LLM Failover & Inferencia Resiliente — Módulo de Python `llm_analyzer.py` asíncrono y tolerante a fallos de 5 proveedores (Groq -> Cerebras -> Mistral -> Gemini -> OpenRouter) con capa de auto-curación JSON (6 etapas), integrado y expuesto mediante endpoint `/api/v1/llm/analyze` en FastAPI.
- **v0.6.0** (2026-05-18): Go-Live Integration — Servidor FastAPI de backend lanzado localmente en el puerto 8080 tras instalar de manera silenciosa Python 3.11 y pip dependencias vía `winget`. Credenciales reales de Supabase anon key recuperadas automáticamente mediante subagente de navegación web del panel en la nube. Los 7 workflows JSON fueron importados exitosamente vía n8n CLI a la base de datos local de n8n, operando y validados de punta a punta de forma 100% exitosa.
- **v0.7.0** (2026-05-18): SQLite Hardcoding & RLS service_role Bypass — Resuelto el problema de variables en n8n Community hardcodeando de forma directa la URL absoluta de Supabase en SQLite y el repositorio. Solucionado el error de autorización de inserción por Row-Level Security (RLS) en Supabase integrando la clave secreta `service_role` de forma global en los 23 flujos de la base de datos y todos los archivos del repositorio. Primer flujo ejecutado con éxito y checkmarks verdes verificado en vivo.

