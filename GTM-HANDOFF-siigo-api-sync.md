# GTM-HANDOFF — Siigo API live sync (Vía 1)

> Documento técnico para la tarea de reemplazar la ingesta manual de CSV por sync automático
> vía Siigo API REST. Autocontenido: un agente sin contexto previo puede abrir un OpenSpec
> proposal solo con este archivo.

---

## §1 Decisión tomada

**Vía 1 — Siigo API REST directa.** Usar las credenciales de la cuenta comercial de Taty
(quien ya opera todos los clientes por NIT dentro de Siigo, con licencia activa y facturación
electrónica habilitada) para sincronizar asientos contables automáticamente, reemplazando la
carga manual de CSV.

**Qué se descarta y por qué:**

| Alternativa | Por qué se descarta |
|---|---|
| Integración DIAN directa | Requiere habilitación como Proveedor Tecnológico DIAN — costo regulatorio alto, innecesario porque Siigo ya expone los XML/CUFE de facturas emitidas |
| SyncManager inmediato | Aprobado como solución a escala (SaaS Azure+IA, $2M setup + $250K/mes), aplazado hasta que el volumen lo justifique; no bloquea esta tarea |

---

## §2 Estado verificado de Shadow GL — lo que ya existe en producción

Shadow GL está **en producción desde julio 2026**. No está "0% implementado" — ese dato del
handoff anterior (`contexia-mcp-servers/HANDOFF-RADAR-SHADOW-GL.md`) era falso. Lo que sí
está confirmado de ese handoff: las clases MCP `RadarRiskTool`/`ShadowGLIngestTool` fueron
**borradas** (no desactivadas). Cualquier exposición de Shadow GL/Radar vía MCP es trabajo
nuevo, no reactivación.

### En producción hoy

| Componente | Estado |
|---|---|
| Tablas `erp_journal_entries`, `erp_journal_lines` | ✅ En Supabase (migración `0016`) |
| Tabla `dian_xml_documents` | ✅ En Supabase (migración `0019`) |
| Flag `is_verified_real` | ✅ En ambas tablas de journal (migración `0042`) |
| `parse_siigo_csv()` | ✅ `apps/backend/services/shadow_gl_service.py:127` |
| `ingest_siigo_csv(tenant_id, csv_text, is_verified_real)` | ✅ `shadow_gl_service.py:408` |
| `ingest_dian_xml(tenant_id, raw_xml, is_verified_real)` | ✅ `shadow_gl_service.py:534` |
| Endpoints HTTP de ingesta | ✅ `apps/backend/presentation/shadow_gl_endpoints.py` |
| Radar scoring (0-100 por reglas) | ✅ `apps/backend/services/radar_service.py` |

### Ingesta hoy = CSV manual

`parse_siigo_csv()` procesa texto CSV exportado y subido manualmente. **Cero código de API
REST de Siigo** en ningún archivo del backend (`SiigoApiClient`, `api.siigo.com` — búsqueda
confirmada: cero resultados). Esta es la brecha que hay que cerrar.

### Cómo funciona el flag `is_verified_real`

- `is_verified_real=False` (default): dato sintético, seed de demo, fixture freemium
- `is_verified_real=True`: dato real verificado; activa las pantallas de datos reales en el cliente
- El job de sync automático debe pasar `is_verified_real=True` al llamar a `ingest_siigo_csv()`

---

## §3 La tarea a implementar

### 3.1 `SiigoApiClient` — nuevo servicio

**Ubicación recomendada:** `apps/backend/services/siigo_api_client.py`

**Responsabilidades:**

1. **Autenticación:** `POST https://api.siigo.com/auth` con `username` + `access_key` (credenciales de la cuenta comercial de Taty) → JWT. Reusar el patrón de cliente HTTP existente en el backend (httpx async, manejo de errores en banda).

2. **Consulta de asientos contables:** endpoints a confirmar contra `developers.siigo.com`, candidatos principales:
   - `GET /v1/journals` — asientos contables
   - `GET /v1/invoices` — facturas emitidas
   - `GET /v1/purchases` — compras
   - `GET /v1/vouchers` — comprobantes
   - `GET /v1/payment-receipts` — recibos de pago

3. **Mapeo al shape de `parse_siigo_csv()`:** la función devuelve una `List[Dict[str, Any]]` con los campos esperados por `ingest_siigo_csv()`. El cliente API debe producir exactamente el mismo shape, para reusar toda la lógica de validación existente (balance débito=crédito, CUFE único, centavos enteros) sin duplicarla.

4. **Sin write-back:** el sync es exclusivamente lectura desde Siigo. Cualquier operación de escritura de vuelta a Siigo requiere Approval Queue humano (Nous Never Approves).

### 3.2 Job de sync programado

**Candidato:** un script Hermes periódico (patrón de `pulso.sh`, `centinela.sh` ya operativos) que llama a un nuevo endpoint interno `POST /internal/siigo-sync/run` en el backend.

**Alternativa:** Hermes cron directo que importa y llama al cliente Python — evaluar según conveniencia operativa.

**Frecuencia inicial:** nocturna (una vez por día), con posibilidad de aumentar a varias veces al día en producción.

**Backfill controlado:** correr el sync primero contra **1 tenant piloto**, verificar `is_verified_real=True` y balance correcto en Supabase, antes de habilitarlo para todos los tenants.

### 3.3 Pregunta abierta — confirmar ANTES de codear

> ¿La cuenta comercial de Taty en Siigo = un solo credential set para acceder a todos los NITs de sus clientes, o cada NIT tiene sus propias credenciales en Siigo?

Esto determina el diseño del cliente:
- **Un credential set para todos los NITs:** el cliente simplemente cambia un parámetro de NIT/empresa en cada request — arquitectura simple.
- **Credenciales por NIT:** el cliente necesita un "credential broker" que resuelva las credenciales por tenant, patrón análogo a `core/tenant_context.py::resolve_request_tenant_scope()` — más trabajo, pero reutiliza el mismo patrón que ya funciona en el backend.

**Este es el primer paso real del hilo — confirmar con el fundador o con soporte de Siigo antes de abrir el OpenSpec change.**

---

## §4 Corrección del plan original

El plan en el txt fuente incluía la tarea:

> "Reactivar las MCP tools `RadarRiskTool`/`ShadowGLIngestTool` en `contexia-mcp-servers/contexia-agents/`"

**Esta tarea no aplica y debe eliminarse.** Las clases no existen (fueron borradas, no desactivadas). Si se quiere exponer Shadow GL/Radar vía MCP para Hermes, es un **nuevo trabajo** que requiere su propio OpenSpec change, no una reactivación.

---

## §5 Restricciones

- **Secretos:** `access_key` de Siigo va a Railway env vars y a Bitwarden. **Nunca a git ni al repo.** Nombre sugerido de la variable: `SIIGO_ACCESS_KEY` (y `SIIGO_USERNAME` si aplica por NIT).
- **Stage 11 obligatorio:** el change OpenSpec de esta tarea no se archiva sin deploy verificado en Railway y verificación de `is_verified_real=True` en Supabase con datos reales.
- **Nous Never Approves:** el sync es solo lectura. Si en algún momento el cliente necesita escribir de vuelta a Siigo (correcciones, notas), eso pasa por Approval Queue.
- **TDD:** tests contra `parse_siigo_csv()` + tests de integración del cliente con un sandbox de Siigo antes de apuntar a producción.

---

## §6 Primer paso para el hilo "Go to Market"

1. **Confirmar modelo de cuentas Siigo** (fundador o soporte Siigo) → un credential set o uno por NIT
2. **Abrir OpenSpec proposal** con el nombre sugerido `siigo-api-live-sync` usando el skill `openspec-propose` del repo
3. **Implementar `SiigoApiClient`** reutilizando la validación de `shadow_gl_service.py`
4. **Backfill piloto:** correr contra 1 tenant, verificar en Supabase (`execute_sql` vía MCP Supabase):
   ```sql
   SELECT id, tenant_id, is_verified_real, created_at
   FROM erp_journal_entries
   WHERE tenant_id = '<tenant-piloto>'
   ORDER BY created_at DESC
   LIMIT 10;
   ```
   Confirmar `is_verified_real=true` y que `debit_total = credit_total` (balance cuadrado).
5. **Habilitar para todos los tenants** solo después de que el piloto pase sin errores.

---

## §7 Referencias

| Recurso | Ruta |
|---|---|
| Función `parse_siigo_csv()` | `apps/backend/services/shadow_gl_service.py:127` |
| Función `ingest_siigo_csv()` | `apps/backend/services/shadow_gl_service.py:408` |
| Flag `is_verified_real` en Supabase | `apps/backend/migrations/0042_shadow_gl_is_verified_real.sql` |
| Spec de integridad del flag | `openspec/specs/shadow-gl-data-integrity/spec.md` |
| Spec del CSV parser (shape de referencia) | `openspec/specs/shadow-gl-siigo-csv-ingestion/spec.md` |
| Change archivado que dejó Siigo API fuera de alcance | `openspec/changes/archive/2026-08-13-shadow-gl-real-data-ingestion/proposal.md` |
| Documentación Siigo API | https://developers.siigo.com/docs/siigoapi |
| SyncManager (alternativa aplazada) | `../contexia-brain/` — análisis guardado en sesiones anteriores |
| Análisis conceptual SyncManager | `C:\Users\contexia\Downloads\Nominal y Contexia_ Análisis Tecnológico.md` |
| Handoff GTM general | `GTM-HANDOFF.md` (mismo directorio) |
