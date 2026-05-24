export const pulsoMock = {
  note: {
    title: "Operación normal",
    message: "Tu negocio está marchando bien. Sin alertas críticas.",
    sentiment: "positive",
  },
  cash: {
    available: 5200000,
    reserved: 800000,
    forecast: 6100000,
  },
  health: {
    liquidity: 8,
    profitability: 7,
    efficiency: 6,
    growth: 8,
  },
  alerts: [
    {
      id: "alert-1",
      title: "Retención próxima",
      description: "Retención por pagar en 15 días",
      severity: "warning",
    },
  ],
};
