---
name: contexia-weekly-review
description: Convierte datos semanales de adquisición, ventas, activación y ejecución Manus en decisiones KEEP, ITERATE o STOP.
argument-hint: "[semana o rango] [rutas de datos]"
disable-model-invocation: true
---

# Revisión semanal GTM

Analiza `$ARGUMENTS` sin modificar campañas, CRM, presupuesto, producto ni tareas programadas.

## Fuentes y control

1. Lee ground truth, mapa del proceso, registro de capacidades, ledger de claims y fichas de experimentos.
2. Usa eventos crudos y definiciones versionadas. Señala datos faltantes, duplicados, cambios de tracking y diferencias de atribución.
3. Separa por oferta, entidad, segmento, canal, campaña, cohorte y etapa. Renta/Entidad A y SaaS/Entidad B son embudos distintos.
4. No uses aperturas o impresiones como éxito final; conecta adquisición con consentimiento, conversación calificada, pago/activación, primer impacto, retención y margen.
5. No declares causalidad a partir de una correlación o una muestra pequeña.

## Métricas mínimas

- alcance, clic, opt-in válido y costo por opt-in;
- inicio y finalización de triage, caso revisable, cotización humana, aceptación y entrega;
- leads B2B consentidos, reuniones agendadas/realizadas/calificadas;
- discovery→demo→piloto→propuesta→pago;
- activación Pulso/GPS, tiempo al primer impacto y uso de acción central;
- win rate, ticket/MRR, ciclo, razón de pérdida/no decisión, CAC incluido tiempo humano y margen;
- consumo de créditos Manus por tarea, ejecución, éxito verificado y pieza reutilizable;
- errores, reintentos, gasto de pauta, frecuencia y señales de fatiga;
- cobertura de claims con fuente/fecha/aprobación.

## Decisión

Para cada experimento compara resultado con baseline, umbral y riesgo. Recomienda exactamente una opción:

- `KEEP`: conservar la variable y ampliar de forma controlada;
- `ITERATE`: cambiar una sola variable y repetir;
- `STOP`: detener por riesgo, falta de valor, economía o integridad de datos.

No asignes automáticamente los 300 créditos diarios de Manus ni los trates como cuota de consumo. Calcula costo real por resultado verificado antes de redistribuir capacidad.

## Salida

Entrega: resumen ejecutivo; salud de datos; tablero; embudos separados; decisiones por experimento; aprendizajes; anomalías; riesgos; máximo tres prioridades; propietarios y fechas; aprobaciones requeridas. Etiqueta `HECHO`, `INFERENCIA`, `HIPÓTESIS` y `DECISIÓN PENDIENTE`.
