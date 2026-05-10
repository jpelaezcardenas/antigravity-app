// ============================================================
// lib/calculations.ts
// Lógica tributaria colombiana — Régimen Simple vs Ordinario
// UVT 2026 = $49.799 (Resolución DIAN)
// ============================================================

export const UVT_2026 = 49799;

// ─── Tarifas Régimen Simple (Art. 908 E.T.) ─────────────────
// Grupo → CIIU → tarifa% según tramo de ingresos (en UVT)
// Fuente: Ley 2010/2019, Ley 2155/2021

export interface TramoSimple {
  desdeUVT: number;
  hastaUVT: number;
  tarifa: number; // porcentaje, ej. 1.8 = 1.8%
}

export const TARIFAS_SIMPLE: Record<string, TramoSimple[]> = {
  // Grupo 1: Tiendas, mini-mercados, panaderías, carnicerías, droguerías
  GRUPO1: [
    { desdeUVT: 0, hastaUVT: 6000, tarifa: 2.0 },
    { desdeUVT: 6000, hastaUVT: 15000, tarifa: 2.8 },
    { desdeUVT: 15000, hastaUVT: 30000, tarifa: 8.1 },
    { desdeUVT: 30000, hastaUVT: 80000, tarifa: 11.6 },
    { desdeUVT: 80000, hastaUVT: 100000, tarifa: 14.96 },
  ],
  // Grupo 2: Comercio al detal (excluidos Grupo 1), servicios técnicos, mecánicos
  GRUPO2: [
    { desdeUVT: 0, hastaUVT: 6000, tarifa: 1.8 },
    { desdeUVT: 6000, hastaUVT: 15000, tarifa: 2.2 },
    { desdeUVT: 15000, hastaUVT: 30000, tarifa: 3.9 },
    { desdeUVT: 30000, hastaUVT: 80000, tarifa: 5.4 },
    { desdeUVT: 80000, hastaUVT: 100000, tarifa: 6.3 },
  ],
  // Grupo 3: Servicios profesionales, consultoría, honorarios
  GRUPO3: [
    { desdeUVT: 0, hastaUVT: 6000, tarifa: 5.9 },
    { desdeUVT: 6000, hastaUVT: 15000, tarifa: 7.3 },
    { desdeUVT: 15000, hastaUVT: 30000, tarifa: 12.0 },
    { desdeUVT: 30000, hastaUVT: 80000, tarifa: 14.5 },
    { desdeUVT: 80000, hastaUVT: 100000, tarifa: 16.0 },
  ],
  // Grupo 4: Educación, actividades deportivas, esparcimiento
  GRUPO4: [
    { desdeUVT: 0, hastaUVT: 6000, tarifa: 3.4 },
    { desdeUVT: 6000, hastaUVT: 15000, tarifa: 3.8 },
    { desdeUVT: 15000, hastaUVT: 30000, tarifa: 5.5 },
    { desdeUVT: 30000, hastaUVT: 80000, tarifa: 7.0 },
    { desdeUVT: 80000, hastaUVT: 100000, tarifa: 8.5 },
  ],
  // Grupo 5: Manufactura, industria, construcción
  GRUPO5: [
    { desdeUVT: 0, hastaUVT: 6000, tarifa: 2.5 },
    { desdeUVT: 6000, hastaUVT: 15000, tarifa: 3.0 },
    { desdeUVT: 15000, hastaUVT: 30000, tarifa: 4.5 },
    { desdeUVT: 30000, hastaUVT: 80000, tarifa: 6.0 },
    { desdeUVT: 80000, hastaUVT: 100000, tarifa: 7.5 },
  ],
};

// Mapeo CIIU → Grupo Simple
export const CIIU_A_GRUPO: Record<string, string> = {
  "1090": "GRUPO5", // Elaboración alimentos para animales
  "4631": "GRUPO2", // Comercio al por mayor alimentos
  "4791": "GRUPO2", // Comercio al por menor internet
  "4773": "GRUPO1", // Comercio minorista especializado
  "5611": "GRUPO1", // Restaurantes
  "6201": "GRUPO3", // Desarrollo de software
  "7500": "GRUPO3", // Servicios veterinarios
  "9609": "GRUPO2", // Otros servicios personales
};

// ─── ICA Medellín (Acuerdo Municipal 67/2017) ───────────────
export const ICA_MEDELLIN: Record<string, number> = {
  manufactura: 7,    // 7‰
  comercio: 10,      // 10‰
  servicios: 5,      // 5‰
  default: 8,
};

export function getIcaMedellin(ciiu: string): number {
  const ciiuNum = parseInt(ciiu);
  if (ciiuNum >= 1000 && ciiuNum <= 3999) return ICA_MEDELLIN.manufactura;
  if (ciiuNum >= 4500 && ciiuNum <= 4799) return ICA_MEDELLIN.comercio;
  if (ciiuNum >= 5000 && ciiuNum <= 5300) return ICA_MEDELLIN.comercio;
  if (ciiuNum >= 5500 && ciiuNum <= 9999) return ICA_MEDELLIN.servicios;
  return ICA_MEDELLIN.default;
}

// ─── Cálculo Régimen Simple ──────────────────────────────────

export interface ResultadoSimple {
  aplicable: boolean;
  razonNoAplicable?: string;
  ingresosAnuales: number;
  ingresosEnUVT: number;
  grupo: string;
  tarifa: number; // %
  impuestoAnual: number;
  incluye: string[];
}

export function calcularSimple(ingresosAnuales: number, ciiu: string): ResultadoSimple {
  const ingresosEnUVT = ingresosAnuales / UVT_2026;
  const MAX_UVT = 100000;

  if (ingresosEnUVT > MAX_UVT) {
    return {
      aplicable: false,
      razonNoAplicable: `Supera 100.000 UVT (~$${formatMillones(MAX_UVT * UVT_2026)}) — obligado a Régimen Ordinario`,
      ingresosAnuales,
      ingresosEnUVT,
      grupo: "",
      tarifa: 0,
      impuestoAnual: 0,
      incluye: [],
    };
  }

  const grupo = CIIU_A_GRUPO[ciiu] || "GRUPO2";
  const tramos = TARIFAS_SIMPLE[grupo];
  const tramo = tramos.find(
    (t) => ingresosEnUVT >= t.desdeUVT && ingresosEnUVT < t.hastaUVT
  ) || tramos[tramos.length - 1];

  const tarifa = tramo.tarifa;
  const impuestoAnual = ingresosAnuales * (tarifa / 100);

  return {
    aplicable: true,
    ingresosAnuales,
    ingresosEnUVT,
    grupo,
    tarifa,
    impuestoAnual,
    incluye: ["Renta", "ICA integrado", "CREE parcial"],
  };
}

// ─── Cálculo Régimen Ordinario ───────────────────────────────

export interface ResultadoOrdinario {
  ingresosAnuales: number;
  costosTotales: number;
  utilidadBruta: number;
  rentaAnual: number;
  ivaAnual: number;
  icaAnual: number;
  totalImpuestos: number;
  margenNeto: number;
}

export function calcularOrdinario(
  ingresosAnuales: number,
  costosPct: number, // 0-100
  ciiu: string,
  ciudad = "Medellin"
): ResultadoOrdinario {
  const costosTotales = ingresosAnuales * (costosPct / 100);
  const utilidadBruta = ingresosAnuales - costosTotales;
  
  // Renta empresarial: 35% sobre utilidad (Art. 240 E.T.)
  const rentaAnual = utilidadBruta > 0 ? utilidadBruta * 0.35 : 0;

  // IVA neto estimado: 19% generado - descontable (aprox 50% de compras gravadas)
  const comprasGravadas = costosTotales * 0.5;
  const ivaGenerado = ingresosAnuales * 0.19;
  const ivaDescontable = comprasGravadas * 0.19;
  const ivaAnual = Math.max(0, ivaGenerado - ivaDescontable);

  // ICA municipal
  const tasaICA = ciudad.toLowerCase().includes("medellin") || ciudad.toLowerCase().includes("medellín")
    ? getIcaMedellin(ciiu)
    : ICA_MEDELLIN.default;
  const icaAnual = ingresosAnuales * (tasaICA / 1000);

  const totalImpuestos = rentaAnual + ivaAnual + icaAnual;
  const margenNeto = ingresosAnuales > 0
    ? ((ingresosAnuales - costosTotales - totalImpuestos) / ingresosAnuales) * 100
    : 0;

  return {
    ingresosAnuales,
    costosTotales,
    utilidadBruta,
    rentaAnual,
    ivaAnual,
    icaAnual,
    totalImpuestos,
    margenNeto,
  };
}

// ─── Comparativo y Ahorro ────────────────────────────────────

export interface ResultadoComparativo {
  simple: ResultadoSimple;
  ordinario: ResultadoOrdinario;
  recomendacion: "simple" | "ordinario";
  ahorroPotencialAnual: number;
  ahorroMensual: number;
}

export function compararRegimenes(
  ingresosAnuales: number,
  costosPct: number,
  ciiu: string,
  ciudad = "Medellín"
): ResultadoComparativo {
  const simple = calcularSimple(ingresosAnuales, ciiu);
  const ordinario = calcularOrdinario(ingresosAnuales, costosPct, ciiu, ciudad);

  let recomendacion: "simple" | "ordinario";
  let ahorroPotencialAnual: number;

  if (!simple.aplicable) {
    recomendacion = "ordinario";
    ahorroPotencialAnual = 0;
  } else {
    ahorroPotencialAnual = ordinario.totalImpuestos - simple.impuestoAnual;
    recomendacion = ahorroPotencialAnual > 0 ? "simple" : "ordinario";
    ahorroPotencialAnual = Math.abs(ahorroPotencialAnual);
  }

  return {
    simple,
    ordinario,
    recomendacion,
    ahorroPotencialAnual,
    ahorroMensual: ahorroPotencialAnual / 12,
  };
}

// ─── Utilidades de formato ───────────────────────────────────

export function formatCOP(value: number): string {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatMillones(value: number): string {
  if (value >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(1)} mil millones`;
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  return formatCOP(value);
}

export function formatUVT(uvt: number): string {
  return `${uvt.toFixed(0)} UVT`;
}
