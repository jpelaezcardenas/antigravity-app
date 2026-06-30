import type { FiscalData } from "@/lib/types/contexia";

export const fiscalMock: FiscalData = {
  risk: {
    level: "bajo",
    sectionLabel: "Tu radar con la DIAN",
    levelLabel: "Estás tranqui · Riesgo bajo",
  },
  exAnte: {
    title: "Te bloqueamos 2 facturas peligrosas",
    description:
      "Eran de proveedores en lista negra DIAN. No las cuentes — te evitamos un dolor de cabeza fiscal.",
    blockedCount: 2,
  },
  shadowAudit: {
    title: "Cuadre con la DIAN",
    highlight: "100% al día",
    description:
      "Tus números coinciden exactos con lo que la DIAN ya tiene de ti. Cero descuadres, cero sustos.",
  },
  thresholds: [
    {
      id: "renta",
      label: "¿Te toca declarar renta?",
      current: 845,
      max: 1400,
      unit: "UVT",
    },
    {
      id: "iva",
      label: "¿Te toca cobrar IVA?",
      current: 2800,
      max: 3500,
      unit: "UVT",
    },
  ],
  taty: {
    title: "Pregúntale a Taty",
    subtitle: "Tu amiga contadora — te explica fácil, sin enredos",
  },
};
