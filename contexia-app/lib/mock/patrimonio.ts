import type { PatrimonioData } from "@/lib/types/contexia";

export const patrimonio: PatrimonioData = {
  header: {
    title: "Tu plata real",
    subtitle: "Cuánta plata tienes tuya — y cuánto puedes sacarte sin riesgo",
  },

  patrimonio: {
    total: 42500000, // $42.5M
    retainedEarnings: 28300000, // Plata ganada y guardada en el negocio
    currentYearEarnings: 14200000, // Lo que llevas ganado este año
  },

  dividendShield: {
    safeAmount: 8500000, // Zona segura para sacar
    safeZoneLabel: "Lo que puedes sacarte tranqui",
    riskLabel: "Si te sacas más del 30%, el negocio se queda corto",
  },

  withdrawalSimulator: {
    amount: 0, // Estado inicial: sin retiro
    cashWithoutWithdrawal: 28500000, // Plata base para calcular impacto
    cashWithWithdrawal: 28500000, // Se actualiza con setState
    status: "sana",
    message:
      "No te has sacado nada. Tu plata real al final del año: $42.5M",
  },

  movements: [
    {
      id: "mov-1",
      date: "Octubre 2024",
      direction: "outflow",
      label: "Te sacaste plata",
      amount: -2500000,
    },
    {
      id: "mov-2",
      date: "Agosto 2024",
      direction: "inflow",
      label: "Metiste plata extra",
      amount: 10000000,
    },
    {
      id: "mov-3",
      date: "Junio 2024",
      direction: "outflow",
      label: "Reparto de ganancias",
      amount: -3200000,
    },
  ],

  insight: {
    body: [
      {
        text: "Taty recomienda dejar invertido hasta ",
      },
      { text: "$8.5M este trimestre", highlight: true },
      {
        text: " para que el negocio aguante. Si quieres crecer, vas a necesitar más plata trabajando.",
      },
    ],
  },
};
