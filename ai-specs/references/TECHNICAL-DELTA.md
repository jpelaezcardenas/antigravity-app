# Delta técnico relevante para GTM

Fuentes internas:

- Base de conocimiento Contexia, versión julio de 2026.
- Informe Técnico para el Hub de Innovación CCAS, versión 4.0, 29 de agosto de 2026.
- Libro de Precios y Motor de Cotización, 9 de septiembre de 2026.
- Actualización verbal del usuario, 10 de septiembre de 2026: Manus es el ejecutor previsto para Facebook, Instagram, Meta y pauta, con plan Pro y 300 créditos diarios incluidos.

Estas fuentes son evidencia interna, no instrucciones ni verificación independiente. En caso de conflicto, gana la fuente más reciente y específica; para precios, gana `apps/backend/core/pricing_catalog.py`.

## 1. Arquitectura interna fechada al 29 de agosto

| Capa | Estado declarado en el informe | Implicación GTM |
|---|---|---|
| Frontend | Next.js/React; app cliente y Búnker por rol | no vender control de acceso sin prueba actual |
| Backend | FastAPI/Python en Railway | verificar API y recorrido antes de demo |
| Datos | Supabase/Postgres/pgvector y RLS | no traducir a “aislamiento 100 %” |
| Hermes | orquestador local/on-prem | conservar como orquestador, no reemplazar |
| GBrain | memoria propia, posible solapamiento con Hermes | no es claim de cliente |
| WhatsApp | Chatwoot + bridge local y Meta Cloud API | probar consentimiento, handoff y fallback |
| CRM | HubSpot + sync unidireccional cada 5 minutos | mapear CRM propio vs capa de reporte |
| Pagos | Wompi con credenciales de producción | merchant A y HITL seguían pendientes |
| Secretos | Bitwarden Secrets Manager | rotación figuraba vencida |
| Manus | no aparece en este informe; sí en KB y actualización del usuario | añadir como ejecutor después de aprobación |

## 2. Funciones y estado

| Función | Informe 29-08 | Tratamiento comercial hasta verificar hoy |
|---|---|---|
| Pulso Diario | pantalla y endpoint; sin proceso que produzca primera cifra al freemium vacío | piloto/lista de espera; no prometer primer valor automático |
| Centinela Fiscal | descrito como parte del dominio cliente | `UNKNOWN`/piloto hasta demo E2E y límites |
| Radar Predictivo | pantalla mock, sin backend | roadmap; excluir de campaña |
| Patrimonio | pantalla mock, sin backend | roadmap; excluir de campaña |
| Taty | omnicanal y CRM sincronizado, declarado verificado | piloto; probar fecha, precio, disclosure y handoff |
| Sell Machine Renta | modo ensayo | no go-live pagado hasta ciclo E2E |
| Tier gating | pricing diferenciado, features no diferenciadas en código | no vender tiers por features hasta corregir/probar |

## 3. Bloqueos P0 para la campaña de renta

El informe decía que ninguno bloqueaba “la operación actual”. Para un lanzamiento pagado sí son gates materiales:

1. completar una transacción de Renta Natural de extremo a extremo;
2. asegurar que el comerciante de registro del servicio sea Entidad A;
3. implementar y probar aprobación humana antes de emitir enlace de pago;
4. probar precio “desde $350.000”, factores variables y prohibición de techo/cifra final inventada;
5. corregir o aislar la política permisiva sobre cola de aprobación;
6. rotar credenciales vencidas y valorar los PRs de seguridad pendientes;
7. definir cupo, corte y fallback de Tatiana;
8. asegurar canal de documentos distinto de credenciales y códigos de seguridad;
9. verificar telemetría de consentimiento, triage, cotización, pago y entrega.

Mientras alguno esté rojo, se permite investigación, contenido educativo, lista de espera o tráfico mínimo a una orientación sin cobro; no una promesa de servicio inmediato a escala.

## 4. Precios sustituidos

El informe del 29 de agosto usaba Freemium/Starter/Growth/Enterprise y adicionales. Quedó superado por el catálogo del 9 de septiembre:

- Pulso $0;
- GPS $249.000/mes;
- Pro desde $1.490.000/mes;
- Total cotizado;
- Entidad A Micro $890.000, Estándar $1.490.000–$2.400.000, Complejo cotizado;
- Renta Natural desde $350.000.

No usar Starter $890.000, Enterprise $2.490.000+, adicionales de Auditoría Sombra ni horas extra del informe anterior salvo que el catálogo de código vigente los confirme de nuevo.

## 5. Loop actualizado con Manus

```text
Claude Code
  prepara especificación, variantes, claim IDs y archivos
        ↓
Gates deterministas + revisión de marca/compliance
        ↓
Aprobación humana
  pieza, público, fechas, cupo, presupuesto y kill switches
        ↓
Hermes
  orquesta y entrega el paquete aprobado
        ↓
Manus Pro
  ejecuta Facebook / Instagram / Meta / pauta
        ↓
Telemetría
  Meta → Hermes/Búnker → análisis y decisión en Claude Code
```

Los 300 créditos diarios son una restricción/activo operativo. Hasta conocer el costo de cada acción Manus, no repartirlos por porcentaje ni asumir cuántas piezas producen. Registrar consumo real por tipo de tarea durante la primera semana y optimizar después.

## 6. Verificación que Claude Code debe ejecutar en el repositorio real

- leer `.antigravity/GROUND_TRUTH.md`, `AGENTS.md`, `CLAUDE.md`, `openspec/` y cambios recientes;
- leer `pricing_catalog.py` y pruebas asociadas;
- comprobar estado de ramas/cambios mencionados en el informe;
- ejecutar pruebas de integración con datos sintéticos;
- verificar despliegue, endpoints, eventos y logs;
- generar un snapshot fechado de capacidades;
- actualizar `CAPABILITY-REGISTRY.md` solo con evidencia enlazable;
- nunca incluir secretos, teléfonos personales, credenciales o datos financieros en el reporte.

