# Contexia GTM Operating Kit

Versión de investigación: **10 de septiembre de 2026**  
Uso previsto: **Claude Code**, como capa adaptable sobre el proceso existente de Hermes y ventas de Contexia.

## Resultado

Este paquete convierte la temporada de renta de personas naturales en un experimento de adquisición y aprendizaje para Contexia:

1. atraer demanda con contenido, aliados, referidos y formularios con autorización;
2. orientar y calificar el caso de Renta Natural sin emitir una conclusión tributaria automática;
3. derivar el servicio profesional a **Entidad A**;
4. identificar, con consentimiento independiente, si el usuario dirige una empresa con problemas que Contexia puede resolver;
5. activar únicamente la oferta tecnológica cuya disponibilidad haya sido verificada;
6. medir qué segmento, problema, mensaje, canal y oferta producen valor y ventas repetibles.

No es un rediseño del proceso Hermes–Claude Code. Los puntos de integración que todavía no conocemos quedan declarados como campos por completar.

## Regla de salida al mercado

> Contexia no “lanza todo”. Lanza una cuña pequeña, verificable y reversible; aprende; y solo amplía aquello que supera los gates de capacidad, evidencia, entidad, precio, privacidad y entrega.

## Contenido

- `PLAYBOOK.md`: estrategia, ICP, embudo, campaña por oleadas, métricas y cadencia.
- `REFERENTES.md`: tres referentes hispanohablantes y tres anglosajones elegidos para este caso.
- `GUIONES.md`: mensajes, discovery, objeciones, demo, propuesta, seguimiento y referidos.
- `CLAUDE.md.fragment.md`: reglas persistentes para fusionar con el `CLAUDE.md` real del repositorio.
- `reference/COMMERCIAL-GROUND-TRUTH.md`: identidad, precios conocidos y límites.
- `reference/CLAIMS-LEDGER.md`: semáforo de afirmaciones comerciales.
- `reference/TECHNICAL-DELTA.md`: contraste del informe técnico del 29 de agosto con el catálogo del 9 de septiembre.
- `reference/MANUS-EXECUTION-CONTRACT.md`: auditoría del paquete Manus v1.1.0 y contrato actualizado de ejecución.
- `reference/TELEGRAM-CONTROL-ROOM.md`: diseño de una sola conversación para Hermes, Claude Code, Búnker y Manus.
- `reference/EVIDENCE.md`: investigación y fuentes.
- `templates/CURRENT-PROCESS-MAP.md`: contrato para mapear el proceso Hermes–Claude Code existente.
- `templates/CAPABILITY-REGISTRY.md`: gate de disponibilidad de producto.
- `templates/EXPERIMENT-CARD.md`: ficha de experimento.
- `.claude/skills/`: habilidades invocables desde Claude Code.

## Instalación segura

1. Copiar `.claude/skills/` al repositorio real de Contexia.
2. Fusionar —no reemplazar— `CLAUDE.md.fragment.md` con el `CLAUDE.md` vigente.
3. Completar `templates/CURRENT-PROCESS-MAP.md` con el flujo real de Hermes, CRM, Taty, aprobaciones y handoffs.
4. Completar `templates/CAPABILITY-REGISTRY.md` mediante demos y pruebas en producción.
5. Ejecutar `/contexia-readiness` antes de generar una pieza comercial.
6. Ejecutar `/contexia-renta-campaign` para preparar la oleada correspondiente.
7. Ejecutar `/contexia-manus-package` para convertir una campaña aprobable en un manifiesto de ejecución; contrastarlo con el paquete Manus v1.1.0 existente.
8. Mantener todo envío, publicación, cambio de precio y actualización externa bajo aprobación humana.

## Orden recomendado de uso

```text
/contexia-readiness
        ↓
/contexia-claim-check
        ↓
/contexia-telegram-control   (auditoría de la cabina Taty/Hermes)
        ↓
/contexia-renta-campaign
        ↓
/contexia-icp-score       /contexia-prospect-brief
        ↓
/contexia-outreach        /contexia-renta-triage
        ↓
/contexia-discovery       /contexia-demo       /contexia-pilot
        ↓
/contexia-offer-route     /contexia-proposal
        ↓
/contexia-follow-up       /contexia-referral
        ↓
/contexia-experiment      /contexia-weekly-review
        ↓
/contexia-manus-package → Hermes/Búnker → Manus Operations
```

## Decisiones pendientes antes de producción comercial

- Confirmar la forma jurídica, contractual y de facturación del recorrido Pro/Total cuando interviene Entidad A.
- Verificar el estado real de cada capacidad que aparece en la base de conocimiento; el documento mezcla producción, prototipo y roadmap.
- Revalidar los bloqueos del informe técnico del 29 de agosto: Sell Machine en ensayo, comerciante de registro, aprobación humana del pago, seguridad, primera cifra freemium y gating de tiers.
- Confirmar métricas, clientes, testimonios y permisos de uso.
- Mapear estados, identificadores, automatizaciones y aprobaciones del proceso Hermes–Claude Code actual.
- Auditar la configuración real de los tres proyectos Manus frente al paquete local v1.1.0: fuentes, campos pendientes, conectores, permisos, webhook, tareas y pruebas.
- Validar con asesoría jurídica el consentimiento, la transferencia de datos entre entidades y cada canal de prospección.

## Supuestos explícitos

- “Claude Code” es la herramienta a la que el usuario se refirió oralmente como “Cloud Code”.
- El foco geográfico inicial es el Área Metropolitana del Valle de Aburrá.
- Renta Natural es una oferta profesional de Entidad A y la cuña de adquisición; no es evidencia de product–market fit del SaaS.
- Los precios aquí citados son el estado interno del 9 de septiembre de 2026. En operación manda la fuente canónica del repositorio.
