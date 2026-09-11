# Registro de capacidades comercializables

Estados permitidos:

- `LIVE_VERIFIED`: demostrada en producción con evidencia fechada.
- `PILOT_ONLY`: funcional en alcance controlado; se vende solo como piloto.
- `ROADMAP`: planeada, no comercializable.
- `UNKNOWN`: evidencia insuficiente; bloqueada.

| Oferta/capacidad | Entidad | Estado | Evidencia y fecha | Alcance exacto | Exclusiones | Datos requeridos | Revisión humana | Owner | Próxima prueba |
|---|---|---|---|---|---|---|---|---|---|
| Renta Natural (canal de captación) | A | `LIVE_VERIFIED` (canal técnico) | `renta-natural-first-sale`, 10-09/11-09: webhook consolidado + inbox durable deployados, 64/64 eventos reales procesados en producción, verificado vía Supabase MCP | WhatsApp → Taty triage → handoff a Tatiana | Taty no cotiza precio final, no fija fecha exacta de obligación, no cobra | Ninguno adicional al canal ya vivo | Sí, Tatiana confirma precio y cierra | Tatiana | Que ocurra una venta real (pendiente, no técnico) |
| Renta Natural (cierre/cobro) | A | `PILOT_ONLY` — cash/QR en persona | Decisión del fundador 10-09-2026: Wompi diferido, cierre en efectivo/transferencia directa con Tatiana | Cobro en persona, sin rail digital | Sin recibo automático de sistema; el registro es la palabra de Tatiana | Sí, Tatiana | Tatiana | Primera venta real observada |
| Pulso | B | `UNKNOWN` | Sin verificación E2E propia esta sesión — no confundir con el canal de Renta Natural, que sí está verificado | Vista inicial freemium | No prometer valor día 1 sin proceso confirmado | [POR CONFIRMAR] | [POR CONFIRMAR] | [POR CONFIRMAR] | Alta nueva + primera cifra + fallback |
| GPS | B | `LIVE_VERIFIED` (precio) / `UNKNOWN` (demo E2E) | Precio $249.000/mes en `pricing_catalog.py`, verificado 09-09; demo de producción no verificada esta sesión | Cliente conserva su contador | No servicio profesional de B | [POR CONFIRMAR] | [POR CONFIRMAR] | [POR CONFIRMAR] | Demo de producción y contrato |
| Pro | B + recorrido A | `LIVE_VERIFIED` (precio) / `UNKNOWN` (empaquetado) | Precio "desde $1.490.000/mes" en `pricing_catalog.py`; empaquetado A/B sigue sin resolver contractualmente | [POR CONFIRMAR] | No mezclar contrato/factura | [POR CONFIRMAR] | Sí | [POR CONFIRMAR] | Resolver arquitectura contractual |
| Total | B + recorrido A | `LIVE_VERIFIED` (precio: cotizado) / `UNKNOWN` (alcance) | `pricing_catalog.py`; alcance por confirmar | [POR CONFIRMAR] | No afirmar revisoría por B | [POR CONFIRMAR] | Sí | [POR CONFIRMAR] | Resolver arquitectura contractual |
| Legiste/legaltech | [POR CONFIRMAR] | `ROADMAP` | Sin cambios esta sesión | [POR CONFIRMAR] | No vender ni nombrar como live | [POR CONFIRMAR] | Sí | [POR CONFIRMAR] | Confirmar existencia/nombre |
| Radar Predictivo — proyección de caja 13 semanas | B | `LIVE_VERIFIED` con límites declarados | `radar-cash-projection-13w` (ARCHITECTURE.md, archivado): endpoint real sobre Shadow GL, no mock; confianza nunca "alta", `impuesto_futuro_estimado` siempre null | Proyección solo-histórico, 13 semanas | No vender como cálculo de impuesto futuro ni confianza alta | Historial ≥4 semanas de Shadow GL | No requiere aprobación por lectura | [POR CONFIRMAR] | Vender el límite junto con la capacidad |
| Patrimonio | B | `ROADMAP`/mock hasta nueva prueba | Sin evidencia de backend real verificada esta sesión — no confundir con el Radar de Caja, que sí es real | Demostración visual no productiva | No vender como módulo activo | N/A | Sí | [POR CONFIRMAR] | Evidencia de backend + prueba E2E |
| Taty omnicanal | B como interfaz; A para servicio | `LIVE_VERIFIED` | `taty-pricing-skill` (archivado) + `renta-natural-first-sale`: cita precios reales en WhatsApp/Telegram/PWA, canal deployado con tráfico real verificado 10-09/11-09 | Orientación, cotización de banda, routing a Tatiana | No fija precio final ni fecha de obligación exacta; no cobra | Ninguno adicional | Sí, Tatiana | Tatiana | Ya en producción — seguir midiendo conversaciones |
| Manus para Meta | Ejecutor tecnológico | `PILOT_ONLY` (~70% construido) | Informe Manus 15-08 + playbook de campaña: poller real, 3 brechas con parche listo sin integrar, webhook sin registrar | Ejecución FB/IG/Meta y pauta aprobada, alimenta el mismo canal de WhatsApp arriba | No estratega, no aprobador, no cambio autónomo | Paquete aprobado | Sí | [POR CONFIRMAR] | Integrar los 3 parches + registrar webhook |

## Prueba mínima para `LIVE_VERIFIED`

1. recorrido completo reproducible;
2. datos sintéticos o autorizados;
3. resultado observable y limitaciones documentadas;
4. manejo de errores y fallback humano;
5. owner de soporte;
6. términos, privacidad, entidad y precio aprobados;
7. evidencia fechada enlazada.
