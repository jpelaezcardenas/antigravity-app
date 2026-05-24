export const flujoDetalleMock = {
  structuralInsight: {
    message: "Estructura de liquidez sana, soportando operaciones sin apalancamiento.",
    trend: "positive" as const,
  },
  composition: {
    ingresosOperativos: 55000000,
    costosOperativos: 18000000,
    gastosFijos: 12000000,
    otrosIngresos: 1500000,
    otrosEgresos: 800000,
  },
  monthlyLiquidity: {
    months: ["Ene", "Feb", "Mar", "Abr", "May"],
    values: [10000000, 15000000, 12000000, 18000000, 22000000]
  }
};
