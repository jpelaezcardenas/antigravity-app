import type { Scenario, RadarScenarioData } from "@/lib/types/contexia";

export const radarMock = {
  header: {
    title: "Radar Financiero",
    subtitle: "Proyecciones de flujo de caja y provisión tributaria en 3 escenarios",
  },

  scenarios: {
    pesimista: {
      cashProjection: {
        forecast: 2800000,
        baselineDate: "2026-05-24",
        scenarios: {
          pesimista: 2800000,
          base: 5200000,
          optimista: 8100000,
        },
      },
      taxProvision: {
        estimatedMonthly: 450000,
        estimatedQuarterly: 1350000,
        notes: "Retención por pagar en 15 días. Renta provisional activa.",
      },
      strategicInsight: {
        title: "Presupuesto ajustado recomendado",
        description:
          "En escenario pesimista, mantener reserva de contingencia de $2M mínimo para impuestos y gastos operativos.",
        actionItems: [
          "Reducir gastos discrecionales",
          "Acelerar cobranza a clientes",
          "Evaluar línea de crédito stand-by",
        ],
      },
      upcomingMilestones: [
        {
          date: "2026-06-08",
          description: "Pago de retención en la fuente",
          impact: "high",
        },
        {
          date: "2026-06-30",
          description: "Cierre trimestral Q2",
          impact: "medium",
        },
        {
          date: "2026-07-15",
          description: "Presentación renta provisional",
          impact: "high",
        },
      ],
    },

    base: {
      cashProjection: {
        forecast: 5200000,
        baselineDate: "2026-05-24",
        scenarios: {
          pesimista: 2800000,
          base: 5200000,
          optimista: 8100000,
        },
      },
      taxProvision: {
        estimatedMonthly: 620000,
        estimatedQuarterly: 1860000,
        notes: "Cumplimiento tributario según proyección normal. Régimen Común activo.",
      },
      strategicInsight: {
        title: "Posición financiera sana",
        description:
          "Escenario base indica salud financiera estable con capacidad para reinversión.",
        actionItems: [
          "Mantener rotación de caja normal",
          "Reservar 30% de utilidades para impuestos",
          "Planificar reinversión estratégica",
        ],
      },
      upcomingMilestones: [
        {
          date: "2026-06-08",
          description: "Pago de retención en la fuente",
          impact: "medium",
        },
        {
          date: "2026-06-30",
          description: "Cierre trimestral Q2",
          impact: "medium",
        },
        {
          date: "2026-08-15",
          description: "Revisión de régimen tributario",
          impact: "low",
        },
      ],
    },

    optimista: {
      cashProjection: {
        forecast: 8100000,
        baselineDate: "2026-05-24",
        scenarios: {
          pesimista: 2800000,
          base: 5200000,
          optimista: 8100000,
        },
      },
      taxProvision: {
        estimatedMonthly: 950000,
        estimatedQuarterly: 2850000,
        notes: "Proyección con crecimiento acelerado. Verificar viabilidad tributaria.",
      },
      strategicInsight: {
        title: "Oportunidad de escalabilidad",
        description:
          "Escenario optimista muestra potencial de crecimiento significativo. Planificar cambios de régimen si procede.",
        actionItems: [
          "Evaluar cambio a Régimen Simple si aplica",
          "Planificar aumento de activos fijos",
          "Estructurar incentivos tributarios (I+D, etc.)",
        ],
      },
      upcomingMilestones: [
        {
          date: "2026-06-08",
          description: "Pago de retención en la fuente",
          impact: "low",
        },
        {
          date: "2026-06-30",
          description: "Cierre trimestral Q2",
          impact: "high",
        },
        {
          date: "2026-09-01",
          description: "Potencial cambio de régimen tributario",
          impact: "high",
        },
      ],
    },
  } as Record<Scenario, RadarScenarioData>,
};
