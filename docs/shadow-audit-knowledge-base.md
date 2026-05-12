# Shadow Audit — Base de Conocimiento Contexia

> Documento de referencia integral del Shadow Audit (Wizard) de Contexia.
> Fuente única de verdad para NotebookLM, asistentes IA y nuevos miembros del equipo.
> Última actualización: 12 de mayo de 2026.

---

## 1. Resumen Ejecutivo

El **Shadow Audit** es la herramienta lead-magnet de Contexia: un wizard gratuito de 8 pasos que en menos de 5 minutos entrega a un emprendedor o PyME colombiana un diagnóstico tributario personalizado, comparando **Régimen Simple vs Ordinario**, identificando **riesgos DIAN**, oportunidades fiscales y un **plan de acción 30-60-90 días**.

- **URL pública**: `https://contexia.online/wizard/`
- **Modo demo (datos pre-llenados)**: `?prefill=connatural` o `?prefill=lead-caliente`
- **Costo para el usuario**: $0, sin tarjeta, sin compromiso
- **Tiempo promedio de finalización**: 4-6 minutos
- **Output**: Diagnóstico web + PDF descargable + email + opción de compartir por WhatsApp

### Propuesta de valor
> ¿Tu empresa paga más impuestos de los que debe? Responde 7 preguntas y descubre cuánto pagarías en Régimen Simple vs Ordinario, tus riesgos DIAN y un plan de acción concreto.

### Objetivo de negocio
- **Lead generation**: capturar contactos calificados con email + WhatsApp + datos de empresa
- **Calificación**: el diagnóstico genera urgencia (riesgos visibles + ahorro cuantificado)
- **Conversión**: CTAs hacia "Crear mi empresa" ($1.2M+), "Agendar asesoría" (Cal.com 30 min), descarga de PDF
- **Posicionamiento**: Contexia como autoridad técnica con cálculos basados en normativa vigente 2026

---

## 2. Identidad de Marca y Tono

- **Contexia** es una **Entidad B tecnológica** (no firma contable tradicional)
- Se posiciona como **GPS de Flujo de Caja y Riesgo Fiscal** para PyMEs en Colombia
- **Taty** es el agente IA front-stage (Tu Amiga Contadora) — voz cercana, técnica, accionable
- **Paleta**: Teal `#2DD4BF`, Violet `#8B5CF6`, Navy `#0F172A` / `#020617`
- **Tipografía**: Orbitron (titulares) + Rajdhani (UI) + Inter (cuerpo)
- **Estética**: Glassmorphism + dark mode + gradientes

---

## 3. Arquitectura Técnica

### Stack
| Capa | Tecnología |
|---|---|
| Framework | Next.js 16.2.4 (App Router + Turbopack) |
| UI | React + CSS-in-JS + Tailwind utilities |
| Estado | Zustand con persistencia en `localStorage` |
| Validación | Zod schemas por paso |
| Backend | API Routes Next.js + Supabase (Postgres) |
| Email | Resend (`growth@contexia.online`) |
| PDF | `@react-pdf/renderer` (server-side) |
| Analytics | Google Analytics 4 (`G-Q03PYP6RBH`) |

### Configuración crítica
```ts
// next.config.ts
basePath: "/wizard"      // se sirve desde contexia.online/wizard
trailingSlash: true
```

### Despliegue
- **Landing**: `contexia.online`
- **Shadow Audit / Wizard**: `contexia.online/wizard/`
- **Portal de Clientes (Búnker)**: `contexia.online/app/`
- **API Backend (planificado)**: `api.contexia.online`
- **Hosting**: Vercel (auto-deploy desde rama `main` en GitHub `jpelaezcardenas/antigravity-app`)

---

## 4. Flujo del Usuario (Funnel)

```
[Landing] ──► [Wizard Hero] ──► Paso 1 ──► Paso 2 ──► ... ──► Paso 7 ──► [Paso 8: Ejecutar Audit]
                                                                              │
                                                                              ▼
                                                              ┌──────────────────────────────┐
                                                              │  Resultados Shadow Audit     │
                                                              │  + Email + PDF + WhatsApp    │
                                                              └──────────────────────────────┘
                                                                              │
                                                              ┌───────────────┼────────────────┐
                                                              ▼               ▼                ▼
                                                        Crear Empresa   Agendar Asesoría    Compartir
```

### Hero Pre-Wizard (pantalla de bienvenida)
- Badge: "🔍 Shadow Audit — Gratis & Sin compromiso"
- Proof points: ⚡ 5 minutos · 🔒 100% confidencial · 🎯 Basado en UVT 2026 · 💡 Plan de acción real
- Sellos de confianza: Estatuto Tributario · Ley 2155/2021 · DIAN UVT 2026 · Cámara de Comercio
- CTA principal: **"Hacer mi diagnóstico gratuito →"**

---

## 5. Los 8 Pasos del Wizard

### Paso 1 — Solicitante
Identifica al humano detrás del lead.

| Campo | Tipo | Validación |
|---|---|---|
| `nombre` | string | mín. 3 caracteres |
| `cedula` | string | regex `^\d{8,10}$` |
| `email` | string | formato email válido |
| `pais_codigo` | string | default `+57` |
| `whatsapp` | string | mín. 7 dígitos, solo números |
| `ciudad` | string | mín. 2 caracteres |
| `rol` | enum | Propietario, CEO, Director, Contador, Asesor, Otro |

**Acción colateral**: al avanzar, se llama `/api/leads/save` para crear/actualizar el registro en Supabase (`leads` table).

### Paso 2 — Empresa
Captura identidad jurídica y económica.

| Campo | Detalle |
|---|---|
| `nombre_opcion1/2/3` | Hasta 3 opciones de razón social |
| `tipo_sociedad` | SAS, Ltda, persona natural comercio, persona natural servicios, otro |
| `sector` | Descripción libre de actividad |
| `ciiu_principal` | Código CIIU (4 dígitos) — clave para cálculo tributario |
| `ciiu_secundario` | Opcional |
| `direccion` | Dirección de operación |
| `tiene_rut_actual` | si/no |
| `nit_actual` | Opcional |

> El **CIIU** es el determinante más importante: define el grupo Simple (1-5), las tarifas, los riesgos sectoriales (INVIMA, ICA agropecuario, etc.) y el banner especial CIIU 1090.

### Paso 3 — Sociedad
Estructura accionaria.

| Campo | Detalle |
|---|---|
| `num_socios` | 1-10 |
| `socios[]` | Array con `nombre`, `cedula`, `participacion (%)`, `rol` |
| `representante_legal` | Quién firma legalmente |
| `capital_suscrito` | Monto en COP |
| `aportes_en_especie` | boolean |
| `descripcion_aportes` | Texto libre (equipos, dominios, IP, cartera) |

### Paso 4 — Financiera (la más crítica para cálculo)
| Campo | Detalle |
|---|---|
| `ingresos_mensuales` | COP — multiplica por 12 para anuales |
| `costos_pct` | 0-100 — define margen y utilidad para Ordinario |
| `modelo_negocio` | ecommerce, manufactura, servicios, comercio_fisico, mixto |
| `medios_pago[]` | Transferencia, PSE, Nequi, Daviplata, Stripe, Wompi, efectivo, etc. |
| `tiene_ingresos_previos` | boolean |
| `ingreso_anual_previo` | Para sanity-check |
| `ha_declarado_renta` | boolean |
| `ultimo_año_declarado` | "2024", "2023", etc. |

### Paso 5 — Contable
| Campo | Detalle |
|---|---|
| `tiene_contador` | boolean — **detonante de riesgo si false** |
| `nombre_contador` / `email_contador` | Opcional |
| `maneja_inventarios` | boolean |
| `facturacion_electronica` | si / no / no_se — **CRÍTICO regulatorio** |
| `regimen_preferido` | simple / ordinario / analisis (default) |
| `registros_actuales` | manual / excel / software / ninguno |

### Paso 6 — Administrativa
| Campo | Detalle |
|---|---|
| `empleados` | número (0+) |
| `tipos_vinculacion[]` | Nómina, Prestación servicios, Freelance, Honorarios |
| `salario_promedio` | COP |
| `requiere_nomina` | boolean |
| `contratos_proveedores` | boolean |
| `tiene_bpa` | boolean — Buenas Prácticas Agrícolas (alimentos) |

### Paso 7 — Digital
| Campo | Detalle |
|---|---|
| `tiene_ecommerce` | boolean |
| `dominio_web` | URL |
| `redes_sociales[]` | Instagram, Facebook, TikTok, LinkedIn, YouTube, X |
| `software_contable` | Siigo, Alegra, Loggro, ninguno |

### Paso 8 — Diagnóstico (no captura datos, los procesa)
Ver sección 6.

---

## 6. Algoritmo del Shadow Audit (Paso 8)

Al pulsar **"🔍 Ejecutar Shadow Audit"** se desencadenan 4 cálculos en paralelo + persistencia:

```
       ┌─► compararRegimenes()  ──► Simple vs Ordinario
       │
Audit ─┼─► detectarRiesgos()    ──► Lista de riesgos por nivel
       │
       ├─► detectarOportunidades() ─► Lista de oportunidades fiscales
       │
       └─► calcularReadiness()   ──► Score 0-100 + banda verde/ambar/rojo
                │
                ▼
       POST /api/audit/execute  ──► Persiste en Supabase
                │
                ▼
       GA4 event: audit_executed
```

### 6.1 Cálculo Régimen Simple (Art. 908 E.T. / Ley 2155/2021)

**UVT 2026** = `$49.799` COP (Resolución DIAN)

#### Grupos de actividades y tarifas (% sobre ingresos brutos)
| Grupo | Actividades | Tramos UVT y tarifas |
|---|---|---|
| **GRUPO 1** | Tiendas, mini-mercados, panaderías, carnicerías, droguerías | 0-6k: 2.0% · 6-15k: 2.8% · 15-30k: 8.1% · 30-80k: 11.6% · 80-100k: 14.96% |
| **GRUPO 2** | Comercio al detal (excluidos Grupo 1), servicios técnicos, mecánicos | 0-6k: 1.8% · 6-15k: 2.2% · 15-30k: 3.9% · 30-80k: 5.4% · 80-100k: 6.3% |
| **GRUPO 3** | Servicios profesionales, consultoría, honorarios | 0-6k: 5.9% · 6-15k: 7.3% · 15-30k: 12.0% · 30-80k: 14.5% · 80-100k: 16.0% |
| **GRUPO 4** | Educación, deportes, esparcimiento | 0-6k: 3.4% · 6-15k: 3.8% · 15-30k: 5.5% · 30-80k: 7.0% · 80-100k: 8.5% |
| **GRUPO 5** | Manufactura, industria, construcción | 0-6k: 2.5% · 6-15k: 3.0% · 15-30k: 4.5% · 30-80k: 6.0% · 80-100k: 7.5% |

#### Mapeo CIIU → Grupo
| CIIU | Actividad | Grupo |
|---|---|---|
| 1090 | Elaboración alimentos para animales | GRUPO5 |
| 4631 | Comercio mayor de alimentos | GRUPO2 |
| 4791 | Comercio menor por internet | GRUPO2 |
| 4773 | Comercio minorista especializado | GRUPO1 |
| 5611 | Restaurantes | GRUPO1 |
| 6201 | Desarrollo de software | GRUPO3 |
| 7500 | Servicios veterinarios | GRUPO3 |
| 9609 | Otros servicios personales | GRUPO2 |
| *(otros)* | *(fallback)* | GRUPO2 |

**Tope del Simple**: 100.000 UVT (~$4.980M COP en 2026). Por encima → obligatorio Ordinario.

**Fórmula**: `impuesto_simple = ingresos_anuales × tarifa%`
Incluye: Renta + ICA integrado + parte de CREE.

### 6.2 Cálculo Régimen Ordinario (Art. 240 E.T.)

```
costos_totales      = ingresos_anuales × (costos_pct / 100)
utilidad_bruta      = ingresos_anuales − costos_totales
renta_anual         = utilidad_bruta × 0.35              # 35% Renta empresarial
iva_generado        = ingresos_anuales × 0.19
iva_descontable     = (costos × 0.5) × 0.19              # ~50% compras gravadas
iva_neto            = max(0, iva_generado − iva_descontable)
ica_anual           = ingresos × tasa_ICA / 1000
total_impuestos     = renta_anual + iva_neto + ica_anual
```

#### ICA Medellín (Acuerdo Municipal 67/2017)
| Sector | Tasa |
|---|---|
| Manufactura (CIIU 1000-3999) | 7‰ |
| Comercio (CIIU 4500-5300) | 10‰ |
| Servicios (CIIU 5500-9999) | 5‰ |
| Default | 8‰ |

### 6.3 Comparativo y Recomendación
```ts
ahorro = ordinario.total - simple.impuesto
if (simple.aplicable && ahorro > 0) → "simple"
else → "ordinario"
```

### 6.4 Detección de Riesgos (niveles: CRÍTICO / ALTO / MEDIO / BAJO)

| Riesgo | Nivel | Detonante | Acción sugerida |
|---|---|---|---|
| Sin registro ICA — Fabricante alimento animal | CRÍTICO | CIIU 1090 | Trámite SimplifICA + veterinario asesor + BPMAA |
| Supera 100.000 UVT | CRÍTICO | Ingresos > $4.980M anuales | Optimizar deducciones con contador |
| Sin facturación electrónica | CRÍTICO/ALTO | `facturacion_electronica = no` | Habilitación DIAN obligatoria |
| Uso de suelos / sanitario | ALTO | CIIU 1090, 5611, 1011 | Concepto municipal antes de operar |
| Sin contador con ingresos altos | ALTO | `!tiene_contador && ingresos > 3500 UVT` | Contratación / outsourcing contable |
| Vinculación por servicios siendo nómina | MEDIO | Empleados + `tipos_vinculacion incluye "Prestación"` | Reclasificar contratos |
| E-commerce sin formalizar | MEDIO | `tiene_ecommerce && tipo_sociedad = persona_natural_servicios` | Constituir SAS |
| No ha declarado renta teniendo ingresos previos | ALTO | `tiene_ingresos_previos && !ha_declarado_renta` | Regularización antes de DIAN |

> **Banner especial CIIU 1090** (alimentos para animales): badge violet con CTA WhatsApp a especialista INVIMA/BPM. Se trackea con `ga4.ciiu1090BannerShown()`.

### 6.5 Detección de Oportunidades

Ejemplos:
- **Régimen Simple** si genera ahorro > 0 (impacto: monto exacto)
- **Deducción por aportes ARL/SS** si tiene empleados
- **IVA descontable software/SaaS** si modelo es digital
- **Beneficio BPA/BPMAA** si es agropecuario y aplica
- **Constitución SAS** si actualmente persona natural con ingresos altos

### 6.6 Readiness Score (0-100)

Pondera 7-8 señales del wizard:
| Señal | Peso |
|---|---|
| `tiene_contador` | +15 |
| `facturacion_electronica = si` | +20 |
| `software_contable ≠ ninguno` | +15 |
| `ha_declarado_renta` | +10 |
| `maneja_inventarios` (si aplica) | +10 |
| `tiene_bpa` (si CIIU lo requiere) | +15 |
| Empleados formalizados | +10 |
| Mix digital (e-commerce + dominio + redes) | +5 |

**Bandas**:
- 🟢 **80-100 verde**: "Listo para formalizar — Empieza ya"
- 🟡 **50-79 ambar**: "Requiere ajustes — Te acompañamos"
- 🔴 **0-49 rojo**: "Foundation building crítico — Paquete completo recomendado"

### 6.7 Plan de Acción 30-60-90

Tres fases fijas con checklist:

- **Días 0-30 — Constitución legal**: RUES, estatutos SAS, CC, NIT+RUT, facturación electrónica DIAN, cuenta bancaria empresarial
- **Días 30-60 — Cumplimiento sectorial**: uso de suelos, concepto sanitario, registro ICA SimplifICA (si aplica), software contable
- **Días 60-90 — Operación formalizada**: migración a SAS, primera declaración Simple, plan regulatorio, capacitación BPMAA

---

## 7. APIs Funcionales

| Endpoint | Método | Rol |
|---|---|---|
| `/api/leads/save` | POST | Upsert lead por email (case-insensitive). Captura IP, UA, referer. |
| `/api/audit/execute` | POST | Persiste `audit_result`, `audit_executed_at`, `status = "audited"` |
| `/api/audit/email` | POST | Envía email HTML con resultados vía Resend. Remitente: `Taty de Contexia <growth@contexia.online>` |
| `/api/audit/pdf` | GET | Genera PDF con `@react-pdf/renderer`. Query: `?email=` o `?leadId=` |

### Variables de entorno (Vercel)
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `RESEND_API_KEY`

---

## 8. Modelo de Datos — Tabla `leads` (Supabase)

| Columna | Tipo | Notas |
|---|---|---|
| `id` | uuid | Primary key |
| `email` | text | Único, case-insensitive |
| `nombre` | text | De paso 1 |
| `whatsapp` | text | Con código país |
| `ciudad`, `rol` | text | |
| `paso2`, `paso3`, ..., `paso7` | jsonb | Snapshot completo por paso |
| `audit_result` | jsonb | Resultado del análisis |
| `audit_executed_at` | timestamp | Cuando se corrió el audit |
| `status` | enum | `lead`, `audited`, `contacted`, `converted` |
| `ip`, `user_agent`, `referer` | text | Atribución |
| `created_at`, `updated_at` | timestamp | |

### Forma del `audit_result` (jsonb)
```json
{
  "recomendacion": "simple" | "ordinario",
  "ingresosAnuales": number,
  "costosTotales": number,
  "utilidadBruta": number,
  "margenPct": number,
  "impuestoSimple": number,
  "impuestoOrdinario": number,
  "ahorroPotencial": number,
  "readinessScore": 0-100,
  "readinessBand": "verde" | "ambar" | "rojo",
  "riesgos": [{ "nivel", "titulo", "descripcion", "accion" }],
  "oportunidades": [{ "titulo", "descripcion", "impactoEstimado" }]
}
```

---

## 9. Casos de Prueba Pre-llenados

### 9.1 `?prefill=connatural` — Caso Manufactura Alimentos
**Empresa**: Connatural Dieta BARF S.A.S.
- Sector: Manufactura BARF (Biologically Appropriate Raw Food) para mascotas
- **CIIU principal**: 1090 → activa banner INVIMA/BPM
- Ingresos: $8M/mes ($96M anuales)
- Costos: 65% — margen apretado
- Sin contador, sin facturación electrónica
- Tiene BPA
- **Resultado esperado**: Régimen Simple (Grupo 5), riesgos CRÍTICOS por ICA-SimplifICA y uso de suelos
- **Solicitante**: Juan Esteban Gutiérrez Caicedo

### 9.2 `?prefill=lead-caliente` — Caso Servicios Profesionales (Lead Caliente Growth)
**Empresa**: TechFlow Digital SAS
- Sector: Agencia digital (web + e-commerce + growth)
- **CIIU principal**: 7020 (consultoría) — fallback GRUPO2 en código actual
- Ingresos: $35M/mes ($420M anuales)
- Costos: 32% — margen alto
- Sin contador, sin facturación electrónica
- E-commerce activo, ya declaró renta 2024
- **Resultado esperado**: Régimen Simple, ahorro ~$160M/año, readiness ~50/100 (ambar)
- **Solicitante**: Catalina Restrepo Vélez
- **Email destino**: `growth@contexia.online`
- **WhatsApp destino**: `+57 3504187902`
- **Comportamiento**: salta directo al Paso 8 (no requiere clic en cada paso)

---

## 10. CTAs Finales y Distribución de Resultados

| CTA | Acción |
|---|---|
| 🏢 **Crear mi empresa** | Link a `contexia.online/crear-empresa.html` (paquetes desde $1.2M) |
| 📞 **Agendar asesoría gratis** | Link a `cal.com/juan-david-pelaez-cardenas-jrurh5/30min` (30 min Google Meet) |
| 📄 **Descargar PDF** | `/wizard/api/audit/pdf?email=...&leadId=...` — informe detallado |
| 📧 **Enviar por email** | Input pre-llenado con email del paso 1. Submit dispara Resend |
| 📲 **Compartir por WhatsApp** | Abre `wa.me/57<whatsapp>` con resumen pre-llenado (régimen + ahorro + readiness + #riesgos + #oportunidades) |

### Plantilla del mensaje WhatsApp
```
🔍 *Shadow Audit — {empresa}*

👤 Solicitante: {nombre}
📧 Email: {email}

📊 Régimen recomendado: *{Simple|Ordinario}*
💰 Ahorro potencial: *{$X}/año*
📈 Readiness Score: *{score}/100*
⚠️ Riesgos: {count}
💡 Oportunidades: {count}

Generado por Contexia · contexia.online/wizard
```

---

## 11. Eventos GA4 (Tracking)

| Evento | Cuándo se dispara |
|---|---|
| `wizard_started` | El usuario pulsa "Hacer mi diagnóstico gratuito" |
| `step_completed` | Al pasar de cualquier paso al siguiente (incluye `step_number`) |
| `audit_executed` | Tras ejecutar Shadow Audit (incluye régimen, score, ahorro, #riesgos) |
| `ciiu_1090_banner_shown` | Cuando se muestra banner especial alimentos |
| `email_sent` | Email enviado con éxito vía Resend |
| `pdf_downloaded` | Clic en descargar PDF |
| `whatsapp_opened` | Clic en CTAs de WhatsApp (Taty especialista o share) |
| `cta_clicked` | Cualquier CTA final (`crear_empresa`, `agendar_asesoria`, `whatsapp_share`) |

---

## 12. Cumplimiento Legal y Disclaimer

> Este diagnóstico es una herramienta de orientación generada automáticamente. **NO constituye asesoría legal, contable o tributaria formal**. Las cifras son estimaciones basadas en normativa vigente y pueden variar al validar con tus números reales. La firma de declaraciones tributarias requiere Contador Público titulado.

### Fuentes normativas referenciadas
- Estatuto Tributario (E.T.) — Arts. 240, 908
- Ley 1819 de 2016 (reforma estructural)
- Ley 2010 de 2019 (crecimiento económico)
- Ley 2155 de 2021 (inversión social)
- Resolución DIAN UVT 2026
- Resolución ICA 061252/2020 (SimplifICA)
- Acuerdo Municipal Medellín 67/2017 (ICA)
- INVIMA Decreto 1500 / 1571 (BPM alimentos)

---

## 13. Reglas de Producto (Contexia)

1. **Multi-tenant**: Todo registro debe estar vinculado a un `company_id`
2. **Seguridad**: Row Level Security (RLS) en Postgres; no exponer lógica sensible en cliente
3. **Estética**: Mantener el estándar premium (Teal/Violet/Navy)
4. **Validación documental**: el XML de la DIAN es la fuente de verdad
5. **No secretos**: nunca subir llaves de API al repo (usar `.env`)

---

## 14. Casos de Uso por Persona

### 14.1 Emprendedor que aún no constituye
**Problema**: no sabe si crear SAS o seguir como persona natural, ni qué régimen elegir.
**Output del Shadow Audit**: comparativo tributario claro + plan 30-60-90 + CTA "Crear mi empresa".

### 14.2 PyME informal con ingresos crecientes
**Problema**: factura sin RUT correcto, no declara renta, expuesta a multas DIAN.
**Output**: riesgos CRÍTICOS visibles + readiness bajo + CTA "Agendar asesoría".

### 14.3 Empresa establecida sin contador
**Problema**: paga ordinario sin saber que Simple le ahorraría millones.
**Output**: ahorro potencial cuantificado + recomendación de migración de régimen.

### 14.4 Sector regulado (alimentos, salud, agro)
**Problema**: desconoce obligaciones INVIMA/ICA/sanitario.
**Output**: banner especial sectorial + acción inmediata + WhatsApp a especialista.

---

## 15. Roadmap y Mejoras Futuras

### Fase 1 — Funcional (✅ actual)
- 8 pasos completos con validación Zod
- Cálculo Simple vs Ordinario con UVT 2026
- Detección de riesgos y oportunidades
- Readiness score con plan 30-60-90
- Email, PDF, WhatsApp
- 2 casos de prueba (`connatural`, `lead-caliente`)

### Fase 2 — Datos persistentes y portal cliente (en curso)
- Conexión completa con Supabase (auth real)
- Portal cliente (`/app`) con datos reales del lead post-audit
- Búnker admin con vista multi-cliente

### Fase 3 — Agentes IA
- Backend FastAPI con agentes Ollama
- Taty conversacional sobre los resultados
- Auditoría continua mensual con datos DIAN sincronizados
- Radar predictivo de impuestos 90 días

---

## 16. Glosario

| Término | Definición |
|---|---|
| **UVT** | Unidad de Valor Tributario — referencia anual DIAN |
| **CIIU** | Clasificación Industrial Internacional Uniforme — código de actividad económica |
| **SAS** | Sociedad por Acciones Simplificada |
| **SimplifICA** | Plataforma ICA para registro de productores de alimento animal |
| **BPMAA** | Buenas Prácticas en Manufactura de Alimentos para Animales |
| **BPA** | Buenas Prácticas Agrícolas |
| **DIAN** | Dirección de Impuestos y Aduanas Nacionales |
| **RUES** | Registro Único Empresarial y Social (Cámaras de Comercio) |
| **Régimen Simple** | Régimen unificado de tributación (Art. 908 E.T.) — sustituye Renta + ICA + parcial CREE |
| **Régimen Ordinario** | Renta empresarial 35% + IVA 19% + ICA municipal |
| **Readiness Score** | Métrica 0-100 que mide qué tan preparada está la empresa para formalizarse |
| **Shadow Audit** | Diagnóstico tributario automatizado de Contexia |
| **Búnker** | Vista admin del portal Contexia para gestión multi-cliente |
| **Taty** | Agente IA front-stage de Contexia (Tu Amiga Contadora) |

---

## 17. Métricas Clave para Seguimiento

| Métrica | Definición | Objetivo |
|---|---|---|
| **Tasa de inicio** | % visitantes que pulsan "Hacer mi diagnóstico" | > 25% |
| **Tasa de completación** | % que llega al paso 8 | > 60% |
| **Tasa de audit ejecutado** | % que pulsa "Ejecutar Shadow Audit" | > 90% del que llega a paso 8 |
| **Tasa de email enviado** | % que solicita su informe por email | > 40% |
| **Tasa de PDF descargado** | % que descarga PDF | > 25% |
| **Tasa de CTA principal** | % que pulsa "Crear empresa" o "Agendar asesoría" | > 15% |
| **Tiempo medio de finalización** | Minutos del paso 1 al 8 | 4-6 min |

---

## 18. Contactos Operativos

- **Email transaccional**: `growth@contexia.online`
- **WhatsApp Taty**: `+57 3018948151`
- **Cal.com asesoría**: `cal.com/juan-david-pelaez-cardenas-jrurh5/30min`
- **Repo GitHub**: `jpelaezcardenas/antigravity-app`
- **Branch productiva**: `main`
- **GA4 ID**: `G-Q03PYP6RBH`

---

*Fin del documento. Cualquier cambio sustancial en el wizard debe reflejarse aquí antes de mergear a `main`.*
