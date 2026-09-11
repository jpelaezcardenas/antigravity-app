# Registro de capacidades comercializables

Estados permitidos:

- `LIVE_VERIFIED`: demostrada en producción con evidencia fechada.
- `PILOT_ONLY`: funcional en alcance controlado; se vende solo como piloto.
- `ROADMAP`: planeada, no comercializable.
- `UNKNOWN`: evidencia insuficiente; bloqueada.

| Oferta/capacidad | Entidad | Estado | Evidencia y fecha | Alcance exacto | Exclusiones | Datos requeridos | Revisión humana | Owner | Próxima prueba |
|---|---|---|---|---|---|---|---|---|---|
| Renta Natural | A | `PILOT_ONLY` hasta nueva prueba | Informe 29-08: Sell Machine en ensayo, sin E2E ni comerciante A resueltos; precio actualizado 09-09 | Servicio profesional | No cotización/precio/enlace de pago final automáticos | [POR CONFIRMAR] | Sí, Tatiana | Tatiana | Probar E2E, merchant A y HITL de pago |
| Pulso | B | `PILOT_ONLY` hasta nueva prueba | Informe 29-08: pantalla real, pero primera cifra freemium no automatizada | Vista inicial por verificar | No prometer valor día 1 sin proceso | [POR CONFIRMAR] | [POR CONFIRMAR] | [POR CONFIRMAR] | Alta nueva + primera cifra + fallback |
| GPS | B | `UNKNOWN` | Precio interno $249.000/mes desde 09-09; alcance/E2E sin evidencia adjunta equivalente | Cliente conserva su contador | No servicio profesional de B | [POR CONFIRMAR] | [POR CONFIRMAR] | [POR CONFIRMAR] | Demo de producción y contrato |
| Pro | B + recorrido A | `UNKNOWN` | Conflicto de empaquetado A/B | [POR CONFIRMAR] | No mezclar contrato/factura | [POR CONFIRMAR] | Sí | [POR CONFIRMAR] | Resolver arquitectura contractual |
| Total | B + recorrido A | `UNKNOWN` | Cotizado; alcance por confirmar | [POR CONFIRMAR] | No afirmar revisoría por B | [POR CONFIRMAR] | Sí | [POR CONFIRMAR] | Resolver arquitectura contractual |
| Legiste/legaltech | [POR CONFIRMAR] | `ROADMAP` salvo evidencia posterior | KB lo ubica en expansión | [POR CONFIRMAR] | No vender ni nombrar como live | [POR CONFIRMAR] | Sí | [POR CONFIRMAR] | Confirmar existencia/nombre |
| Radar Predictivo | B | `ROADMAP`/mock hasta nueva prueba | Informe 29-08 declara pantalla con datos de ejemplo, sin backend real | Demostración visual no productiva | No vender como predicción activa | N/A | Sí | [POR CONFIRMAR] | Evidencia de backend + prueba E2E |
| Patrimonio | B | `ROADMAP`/mock hasta nueva prueba | Informe 29-08 declara pantalla con datos de ejemplo, sin backend real | Demostración visual no productiva | No vender como módulo activo | N/A | Sí | [POR CONFIRMAR] | Evidencia de backend + prueba E2E |
| Taty omnicanal | B como interfaz; A para servicio | `PILOT_ONLY` hasta nueva prueba | Informe 29-08 lo declara verificado; anexo 09-09 actualiza pricing | Orientación y routing | No decisión/firma/precio final automáticos | [POR CONFIRMAR] | Sí | Tatiana | Probar fecha, precio, handoff y pago |
| Manus para Meta | Ejecutor tecnológico | `UNKNOWN` hasta mapear contrato | Actualización verbal del usuario 10-09; KB interna lo describe | Ejecución FB/IG/Meta y pauta aprobada | No estratega, no aprobador, no cambio autónomo | Paquete aprobado | Sí | [POR CONFIRMAR] | Ejecución sandbox + telemetría + kill switch |

## Prueba mínima para `LIVE_VERIFIED`

1. recorrido completo reproducible;
2. datos sintéticos o autorizados;
3. resultado observable y limitaciones documentadas;
4. manejo de errores y fallback humano;
5. owner de soporte;
6. términos, privacidad, entidad y precio aprobados;
7. evidencia fechada enlazada.
