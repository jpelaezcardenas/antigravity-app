# Brief: ícono "Jarvis" para el header de Contexia

## Qué es esto

Un botón/badge que va a vivir en el header de la app de Contexia (arriba, centrado en
desktop). Al hacer click abre un chat con "Jarvis" (el asistente IA). Reemplaza el logo de
Contexia y una tarjeta de "Taty / WhatsApp" que estaban ahí antes.

## Lo que ya probé y no funcionó (para no repetirlo)

Iteré en código (CSS/SVG puro) intentando combinar: la silueta del pin de Contexia + anillos
HUD estilo Iron Man/Jarvis + el arte original del logo (barras, flecha, check) + el nombre de
la empresa como texto encima. El resultado quedó sobrecargado y sin jerarquía clara — texto
compitiendo con el arte del logo, anillos que no se leían bien a tamaño pequeño (~64-96px).

**No pidas "arréglalo con más CSS" — el problema es de composición/jerarquía visual, no de
código.** Necesito un diseño resuelto (Figma, Illustrator, o el propio Claude Design) antes de
volver a tocar el componente.

## Archivos anexos que debes darle a Design

1. `contexia-app/public/assets/img/logo_official.png` — el logo completo de Contexia (pin +
   barras + flecha + check + wordmark "CONTEXIA").
2. `contexia-app/public/assets/img/jarvis_mark.png` — el mismo ícono, recortado sin el texto
   "CONTEXIA" de abajo (ya aislado, por si sirve como base).
3. Las 3 referencias de estilo J.A.R.V.I.S. que usé de guía (arc-reactor con anillos
   concéntricos, marcas tipo dial, brillo cian) — búscalas en esta conversación o dime y te las
   reexporto como archivos.

## Lo que necesito que el diseño resuelva

- **Tamaño real de uso**: 56–96px de diámetro en el header (no una ilustración grande — tiene
  que leerse bien de pequeño, en un celular).
- **Estado 1 — reposo**: el ícono/badge de Contexia, con algún tratamiento "premium" (brillo,
  pulso, no plano) que se sienta como un asistente de IA, no como un logo estático.
- **Estado 2 — personalizado por cliente**: cada empresa cliente ve **su propio nombre** en
  vez de "Contexia" (ejemplos reales: "FEREZ", "CODIGO520"). Necesito que el diseño defina
  *dónde y cómo* se ve ese texto sin ensuciar el ícono — puede ser: reemplazando el ícono por
  texto, un badge/etiqueta aparte, un anillo con el texto alrededor, lo que se vea mejor.
- **Estado 3 — abierto**: qué pasa visualmente cuando el usuario hace click (¿se transforma en
  una X? ¿se expande?).
- **Formato de entrega que necesito de vuelta**: idealmente un SVG exportado (o instrucciones
  precisas de capas/colores/tamaños) que yo pueda implementar 1:1 en React, no solo una imagen
  de referencia.

## Restricciones técnicas (para que el diseño sea implementable)

- Es un componente React (`contexia-app/components/jarvis/JarvisBubble.tsx`), no una imagen
  estática — el texto del nombre de empresa es dinámico (viene de la base de datos por tenant).
- Sin librerías nuevas de animación — cualquier animación tiene que poder hacerse con
  CSS/SVG puro.
- Tiene que verse bien tanto en el header de escritorio como en el de celular (mismo diseño,
  dos tamaños).
