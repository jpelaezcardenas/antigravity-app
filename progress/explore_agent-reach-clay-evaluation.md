# Investigación — Agent Reach / Clay como hipótesis de producto futuro

**Fecha**: 2026-09-11
**Tipo**: Investigación (docs-only, sin código) — mismo patrón que
`auditoria-sombra-lead-capture-investigation` y `chatwoot-b2b-lead-capture-investigation`.
**Contexto**: Paso 4 del plan maestro GTM, explícitamente marcado como HIPÓTESIS, no compromiso
de build.

## Qué es Clay, concretamente

Clay es una plataforma de enriquecimiento de datos B2B: dado un nombre de empresa o contacto,
busca y devuelve datos de firmografía (tamaño, industria, tecnologías que usa) y de contacto
(cargo, correo, LinkedIn) desde fuentes públicas/agregadas. No es scraping propio de Contexia —
es un proveedor externo que ya hace ese trabajo y lo expone vía API/MCP.

## Estado real, verificado en vivo (no asumido)

- El MCP `plugin:sales:clay` está conectado a **`Juan's Workspace`** (workspace real, no una
  cuenta de prueba) — `workspaceId: 1235868`.
- Tiene créditos disponibles (`hasWorkspaceCredits: true`, `hasSalesRepCredits: true`).
- **Cero subroutines/funciones personalizadas configuradas** (`list_subroutines` devuelve lista
  vacía) — es decir, la cuenta existe y tiene presupuesto, pero nadie ha definido todavía un flujo
  de enriquecimiento específico para Contexia. Las herramientas genéricas disponibles (buscar y
  enriquecer una empresa, buscar y enriquecer contactos en una empresa, buscar y enriquecer una
  lista de contactos) sí están operativas hoy mismo, ad-hoc.

## Dónde encajaría en el GTM ya construido

El caso de uso que el fundador confirmó (enriquecimiento de leads, no scraping/outreach masivo)
encaja en un solo lugar del embudo ya documentado: **el score de ICP B2B**
(`ai-specs/gtm-kit/PLAYBOOK.md` §3.2), que hoy pide evidencia manual por dimensión (dolor
recurrente, ajuste al producto, evento crítico, acceso al comprador, preparación de datos,
economía, aprendizaje) sin ninguna fuente automatizada. Clay podría rellenar las dimensiones
verificables objetivamente (tamaño de empresa, tecnologías, cargo del contacto) — nunca las
subjetivas (dolor, urgencia), que siguen necesitando una conversación real.

**No encaja** en Renta Natural (B2C, personas naturales) — Clay es una herramienta de datos B2B.

## Gates de soberanía de datos aplicables (mismo principio que Hermes/GBrain/VoiceBox)

A diferencia de Hermes/GBrain/VoiceBox, Clay **no es un candidato a correr local** — es
inherentemente un servicio de terceros que agrega datos públicos, no un modelo de IA que procesa
datos sensibles de clientes. El riesgo es distinto y menor en naturaleza, pero real:

1. **Qué datos salen de Contexia hacia Clay**: solo nombre de empresa/contacto y campos ya
   públicos (LinkedIn, dominio) — nunca datos de clientes actuales (Shadow GL, expedientes
   tributarios, CRM interno) deben pasar a Clay como input de enriquecimiento.
2. **Auditabilidad de la fuente**: a diferencia de un scraper propio, Clay es una caja negra sobre
   de dónde saca sus datos — no se puede auditar su pipeline como si fuera código propio. Aceptable
   para datos de prospección (públicos por definición) pero no debe tratarse como fuente de verdad
   legal.
3. **Costo real por operación**: no verificado en esta investigación — antes de automatizar
   cualquier flujo, correr unas pocas búsquedas manuales y confirmar el costo en créditos por
   enriquecimiento contra el presupuesto disponible.

## Recomendación

**No abrir un change OpenSpec todavía.** Faltan dos decisiones del fundador antes de que tenga
sentido construir algo:

1. **Qué subroutine específica construir primero** — la herramienta más simple y de mayor
   apalancamiento sería enriquecer automáticamente cada lead que entra por el flujo B2B
   (`whatsapp-b2b-lead-bridge`, ya en producción) con firmografía de la empresa, para alimentar el
   score de ICP con menos trabajo manual. Pero eso es una elección de producto, no algo que deba
   decidir un agente.
2. **Presupuesto de créditos aceptable** — cuántas búsquedas/mes está dispuesto a gastar antes de
   que el costo de Clay compita con el valor que aporta.

Cuando el fundador tenga esas dos respuestas, la siguiente sesión puede abrir un change OpenSpec
chico y acotado (una sola subroutine, un solo punto de integración con `whatsapp-b2b-lead-bridge`),
siguiendo el mismo patrón de gates de soberanía de datos que ya rige Hermes/GBrain/VoiceBox en
`ARCHITECTURE.md`.
