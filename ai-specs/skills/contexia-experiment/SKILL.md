---
name: contexia-experiment
description: Diseña un experimento GTM pequeño, medible y reversible para validar segmento, problema, mensaje, canal u oferta de Contexia.
argument-hint: "[pregunta de aprendizaje] [cohorte] [ventana]"
disable-model-invocation: true
---

# Experimento GTM

Convierte `$ARGUMENTS` en una ficha experimental; no ejecutes el experimento.

## Diseño

1. Lee reglas locales, mapa del proceso, registro de capacidades y claims aprobados.
2. Formula una hipótesis falsable con una sola variable principal.
3. Define población, unidad, asignación, baseline, ventana, métrica primaria, guardrails y umbral antes de ver resultados.
4. Identifica sesgos: selección, estacionalidad de Renta, canal, muestra, medición, intervención humana y atribución.
5. Limita exposición, gasto y datos. Define kill switch y rollback.
6. Separa aprendizaje B2C de Renta del aprendizaje B2B de SaaS; uno no prueba el PMF del otro.
7. Si se usa Manus, prepara la salida para `/contexia-manus-package` y registra créditos reales por unidad ejecutada.

## Restricciones

No uses una capacidad `UNKNOWN`, `ROADMAP` o `CONFLICT`; no mezcles Entidad A/B; no inventes benchmark; no cambies más de una variable cuando pretendas inferir causa; no uses presión engañosa; no ejecutes contacto sin base legítima y aprobación.

## Salida

Completa: ID y versión; pregunta; hipótesis; evidencia previa; cohorte/inclusiones/exclusiones; variante/control; recorrido; métrica primaria/secundarias/guardrails; instrumentación; muestra como decisión pendiente si no hay base; ventana; presupuesto/cupo; gates; riesgos; criterio `KEEP/ITERATE/STOP`; responsable; aprobador; archivos que producirá.

Marca cada afirmación como `HECHO`, `INFERENCIA`, `HIPÓTESIS` o `DECISIÓN PENDIENTE`. Encabeza `BLOCKED` si falta capacidad, consentimiento, medición, presupuesto, cupo o aprobación.
