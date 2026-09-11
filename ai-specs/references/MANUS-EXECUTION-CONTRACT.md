# Contrato operativo de Manus para el GTM de Contexia

Estado: **overlay de integración para validar contra el sistema real**  
Fuentes internas contrastadas: paquete `Manus-Contexia-Sell-Machine` v1.1.0 del 25 de julio de 2026, conversación operativa anexada el 10 de septiembre de 2026 y decisiones actuales del usuario.

## Dictamen

El paquete de julio no debe reconstruirse. Su separación en tres proyectos es útil y puede conservarse, pero necesita una actualización de autoridad, verdad comercial y gates antes de ejecutar la campaña de Renta Natural. La copia local verificada declara versión 1.1.0, contiene 64 archivos y todavía conserva 52 marcadores `POR_COMPLETAR` distribuidos en 48 líneas. Además coexiste un ZIP v1.0.0: debe archivarse o marcarse inequívocamente como obsoleto para evitar una reinstalación accidental.

La decisión vigente es:

> Hermes conserva la orquestación; Claude Code conserva especificación, verificación y aprendizaje; el Búnker conserva la aprobación; Manus ejecuta tareas externas aprobadas y devuelve evidencia.

Manus puede investigar, producir activos o operar plataformas, pero esas son modalidades de **ejecución**. Strategy y Content deben operar como sandboxes subordinados y de solo preparación; solo Operations puede realizar una acción externa aprobada. Manus no define estrategia final, no aprueba claims, no decide presupuesto y no modifica por sí mismo el sistema Hermes–Claude Code.

## 1. Qué ya existe y se conserva

| Proyecto Manus v1.1 | Función que se conserva | Autoridad máxima |
|---|---|---|
| CTX — Strategy & Market Intelligence | ejecutar investigación pública y devolver evidencia | recomendar; nunca decidir, publicar o gastar |
| CTX — Content Studio | materializar borradores y activos desde un brief aprobado | producir `DRAFT`; nunca aprobar ni publicar |
| CTX — Social Operations | publicar o medir un paquete exacto aprobado | ejecutar el alcance autorizado; nunca improvisar |

Controles valiosos ya descritos en v1.1:

- separación de proyectos y conectores;
- `Campaign Package` y `Approval Package`;
- aprobación humana en Búnker;
- Hermes como dispatcher y capa de idempotencia;
- hash de contenido, expiración y acciones/plataformas permitidas;
- perfil de navegador exclusivo y botón de detención;
- webhook firmado, ventana anti-replay y deduplicación de eventos;
- `dry_run`, pruebas de cuenta equivocada, hash incorrecto y duplicados;
- telemetría estructurada y reconciliación de resultados;
- prohibición de datos financieros y autoridad de aprobación en Manus.

## 2. Correcciones necesarias por el nuevo GTM

### 2.1 Verdad comercial

Los documentos compartidos a los tres proyectos en julio son un snapshot, no verdad perpetua. Deben reemplazarse o versionarse con:

- identidad Entidad A/Entidad B vigente;
- catálogo vigente leído del repositorio;
- registro de capacidades verificadas;
- ledger de claims aprobados;
- calendario DIAN oficial con fecha;
- límites de privacidad y consentimiento por finalidad;
- cupo real de Tatiana y estado del recorrido de cobro/entrega.

No se deben reutilizar precios, oferta, ICP, claims o estados de producto de julio sin revalidación.

### 2.2 Authority model

El proyecto Strategy de Manus no es la torre de control estratégica. Ejecuta búsquedas y resume evidencia; Claude Code contrasta fuentes y formula el experimento; la decisión es humana.

El proyecto Content no crea libremente una campaña para luego autoimpulsarla. Recibe un brief versionado, genera borradores y devuelve un manifiesto para claim-check y aprobación.

Operations no corrige sobre la marcha copy, audiencia, activo, CTA, calendario o presupuesto. Una modificación crea nueva versión y requiere nueva aprobación.

### 2.3 Resultado verificable

`structured_output.success=true`, una tarea terminada o un texto de confirmación no prueban publicación. Para `SUCCEEDED_VERIFIED` deben existir:

- estado de plataforma;
- ID o URL recuperable;
- cuenta/plataforma exacta;
- timestamp;
- hash o correspondencia con el activo aprobado;
- reconciliación independiente posterior;
- gasto real cuando aplique.

## 3. Contradicción resuelta: Chief of Staff versus brazo social

El texto previo asigna a Manus, al mismo tiempo, mantenimiento de runway, burn rate, cash on hand, CRM y correo, y luego prohíbe que toque datos financieros o tablas completas de clientes. Esas dos fronteras no pueden coexistir en el mismo contexto operativo sin un diseño de permisos distinto.

Para este GTM queda resuelto así:

- **Sell Machine:** Manus no recibe estados financieros, expediente tributario, base completa de CRM, correo privado, credenciales ni datos personales no necesarios.
- **Chief of Staff general:** cualquier función financiera, correo o CRM es otro flujo, con proyecto, permisos, finalidades, fuentes y aprobación propios; queda fuera de este kit hasta auditarlo.
- Los indicadores de campaña que Manus puede devolver son gasto de pauta, impresiones, clics, conversiones atribuidas y créditos de ejecución; no el Financial Pulse corporativo.

## 4. Contrato de despacho

### Entrada mínima Hermes → Manus

| Campo | Regla |
|---|---|
| `campaign_id`, `version`, `experiment_id` | estables y auditables |
| `approval_id`, aprobador, fecha, expiración | obligatorios; alcance granular |
| `content_hash` y activo | coincidencia exacta |
| plataforma y cuenta | allowlist; verificación antes de actuar |
| acción | `dry_run`, publicar, programar, pausar o medir; una lista explícita |
| audiencia y exclusiones | versión aprobada; sin ampliación automática |
| presupuesto, moneda, tope y duración | obligatorio para pauta; sin incremento automático |
| CTA, landing y UTM | probados antes del despacho |
| claims y versión de política | todos aprobados y enlazados |
| idempotencia, timeout y reintentos | controlados por Hermes |
| kill switch y fallback | propietario humano identificado |

El `Approval Package` también debe fijar: entidad anunciante, entidad prestadora, responsable del tratamiento, tipo de oferta, versión de Ground Truth, versión/hash del Claim Ledger, fuente/versionado del precio, resultado del gate de privacidad y cohorte DIAN cuando la pieza dependa de vencimientos. El hash debe cubrir copy, creativo, CTA, landing, audiencia, fechas, cuentas, presupuesto y claims; cualquiera de esos cambios invalida la aprobación.

### Salida mínima Manus → backend/Hermes

- task/request ID asociados al `approval_id`;
- estado de ejecución normalizado;
- resultado por plataforma y acción;
- URL/ID, timestamp y evidencia;
- publicación parcial o intervención requerida;
- gasto y moneda;
- métricas disponibles y fecha de lectura;
- créditos Manus estimados y reales;
- errores estructurados sin secretos;
- resultado de reconciliación.

Estados de negocio permitidos:

```text
BLOCKED
DISPATCHED
RUNNING
NEEDS_HUMAN
SUCCEEDED_UNVERIFIED
SUCCEEDED_VERIFIED
PARTIAL
FAILED_RETRYABLE
FAILED_FINAL
```

## 5. Créditos Manus Pro

Los 300 créditos diarios incluidos son capacidad disponible, no objetivo de consumo. Durante la primera semana debe medirse:

```text
créditos por investigación útil
créditos por borrador aprobado
créditos por activo aprobado
créditos por publicación verificada
créditos por métrica reconciliada
créditos desperdiciados por error, duplicado o pieza rechazada
```

Solo después se define un presupuesto por tipo de tarea. Se bloquea una tarea si excede el límite aprobado, repite trabajo disponible o no tiene decisión asociada.

## 6. Activación por etapas

1. **Read-only:** validar los tres proyectos, fuentes, conectores y permisos; research con citas.
2. **Content dry-run:** producir paquetes sin publicación; claim-check y hashes.
3. **Operations supervisado:** diez ejecuciones controladas con activos no sensibles y cuenta exacta.
4. **Orgánico aprobado:** automatizar solo tareas repetibles posteriores al Búnker.
5. **Pauta limitada:** presupuesto, audiencia, objetivo y kill switch aprobados por ejecución o regla estrecha.
6. **Optimización:** Claude Code recomienda `KEEP/ITERATE/STOP`; una persona aprueba; Manus aplica la nueva versión.

No se salta una etapa por tener créditos disponibles.

## 7. Gates específicos de Renta Natural

Antes de que Manus publique una campaña de Renta deben estar verdes:

- servicio y cupo de Entidad A;
- recorrido de triage, revisión humana, cotización, cobro y entrega;
- comerciante de registro y facturación correctos;
- copy sin conclusión automática, miedo o garantía tributaria;
- precio canónico y aprobación final de Tatiana;
- consentimiento de la captación y canal seguro de documentos;
- opt-in separado para cualquier oferta de Entidad B;
- landing, UTM, eventos y capacidad de pausa.

Si el SaaS sigue bloqueado pero el servicio de Renta está listo, Manus puede ejecutar únicamente la campaña profesional aprobada. No puede promocionar una capacidad SaaS no verificada.

## 8. Campos del paquete de julio que deben verificarse, no heredarse

- nombres e IDs reales de proyectos y conectores;
- disponibilidad y geografía de Creator Marketplace;
- URLs exactas de Facebook e Instagram;
- estado actual de My Browser y autorizaciones;
- endpoint y URL pública del webhook;
- esquema y firma vigentes de la API de Manus;
- implementación real de idempotencia, cola, reintentos y reconciliación;
- campos `POR_COMPLETAR` del snapshot local;
- tarea de Telegram y sus permisos actuales;
- uso de “skip confirmations”, que debe permanecer desactivado hasta evidencia suficiente.

También deben eliminarse o corregirse antes de usar el paquete:

- cualquier ejemplo con “Contexia te protege” u otra promesa absoluta;
- rutas de webhook inconsistentes, incluida la variante con y sin `/api/v1`;
- filas o dominios de ejemplo;
- divergencia entre `draft_pending_approval` y la máquina de estados `draft → pending_approval`;
- referencias a modelos, conectores o esquemas que la API vigente ya no reconozca;
- una API key, llave pública o ID copiado como si fuera vigente sin consulta actual.

## 9. Controles de cuenta, API y Telegram

- La API key de Manus vive solo en Hermes/backend y en un gestor de secretos; nunca en prompts, archivos de proyecto, Browser Operator o Telegram.
- El dispatch debe enviar allowlists explícitas de proyecto, skill, conector, cuenta y acción. No hereda herramientas por defecto ni reutiliza referencias de otras tareas.
- Browser Operator usa un perfil exclusivo, rol mínimo, 2FA y ninguna sesión de banca, correo, billing, Supabase admin o información privada.
- Una aprobación nunca llega como texto escrito por Manus: Hermes la consulta en Búnker y valida actor, expiración, alcance y hash.
- Para pauta, el esquema valida condicionalmente presupuesto, moneda, duración, audiencia y tope; no basta con que el JSON sea válido.
- Telegram se unifica mediante un bot gateway privado de Contexia; no mediante un grupo que intente hacer conversar al bot nativo de Manus con Hermes. Sirve para dar órdenes, recibir informes y abrir el Búnker. Un botón de publicar, reintentar, cambiar audiencia o gastar crea una nueva solicitud de aprobación; no ejecuta directamente. Véase `reference/TELEGRAM-CONTROL-ROOM.md`.
- El kill switch debe funcionar aunque Manus esté caído: detener despachos en Hermes, cerrar el perfil dedicado y revocar credencial/conector.

La presencia de una instrucción o contrato en archivos no demuestra que esté configurado en la cuenta, desplegado o probado.
