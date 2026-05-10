// ============================================================
// lib/riskAnalysis.ts
// Detección de riesgos tributarios y regulatorios
// ============================================================

import { UVT_2026 } from "./calculations";

export type NivelRiesgo = "CRÍTICO" | "ALTO" | "MEDIO" | "BAJO";

export interface Riesgo {
  id: string;
  nivel: NivelRiesgo;
  titulo: string;
  descripcion: string;
  accion: string;
  esBannerCIIU1090?: boolean;
}

export interface Oportunidad {
  id: string;
  titulo: string;
  descripcion: string;
  impactoEstimado?: string;
}

interface DatosWizard {
  // Paso 2
  ciiu_principal?: string;
  tipo_sociedad?: string;
  // Paso 4
  ingresos_mensuales?: number;
  costos_pct?: number;
  tiene_ingresos_previos?: boolean;
  ha_declarado_renta?: boolean;
  // Paso 5
  tiene_contador?: boolean;
  facturacion_electronica?: "si" | "no" | "no_se";
  regimen_preferido?: string;
  // Paso 6
  empleados?: number;
  tiene_bpa?: boolean;
  // Paso 7
  tiene_ecommerce?: boolean;
}

export function detectarRiesgos(datos: DatosWizard): Riesgo[] {
  const riesgos: Riesgo[] = [];
  const ingresosAnuales = (datos.ingresos_mensuales || 0) * 12;
  const ingresosEnUVT = ingresosAnuales / UVT_2026;

  // ── CRÍTICO: CIIU 1090 sin registro ICA ─────────────────
  if (datos.ciiu_principal === "1090") {
    riesgos.push({
      id: "ica_1090",
      nivel: "CRÍTICO",
      titulo: "Sin registro ICA — Fabricante de Alimento Animal",
      descripcion:
        "La Resolución ICA 061252/2020 obliga a TODOS los fabricantes de alimento comercial para animales a registrarse en la plataforma SimplifICA. Operar sin este registro expone a decomiso del producto en bodega y en tránsito, cierre del establecimiento por autoridad sanitaria, multas hasta 10.000 SMMLV (~$14.230 millones COP en 2026) e inhabilitación para volver a operar.",
      accion:
        "Iniciar trámite de registro en SimplifICA (ICA). Requiere: vehículo legal SAS, veterinario asesor técnico contratado, y cumplimiento BPMAA. Contexia te acompaña en la ruta de mitigación.",
      esBannerCIIU1090: true,
    });
  }

  // ── CRÍTICO: Supera 100.000 UVT → Ordinario obligatorio ─
  if (ingresosEnUVT > 100000) {
    riesgos.push({
      id: "supera_uvt",
      nivel: "CRÍTICO",
      titulo: "Supera 100.000 UVT — Régimen Simple no aplica",
      descripcion: `Tus ingresos proyectados superan 100.000 UVT (~$4.980M). Por ley, el Régimen Simple de Tributación aplica SOLO hasta ese tope. Tu empresa está obligada al Régimen Ordinario (Renta 35%).`,
      accion:
        "Optar por Régimen Ordinario y optimizar deducciones permitidas. Un contador puede reducir significativamente la base gravable.",
    });
  }

  // ── ALTO: Uso de suelos para manufactura/alimentos ───────
  if (
    datos.ciiu_principal === "1090" ||
    datos.ciiu_principal === "5611" ||
    datos.ciiu_principal === "4723"
  ) {
    riesgos.push({
      id: "uso_suelos",
      nivel: "ALTO",
      titulo: "Sin concepto de uso de suelos — Riesgo de cierre de planta",
      descripcion:
        "Tu actividad económica (manufactura/alimentos) requiere concepto de uso de suelos emitido por Planeación Municipal. Sin este documento, la autoridad puede ordenar el cierre inmediato del establecimiento.",
      accion:
        "Tramitar concepto de uso de suelos ante la Secretaría de Planeación de tu municipio antes de iniciar operaciones formales.",
    });

    riesgos.push({
      id: "concepto_sanitario",
      nivel: "ALTO",
      titulo: "Sin concepto sanitario municipal",
      descripcion:
        "Las actividades de manufactura y preparación de alimentos requieren concepto sanitario favorable emitido por la Secretaría de Salud Municipal (o INVIMA según escala). Sin él, operar expone al cierre sanitario.",
      accion:
        "Solicitar visita de inspección sanitaria. Asegúrate de que las instalaciones cumplan BPM antes de la visita.",
    });
  }

  // ── ALTO: Sin contador ───────────────────────────────────
  if (!datos.tiene_contador) {
    riesgos.push({
      id: "sin_contador",
      nivel: "ALTO",
      titulo: "Sin asesor contable firmante",
      descripcion:
        "Las declaraciones tributarias ante la DIAN (IVA, Renta, Industria y Comercio) deben ser firmadas por un Contador Público titulado (Ley 43/1990). Sin contador, es imposible declarar válidamente.",
      accion:
        "Contratar contador público o acceder al servicio de Contabilidad 4.0 de Contexia.",
    });
  }

  // ── ALTO: Sin facturación electrónica ────────────────────
  if (
    datos.facturacion_electronica === "no" ||
    datos.facturacion_electronica === "no_se"
  ) {
    riesgos.push({
      id: "sin_facturacion",
      nivel: "ALTO",
      titulo: "Sin habilitación DIAN para factura electrónica",
      descripcion:
        "La facturación electrónica es obligatoria para todas las empresas formalizadas en Colombia (Resolución DIAN 000042/2020). Sin habilitación, no puedes inscribirte al Régimen Simple ni emitir facturas válidas.",
      accion:
        "Habilitar facturación electrónica en el portal DIAN (RADIAN). Contexia gestiona esto en el paquete Crear Empresa.",
    });
  }

  // ── ALTO: Persona natural — Patrimonio expuesto ──────────
  if (datos.tipo_sociedad?.includes("persona_natural") || datos.tipo_sociedad === "otro") {
    riesgos.push({
      id: "persona_natural",
      nivel: "ALTO",
      titulo: "Patrimonio personal expuesto — Sin blindaje vía SAS",
      descripcion:
        "Como persona natural, tu casa, ahorros, vehículo y bienes personales responden solidariamente por las deudas de tu negocio. Una demanda, un incumplimiento comercial o una sanción DIAN puede afectar tu patrimonio familiar.",
      accion:
        "Constituir una SAS (Ley 1258/2008) separa completamente tu patrimonio personal del empresarial. Esto es el primer paso que Contexia ejecuta en Crear Empresa.",
    });
  }

  // ── MEDIO: Margen muy bajo ───────────────────────────────
  if ((datos.costos_pct || 0) > 70) {
    riesgos.push({
      id: "margen_bajo",
      nivel: "MEDIO",
      titulo: "Margen operativo muy bajo",
      descripcion: `Con ${datos.costos_pct}% de costos sobre ingresos, el margen es menor al 30%. Agregar carga tributaria puede hacer el negocio inviable sin optimización.`,
      accion:
        "Revisión de estructura de costos y optimización de deducciones fiscales permitidas. El CFO as a Service de Contexia identifica oportunidades de ahorro.",
    });
  }

  // ── MEDIO: Ingresos previos sin formalizar ───────────────
  if (datos.tiene_ingresos_previos && !datos.ha_declarado_renta) {
    riesgos.push({
      id: "ingresos_previos",
      nivel: "MEDIO",
      titulo: "Ingresos previos sin declarar",
      descripcion:
        "Tienes ingresos como persona natural del año anterior que no habrías declarado. La DIAN puede cruzar información bancaria, EXOGENA y plataformas de pago (Nequi, Daviplata) y generar requerimientos automáticos.",
      accion:
        "Presentar declaración de renta persona natural antes de constituir la empresa. Contexia puede gestionar una declaración correctiva o voluntaria.",
    });
  }

  return riesgos.sort((a, b) => {
    const orden: Record<NivelRiesgo, number> = { CRÍTICO: 0, ALTO: 1, MEDIO: 2, BAJO: 3 };
    return orden[a.nivel] - orden[b.nivel];
  });
}

export function detectarOportunidades(datos: DatosWizard, ingresosAnuales: number, ahorroPotencial: number): Oportunidad[] {
  const oportunidades: Oportunidad[] = [];
  const ingresosEnUVT = ingresosAnuales / UVT_2026;

  if (ingresosEnUVT <= 100000 && !datos.tipo_sociedad?.includes("persona_natural")) {
    oportunidades.push({
      id: "califica_simple",
      titulo: "Califica para Régimen Simple de Tributación",
      descripcion:
        "Con tus ingresos actuales y tipo de sociedad, puedes acogerte al Régimen Simple, que integra Renta + ICA en un solo pago simplificado.",
      impactoEstimado:
        ahorroPotencial > 0
          ? `Ahorro proyectado: ${new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(ahorroPotencial)}/año`
          : undefined,
    });
  }

  if (datos.tipo_sociedad === "SAS" || datos.tipo_sociedad === "sas") {
    oportunidades.push({
      id: "blindaje_sas",
      titulo: "Blindaje patrimonial vía Ley 1258/2008",
      descripcion:
        "Con la SAS, tu casa, ahorros y bienes personales NO responden por deudas de la empresa. Máxima protección con mínima carga administrativa.",
    });
  }

  if (datos.ciiu_principal === "1090" && datos.tiene_bpa) {
    oportunidades.push({
      id: "bpa_ventaja",
      titulo: "BPA implementadas — Camino más corto al registro ICA",
      descripcion:
        "Tener Buenas Prácticas Apícolas/de Manufactura ya operativas reduce el tiempo de registro en SimplifICA. Contexia te ayuda a estructurar la documentación.",
    });
  }

  if (datos.tiene_ecommerce) {
    oportunidades.push({
      id: "ecommerce_radian",
      titulo: "E-commerce + Factura Electrónica → RADIAN",
      descripcion:
        "Tu canal digital justifica CIIU 4791 y la habilitación en RADIAN (plataforma de facturas electrónicas DIAN). Esto te posiciona para recibir pagos formales y negociar con grandes clientes.",
    });
  }

  return oportunidades;
}
