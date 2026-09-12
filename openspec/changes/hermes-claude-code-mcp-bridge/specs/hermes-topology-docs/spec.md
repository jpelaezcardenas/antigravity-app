## ADDED Requirements

### Requirement: Documentación de Hermes libre de contenido fabricado
La documentación de Hermes en este repo (`docs/integrations/HERMES-SELF-CONFIG.md`,
`ARCHITECTURE.md`, `AGENTES.md`) SHALL describir únicamente perfiles, bots, jobs y rutas de
configuración verificados contra la instalación real de Hermes (dashboard, sistema de archivos, o
confirmación directa del fundador). Ningún nombre de rol, ruta, o componente SHALL aparecer en la
documentación sin una fuente verificable citada.

#### Scenario: Referencia a un rol sin evidencia real
- **WHEN** un documento de este repo menciona un rol, perfil o script de Hermes
- **THEN** ese nombre debe corresponder a un perfil real en `/home/contexia/.hermes/profiles/`
  (o la ruta que la Fase 0 de este change confirme como fuente de verdad), a un bot real visible
  en el Electron Desktop, o a un job real del dashboard de Scheduled Jobs — de lo contrario se
  elimina, no se deja como referencia sin verificar

#### Scenario: Los 3 roles fabricados quedan eliminados
- **WHEN** se revisa `docs/integrations/HERMES-SELF-CONFIG.md` tras este change
- **THEN** no aparece ninguna mención a `centinela-monitor`, `auditoria-runner`, ni
  `resolucion-executor`

### Requirement: Topología de Hermes documentada con sus tres piezas reales
`ARCHITECTURE.md` SHALL documentar las tres piezas reales de Hermes: el núcleo orquestador en WSL,
la app de escritorio Electron en Windows nativo, y el gateway que conecta el Electron Desktop al
backend de Contexia en Railway (`-175a`, `/api/v1/*`) — nunca directo a Supabase.

#### Scenario: Un lector de ARCHITECTURE.md busca cómo se conecta Hermes Desktop al backend
- **WHEN** se lee la tabla de contenedores de `ARCHITECTURE.md`
- **THEN** existe una fila para "Hermes Desktop (Electron)" que indica explícitamente que conecta
  vía el gateway Railway, no directo a Supabase

### Requirement: Fuente de verdad única de la config de Hermes confirmada
Este change SHALL resolver, mediante inspección directa de la máquina del fundador (no asunción),
si la fuente de verdad de la configuración de Hermes es `/home/contexia/.hermes/profiles/`,
`/home/contexia/hermes-workspace/`, ambas coexistiendo con roles distintos, o ninguna de las dos
rutas asumidas por el contexto previo del proyecto. El resultado SHALL quedar documentado en
`ARCHITECTURE.md` de forma explícita, citando cómo se verificó.

#### Scenario: Existe ambigüedad entre dos rutas de configuración candidatas
- **WHEN** se investiga si `/home/contexia/.hermes/` y `/home/contexia/hermes-workspace/` existen
  simultáneamente en la máquina del fundador
- **THEN** el resultado (una sola ruta vigente, o ambas con roles distintos y documentados) queda
  registrado en `ARCHITECTURE.md`, reemplazando cualquier suposición anterior no verificada

### Requirement: Scheduled Jobs de Hermes en producción sin errores de gateway
Los 8 Scheduled Jobs de Hermes en producción (Pulso Diario, Conciliación Shadow GL, Pulso Diario
Insight Bridge, Radar Predictivo, Centinela Fiscal, Auditoría Sombra, Social Ops, Metrics
Snapshot) SHALL completar su ciclo de ejecución sin `error` ni `delivery_failed` causado por
`SESSION_NOT_OWNED` o módulos de gateway desincronizados ("mixed sys.modules").

#### Scenario: Social Ops corre su siguiente ciclo tras el fix
- **WHEN** se observa la siguiente ejecución programada de Social Ops después de aplicar
  `hermes update`/`hermes gateway restart` y cerrar correctamente el lease huérfano
- **THEN** el job completa sin `delivery_failed` ni el error `SESSION_NOT_OWNED`

#### Scenario: Pulso Diario corre su siguiente ciclo sin interrupción
- **WHEN** se observa la siguiente ejecución programada de Pulso Diario después del fix de gateway
- **THEN** el job completa sin mostrar `error` ni "Interrupted by shutdown before terminal
  completion"

#### Scenario: No se fuerza un lease de sesión viva
- **WHEN** se diagnostica el lease huérfano de la sesión `20260829_193718_5b2db1` (pid 44191)
- **THEN** el proceso se confirma como terminado antes de cualquier acción, y si estuviera vivo,
  la sesión se cierra únicamente desde su superficie propietaria (CLI) — nunca se borra el lease
  a la fuerza
