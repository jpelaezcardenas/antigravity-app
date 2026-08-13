# Instrucciones para los dos hilos de MCP (HubSpot y Canva)

Ninguno de los dos puede activarse desde un hilo no-interactivo — la autorización OAuth la tienes
que hacer tú. Estos son los dos hilos separados, cada uno con su prompt de arranque.

**Cómo autorizar (aplica a los dos, hazlo ANTES de abrir el hilo):**
- Si usas la app de Claude / claude.ai → ajustes de **conectores** → busca el servicio → Conectar.
- Si usas la terminal → sesión interactiva de `claude` → comando `/mcp` → selecciona el servidor →
  sigue el flujo del navegador.
- Nunca le pases al agente el código de autorización, el token ni la URL de callback. El agente no
  los necesita y no debe manejarlos.

---

## HILO 1 — HubSpot

**Nombre sugerido del hilo:** `CTX · HubSpot sync (CRM B2B/B2C)`

### Antes de abrirlo
1. Crea la cuenta gratuita de HubSpot con el correo corporativo de Contexia
   (`contexia.marketing@gmail.com`), no con tu correo personal.
2. Autoriza el conector `hubspot` (ver arriba).
3. Verifica en el hilo que responde: pídele al agente que liste tus pipelines antes de nada.

### Prompt de arranque

```
Vamos a evaluar e integrar HubSpot (free tier) con el CRM que Contexia ya tiene en Supabase.
Este es un hilo dedicado a HubSpot — el CRM propio y la campaña Renta Natural viven en otros hilos.

CONTEXTO OBLIGATORIO (léelo antes de proponer nada):
- HANDOFF-RENTA-NATURAL-2026.md — estado real verificado del CRM
- ARCHITECTURE.md, CLAUDE.md, HARNESS.md — canon del repo
- El CRM propio NO se reemplaza. Supabase sigue siendo la fuente de verdad operativa
  (b2b_clients, b2b_payments, crm_leads). HubSpot entra como capa comercial/reportes al lado.

PRIMER PASO — verificación real, no supuestos:
1. Confirma que el MCP de HubSpot responde: lista los pipelines, propiedades y objetos disponibles
   en la cuenta free.
2. Contrasta contra los límites documentados del free tier (1 pipeline de deals, 1.000 contactos
   en cuentas nuevas, 2 usuarios, sin workflows). Dime qué de eso es REAL en mi cuenta.
3. Solo entonces propón el diseño de sincronización.

DISEÑO PRELIMINAR A VALIDAR (no lo des por bueno sin verificar):
- Dirección: Supabase -> HubSpot, UNIDIRECCIONAL primero (evita conflictos de "quién manda").
- b2b_clients -> Companies; crm_leads -> Contacts + Deals.
- Autenticación desde el backend: Private App Access Token (no OAuth completo).
- Disparo del sync: Hermes hace polling, igual que el patrón ya construido para Manus
  (apps/hermes-manus-poller/) — las credenciales externas viven local con Hermes, nunca en Railway.
- En el Búnker: solo lectura — un badge "Sincronizado ✓" + link al registro de HubSpot.

DECISIÓN QUE DEBES AYUDARME A TOMAR:
Con 1 solo pipeline gratis, ¿alcanza para modelar B2B retainers + embudo B2C Renta Natural a la vez,
o hay que elegir uno? Dame la recomendación con el tradeoff real, no las dos opciones.

Sigue OpenSpec (propose -> design -> spec -> tasks -> apply -> Stage 11 -> archive) y el harness.
No codifiques hasta que apruebe el plan.
```

### Qué esperar
El agente debería **cuestionar** si HubSpot aporta lo suficiente dado que ya tienes CRM propio
funcionando. Esa es la respuesta correcta, no complacencia — deja que argumente.

---

## HILO 2 — Canva

**Nombre sugerido del hilo:** `CTX · Canva creatives (Renta Natural 2026)`

### Antes de abrirlo
1. Autoriza el conector `canva` (ver arriba).
2. Ten a mano la pieza de referencia: el creative del Post #1 (azul marino con circuitos, logo 3D,
   tarjetas verde lima/cian, CTA WhatsApp verde degradado). Ese es el branding canónico.

### Prompt de arranque

```
Vamos a producir los creatives de la campaña Renta Natural 2026 con Canva.
Este es un hilo dedicado a creatives — la arquitectura y el CRM viven en otros hilos.

CONTEXTO OBLIGATORIO:
- .antigravity/GROUND_TRUTH.md — MANDA en identidad y límites legales. Contexia es Entidad B
  (empresa TIC/AAA), NO firma contable regulada. Nunca prometas resultados fiscales ni
  "protección contra multas".
- HANDOFF-RENTA-NATURAL-2026.md — contexto de la campaña.

CIFRAS FISCALES — USA EXACTAMENTE ESTAS (verificadas contra Resolución DIAN 000193/2024 y 238/2025,
y corregidas en el repo en el commit 8de4dad). NO las recalcules ni las redondees:
- UVT 2025 (aplica a la declaración de Renta 2026, que evalúa ingresos de 2025): $49.799
- UVT 2026 (sanciones y umbrales vigentes hoy): $52.374
- Tope de ingresos / compras / consignaciones para declarar: $69.718.600 (1.400 UVT)
- Tope de patrimonio: $224.095.500 (4.500 UVT)
- Sanción mínima: $523.740 (10 UVT 2026) — se comunica como "$524K"
- Fechas: 12 de agosto a 26 de octubre de 2026, escalonadas por los dos últimos dígitos del NIT

REGLAS DE MARCA (no negociables):
- Branding canónico del Post #1: fondo azul marino con circuitos, logo 3D oficial, tarjetas
  verde lima/cian, CTA de WhatsApp en verde degradado.
- NUNCA incluyas una URL dentro del creative. El link va en el copy o en el primer comentario.
- Copy corto: 120-200 caracteres, espejo del quiz de 3 preguntas de la landing.
- Tono: claro, empático, protector, directo. Sin jerga opaca.
- Landing válida: https://www.contexia.online/landing.html (con .html — /landing.htm da 404)
- WhatsApp: wa.me/573106229289

FLUJO DE TRABAJO CON CANVA MCP (en este orden, siempre):
1. generate-design (o generate-design-structured) con el brief
2. create / edit según haga falta
3. export-design como PNG
No te saltes el export — el PNG es el entregable.

PRIMER PASO:
1. Confirma que el MCP de Canva responde: lista mis brand kits y plantillas disponibles.
2. Muéstrame UN creative de prueba antes de producir la serie completa, para validar branding.

Después de mi visto bueno, produce las piezas del calendario editorial (2/semana: martes Reel,
jueves carrusel/infografía).
```

### Qué esperar
El agente debe pedirte validación del primer creative antes de producir en serie. Si empieza a
generar 8 piezas de una, córtalo — el punto de control visual es lo que evita rehacer todo.

---

## Nota sobre los otros conectores

Hay ~36 servidores MCP más pendientes de autorización en tu entorno (Figma, Notion, Linear, Gong,
Similarweb, etc.). **No los autorices "por si acaso"** — cada conector autorizado es superficie de
acceso a datos. Autoriza solo el que vayas a usar en el hilo que estés abriendo.
