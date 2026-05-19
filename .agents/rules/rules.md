---
trigger: always_on
glob: "**/*"
description: "Canonical rules for Contexia Content OS. Single source of truth."
---

# Contexia Content OS — Canonical Rules

> **Este es el archivo canónico de reglas.** Todos los demás archivos de reglas (.antigravity/rules.md, root rules.md) son copias de referencia. Si hay conflicto, este archivo manda.

## 1. Ground truth de marca
- Contexia es una AI Automation Agency (AAA) en Colombia.
- Contexia NO es una firma contable regulada.
- Contexia NO firma estados financieros, declaraciones ni dictámenes.
- Siempre mantener separación entre capa tecnológica y capa regulada.
- La propuesta central es Claridad Predictiva.
- El tono debe sonar humano, empático, claro y estratégico, tipo amiga contadora con criterio.

## 2. Modo de trabajo obligatorio
- Antes de diseñar o construir, hacer discovery priorizado.
- Hacer preguntas cerradas cuando sea posible.
- Si falta información, proponer defaults inteligentes y marcarlos como asunciones.
- No detener el MVP por decisiones no críticas.
- Trabajar en fases: discovery -> decisiones -> arquitectura -> build plan -> QA -> go-live.

## 3. Formato mínimo de toda respuesta
Toda respuesta debe incluir:
- lo confirmado
- lo indefinido
- recomendaciones por defecto
- próximos pasos

## 4. Reglas para workflows n8n
Si diseñas workflows n8n, siempre incluir:
- nombre
- objetivo
- trigger
- nodos sugeridos
- inputs
- outputs
- validaciones
- manejo de errores
- edge cases
- cambios en base de datos
- acción humana requerida

## 5. Reglas para base de datos
Si diseñas base de datos, siempre incluir:
- tablas
- campos
- tipos de datos
- relaciones
- IDs
- naming conventions
- vistas recomendadas
- estados
- manejo de versiones

## 6. Reglas para prompts
Si diseñas prompts, siempre incluir:
- objetivo
- cuándo usarlo
- variables
- instrucciones
- restricciones
- formato de salida estructurado
- guardrails de marca

## 7. Reglas de decisión
Allowed without asking:
- proponer defaults
- reorganizar estructura lógica
- elegir stack MVP simple
- simplificar arquitectura
- sugerir workaround manual temporal

Ask first:
- cambiar herramienta base escogida
- introducir herramientas pagas nuevas
- mover de Sheets a Airtable o viceversa si ya se decidió
- introducir complejidad enterprise

Never:
- describir a Contexia como firma contable regulada
- inventar capacidades no confirmadas
- diseñar soluciones enterprise innecesarias
- usar tono corporativo frío o robótico

## 8. Humanización obligatoria
- Todo copy debe sonar humano, claro y colombiano entendible.
- Evitar jerga opaca.
- Traducir complejidad a lenguaje simple.
- Priorizar protección, empatía y claridad.
- Si un texto suena robótico, reescribirlo automáticamente.
- Mantener autoridad sin perder cercanía.

## 9. Calidad
- Priorizar MVP funcional en 7 días.
- Cada diseño debe incluir versión MVP y fase 2.
- Todo sistema debe poder ser operado por una sola persona.
- Toda salida debe ser accionable, no solo conceptual.

## 10. Regla de salida inicial
La primera salida del agente debe ser:
1. lo ya confirmado
2. preguntas críticas de discovery
3. defaults propuestos
4. arquitectura de trabajo por fases
5. bloqueos o dependencias a resolver

## 11. Definition of Done (DoD)
Antes de cerrar cualquier tarea:
- Explicar WHY (por qué esta solución)
- Explicar HOW (cómo se implementó)
- Verificar resultado (visual o funcional)
- Enumerar riesgos y tradeoffs
- Actualizar PLAN.md

## 12. /audit Quality Gate
Todo feature debe pasar:
1. Environmental Check: verificar build estable
2. Visual/Functional Audit: verificar que funciona como se espera
3. Trust Audit: confirmar que el dato es auditable
4. Audit Report: scores Visual/Functional/Trust [1-10]
5. Self-Correction Loop: threshold ≥9/10, si <9 corregir y re-auditar

## 13. Auto-corrección
- Nunca fallar dos veces por lo mismo.
- Ciclo: diagnosticar → parchear → documentar → re-verificar.
- Cada bug recurrente deja registro en docs/runbooks/.
