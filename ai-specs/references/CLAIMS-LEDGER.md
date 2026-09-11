# Claims ledger — semáforo comercial

Estados:

- `APPROVED_CONDITIONAL`: utilizable solo con condición/límite indicado.
- `INTERNAL_DATED`: afirmación interna fechada; requiere verificación antes de hacerla pública.
- `CONFLICT`: fuentes internas se contradicen.
- `ROADMAP`: no comercializable.
- `BLOCKED`: no usar.

| Claim o tema | Estado | Redacción permitida | Bloqueo / prueba requerida |
|---|---|---|---|
| Contexia es Entidad B tecnológica | `APPROVED_CONDITIONAL` | “Contexia provee software y automatización” | verificar razón social y términos públicos |
| Contexia no firma declaraciones/estados/dictámenes | `APPROVED_CONDITIONAL` | límite visible en propuesta y landing | mantener rol A explícito |
| Entidad A presta el servicio profesional | `APPROVED_CONDITIONAL` | usar razón social real y profesional responsable | contrato/factura/política A |
| Claridad Predictiva | `APPROVED_CONDITIONAL` | macroconcepto seguido de resultado medible | no usar “exactamente”, “sin sorpresas” |
| Renta Natural desde $350.000 | `APPROVED_CONDITIONAL` | “desde…, varía por trámites, movimientos y patrimonio; Tatiana confirma” | leer catálogo vigente antes de publicar |
| Pulso $0 | `INTERNAL_DATED` | solo después de confirmar términos y alta | prueba E2E y primer valor |
| GPS $249.000/mes | `INTERNAL_DATED` | cliente conserva su contador | precio de código + alcance + demo |
| Pro desde $1.490.000/mes | `CONFLICT` | no publicar todavía | resolver “incluye contadora” vs separación A/B |
| Total cotizado | `CONFLICT` | “alcance por cotizar” sin atribuir revisoría a B | resolver contrato/factura/roles |
| Micro/Estándar/Complejo A | `INTERNAL_DATED` | bandas A, con confirmación de Tatiana | fuente canónica y drivers completos |
| Starter/Growth/Enterprise antiguos | `BLOCKED` | ninguna | sustituidos el 09-09-2026 |
| Auditoría Sombra adicional $1,2M–$2,5M | `BLOCKED` | ninguna | precio antiguo no aparece en catálogo nuevo |
| Horas estratega $180.000/h | `BLOCKED` | ninguna | precio antiguo no aparece en catálogo nuevo |
| Pulso Diario funciona para freemium día 1 | `CONFLICT` | “recorrido en validación” | informe 29-08 dice pantalla vacía sin proceso automático |
| Centinela Fiscal está activo | `INTERNAL_DATED` | “capacidad en verificación” | demo, backend, falsos positivos y fallback |
| Radar Predictivo está activo | `ROADMAP` | “en desarrollo”, solo si conviene nombrarlo | informe 29-08: mock sin backend |
| Patrimonio está activo | `ROADMAP` | “en desarrollo”, solo si conviene nombrarlo | informe 29-08: mock sin backend |
| Taty opera en app/Telegram/WhatsApp | `INTERNAL_DATED` | “canal en prueba/verificación” | recorrido actual, disclosure, HITL y logs |
| Sell Machine de renta está live | `CONFLICT` | “en prueba controlada” | informe 29-08: modo ensayo; verificar actualización |
| Wompi listo para cobrar renta | `CONFLICT` | ninguna promesa de cobro live | merchant A, transacción E2E y HITL |
| Hermes bridge autenticado | `INTERNAL_DATED` | no es claim de cliente | prueba actual y sin revelar detalle sensible |
| HubSpot sincronizado cada 5 minutos | `INTERNAL_DATED` | no es claim de campaña | verificar mapeo, errores y fuente maestra |
| Manus ejecuta Meta/FB/IG | `INTERNAL_DATED` | “ejecutor del flujo aprobado” | mapear contrato, sandbox, telemetría y kill switch |
| 300 créditos Manus/día incluidos | `INTERNAL_DATED` | uso interno de capacidad | verificar plan/consumo; no claim público |
| Aislamiento 100 % por cliente | `BLOCKED` | “controles de acceso por verificar” | política RLS permisiva pendiente en informe |
| Datos 100 % locales / nunca salen | `CONFLICT` | describir diagrama exacto por componente | cloud + múltiples proveedores + nodo local futuro |
| Cero retención / no entrenamiento | `BLOCKED` | ninguna | contratos/configuración/subencargados vigentes |
| Integración directa/proveedor DIAN | `BLOCKED` | describir importación o mecanismo exacto | autorización/proveedor/integración demostrados |
| IA entrenada en todo el Estatuto | `BLOCKED` | “consulta fuentes verificadas” si existe | corpus, fecha, retrieval y evals |
| Impuesto exacto | `BLOCKED` | “estimación/revisión” | criterio profesional y evidencia |
| Cero multas / inmunidad / riesgo cero | `BLOCKED` | “ayuda a detectar/revisar” | resultados no garantizables |
| 90–95 % automatización | `BLOCKED` | ninguna cifra | baseline y medición propia |
| 40–60 % ahorro/costos/DSO | `BLOCKED` | ninguna cifra | estudio propio con denominador |
| ROI 3–4 meses / +39 % ingresos | `BLOCKED` | ninguna cifra | evidencia propia y metodología |
| “Ningún competidor” / “único” | `BLOCKED` | “diferencia que estamos validando” | landscape actual y criterio comparable |
| 10 clientes / 9 empresas / primera cartera | `CONFLICT` | no usar números | CRM, pagos, periodo y definición común |
| Legaltech / Legiste disponible | `ROADMAP` | no vender ni nombrar como live | confirmar nombre, funciones, seguridad, precio y estado |
| Fintech, crédito, open banking, scoring | `ROADMAP` | no vender | permisos, producto, partners y estado |

## Plantilla para aprobar un claim nuevo

```yaml
claim_id: [ID]
exact_text: [TEXTO]
scope: [SEGMENTO/OFERTA/CANAL]
source_type: [CODE|TEST|CUSTOMER_DATA|CONTRACT|PRIMARY_PUBLIC]
source_link: [REFERENCIA]
observed_at: [FECHA]
sample_and_denominator: [DEFINICION]
limitations: [LISTA]
permission_to_publish: [SI/NO]
owner: [PERSONA]
reviewed_by: [PERSONA]
expires_at: [FECHA]
status: [APPROVED|BLOCKED]
```

