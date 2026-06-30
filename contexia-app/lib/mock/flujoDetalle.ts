import type { FlujoDetalleData } from "@/lib/types/contexia";

export const flujoDetalleMock: FlujoDetalleData = {
  header: {
    title: "Cómo se mueve tu plata",
    subtitle: "De dónde viene y a dónde va — sin enredos",
  },

  insight: {
    body: [
      {
        text: "Estás vendiendo bien, pero te apalancas mucho con créditos. ",
      },
      {
        text: "Cobra más rápido a tus clientes",
        highlight: true,
      },
      {
        text: " para que la plata fluya sin pedirle prestado al banco.",
      },
    ],
  },

  flowComposition: [
    {
      id: "operacion",
      label: "Tu negocio",
      percentage: 65,
      color: "text-status-success",
    },
    {
      id: "inversion",
      label: "Inversiones",
      percentage: -15,
      color: "text-primary",
    },
    {
      id: "financiacion",
      label: "Créditos / banco",
      percentage: 20,
      color: "text-status-warning",
    },
  ],

  liquidityBridge: {
    initialBalance: 45200,
    inflows: 128500,
    outflows: -112300,
    finalBalance: 61400,
  },

  healthMetrics: [
    {
      id: "liquidez",
      label: "Plata disponible",
      description: "Cuánta plata tienes lista para lo que se te ofrezca hoy.",
      status: "sana",
      percentage: 85,
      color: "text-status-success",
    },
    {
      id: "solvencia",
      label: "Aguantar a largo plazo",
      description: "Si puedes responder por las deudas grandes sin ahogarte.",
      status: "vigilancia",
      percentage: 45,
      color: "text-status-warning",
    },
  ],
};
