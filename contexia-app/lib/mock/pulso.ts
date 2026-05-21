import type { PulsoData } from "@/lib/types/contexia";

export const pulsoMock: PulsoData = {
  note: {
    title: "Hoy en tu negocio:",
    body: "Tu plata está sana, pero bajó un poco por una cuota del banco. Nada grave, sigue tranqui 💪",
  },
  cash: {
    total: 42_850_000,
    yours: 38_500_000,
    yesterdaySales: 1_250_000,
    expenses: 345_000,
    detailHref: "/app/flujo-detalle",
  },
  health: [
    {
      id: "liquidez",
      icon: "water_drop",
      label: "Plata disponible",
      status: "sana",
      detailHref: "/app/flujo-detalle",
    },
    {
      id: "rentabilidad",
      icon: "trending_up",
      label: "Tu ganancia",
      status: "sana",
    },
    {
      id: "endeudamiento",
      icon: "account_balance",
      label: "Lo que debes",
      status: "vigilancia",
    },
    {
      id: "eficiencia",
      icon: "bolt",
      label: "Aprovechas tu plata",
      status: "sana",
      detailHref: "/app/flujo-detalle",
    },
  ],
  alerts: [
    {
      id: "iva-vencimiento",
      icon: "schedule",
      severity: "warning",
      message: "En 3 días vence tu IVA — separa la plata ahora",
    },
    {
      id: "tx-sin-clasificar",
      icon: "rule_folder",
      severity: "critical",
      message: "Hay 5 movimientos sin organizar — Taty te ayuda",
    },
  ],
};
