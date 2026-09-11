---
name: contexia-referral
description: Diseña una solicitud de referido o alianza después de valor observable, con perfil específico y texto reenviable.
argument-hint: "[cliente o aliado] [valor observado] [perfil buscado]"
disable-model-invocation: true
---

# Referidos y alianzas

Redacta para `$ARGUMENTS`; no envíes, publiques ni actualices sistemas.

## Preconditions

- Existe valor observable, permiso para contactar y relación real documentada.
- El resultado citado está aprobado para ese contexto; un testimonio público requiere autorización expresa.
- El perfil buscado es específico y relevante, no una lista masiva.
- La oferta y capacidad están verificadas.

Si falta alguna condición, devuelve `BLOCKED` o recomienda esperar.

## Reglas

1. Lee ground truth y claims; separa siempre Entidad B tecnológica de Entidad A profesional.
2. No pidas al referente compartir expedientes, diagnósticos tributarios ni datos sensibles.
3. No atribuyas a Contexia resultados no medidos ni garantices ahorro, exactitud, sanciones evitadas o crecimiento.
4. Facilita una introducción de doble opt-in. El destinatario puede rechazar sin seguimiento automático.
5. Para partners, define problema mutuo, cliente compartido, handoff, consentimiento, datos, atribución, compensación por aprobar y criterio de salida; no inventes acuerdos.

## Salida

Entrega: momento recomendado; mensaje de solicitud; texto reenviable; perfil y señales; razón de relevancia; límites de datos; propuesta de handoff; seguimiento único; criterios de partner; claims/fuentes; aprobaciones.

Etiqueta `HECHO`, `INFERENCIA`, `HIPÓTESIS` y `DECISIÓN PENDIENTE`.
