# HANDOFF — Agentic OS port (blocked on T23 tunnel hardening)

## Proyecto

**Nombre**: antigravity-app (Contexia)
**Owner ahora**: sesión de Claude Code que cerró T23 (parcial) 2026-07-19
**Owner siguiente**: nueva sesión de Claude Code
**Contexto**: Contexia, GPS Financiero para PyMEs colombianas. El Búnker (`contexia.online/app/bunker`) es el panel admin interno. Este handoff es para terminar el port de la sección "Agentic OS" del sidebar del Búnker — hoy placeholder "coming soon".

---

## Estado Actual

### Qué está listo para usar
- [x] Búnker con sidebar de 6 secciones (Dashboard, CRM/Ventas, Onboarding, Social Content Ops, Agentic OS, Configuración) — `contexia-app/app/app/bunker/page.tsx`. Deployado, verificado, archivado (`openspec/changes/archive/2026-07-19-bunker-admin-sidebar-nav/`).
- [x] Infrastructure Dashboard (Dashboard section) — estático, con gráficas SVG nativas.
- [x] Social Content Ops (9 tabs reales, backend canónico) — archivado (`openspec/changes/archive/2026-07-19-bunker-social-content-ops-port/`).
- [x] Onboarding (real, backend canónico) — archivado (`openspec/changes/archive/2026-07-19-bunker-onboarding-port/`).
- [x] **T23 parcial** (`openspec/changes/hermes-multi-tenant-wrapper/tasks.md`, buscar "T23"): `api/hermes/status.ts` ahora exige `Authorization: Bearer <HERMES_TUNNEL_TOKEN>` antes de hacer proxy al túnel — verificado en vivo: sin token → 401, con token correcto → pasa al proxy (502 solo porque Hermes no estaba corriendo en ese momento). Token nuevo generado y ya seteado en Vercel producción (`HERMES_TUNNEL_TOKEN` + `NEXT_PUBLIC_HERMES_TUNNEL_TOKEN`). **Pendiente que el usuario guarde el valor en Bitwarden** (`Contexia/Infrastructure/Hermes-Tunnel-Token`) — el valor se mostró una sola vez en el chat anterior, no quedó guardado en ningún archivo por seguridad. Si no lo guardó, hay que regenerarlo.

### Qué está en progreso / bloqueado
- [ ] **Agentic OS (sección del sidebar)**: sigue como placeholder "coming soon". Bloqueador real: el túnel Cloudflare hoy es un **quick tunnel efímero** (`*.trycloudflare.com`, resuelto dinámicamente desde la tabla Supabase `hermes_tunnel`), no un **named tunnel** persistente. Migrar a named tunnel requiere `cloudflared tunnel login` (abre OAuth en navegador) + `cloudflared tunnel create` — **el usuario tiene que correr esto él mismo**, un agente no puede.
  - Next exacto: el usuario corre los comandos de la sección "Cómo Correr Todo Localmente" abajo. Cuando el named tunnel exista, la siguiente sesión:
    1. Completa T23 paso 1 (escribir `.cloudflared/config.yaml` con el `ingress` real).
    2. Porta `frontend/dashboard/src/components/ops/AgenticOpsView.tsx` → `contexia-app/components/bunker/agentic-os/AgenticOsSection.tsx`, **corrigiendo el bug de ruta**: el componente viejo llama a `/api/hermes/os-status` (no existe); la ruta real es `/api/hermes/status` (`antigravity-app/api/hermes/status.ts`).
    3. Añade un estado explícito "Hermes no conectado ahora mismo" para el caso 502 (Hermes/cloudflared apagado) — mismo patrón de degradado gracioso que Social Content Ops/Onboarding, nunca pantalla en blanco ni error crudo.
    4. Mismo patrón que los ports anteriores: OpenSpec change nuevo (`bunker-agentic-os-port` o similar) → proposal/design/specs/tasks → build → verificar local (apuntando `.env.development.local` temporalmente a producción, revertir después) → sync `contexia-app/out/` → `app/` → commit/push → verificar Vercel → reporte Stage 11 → archivar.

### Qué está roto o pending
- [ ] `login.html` (pantalla demo de credenciales) + `middleware.ts`'s `ADMIN_ONLY` gate — el usuario pidió pausar esto explícitamente, sigue sin tocar. No retomar sin que el usuario lo pida.
- [ ] Token `HERMES_TUNNEL_TOKEN` sin confirmar guardado en Bitwarden (ver arriba).

---

## Cómo Correr Todo Localmente (lo que el usuario debe hacer para desbloquear)

```bash
# 1. Login interactivo a Cloudflare (abre navegador, requiere cuenta Cloudflare)
cloudflared tunnel login

# 2. Crear un tunnel con nombre (persistente, no efímero)
cloudflared tunnel create hermes-gateway
# Esto genera ~/.cloudflared/<tunnel-id>.json (credentials-file)

# 3. Escribir antigravity-app/.cloudflared/config.yaml (NO existe hoy, hay que crearlo):
```
```yaml
tunnel: <tunnel-id>
credentials-file: ~/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: hermes-gateway.contexia.local   # o el hostname real que se decida
    service: http://localhost:8642
  - service: http_status:404
```
```bash
# 4. Correr el tunnel (mantiene el proceso vivo mientras Hermes esté activo)
cloudflared tunnel run hermes-gateway

# 5. Actualizar la tabla Supabase hermes_tunnel con la URL nueva (si el wrapper
#    PC-side que ya existe no lo hace automático para named tunnels)
```

**Env vars relevantes ya configurados en Vercel** (no re-crear, solo confirmar):
- `HERMES_TUNNEL_TOKEN`: gate de auth en `api/hermes/status.ts` (ya seteado, valor solo en Bitwarden/chat anterior)
- `NEXT_PUBLIC_HERMES_TUNNEL_TOKEN`: mismo valor, visible en el browser (aceptado, ver comentario en el código)
- `HERMES_WEBHOOK_SECRET`: firma HMAC saliente hacia Hermes (ya existía, sin tocar)
- `NEXT_PUBLIC_HERMES_GATEWAY_URL`: fallback si Supabase no resuelve (ya existía)

---

## Estructura relevante del repo

```
antigravity-app/
├── api/hermes/status.ts                    # Proxy Vercel → cloudflared → Hermes gateway (T23 done aquí)
├── contexia-app/
│   ├── app/app/bunker/page.tsx             # Composición del Búnker, sección "agentic-os" sigue en ComingSoonSection
│   └── components/bunker/
│       ├── social-ops/                      # Referencia de patrón (9 tabs reales, ya portado)
│       └── onboarding/                      # Referencia de patrón (ya portado)
├── frontend/dashboard/src/components/ops/
│   └── AgenticOpsView.tsx                   # Componente viejo a portar (fuente)
├── openspec/changes/hermes-multi-tenant-wrapper/
│   └── tasks.md                             # T23 completo con todo el detalle real (buscar "T23")
└── openspec/changes/archive/2026-07-19-bunker-*  # Los 3 ports anteriores ya archivados, como referencia de patrón
```

---

## Decisiones Importantes

- **Por qué Hermes es local-only**: soberanía de datos financieros (`ARCHITECTURE.md` decisión #1). No es negociable sin un ADR explícito.
- **Por qué el token viaja también como `NEXT_PUBLIC_*`**: el Búnker llama al proxy desde el browser (same-origin), así que el token no puede ser 100% secreto — solo frena tráfico anónimo/bots, no es una barrera fuerte. Ver comentario en `api/hermes/status.ts`.
- **Por qué no toqué Railway**: `HERMES_TUNNEL_TOKEN` solo lo lee la función Vercel, nada en el backend FastAPI (Railway) lo usa. El texto original de T23 mencionaba Railway pero el código real no lo confirma.
- **Por qué no usé Bitwarden CLI**: `bw` está instalado pero sin sesión; desbloquearlo requeriría la master password, que un agente nunca debe manejar aunque el usuario lo autorice.

---

## Next Person (nueva sesión): Primeros pasos

1. Leer este archivo completo.
2. Leer `openspec/changes/hermes-multi-tenant-wrapper/tasks.md`, sección T23 (tiene todo el detalle técnico real, no resumido).
3. Preguntar al usuario: ¿ya corriste `cloudflared tunnel login` + `tunnel create`? ¿Guardaste el `HERMES_TUNNEL_TOKEN` en Bitwarden?
4. Si el named tunnel ya existe: escribir `.cloudflared/config.yaml`, cerrar T23, empezar el port de Agentic OS (ver pasos arriba).
5. Si no: dar las instrucciones de arriba y esperar a que el usuario las corra antes de escribir código.

---

## Contacto / continuidad

**Este archivo + `openspec/changes/hermes-multi-tenant-wrapper/tasks.md`** son la fuente de verdad completa — no hace falta releer todo el historial del chat anterior, todo el contexto necesario está aquí.
