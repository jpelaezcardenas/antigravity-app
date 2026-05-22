import type { RadarData } from "@/lib/types/contexia";

/**
 * Mock con 3 escenarios completos.
 *
 * Coordenadas SVG: viewBox 0 0 100 100 con preserveAspectRatio="none".
 * X=0..100 cubre el ancho del chart, Y=0..100 cubre la altura.
 * Y=0 es arriba (caja alta), Y=100 es abajo (caja baja).
 *
 * pointTopPct dentro del marcador IVA = Y del path en X=60.
 * Mantén ambos consistentes para que el dot caiga sobre la línea.
 */
export const radarMock: RadarData = {
  header: {
    title: "Lo que viene",
    subtitle: "Cómo se verá tu plata en los próximos 90 días",
  },
  scenarios: {
    pesimista: {
      cashProjection: {
        tone: "warning",
        pathD: "M0,70 L20,78 L40,72 L60,55 L80,65 L100,60",
        obligation: { label: "IVA", positionPct: 60, pointTopPct: 55 },
        axisLabels: ["Hoy", "30d", "60d", "90d"],
      },
      taxProvision: {
        estimated: 22_500_000,
        reserved: 8_000_000,
        goalPct: 36,
      },
      strategicInsight: {
        body: [
          { text: "En " },
          { text: "21 días", highlight: true },
          {
            text: " tu plata podría apretarse. Adelanta cobros o pide más plazo antes que llegue el IVA — Taty te ayuda.",
          },
        ],
      },
      upcomingMilestones: [
        {
          id: "iva",
          monthAbbr: "OCT",
          day: "15",
          severity: "critical",
          title: "Pagas IVA",
          subtitle: "Plata para la DIAN",
          amount: 4_200_000,
        },
        {
          id: "alquiler",
          monthAbbr: "OCT",
          day: "20",
          severity: "critical",
          title: "Arriendo oficina",
          subtitle: "Gasto fijo importante",
          amount: 3_800_000,
        },
        {
          id: "cloud",
          monthAbbr: "NOV",
          day: "05",
          severity: "warning",
          title: "Renovación de programas",
          subtitle: "Gasto del día a día",
          amount: 1_150_000,
        },
      ],
    },
    base: {
      cashProjection: {
        tone: "base",
        pathD: "M0,80 L20,60 L40,65 L60,30 L80,45 L100,20",
        obligation: { label: "IVA", positionPct: 60, pointTopPct: 30 },
        axisLabels: ["Hoy", "30d", "60d", "90d"],
      },
      taxProvision: {
        estimated: 18_450_000,
        reserved: 12_000_000,
        goalPct: 65,
      },
      strategicInsight: {
        body: [
          { text: "En " },
          { text: "45 días", highlight: true },
          {
            text: " vas a tener plata de sobra. Buena chance para invertir en publicidad — eso te baja los impuestos al final del año.",
          },
        ],
      },
      upcomingMilestones: [
        {
          id: "iva",
          monthAbbr: "OCT",
          day: "15",
          severity: "critical",
          title: "Pagas IVA",
          subtitle: "Plata para la DIAN",
          amount: 4_200_000,
        },
        {
          id: "cloud",
          monthAbbr: "NOV",
          day: "05",
          severity: "warning",
          title: "Renovación de programas",
          subtitle: "Gasto del día a día",
          amount: 1_150_000,
        },
      ],
    },
    optimista: {
      cashProjection: {
        tone: "positive",
        pathD: "M0,80 L20,55 L40,40 L60,18 L80,12 L100,5",
        obligation: { label: "IVA", positionPct: 60, pointTopPct: 18 },
        axisLabels: ["Hoy", "30d", "60d", "90d"],
      },
      taxProvision: {
        estimated: 15_000_000,
        reserved: 13_500_000,
        goalPct: 90,
      },
      strategicInsight: {
        body: [
          { text: "Tu plata puede crecer " },
          { text: "18% en 60 días", highlight: true },
          {
            text: ". Aprovecha para reinvertir antes que cierre el año — así pagas menos a la DIAN.",
          },
        ],
      },
      upcomingMilestones: [
        {
          id: "iva",
          monthAbbr: "OCT",
          day: "15",
          severity: "warning",
          title: "Pagas IVA",
          subtitle: "Plata para la DIAN",
          amount: 4_200_000,
        },
        {
          id: "cloud",
          monthAbbr: "NOV",
          day: "05",
          severity: "warning",
          title: "Renovación de programas",
          subtitle: "Gasto del día a día",
          amount: 1_150_000,
        },
        {
          id: "campaign",
          monthAbbr: "NOV",
          day: "30",
          severity: "warning",
          title: "Pauta digital del próximo trimestre",
          subtitle: "Inversión que baja impuestos",
          amount: 2_500_000,
        },
      ],
    },
  },
};
