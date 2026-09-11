# Guiones comerciales y de campaña

Todos son **borradores**. Antes de usarlos: pasar `/contexia-readiness`, reemplazar campos, verificar fecha/precio/capacidad, revisar entidad y privacidad, y obtener aprobación humana. Ningún guion autoriza un envío automático.

## 1. Fórmula de mensaje Contexia

```text
SEÑAL verificable
→ PROBLEMA como hipótesis, no acusación
→ CONSECUENCIA concreta
→ MECANISMO disponible y demostrable
→ LÍMITE profesional/técnico
→ PRUEBA aprobada
→ SIGUIENTE PASO pequeño
```

Excluir por defecto:

- miedo a la DIAN;
- “cero multas”, “inmunidad”, “garantizado”;
- números de ahorro, precisión o automatización no demostrados;
- features en `ROADMAP`, `UNKNOWN` o `CONFLICTO`;
- cualquier frase que mezcle Entidad A y Entidad B.

## 2. Campaña Renta Natural

### 2.1 Brief maestro para una oleada

```yaml
campaign_id: [ID]
version: [N]
wave_dates: [INICIO - FIN]
deadline_cohort: [DOS ULTIMOS DIGITOS]
audience_hypothesis: [SEGMENTO]
customer_job: [DECISION QUE NECESITA TOMAR]
approved_offer: Renta Natural - Entidad A
price_source: apps/backend/core/pricing_catalog.py
approved_price_phrase: [LEER DE FUENTE CANONICA]
capacity_today: [CUPOS]
intake_cutoff: [FECHA/HORA]
primary_event: professional_review_requested
guardrail_events:
  - consent_revoked
  - wrong_date_detected
  - wrong_price_detected
  - capacity_exceeded
  - privacy_incident
channel: [META / ORGANICO / REFERIDO / PARTNER]
executor: Manus
orchestrator: Hermes
human_approver: [NOMBRE/ROL]
budget_cop: [APROBADO]
manus_credit_limit: [APROBADO, MAX 300/DIA SEGUN PLAN DEL USUARIO]
```

### 2.2 Anuncio A — fecha y criterios

**Texto principal**

> Tu fecha para declarar renta depende de los dos últimos dígitos del NIT, pero esa fecha no dice por sí sola si estás obligado. Revisa los criterios oficiales, identifica lo que te falta y solicita valoración profesional antes de enviar documentos. Renta Natural desde $350.000; el valor final depende de trámites, movimientos y patrimonio y lo confirma Tatiana al revisar el caso.

**Título:** Revisa tu caso de renta 2026  
**CTA:** Revisar fecha y criterios  
**Pie de entidad:** Tecnología de orientación: Contexia, Entidad B. Servicio profesional, si se contrata: `[RAZÓN SOCIAL ENTIDAD A]`.

No publicar si el precio canónico o la capacidad difieren.

### 2.3 Anuncio B — documentos

> La información exógena ayuda, pero no reemplaza tus soportes ni tu realidad económica. Organiza primero tus ingresos, patrimonio, compras, consumos, tarjetas y movimientos financieros; después una profesional revisa tu caso. Empieza con una orientación y conoce el alcance antes de contratar.

**Título:** Organiza tu renta sin improvisar  
**CTA:** Ver lista de documentos

### 2.4 Anuncio C — negocios digitales

> ¿En 2025 recibiste dinero por plataformas, clientes del exterior o varios medios de pago? No significa automáticamente que debas declarar ni determina cuánto pagarías, pero sí merece una revisión completa. Consulta tu fecha, organiza los soportes y deja que Tatiana valore el caso profesionalmente.

**Título:** Ingresos digitales: revisa el panorama completo  
**CTA:** Revisar mi caso

### 2.5 Landing mínima

**Hero**

> Revisa tu fecha y organiza tu caso de Renta Natural

> Orientación guiada para identificar los criterios y documentos que deben revisarse. Si decides continuar, Tatiana confirma alcance y precio antes de prestar el servicio profesional.

**Precio**

> Desde $350.000, según la fuente interna vigente al 9 de septiembre de 2026. Varía por trámites, movimientos y patrimonio. Tatiana confirma el valor final. Verificar el catálogo de código antes de publicar.

**Lo que ocurre**

1. Consulta la fecha asociada a tus dos últimos dígitos.
2. Responde cada criterio con “sí”, “no” o “no sé”.
3. Recibe la lista de información que requiere revisión.
4. Decide si deseas valoración profesional.
5. Tatiana confirma alcance, valor y siguiente paso.

**Límites visibles**

> La orientación automática no concluye por sí sola si debes declarar, no calcula un impuesto definitivo y no presenta declaraciones. El servicio profesional se contrata con `[ENTIDAD A]`; Contexia es la capa tecnológica.

**CTA:** Continuar con la orientación

### 2.6 Bienvenida de Taty — tráfico entrante

> Hola, soy Taty, la interfaz tecnológica que te ayuda a organizar la información inicial. No sustituyo la revisión profesional ni fijo el precio final. Primero puedo mostrarte la fecha según tus dos últimos dígitos y recorrer contigo los criterios oficiales. Antes de compartir datos o documentos, verás quién los tratará, para qué y cómo retirar tu autorización. ¿Quieres continuar?

### 2.7 Texto de consentimiento inicial

**BORRADOR sujeto a revisión jurídica; no publicar como política final.**

> Autorizo a `[ENTIDAD RESPONSABLE]` a tratar los datos mínimos que entregue para orientarme, valorar y, si lo contrato, prestar el servicio de Renta Natural. Entiendo la finalidad, los canales de atención, el plazo de conservación, cómo consultar la política y cómo revocar o solicitar supresión. Esta autorización no incluye publicidad de Contexia ni transfiere automáticamente mi expediente a otra entidad.

Botones separados: `Autorizo y continúo` / `No autorizo` / `Ver política`.

### 2.8 Triage informativo

Taty debe preguntar por bloques y aceptar `NO SÉ`:

1. dos últimos dígitos del NIT, únicamente para ubicar la fecha;
2. condición de responsable de IVA al cierre de 2025;
3. patrimonio bruto;
4. ingresos brutos;
5. consumos con tarjeta;
6. total de compras y consumos;
7. consignaciones, depósitos o inversiones;
8. fuentes de ingreso relevantes y documentos disponibles;
9. fecha actual y urgencia;
10. solicitud expresa de valoración profesional.

Respuesta cuando falta información:

> Con lo que tenemos no es responsable concluir “debes” o “no debes” declarar. Marcaste `[CAMPO]` como desconocido y los criterios se evalúan en conjunto. Puedo ayudarte a identificar el soporte necesario o derivar el caso a Tatiana para valoración.

### 2.9 Caso vencido

> La fecha ordinaria asociada a esos dígitos ya pasó. No te prometo que el caso pueda resolverse como uno presentado a tiempo ni calculo consecuencias automáticamente. Si quieres, lo derivo a Tatiana para revisar situación, documentos y opciones antes de cotizar.

### 2.10 Handoff a Tatiana

> Ya organicé: fecha estimada `[FECHA]`, respuestas completas `[N/6]`, pendientes `[LISTA]` y documentos disponibles `[LISTA SIN CONTENIDO SENSIBLE]`. ¿Autorizas que `[ENTIDAD A]` reciba este resumen mínimo para que Tatiana valore el caso? Los documentos se solicitarán por el canal seguro indicado por ella.

### 2.11 Cotización

> Gracias. El servicio de Renta Natural parte desde $350.000 y el valor varía según trámites, movimientos y patrimonio. Taty no fija el valor final. Tatiana revisará el caso y confirmará por escrito alcance, honorario, entidad contratante y siguiente paso.

### 2.12 Capacidad agotada

> Para ser transparentes, la capacidad de revisión antes de tu fecha está completa. No vamos a prometer un plazo que no podemos cumplir. Puedo registrar tu solicitud para que el equipo confirme si existe disponibilidad o darte la lista oficial para que continúes por otra vía.

## 3. Transición opcional a Contexia

Solo después de valor entregado por Entidad A y sin condicionar el servicio.

### 3.1 Invitación

> Durante la revisión apareció un problema que puede repetirse en tu negocio: `[PROBLEMA DESCRITO SIN DATOS DEL EXPEDIENTE]`. Contexia es una entidad tecnológica distinta y ofrece herramientas de visibilidad financiera. Si quieres, puedes autorizar una invitación separada para conocer Pulso; es opcional y no afecta tu servicio de renta.

### 3.2 Consentimiento separado

**BORRADOR sujeto a revisión jurídica.**

> Sí, quiero que Contexia `[RAZÓN SOCIAL B]` me contacte por `[CANAL]` únicamente para mostrarme Pulso y contenidos relacionados. Entiendo que es una entidad distinta, que no recibirá mi expediente tributario y que puedo retirar esta autorización en cualquier momento.

### 3.3 Activación

> Pulso es la entrada gratuita de Contexia. Antes de activarlo confirmaremos qué función está disponible hoy, qué datos usa y cuál es el primer resultado esperado. No es asesoría contable ni sustituye a tu contador. ¿Quieres ver el recorrido con datos de ejemplo?

No usar este guion si el alta y la primera cifra de un usuario nuevo no han superado el gate técnico.

## 4. Prospección B2B permitida

No usar en WhatsApp personal sin autorización. Para un canal corporativo institucional y después de revisión jurídica:

### 4.1 Correo breve

**Asunto:** Una pregunta sobre la caja de `[EMPRESA]`

> Hola, `[NOMBRE/ROL]`. Vi que `[GATILLO PUBLICO VERIFICABLE]`. En negocios con `[CONTEXTO]`, ventas, comisiones, reembolsos y obligaciones pueden quedar repartidos entre plataformas, bancos y hojas de cálculo. No sé si les pasa, pero cuando ocurre la pregunta difícil es qué parte de la caja está realmente disponible para decidir. Contexia es software de visibilidad financiera; no firma declaraciones ni reemplaza a su contador. ¿Te sería útil comparar durante 20 minutos cómo lo resuelven hoy?

No añadir enlace, deck y calendario en el primer mensaje salvo que la persona lo pida.

### 4.2 Presentación cálida reenviable

> Hola, `[NOMBRE]`. Te presento a `[FUNDADOR]` de Contexia. Están validando con PyMEs del Valle de Aburrá una capa tecnológica para entender caja y excepciones sin reemplazar al contador. Pensé en ti por `[RAZÓN CONCRETA]`. Si ambos ven sentido, los dejo conversar; no compartiré más información ni tu teléfono sin tu autorización.

### 4.3 Mensaje de partner

> Estamos buscando entre tres y cinco aliados para comprobar una hipótesis: que ciertos clientes digitales necesitan una vista más oportuna sin cambiar de contador. No buscamos que entregues bases ni teléfonos. La dinámica sería un taller o enlace voluntario, reglas de datos claras y atribución transparente. ¿Te interesa revisar el modelo y decidir si protege a tus clientes y tu relación con ellos?

## 5. Discovery B2B

### 5.1 Apertura

> El objetivo de esta conversación no es mostrarte todo Contexia. Quiero comprobar tres cosas: si hay un problema económico recurrente, si existe una fuente de datos legítima para observarlo y si podemos probar una mejora sin invadir el trabajo profesional de tu contador. Si no encaja, te lo diré; si encaja, terminamos con una prueba y un criterio de decisión.

### 5.2 Preguntas

**Situación**

- ¿Cómo obtienes hoy la cifra con la que decides qué pagar, invertir o reservar?
- ¿Qué sistemas, bancos, plataformas y hojas intervienen?
- ¿Cuál es la fuente oficial y cuál es una vista de trabajo?
- ¿Qué papel tiene tu contador y cuándo recibe la información?

**Dolor**

- Cuéntame la última ocasión en que una cifra llegó tarde o no cuadró.
- ¿Qué tuvo que reconstruirse manualmente?
- ¿Qué excepción se repite?

**Impacto**

- ¿Qué decisión se retrasó o cambió?
- ¿Cuántas horas/personas intervinieron?
- ¿Qué costo o riesgo puedes documentar, sin estimarlo todavía?

**Evento crítico**

- ¿Qué cambió para que esto importe ahora?
- ¿Qué fecha o consecuencia obliga a resolverlo?

**Decisión**

- ¿Quién usaría la vista y quién aprobaría la compra?
- ¿Quién puede vetarla por contabilidad, datos, seguridad o integración?
- ¿Qué no aceptarías que un sistema automatizara?
- ¿Qué resultado haría que una prueba continúe o se detenga?

**Datos y confianza**

- ¿Tienen derecho y autorización para usar esas fuentes?
- ¿Qué información debe redactarse o permanecer fuera?
- ¿Dónde puede procesarse, quién accede y cuándo se elimina?
- ¿Qué evidencia necesitas ver antes de confiar?

### 5.3 Cierre

> Entendí `[PROBLEMA]`, que hoy produce `[IMPACTO CONFIRMADO]` y debe mejorar antes de `[EVENTO]`. Falta comprobar `[INCERTIDUMBRE]`. El siguiente paso más pequeño sería `[PASO]`, con `[OWNER]` para el `[FECHA]`. ¿Qué entendí mal?

## 6. Demo

1. “Esto entendimos” — repetir el lenguaje del comprador.
2. Mostrar la fuente original.
3. Mostrar la transformación y su trazabilidad.
4. Mostrar un caso normal.
5. Mostrar una excepción y la incertidumbre.
6. Mostrar la aprobación/escalamiento humano.
7. Mostrar lo que el producto **no** hace.
8. Volver al baseline y criterio de éxito.
9. Acordar siguiente decisión, owner y fecha.

Frase de límite:

> Esta es una vista tecnológica de apoyo. No altera el libro oficial, no presenta declaraciones y no convierte una alerta en decisión profesional automática.

## 7. Objeciones

### “Ya tengo contador”

> Perfecto; GPS está pensado para que puedas conservarlo. La pregunta no es reemplazarlo, sino si ambos pueden ver antes una excepción y resolverla con menos reconstrucción. Lo incluimos desde el diseño de la prueba.

### “No confío en IA para impuestos”

> Es una cautela correcta. No te pedimos confiar en una respuesta opaca. La prueba debe mostrar fuente, fecha, transformación, incertidumbre y revisión humana. Contexia no firma ni presenta.

### “No puedo compartir datos”

> Entonces no debemos empezar con datos reales. Primero se aprueba finalidad, flujo, contrato, acceso, subencargados, retención y borrado. Una muestra sintética o redactada puede decirnos si vale la pena seguir.

### “¿Me garantizan pagar menos o evitar sanciones?”

> No. Podemos medir cobertura, oportunidad, consistencia y trazabilidad. El resultado tributario depende de hechos, soportes y criterio profesional; no sería responsable garantizarlo.

### “Es caro”

> Separemos licencia tecnológica y servicio profesional, y comparémoslos con el costo actual que sí podemos demostrar. Si la evidencia todavía es insuficiente, no conviene sobredimensionar: validemos una entrada menor o no avancemos.

### “Quiero una sola factura”

> Las responsabilidades son distintas. La tecnología y el servicio profesional deben quedar identificados y contratados por separado, aunque la experiencia se coordine.

### “¿Está integrado con DIAN?”

> Te responderemos solo con el mecanismo que podamos demostrar hoy. Una importación, un XML o un proveedor tercero no se describen como autorización o integración directa si no lo son.

### “¿Todo queda 100 % local?”

> No usamos absolutos. Mostramos el diagrama vigente: sistemas, regiones, proveedores, retención, accesos y qué parte corre localmente.

### “Quiero Radar Predictivo”

> En el último informe aportado, Radar todavía era una pantalla con datos de ejemplo. Debemos verificar si eso cambió. Si no existe evidencia actual, no lo incluiremos en oferta ni contrato.

## 8. Propuesta

### Portada ejecutiva

- situación actual;
- impacto confirmado por el cliente;
- evento crítico;
- resultado acordado;
- recomendación y siguiente decisión.

### Bloque Entidad B

- licencia/implementación;
- funciones `LIVE_VERIFIED`;
- funciones piloto claramente marcadas;
- datos, accesos y controles;
- métrica de aceptación;
- precio canónico y periodicidad;
- soporte, salida y borrado.

### Bloque Entidad A, si aplica

- servicio profesional exacto;
- profesional responsable;
- exclusiones;
- honorario confirmado por Tatiana;
- contrato y factura separados.

### Cierre

> Esta propuesta documenta la decisión conversada; no amplía capacidades, garantías ni responsabilidades más allá del alcance escrito. Para avanzar: `[ACCION]`, responsable `[PERSONA]`, fecha `[FECHA]`.

## 9. Seguimiento

### Día 0 — recap

> Resumo lo acordado: `[PROBLEMA]`, baseline `[METRICA]`, riesgo `[RIESGO]` y próximo paso `[PASO]`. Para decidir faltan `[CAMPO]`. `[OWNER]` lo confirma el `[FECHA]`. Si algo está mal, corrígeme antes de avanzar.

### Seguimiento con valor

> Preparé `[MAPA/BASELINE/RESPUESTA]` y marqué como desconocido lo que todavía no pudimos verificar. Si completamos `[CAMPO]`, podremos decidir `[DECISION]`; si no, cerramos sin compromiso.

### Breakup respetuoso

> Cierro el hilo para no perseguirte. Por lo conversado, tendría sentido retomarlo solo si cambia `[CONDICION]`. Puedes reabrir desde aquí cuando ocurra; entretanto no asumiré que la oportunidad sigue activa.

### Baja inmediata

> Entendido. No volveremos a enviarte mensajes comerciales por este canal. Registramos tu solicitud y te indicaremos el medio para ejercer cualquier derecho adicional sobre tus datos.

## 10. Referido después de valor

> Me alegra que `[RESULTADO OBSERVABLE]` haya sido útil. Estamos buscando hablar con dueños de `[PERFIL]` que hoy `[PROBLEMA]`. Si conoces a alguien, ¿podrías reenviarle este enlace? No nos compartas su número; que esa persona decida si quiere contactarnos.

Texto reenviable:

> Contexia está validando con PyMEs una forma de entender caja y excepciones sin reemplazar al contador. Si ese problema te suena, aquí puedes pedir una conversación voluntaria: `[ENLACE]`.

## 11. Paquete de ejecución para Manus

Claude Code debe producir un archivo estructurado con este contenido; Hermes solo lo despacha después de aprobación humana:

```yaml
campaign:
  id: [ID]
  version: [VERSION]
  objective: [OBJETIVO]
  hypothesis: [HIPOTESIS]
  wave: [COHORTE Y FECHAS]
  entity_shown: [A/B/AMBAS CON ROLES SEPARADOS]
creative:
  copy_id: [ID]
  primary_text: [TEXTO APROBADO]
  headline: [TITULO]
  cta: [CTA]
  asset_path: [RUTA]
  approved_claim_ids: [LISTA]
destination:
  url: [LANDING]
  event: [EVENTO PRIMARIO]
audience:
  definition: [CRITERIOS NO SENSIBLES]
  exclusions: [LISTA]
  consent_basis: [DOCUMENTADA]
delivery:
  platforms: [facebook, instagram]
  start: [FECHA/HORA]
  end: [FECHA/HORA]
  budget_cop: [MONTO]
  daily_cap_cop: [MONTO]
  manus_credit_cap: [MAXIMO APROBADO]
capacity:
  human_slots: [N]
  queue_stop_at: [N]
kill_switches: [LISTA]
approval:
  approver: [PERSONA]
  approved_at: [FECHA/HORA]
  evidence: [REFERENCIA]
```

Manus devuelve:

```yaml
execution:
  status: [CREATED|PUBLISHED|PAUSED|FAILED]
  platform_ids: [REFERENCIAS]
  credits_used: [N]
  spend_cop: [N]
  timestamps: [LISTA]
  deviations: [NINGUNA O LISTA]
telemetry:
  impressions: [N]
  clicks: [N]
  primary_events: [N]
  guardrail_events: [N]
  attribution_window: [DEFINICION]
decision_input:
  data_complete: [SI/NO]
  anomaly: [DETALLE]
```

No entregar a Manus secretos, expedientes tributarios, números personales o datos financieros de clientes dentro del brief creativo.

