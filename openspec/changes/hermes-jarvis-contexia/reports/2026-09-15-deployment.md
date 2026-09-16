# Deployment Report — 2026-09-15 (Fase F: badge JARVIS + navegación desktop)

**Change:** `hermes-jarvis-contexia`
**Fecha:** 2026-09-15
**Rama:** `main`
**Commits:** `e9265cc` (feature + build sync), `5febc01` (fix de rewrite)

---

## Qué se desplegó

Segunda ronda de iteración visual sobre el badge JARVIS del header (Fase E, 2026-09-14), en
sesión en vivo con el fundador. Detalle completo del diseño en `design.md` § "Re-scope
2026-09-15"; resumen operativo aquí:

1. Renombre JARVOS → JARVIS (typo real) en todo el componente y sus keyframes CSS.
2. Rediseño de los anillos HUD: se quitó una capa que invadía el hueco deliberado de la
   anatomía del handoff original, se agregó un anillo incandescente con glow SVG real, y se
   agregó movimiento armónico constante (no solo al presionar).
3. Asset del mark reemplazado (`Pin.png` del fundador) y re-procesado para quitarle el fondo
   negro sólido que traía.
4. **Regresión real encontrada y corregida**: quitar los links de nav del header (sesión
   anterior) había dejado el desktop sin ninguna forma de navegar a Fiscal/Radar/Patrimonio/
   Config. Fix: `DesktopSidebar.tsx` nuevo, con el badge movido ahí (mismo componente, prop
   `panelAnchor` nuevo) — no un segundo punto de acceso.
5. `BottomNav.tsx` ganó a Patrimonio (mobile tampoco lo tenía).
6. `SignOutFooter.tsx` nuevo — consolida "Cerrar Sesión" en un solo lugar, eliminando dos
   duplicados preexistentes (Config y Overview).
7. Núcleo del badge alineado al color real de fondo de la app.
8. `/app/acerca` nueva — reemplaza el link roto a `/landing.html` de Config con una pantalla
   corta, copy tomado de `.antigravity/GROUND_TRUTH.md`.

## Pipeline de deploy ejecutado

```
cd contexia-app && npm run build          # limpio, incluye /app/acerca en las rutas generadas
# CACHE_VERSION bump: v24-2026-09-14 -> v25-2026-09-15 en public/sw.js
npm run build                             # segunda vez, para que el export incluya el bump
# sync manual: out/app/* -> app/ (repo root), resto de out/ -> repo root
git add <archivos específicos>            # sin -A; se excluyó explícitamente trabajo de otras
                                           # sesiones en curso (.claude/settings.json,
                                           # openspec/changes/radar-adoption-tracking/,
                                           # progress/current.md, HANDOFF-*.md, etc.)
git commit                                # e9265cc
git push origin main                      # confirmado por el fundador ("ya")
```

## Verificación en vivo

- Vercel: `dpl_2upGHfPoiwYQXUpQ9AmtVHSEGhfH` → **READY** (commit `e9265cc`).
- `contexia.online/sw.js` sirve `CACHE_VERSION v25-2026-09-15` — confirmado con fetch directo.
- `contexia.online/app/overview` (desktop y mobile): sidebar de escritorio con 5 opciones +
  badge debajo, header reducido a barra delgada en desktop; `BottomNav` mobile con las 5
  opciones (Pulso/Fiscal/Radar/Patrimonio/Config).

### Hallazgo real durante la verificación — `/app/acerca` 404 en producción

`contexia.online/app/acerca` devolvía 404 justo después del primer deploy, pese a que
`contexia-app/out/app/acerca.html` existía y se había sincronizado correctamente a
`app/acerca.html` en el repo. Causa: este repo se sirve como sitio estático puro
(`vercel.json`, `outputDirectory: "."`), sin resolución de clean-URL a nivel de framework —
cada ruta `/app/<nombre>` necesita su propia entrada explícita en `vercel.json`'s `rewrites`
(`/app/<nombre>` → `/app/<nombre>.html`), y cualquier ruta sin entrada cae en el catch-all
`{"source": "/app/:path*", "destination": "/404.html"}`. La nueva ruta `/app/acerca` nunca tuvo
esa entrada.

**Fix**: agregada la entrada faltante en `vercel.json` (commit `5febc01`), colocada antes del
catch-all. Redeploy `dpl_5XiLo1vNnbBM3c8bwLFeLa2ZFjzB` → **READY**. Re-verificado:
`contexia.online/app/acerca` devuelve 200 con el contenido real ("¿Qué es Contexia?", los 4
pilares, la aclaración de marca).

**Lección para `DEPLOYMENT_STAGE/checklist-vercel.md`**: toda nueva ruta `/app/<nombre>` en
`contexia-app` requiere una entrada correspondiente en `vercel.json`'s `rewrites` — esto no es
automático como en un deploy Next.js estándar, y no hay ningún error de build que lo detecte
(el build de `contexia-app` es exitoso aunque la ruta no esté registrada en `vercel.json`, que
vive en la raíz del repo, un proyecto separado a ojos de `next build`).

## Pendiente, no bloqueante

- **Badge "a color" en producción real**: verificado el estado "no disponible" (gris, esperado
  sin sesión) en `contexia.online`, y por separado el estado a color en el preview local
  simulando `isAdmin=true` con una cookie JWT falsa (nunca una credencial real — el backend de
  Railway no es alcanzable desde el dev server local). No se confirmó el estado a color con una
  sesión real logueada en producción. Queda para cuando el fundador entre con su propia cuenta.
- Ítems de Fase A ya documentados como bloqueados en tasks.md (0.2/1.7, `TELEGRAM_JUAN_DAVID_CHAT_ID`)
  siguen sin resolver — sin relación con este deploy.
