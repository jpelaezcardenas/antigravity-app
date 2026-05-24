export const fiscalMock = {
  risk: {
    level: "medium",
    score: 65,
    alerts: 2,
  },
  exAnte: {
    violations: [],
    recommendations: [],
  },
  shadowAudit: {
    findings: [],
  },
  thresholds: [
    { id: "1", label: "Tope Responsable de IVA", current: 3100, max: 3500, unit: "UVT" },
    { id: "2", label: "Tope Régimen Simple", current: 80000, max: 100000, unit: "UVT" }
  ],
  taty: {
    lastQuestion: null,
  },
};
