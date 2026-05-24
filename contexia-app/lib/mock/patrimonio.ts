export const patrimonio = {
  header: {
    title: "Valor Real de la Empresa",
    subtitle: "Lo que realmente vale tu negocio hoy y cómo se compone tu patrimonio",
  },
  patrimonio: {
    total: 250000000,
    liquido: 150000000,
    inmovilizado: 100000000,
    change: 5.2,
    trend: "up" as const
  },
  insight: {
    title: "Crecimiento Sostenido",
    message: "Tu patrimonio creció un 5.2% este mes gracias a la retención de utilidades y la reducción de pasivos financieros.",
    impact: "positive" as const
  },
  dividendShield: {
    available: 50000000,
    protected: 30000000,
    status: "healthy" as const
  },
  withdrawalSimulator: {
    maxSafeWithdrawal: 20000000,
    cashWithoutWithdrawal: 80000000,
    currentSelection: 10000000
  },
  movements: [
    { id: "1", date: "2026-05-01", description: "Capitalización de utilidades", amount: 15000000, type: "in" },
    { id: "2", date: "2026-05-15", description: "Distribución anticipada socios", amount: -5000000, type: "out" }
  ]
};
