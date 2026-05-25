# Auditoría SSO Login — antigravity-app

**Fecha**: 2026-05-25
**Repo**: `antigravity-app/` (monorepo) + `antigravity-app/contexia-wizard/` (Next.js Supabase)
**Síntomas reportados**: login legacy aparece, no redirige a `/app/*`, middleware RBAC ausente, bundle admin con SyntaxError.
**Alcance**: solo auth + routing. **No** se toca lógica fiscal/contable.

---

## 1. Diagnóstico — mapa de superficies de login

| # | Archivo | Rol real | Servido por | Estado |
|---|---|---|---|---|
| 1 | `login.html` (root) | **Login canónico** (Supabase JS SDK, password + OAuth) | Vercel estático | Vivo y activo |
| 2 | `vercel.json:21-25` | Redirige `/wizard/login/` → `/login.html` | Vercel | Vivo — punto de unificación de facto |
| 3 | `contexia-wizard/app/dashboard/page.tsx` | Router post-login por rol/email | Next (`/wizard/dashboard/`) | Vivo, pero asume `/wizard/login/` existe como ruta Next (no existe; cae al redirect #2) |
| 4 | `contexia-wizard/app/` | App Next (wizard onboarding + dashboard) | Vercel/Next con `basePath: "/wizard"` | Vivo — **no tiene `app/login/`** |
| 5 | `js/auth.js` | Pseudo-auth legacy con `localStorage["cx_session"]`, **credenciales en texto plano** (`admin/admin`, `empresario/demo`) | Importado por HTMLs root (`pulso_diario.html` etc.) | Vivo — **debe morir** |
| 6 | `logout.html` (root) | Logout legacy | Vercel estático | Vivo |
| 7 | `app-admin/index.html` | Admin shell SPA (bunker) — bundle con SyntaxError reportado | Vercel rewrite `/app` → `app-admin/index.html` | Vivo, bundle roto |
| 8 | `app/*.html` (overview, fiscal, radar, patrimonio, bunker, config) | Módulos cliente legacy | Vercel rewrites `/app/<x>` → `/app/<x>.html` | Vivos — **sin validación de sesión server-side** |
| 9 | `_next/static/chunks/*.js` (root) | Bundles Next antiguos huérfanos | Vercel estático | Sospechosos — origen probable del SyntaxError |
| 10 | `apps/backend/presentation/auth_router.py` + `auth_endpoints.py` + `application/auth_service.py` | Auth server-side FastAPI (JWT) | Backend (Railway) | Vivo — paralelo a Supabase, no coordinado con el front |
| 11 | `test_login.py` (root) | Test legacy | — | Huérfano |

### ⚠️ Arquitectura Supabase — DOS proyectos distintos (descubierto 2026-05-25)

| Proyecto | URL | Usado por | Contiene |
|---|---|---|---|
| **AUTH** | `kpynymwghfwshvcvevxq.supabase.co` | `login.html`, `app-admin/index.html`, `dashboard/page.tsx` | Usuarios autenticados, sesiones JWT |
| **WIZARD** | `wzqymuzpjbagnbgsiqig.supabase.co` | `contexia-wizard/lib/supabase.ts`, todas las API routes | `leads`, `payments`, `empresas`, `auth_audit` (a crearse) |

**Implicaciones críticas**:
- La migration `20260525_create_auth_audit.sql` debe correrse en **WIZARD** (no AUTH), porque la consume el endpoint `/wizard/api/auth/audit-login`.
- El usuario `growth@contexia.online` y `contexia.marketing@gmail.com` viven en **AUTH**, no en WIZARD.
- El middleware Edge (`middleware.ts`) verifica JWTs firmados por **AUTH** → necesita el `SUPABASE_JWT_SECRET` del proyecto AUTH, no del WIZARD.
- El service_role key del proyecto AUTH NO está en `.env.local` (solo está la anon key). Para administrar usuarios programáticamente hay que obtenerlo de Supabase Dashboard del proyecto AUTH.

**Riesgo**: si alguien hace login en la app y el wizard intenta leer `auth.uid()` del JWT, va a fallar (el WIZARD no reconoce JWTs firmados por AUTH). Hay que verificar si algún endpoint del wizard depende de sesión Supabase del usuario (no de service_role).

### Fuente de verdad real (observada)

- **UI de login**: `login.html` (root) — único punto donde el usuario teclea credenciales.
- **Sesión**: doble: (a) Supabase access_token en `localStorage["token"]`, (b) `localStorage["cx_user"]` con flags de rol calculados client-side, (c) `localStorage["cx_session"]` que escribe `js/auth.js` (legacy).
- **Routing post-login**: `login.html:430` calcula destino y hace `window.location.assign("/app/bunker"|"/app/overview")`. **Nunca pasa por `/wizard/dashboard/`** en el happy path actual.
- **`/wizard/dashboard/page.tsx`**: solo se ejecuta si alguien llega manualmente a esa URL; redirige a `/wizard/login/` que Vercel reescribe a `/login.html`. Loop benigno pero código muerto en el flujo principal.

---

## 2. Bugs identificados (priorizados)

### P0 — bloqueantes

**P0-1. Credenciales hardcodeadas en repo público** — `js/auth.js:13-41` (FIX APLICADO 2026-05-25)
- `admin/admin`, `empresario/demo` en texto plano.
- Aunque sea "demo", está en main y junto a `localStorage["cx_session"]` que algunos módulos podrían leer.
- **Aplicado**:
  - `js/auth.js` borrado.
  - `<script src="./js/auth.js"></script>` removido de 9 HTMLs (tesoreria, oraculo, portal, pulso_diario, copiloto, documentos, conciliacion, centinela, benchmarking).
  - `portal.html`: `<button onclick="window.auth.logout()">` → `<a href="/logout.html">`.
  - `copiloto.html`: `user: window.auth.getUser()` → `user: JSON.parse(localStorage.getItem('cx_user') || '{}')`.

**P0-2. Sin validación server-side de sesión en `/app/*`** — `vercel.json` rewrites + ausencia de middleware (FIX APLICADO 2026-05-25, requiere config Vercel + deploy)
- `/app/bunker`, `/app/overview`, `/app/fiscal`, etc. son HTML estáticos servidos por Vercel sin gate.
- Cualquiera con la URL accede; la validación es 100% client-side dentro de cada HTML (frágil, bypasseable).
- **Aplicado**:
  - `antigravity-app/middleware.ts` creado — Edge Middleware que verifica JWT Supabase (HS256 via Web Crypto API, sin npm deps), gatea `/app/*` y `/app-admin/*`, redirige a `/login.html?next=<original>` si falta o expiró, y exige rol admin para `/app/bunker` y `/app-admin/*`.
  - `login.html`: `storeSession()` ahora setea cookie `sb-access-token` (Path=/, SameSite=Lax, Secure) además de localStorage.
- **Requisitos PRE-deploy** (sin esto el middleware fail-open por seguridad MVP):
  1. En Vercel → contexia-web-app → Settings → Environment Variables → agregar `SUPABASE_JWT_SECRET` con el valor de Supabase Dashboard → Settings → API → JWT Secret.
  2. Verificar que `contexia-web-app` project tenga "Other" o "Next.js" framework setting (Edge Middleware funciona en ambos).
  3. Una vez confirmado SUPABASE_JWT_SECRET seteado, cambiar el `console.warn` fail-open por `return Response.redirect(loginUrl, 302)` (línea 96 de middleware.ts).
- **Limitación conocida** (P1 follow-up):
  - Cookie tiene Max-Age = token exp (~1h). Supabase JS refresca tokens en memoria pero no actualiza la cookie. Resultado: usuarios en sesión activa son rebotados a login cada ~1h. Fix limpio = listener `supabase.auth.onAuthStateChange` en cada HTML protegido que re-setea cookie. Pesado para MVP; aceptamos el rebote por ahora.

**P0-3. Triple fuente de sesión desincronizada** — `login.html:397-406` + `js/auth.js:7-42` + backend `auth_router.py` (FIX PARCIAL APLICADO 2026-05-25)
- Tres mecanismos coexisten: Supabase token, `cx_user` JSON, `cx_session` legacy. Logout en uno no limpia los otros.
- **Aplicado**: `logout.html` ahora llama `supabase.auth.signOut({ scope: 'global' })` (revoca refresh token server-side, mata sesiones en todos los devices del usuario), limpia `cx_session` legacy, mantiene la limpieza previa de localStorage/sessionStorage/IndexedDB/cookies, y tiene fallback de 2s si signOut cuelga.
- **Pendiente**: `js/auth.js` ya murió (P0-1) y `cx_session` no se escribe más. Backend `auth_router.py` queda fuera de scope hasta que se decida si vive o muere en P0-2.

**P0-4. Listas de emails autorizadas duplicadas** — `login.html:~340-360` (ADMIN_EMAILS/CLIENT_EMAILS) y `contexia-wizard/app/dashboard/page.tsx:10-18`
- Dos listas hardcodeadas que pueden divergir. Ya divergen: `dashboard/page.tsx` incluye `fperez@ferez.co` y `cliente@demo.co`; `login.html` debe verificarse.
- **Acción**: mover a `app_metadata.role` en Supabase (fuente única), eliminar listas locales.

### P1 — funcionales / deuda

**P1-1. `/wizard/dashboard/` era código muerto** (RESUELTO 2026-05-25)
- Decisión: **eliminado**. Sin emails dual-role, el router por rol no aporta nada (login.html ya decide destino con email-lookup puro).
- **Aplicado**:
  - Carpeta `contexia-wizard/app/dashboard/` borrada por completo.
  - `vercel.json`: agregados redirects `/wizard/dashboard` y `/wizard/dashboard/` → `/login.html` (red de seguridad para bookmarks viejos).
  - 0 referencias restantes en el repo (grep limpio).

**P1-2. Bundles `_next/static/chunks/*.js` huérfanos en root** — origen probable del SyntaxError admin
- Restos de un build anterior de Next que conviven con el wizard nuevo. Posible mismatch de versión cargado por `app-admin/index.html`.
- **Acción**: auditar qué bundle carga `app-admin/index.html`; borrar bundles huérfanos.

**P1-3. OAuth callback redirige a `/login.html?oauth=1`** — `login.html:443`
- Tras OAuth, vuelve al login y un handler en línea 459+ rerutea. Funciona pero suma un round-trip visible y enmascara errores.
- **Acción**: usar `/wizard/auth/callback/` dedicado.

**P1-4. Sin logging auditable de intentos de login** — `login.html:418-436` (FIX APLICADO 2026-05-25)
- Violación directa de CLAUDE.md §2 ("loggeable: cada transacción registrada con timestamp, user, before/after").
- **Aplicado**:
  - Migration `contexia-wizard/supabase/migrations/20260525_create_auth_audit.sql` — tabla `auth_audit` con RLS habilitada (sin policies = solo service_role escribe/lee).
  - Endpoint `contexia-wizard/app/api/auth/audit-login/route.ts` — POST con email, outcome, method, requested_role, resolved_role, destination, ip, user_agent.
  - `login.html` POSTea fire-and-forget con `keepalive: true` (sobrevive al redirect) en cada submit (success + 2 tipos de error).
- **Pendiente**: correr la migration en Supabase (manual o via `supabase db push`). OAuth path (signInWithOAuth) aún no audita — se hace en T-followup junto con P1-3 (callback dedicado).

**P1-5. Wizard Next configurado con `basePath: "/wizard"` pero `vercel.json` no rewritea `/wizard/*` al build de Next**
- `next.config.ts:5` declara basePath; en `vercel.json` solo veo redirects para `/wizard/login/` y `/wizard/`. Hay que verificar que Vercel realmente sirve el build Next bajo `/wizard/*`.
- **Acción**: verificar `vercel.json` completo + Project Settings de Vercel.

**P0-5. Toggle "Cliente/Admin" en `login.html` era cosmético** — `login.html:363-394` (RESUELTO POR SIMPLIFICACIÓN 2026-05-25)
- **Decisión del usuario**: matar el patrón dual-role completamente. Cada email mapea a exactamente UN rol. Cuentas de prueba:
  - `contexia.marketing@gmail.com` → admin
  - `growth@contexia.online` → cliente
- **Aplicado**:
  - `login.html`: borrado `DUAL_ROLE_EMAILS`, `isDualRoleEmail()`, lógica condicional en `destinationFor()`. Toggle UI siempre oculto (`syncRoleVisibility` lo fuerza hidden).
  - `CLIENT_EMAILS` actualizado: `["growth@contexia.online", "fperez@ferez.co", "carlos@importacionesmtz.co"]`.
  - `destinationFor()` vuelve a ser puro email-lookup, simple.
- **Beneficio secundario**: resuelve también [[P1-1]] (decisión sobre `/wizard/dashboard/` — ver abajo).

**P0-6. Deployment legacy `app.contexia.online` sigue vivo y reaparece** — confirmado por usuario 2026-05-25
- Subdominio fantasma de una versión PWA anterior. Debe morir.
- Tres capas posibles donde sigue vivo (matar las tres):
  1. **DNS**: registro CNAME `app.contexia.online` → algún host (Vercel/Netlify/Cloudflare). Eliminar registro en el DNS provider.
  2. **Vercel/Netlify Project**: deployment activo con dominio asignado. Quitar el dominio del project Y pausar/borrar el project si no se usa.
  3. **Service Worker cacheado** en navegadores de usuarios existentes. Subir un `sw.js` "kill switch" al deployment legacy ANTES de bajarlo (que haga `self.registration.unregister()` + `caches.delete()` de todo y redirija a `contexia.online`). Sin esto, usuarios con la PWA instalada seguirán viendo la versión vieja aunque DNS y Vercel mueran.
- **Hallazgos 2026-05-25** (curl directo):
  - `Server: Vercel`, `X-Vercel-Id: iad1::...` → Vercel confirmado.
  - `Last-Modified: 2026-05-23` → **deploy de hace 2 días**, no es fósil olvidado. Coincide con fecha del hotfix `auth-logout-20260524.js` en `contexia.online/app/bunker` → sospecha fuerte de **pipeline CI/CD deployando a 2 projects en paralelo** (Git integration duplicada).
  - `/sw.js` y `/service-worker.js` → 404. **No hay PWA con service worker** → no se necesita kill-switch.
  - `X-Matched-Path: /_not-found` → es Next.js.
  - `findstr` en repos locales → 0 matches de `app.contexia.online` → la asignación del dominio vive en Vercel dashboard, no en código.
- **Acción** (plan simplificado, ~30 min de trabajo manual):
  1. T11 — Identificar Vercel project: dashboard.vercel.com → Domains → buscar `app.contexia.online` → click muestra qué project lo sirve.
  2. T12 — En ese project: Settings → Git → Disconnect (corta el auto-redeploy que lo está manteniendo vivo).
  3. T13 — Mismo project: Settings → Domains → Remove `app.contexia.online`.
  4. T14 — DNS provider (Cloudflare/GoDaddy/donde tengas el dominio `contexia.online`): eliminar CNAME `app`.
  5. T15 — En Vercel: Settings → Advanced → Delete Project (o renombrar a `_archived-app-contexia-legacy` si querés conservar el historial).
  6. T16 — Verificar tras 5-10 min: `curl -I https://app.contexia.online` debe dar NXDOMAIN, connection refused, o 404 sin headers de Vercel.

### P2 — limpieza

- **P2-1.** `crear-empresa-wizard.html` (root) vs `contexia-wizard/` (Next) — dos wizards. Confirmar cuál es vivo.
- **P2-2.** `test_login.py`, `__next.__PAGE__.txt`, `all_commits.txt` y demás huérfanos en root.
- **P2-3.** `landing.html` carga su propio fragmento de auth — auditar.

---

## 3. Flujo esperado vs real

### Esperado (según handoff MVP SSO)
```
Usuario → /wizard/login/ (UI Next) → Supabase Auth
       → /wizard/auth/callback/ (server, set cookie httpOnly)
       → middleware.ts valida sesión en /app/*
       → Redirige por rol a /app/bunker (admin) o /app/overview (cliente)
       → /app/* sirve HTML protegido
```

### Real (observado en código)
```
Usuario → / (Vercel redirect) → /landing.html
       → click "Acceso" → /login.html (canónico, pero LEGACY de hecho)
       → signInWithPassword (Supabase JS, client-only)
       → localStorage.setItem("token", ...) + localStorage.setItem("cx_user", ...)
       → window.location.assign("/app/bunker" | "/app/overview")
       → Vercel rewrite → /app-admin/index.html  ⚠️ bundle con SyntaxError
                       o /app/overview.html      ⚠️ sin validación server-side
       → HTML decide client-side si mostrar o no contenido (frágil)

/wizard/dashboard/ ← código muerto, nunca se llega por el happy path
/wizard/login/     ← no existe en Next; Vercel lo redirige a /login.html
```

**Punto de quiebre 1**: post-login no hay validación server-side; cualquier URL `/app/*` directa funciona.
**Punto de quiebre 2**: el router por rol del wizard (`dashboard/page.tsx`) se baipasea — `login.html` ya decide destino solo.
**Punto de quiebre 3**: `app-admin/index.html` carga bundle Next viejo que rompe con SyntaxError.

---

## 4. Plan de remediación

### Opción A — Limpieza quirúrgica (recomendada para MVP, 1-2 días)

Mantiene `login.html` como UI canónica (ya funciona con Supabase), añade gate server-side y elimina legacy.

| Tarea | Archivo(s) | Criterio de aceptación |
|---|---|---|
| T1 | Borrar `js/auth.js` y todas sus referencias `<script src>` en HTMLs root | grep `auth.js` → 0 matches. App sigue cargando. |
| T2 | Borrar `localStorage["cx_session"]` writes/reads donde existan | grep `cx_session` → 0 matches |
| T3 | Migrar `ADMIN_EMAILS`/`CLIENT_EMAILS` a `app_metadata.role` en Supabase (script de migración) | Usuarios de prueba con rol en metadata, login.html lee de `data.user.app_metadata.role` no de listas locales |
| T4 | Crear `middleware.ts` en raíz de Vercel (Edge Function) que valide JWT Supabase de cookie httpOnly antes de servir `/app/*` y `/app-admin/*` | Acceso directo a `/app/bunker` sin cookie → 302 a `/login.html`. Con cookie válida y rol admin → sirve. Con cookie cliente → 302 a `/app/overview`. |
| T5 | Cambiar `login.html:430` de `localStorage` a setear cookie httpOnly vía endpoint `POST /api/auth/session` (Next API route en wizard) | Tras login, cookie `sb-access-token` presente. localStorage solo guarda metadata no sensible. |
| T6 | Crear `POST /api/auth/audit-login` en wizard que escriba a tabla Supabase `auth_audit` (email, timestamp, ip, ua, ok/fail, before_role/after_role) | Cada submit en login.html produce 1 fila en `auth_audit` |
| T7 | Eliminar bundles huérfanos `_next/static/chunks/*.js` de root; auditar qué carga `app-admin/index.html` y arreglar referencia | `app-admin/index.html` carga sin SyntaxError. Network tab sin 404. |
| T8 | Decidir: eliminar `contexia-wizard/app/dashboard/` O enrutar `login.html` → `/wizard/dashboard/` como single point of role routing | Documentado en spec; código alineado. |
| T9 | Reescribir `logout.html` para `supabase.auth.signOut()` + `fetch("/api/auth/session", {method:"DELETE"})` + `localStorage.clear()` | Tras logout, cookie y localStorage limpios; acceso a `/app/bunker` rebota. |
| T10 | Actualizar `vercel.json`: confirmar que `/wizard/*` enruta al build Next del wizard, no a estáticos root | `/wizard/onboarding/` carga UI Next, no 404 |

**Riesgo**: bajo. No toca lógica de negocio. Reversible commit a commit.
**Costo**: ~1.5 días.
**Deuda residual**: `login.html` sigue como HTML estático (no Next). Aceptable.

### Opción B — Refactor completo a wizard como única SPA (1-2 semanas)

Mueve TODO el auth + shell dentro de `contexia-wizard/`. `/app/*` se renderiza como rutas Next protegidas; HTMLs root se retiran progresivamente.

| Tarea | Detalle |
|---|---|
| B1 | Crear `contexia-wizard/app/login/page.tsx` (port de `login.html` a React + tema) |
| B2 | Crear `contexia-wizard/app/(protected)/app/[module]/page.tsx` con grupo de ruta protegida |
| B3 | Middleware Next nativo (`contexia-wizard/middleware.ts`) — más simple que Edge Function global |
| B4 | Portar `/app/overview`, `/app/bunker`, `/app/fiscal`, etc. uno por uno desde HTML a componentes React |
| B5 | Borrar `vercel.json` rewrites de `/app/*` cuando todos migren |
| B6 | Deprecar `app-admin/`, `app/*.html`, `login.html`, `logout.html`, `landing.html` |

**Riesgo**: medio-alto. Toca UI productiva. Posibles regresiones visuales/funcionales por cada módulo migrado.
**Costo**: 1-2 semanas dedicadas (5+ módulos a portar).
**Deuda residual**: cero. Una sola SPA, un solo modelo de auth.

### Recomendación

**Opción A ahora (MVP Envigado, 5→16 usuarios fundadores).** Razones:
1. CLAUDE.md §1 (plantillas reusables): el middleware Edge + cookie pattern es reusable para futuros tenants sin refactor.
2. CLAUDE.md §3 (spec → tasks → verify): A tiene 10 tareas verificables independientes, cada una commit auditable. B es monolítica.
3. Compliance fiscal (CLAUDE.md §2): T6 (logging auditable) cierra el gap regulatorio inmediato. B lo pospone.
4. Riesgo bajo + reversibilidad alta para una semana crítica de captación de usuarios.

**Opción B en backlog post-MVP** como spec separada `specs/refactor-wizard-spa.md` cuando los 5 módulos legacy se estabilicen.

---

## 5. Checklist de verificación manual post-fix

**Usuarios de prueba** (deben existir en Supabase con `app_metadata.role`):
- `contexia.marketing@gmail.com` → dual (admin + cliente)
- `cliente@demo.co` → cliente
- `fperez@ferez.co` → cliente

**Navegadores**: Chrome desktop, Safari iOS, Firefox desktop.

**Casos**:

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Visitar `/` sin sesión | 302 → `/landing.html` |
| 2 | Click "Acceso" desde landing | → `/login.html` (canónico) |
| 3 | Login con `cliente@demo.co` correcto | → `/app/overview`, cookie `sb-access-token` set, fila en `auth_audit` |
| 4 | Login con `contexia.marketing@gmail.com` | → `/wizard/dashboard/` (role choice) → click "Bunker Admin" → `/app/bunker` |
| 5 | Login con password incorrecto | mensaje error, fila en `auth_audit` con `ok=false` |
| 6 | Visitar `/app/bunker` directo SIN sesión | 302 → `/login.html` con `?next=/app/bunker` |
| 7 | Visitar `/app/bunker` con sesión de `cliente@demo.co` (sin rol admin) | 302 → `/app/overview` (no debe colarse) |
| 8 | Refresh en `/app/overview` con sesión válida | Mantiene sesión, no rebota |
| 9 | Esperar expiración de token (o forzar) y navegar | Auto-refresh Supabase OK; si no, 302 → login con `?next=` |
| 10 | Click "Cerrar sesión" en `/app/*` | → `/logout.html` → `/landing.html`; volver atrás del browser no recupera sesión |
| 11 | Login OAuth Google | → callback → `/app/<destino>` sin pasar visiblemente por `login.html?oauth=1` |
| 12 | Bundle admin: abrir `/app/bunker` con devtools console abierta | **0 SyntaxError**, 0 chunks 404 |
| 13 | Logout y verificar `localStorage` | Vacío de keys `token`, `cx_user`, `cx_session` |
| 14 | Tabla `auth_audit` después de los 13 casos | 1 fila por intento (≈10-12 filas), con before/after role y timestamps UTC |

---

## 6. Fuera de alcance

- Migración de módulos `/app/*.html` a Next (Opción B — spec separada).
- Cambios en backend FastAPI `auth_router.py` — solo se elimina si T4 demuestra que es redundante.
- UI visual del login (login.html ya tiene tema canónico aprobado).
- SSO con Microsoft/Apple — solo Google + email/password en este MVP.

---

## 7. Próximos pasos

1. Validar esta spec con stakeholder (Juan).
2. Crear tareas T1-T10 en gestor de tickets.
3. Branch `feat/sso-cleanup-2026-05-25` desde `develop`.
4. T1-T2 en primer commit (deleciones, bajo riesgo).
5. T4 y T5 son los gates críticos — requieren PR review y verificación manual antes de merge.
