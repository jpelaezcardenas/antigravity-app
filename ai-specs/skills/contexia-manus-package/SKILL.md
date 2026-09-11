---
name: contexia-manus-package
description: Convierte una campaña aprobable en un contrato de ejecución estructurado para Manus, brazo externo de redes y Meta.
argument-hint: "[campaign_id o ruta del paquete] [modo dry_run|organic|paid]"
disable-model-invocation: true
---

# Paquete de ejecución para Manus

Prepara un artefacto determinista para `$ARGUMENTS`. Esta habilidad no llama a Manus, no publica, no autoriza conectores y no gasta presupuesto.

## Rol y fronteras

- Claude Code especifica y verifica; Hermes orquesta/rutea; el Búnker conserva la aprobación; Manus ejecuta acciones aprobadas en Facebook, Instagram, Meta, research y extracción de métricas; el backend/Hermes recibe telemetría.
- Manus no es estratega, fuente de verdad, aprobador, custodio de datos financieros ni sustituto de Claude Code/Hermes.
- No copies secretos, expedientes tributarios, credenciales, teléfonos personales o datos financieros al paquete.
- La arquitectura existente se descubre y se respeta; los endpoints, esquemas, conectores y firmas del material de julio son hipótesis hasta validarse contra código y documentación actual.

## Gates antes de generar modo ejecutable

Exige: campaña versionada; claims aprobados; capacidad verificada; audiencia autorizada; presupuesto y límite diario; cupo operativo; ventana de publicación; aprobador humano; destino/cuenta exactos; activos finales; CTA; tracking; kill switch; rollback; idempotency key; esquema de callback; autenticación/verificación de webhook; dry-run exitoso.

Si falta cualquiera, produce solo un borrador `BLOCKED`. Para pauta, cambios de presupuesto, segmentación, eliminación, mensajes a terceros o cualquier gasto, la aprobación humana debe ser explícita y granular.

## Contrato de entrada

Incluye como mínimo:

- `campaign_id`, `version`, `experiment_id`, `mode`;
- `approved_by`, `approved_at`, `approval_scope`;
- plataforma, cuenta, formato, fecha/ventana y zona horaria;
- copy y asset por hash/ruta aprobada;
- audiencia, exclusiones, frecuencia, presupuesto y límites;
- claim IDs y versión de política;
- CTA/landing/UTM;
- acciones permitidas y prohibidas;
- `dry_run`, idempotencia, timeout, reintentos y kill switch;
- esquema estricto de salida.

## Contrato de salida y prueba de éxito

No tomes `structured_output.success=true` como prueba de publicación. Exige estado de ejecución, URL/ID de plataforma, timestamp, evidencia recuperable, gasto reportado, métricas disponibles, créditos Manus estimados/reales, errores, acciones parciales y reconciliación posterior mediante API/consulta independiente.

Clasifica el resultado como `SUCCEEDED_VERIFIED`, `SUCCEEDED_UNVERIFIED`, `PARTIAL`, `FAILED_RETRYABLE`, `FAILED_FINAL` o `NEEDS_HUMAN`.

## Salida

Entrega: resumen humano; tabla de gates; manifiesto estructurado válido; esquema de respuesta; prueba de reconciliación; plan de rollback; alertas; campos faltantes; aprobaciones. Marca `HECHO`, `INFERENCIA`, `HIPÓTESIS` y `DECISIÓN PENDIENTE`.
