# Ground truth comercial — Contexia

Fecha de síntesis: 10 de septiembre de 2026.  
Este archivo resume información aportada por el usuario; no sustituye el repositorio, contratos, pruebas ni políticas vigentes.

## 1. Identidad

- Contexia es **Entidad B tecnológica**.
- Entidad B posee/desarrolla la capa tecnológica, marca, software, automatización e infraestructura.
- Entidad B no es firma contable regulada, no ejerce fe pública y no firma estados financieros, declaraciones ni dictámenes.
- Entidad A presta los servicios profesionales regulados con profesional habilitado.
- Contratos, facturas, responsabilidades, datos y precios deben separarse, aunque la experiencia se coordine.

## 2. Propósito comercial

- Macroconcepto: **Claridad Predictiva**.
- Objetivo inicial: ayudar a dueños de PyMEs y negocios digitales a tomar decisiones con señales financieras más comprensibles, oportunas y trazables.
- Conceptos del ecosistema: Pulso Diario, Centinela Fiscal, Radar Predictivo y Auditoría Sombra.
- Estos nombres no prueban que todas las capacidades estén disponibles; consultar el registro de capacidades.

## 3. Territorio y segmentos como hipótesis

- Geografía inicial: diez municipios del Área Metropolitana del Valle de Aburrá.
- Segmentos internos propuestos: e-commerce/dropshipping, creadores/infoproductores/exportadores de servicios, agencias de IA/tech y PyMEs tradicionales en digitalización.
- El documento maestro alterna 5–50, 5–100 y solopreneurs; no usar un tamaño único como ICP validado.
- Calificar por dolor, evento, proceso, datos, comprador, economía y capacidad de entrega.

## 4. Oferta y precio interno más reciente

Fuente documental: Libro de Precios, 9 de septiembre de 2026. Fuente operativa superior: `apps/backend/core/pricing_catalog.py`.

### Entidad B

- Pulso: $0, freemium.
- GPS: $249.000/mes; el cliente conserva su contador.
- Contexia Pro: desde $1.490.000/mes.
- Contexia Total: cotizado.

### Entidad A

- Micro: $890.000.
- Estándar: $1.490.000–$2.400.000.
- Complejo: cotizado, sin techo publicado.
- Renta Natural: desde $350.000; varía por trámites, movimientos y patrimonio.

Tatiana confirma siempre el precio profesional final. El motor sugiere banda y no ve todos los drivers; nunca declarar confianza alta ni inventar techo.

## 5. Estado técnico interno al 29 de agosto

El informe v4 afirma:

- Pulso Diario y un endpoint alterno existían, pero faltaba el proceso automático para dar una primera cifra a un freemium sin libro mayor;
- Radar Predictivo y Patrimonio eran pantallas mock sin backend;
- Taty omnicanal y sincronización CRM figuraban verificadas;
- el puente de Hermes había sido autenticado y una restricción de base de datos corregida;
- Sell Machine seguía en ensayo;
- faltaban transacción E2E, merchant de Entidad A y aprobación humana previa al enlace de pago;
- tier gating, rotación de secretos, PRs de seguridad, política permisiva de base, migración de alertas y retiro de backend secundario seguían abiertos.

Actualizaciones posteriores pueden haber cambiado el estado. Solo una prueba actual en el repositorio/producción puede promover una capacidad.

## 6. Arquitectura operativa conocida

- Claude Code: desarrollo, especificación y generación de artefactos.
- Hermes: orquestación existente; no rediseñar con este kit.
- Manus: ejecutor definido por el usuario para Facebook, Instagram, Meta, publicaciones y pauta.
- Aprobación humana: obligatoria antes de enviar, publicar, pautar, cotizar o emitir enlace de pago.
- Manus Pro: el usuario reporta 300 créditos diarios incluidos; registrar consumo, no gastarlos por obligación.

El contrato exacto entre componentes queda en `templates/CURRENT-PROCESS-MAP.md` hasta inspeccionar el sistema real.

## 7. Campaña de Renta Natural

- Es una cuña B2C/profesional de Entidad A, no un lanzamiento completo de Entidad B.
- Taty puede orientar y organizar datos mínimos; no decide obligación definitiva, no fija honorario, no firma ni presenta.
- Servicio A → valor entregado → permiso separado y opcional → invitación B.
- No compartir automáticamente el expediente de renta con Contexia.
- Una persona de renta solo se convierte en PQL si opera un negocio, reconoce un problema recurrente, autoriza contacto B y muestra intención/uso.

## 8. Palabras de uso controlado

| Término | Uso prudente |
|---|---|
| Claridad Predictiva | categoría/macroconcepto; explicar señal y acción concreta |
| Pulso Diario | nombre de producto; afirmar solo capacidades verificadas |
| Centinela Fiscal | alertas/apoyo; no “bloquea toda inconsistencia” sin prueba |
| Radar Predictivo | roadmap/mock según 29-08 hasta prueba posterior |
| Auditoría Sombra | preferir “pre-revisión” o “diagnóstico de consistencia”; no auditoría regulada |
| Shadow GL | libro paralelo derivado; nunca libro oficial |
| Taty | interfaz tecnológica; identificar cuándo escala a profesional |
| CFO as a Service | evitar salvo alcance contractual claro; preferir apoyo a decisiones |
| integración DIAN | usar solo descripción técnica exacta y autorización comprobada |

## 9. Stop conditions

- conflicto entre precio/documento/código;
- capacidad no verificada;
- entidad incorrecta;
- falta de consentimiento o transferencia no definida;
- merchant de registro equivocado;
- pago sin aprobación humana;
- documento por canal inseguro;
- claim absoluto o resultado inventado;
- falta de capacidad profesional antes del vencimiento;
- Manus recibe paquete sin aprobación, presupuesto o kill switch.

