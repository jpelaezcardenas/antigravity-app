---
name: contexia-outreach
description: Redacta contacto B2B relevante y trazable para Contexia a partir de una señal pública y una base legítima de contacto.
argument-hint: "[cuenta] [canal autorizado] [objetivo]"
disable-model-invocation: true
---

# Outreach B2B de Contexia

Redacta, pero no envíes, un mensaje para `$ARGUMENTS`.

## Entradas obligatorias

- brief de cuenta con fuentes públicas;
- segmento/ICP y puntaje;
- señal observable y fechada;
- problema formulado como hipótesis;
- oferta y capacidad `LIVE_VERIFIED` o `PILOT_ONLY`;
- claim aprobado y su evidencia;
- origen del dato de contacto, finalidad, autorización o fundamento revisado;
- canal, persona aprobadora y CTA.

Si falta una entrada, devuelve `BLOCKED`; no la inventes.

## Reglas

1. Lee primero las reglas locales, ground truth, registro de capacidades, ledger de claims y precio canónico.
2. No uses datos sensibles, inferencias tributarias, listas compradas/raspadas ni información personal irrelevante.
3. Prioriza introducción cálida, referido, partner, evento, formulario o relación institucional. Un dato público no equivale por sí solo a consentimiento.
4. Mantén el mensaje corto: señal → hipótesis → prueba pertinente → pregunta pequeña.
5. No abras con “IA”, un tour de funcionalidades ni una promesa absoluta.
6. Contexia/Entidad B es software; no firma declaraciones, dictámenes ni estados financieros y no reemplaza al contador.
7. No inventes clientes, porcentajes, ROI, resultados, integraciones o disponibilidad.
8. Incluye baja o cierre respetuoso cuando el canal lo requiera. Respeta la ventana legal aplicable.

## Salida

Produce: asunto; mensaje; variante breve; CTA; razón de relevancia; mapa oración→claim→fuente; base de contacto; riesgos; aprobaciones; siguiente acción si responde/no responde/no interesa.

Etiqueta `HECHO`, `INFERENCIA`, `HIPÓTESIS` y `DECISIÓN PENDIENTE`. Nunca actualices CRM, programes secuencias ni ejecutes mensajes.
