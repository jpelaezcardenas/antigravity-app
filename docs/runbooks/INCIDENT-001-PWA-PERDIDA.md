# Post-Mortem y Runbook: Incidente 001 - Pérdida de la PWA "Neurocontabilidad"

## 1. Resumen Ejecutivo
Durante más de dos días, se perdió acceso al código fuente de la aplicación PWA principal de los clientes (la que incluía la integración de Neurocontabilidad, "Caja Real de Hoy", Semáforos de salud financiera y el header de "Tu Amiga Contadora - Taty"). Todas las búsquedas en el historial de Git buscando archivos React (`.tsx`, `.jsx`) fallaban, lo que llevó a confusión y frustración al creer que un subagente había borrado el trabajo sin dejar rastro.

## 2. ¿Qué pasó realmente? (Root Cause Analysis)
El problema fue causado por una **fuerte desalineación entre la arquitectura percibida y la arquitectura real**.

1. **La ilusión del React App:** El usuario y un agente trabajaron juntos para diseñar los flujos de "Neurocontabilidad". El usuario creía que se estaba construyendo una aplicación React Vite o Next.js porque así se le instruyó en el prompt inicial.
2. **La modificación en duro (Hardcoding):** El agente no modificó los componentes `.tsx` del código fuente. En su lugar, tomó la salida estática ya compilada de Next.js (los archivos `.html` dentro de la carpeta `app/`, como `app/overview.html`) y les inyectó directamente el código HTML y CSS con el nuevo diseño, textos y semáforos.
3. **El borrado lógico:** Posteriormente, durante una gran refactorización (commit `ce61830 Fase 2-6: Reorganización completa del monolito antigravity-app`), un agente analizó la estructura del repositorio. Al ver que la carpeta `app/` contenía archivos `.html` generados estáticamente, asumió que eran "archivos basura o compilados viejos" que debían limpiarse, y los **eliminó permanentemente**.
4. **La imposibilidad de encontrarla:** Al buscar "Caja Real" o "Semáforo" en los archivos React de la historia de Git, nunca iba a aparecer, porque la lógica y el diseño visual *nunca existió en React*, solo en esos archivos HTML compilados.

## 3. ¿Cómo se arregló?
1. Se analizó el enrutamiento de Vercel (`vercel.json`) y se descubrió que la URL de producción `contexia.online/app/overview` apuntaba explícitamente a un archivo estático: `app/overview.html`.
2. Al examinar el historial profundo de Git (`git log -S`), se rastreó el momento exacto antes de que la carpeta `app/` fuera borrada (`git checkout ce61830^ -- app/`).
3. Se restauró toda la carpeta `app/` con los HTML modificados a mano y se inyectó directamente a la rama `main` para que Vercel la sirviera de nuevo instantáneamente sin ejecutar un nuevo proceso de compilación de React.

## 4. Políticas de Prevención (Para que NUNCA vuelva a pasar)
Para evitar que un agente haga semejante daño en el futuro, quedan instauradas las siguientes reglas estrictas en el OS de Contexia:

- **REGLA 1 (Prohibido editar compilados):** Ningún agente tiene permitido hacer modificaciones lógicas, de UI o de copy directamente en archivos de salida compilados (`.html` estáticos, carpetas `dist/`, `out/`, `build/`). Toda mejora visual o de experiencia se hace en el source code.
- **REGLA 2 (Source of Truth):** Toda mejora de producto DEBE hacerse en los componentes fuente originales (`.tsx`, `.ts`, `.jsx`). Si por alguna razón crítica se necesita un prototipo rápido en HTML puro, debe aislarse en una carpeta llamada `prototypes/` y documentarse explícitamente.
- **REGLA 3 (Protección de Refactorización):** Antes de que un agente ejecute una "Limpieza de Repositorio" o "Reorganización", debe verificar si los archivos que está a punto de borrar contienen modificaciones manuales que no están respaldadas en el código fuente.
- **DEUDA TÉCNICA URGENTE:** El código restaurado actualmente *sigue siendo HTML estático*. Para poder conectar la PWA a la base de datos real y tener lógica viva, **el próximo hito de ingeniería obligatorio** es extraer el código visual de `app/overview.html` y convertirlo limpiamente a componentes de React Vite.
