// ============================================================
// lib/readinessScore.ts
// Readiness Score 0-100 para el Shadow Audit
// ============================================================

interface DatosScore {
  tiene_contador?: boolean;
  facturacion_electronica?: "si" | "no" | "no_se";
  software_contable?: string;
  tiene_ecommerce?: boolean;
  empleados?: number;
  ha_declarado_renta?: boolean;
  maneja_inventarios?: boolean;
  tiene_bpa?: boolean;
}

export interface ReadinessResult {
  score: number;
  band: "verde" | "ambar" | "rojo";
  mensaje: string;
  submensaje: string;
  breakdown: { label: string; puntos: number; obtenido: boolean }[];
}

export function calcularReadiness(datos: DatosScore): ReadinessResult {
  const items = [
    {
      label: "Contador activo",
      puntos: 15,
      obtenido: !!datos.tiene_contador,
    },
    {
      label: "Facturación electrónica habilitada",
      puntos: 15,
      obtenido: datos.facturacion_electronica === "si",
    },
    {
      label: "Software contable en uso",
      puntos: 10,
      obtenido: !!(datos.software_contable && datos.software_contable.trim().length > 0),
    },
    {
      label: "Canal e-commerce activo",
      puntos: 10,
      obtenido: !!datos.tiene_ecommerce,
    },
    {
      label: "Empleados formales",
      puntos: 10,
      obtenido: (datos.empleados || 0) > 0,
    },
    {
      label: "Ha declarado renta antes",
      puntos: 15,
      obtenido: !!datos.ha_declarado_renta,
    },
    {
      label: "Maneja inventarios físicos",
      puntos: 10,
      obtenido: !!datos.maneja_inventarios,
    },
    {
      label: "BPA/BPM implementadas",
      puntos: 15,
      obtenido: !!datos.tiene_bpa,
    },
  ];

  const score = items.reduce(
    (total, item) => total + (item.obtenido ? item.puntos : 0),
    0
  );

  let band: "verde" | "ambar" | "rojo";
  let mensaje: string;
  let submensaje: string;

  if (score >= 80) {
    band = "verde";
    mensaje = "Listo para formalizar — Empieza ya";
    submensaje =
      "Tu empresa tiene bases sólidas. El proceso de constitución será rápido y ordenado.";
  } else if (score >= 50) {
    band = "ambar";
    mensaje = "Requiere ajustes antes — Te acompañamos";
    submensaje =
      "Hay aspectos importantes por fortalecer. Contexia te guía en cada paso para no dejar vacíos.";
  } else {
    band = "rojo";
    mensaje = "Foundation building crítico — Necesitas el paquete completo";
    submensaje =
      "Tu empresa requiere construcción desde los cimientos. El paquete Crear Empresa de Contexia cubre todo esto.";
  }

  return { score, band, mensaje, submensaje, breakdown: items };
}
