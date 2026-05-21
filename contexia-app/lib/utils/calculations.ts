/**
 * Funciones de cálculo locales para simuladores y lógica financiera
 * Mock-first: reglas simples pero realistas
 */

import type { StatusLevel, WithdrawalScenario } from "@/lib/types/contexia";

// === Withdrawal Simulator ===

export function calculateWithdrawalImpact(
  amount: number,
  cashWithoutWithdrawal: number
): Omit<WithdrawalScenario, "amount"> {
  const cashWithWithdrawal = Math.max(0, cashWithoutWithdrawal - amount);
  const ratio = amount / cashWithoutWithdrawal;

  let status: StatusLevel = "sana";
  if (ratio > 0.3) {
    status = "alerta";
  } else if (ratio > 0.15) {
    status = "vigilancia";
  }

  let message = "";
  if (amount === 0) {
    message = "Sin retiro propuesto. Patrimonio proyectado al Q3 2025: $42.5M";
  } else if (status === "sana") {
    message = `Retiro seguro de $${amount.toLocaleString()}. Caja remanente: $${cashWithWithdrawal.toLocaleString()}.`;
  } else if (status === "vigilancia") {
    message = `Retiro moderado de $${amount.toLocaleString()}. Requiere revisión de obligaciones Q3.`;
  } else {
    message = `Retiro agresivo de $${amount.toLocaleString()}. Impacto crítico en cobertura de operación.`;
  }

  return {
    cashWithoutWithdrawal,
    cashWithWithdrawal,
    status,
    message,
  };
}

// === Health Status Derivation ===

/**
 * Deriva el estado de salud (sana/vigilancia/alerta) basado en un ratio.
 * Usado en múltiples contextos: liquidez, solvencia, etc.
 *
 * @param ratio Valor entre 0 y 1
 * @param thresholdWarning Ratio para estado "vigilancia" (default 0.15)
 * @param thresholdCritical Ratio para estado "alerta" (default 0.3)
 */
export function deriveHealthStatus(
  ratio: number,
  thresholdWarning: number = 0.15,
  thresholdCritical: number = 0.3
): StatusLevel {
  if (ratio > thresholdCritical) return "alerta";
  if (ratio > thresholdWarning) return "vigilancia";
  return "sana";
}

// === Progress Calculations ===

/**
 * Calcula el porcentaje de progreso hacia una meta.
 * @param current Valor actual
 * @param goal Valor meta
 * @returns Porcentaje (0-100)
 */
export function calculateProgressPercentage(current: number, goal: number): number {
  if (goal === 0) return 0;
  return Math.min(100, (current / goal) * 100);
}

/**
 * Calcula si el progreso actual está en zona "sana" o requiere atención.
 * Usado para provision de impuestos, shields, etc.
 */
export function evaluateProgressStatus(percentage: number): StatusLevel {
  if (percentage < 50) return "alerta";
  if (percentage < 80) return "vigilancia";
  return "sana";
}

// === Formatting Helpers ===

/**
 * Nota: formatCop ya existe en lib/format.ts, así que aquí solo importamos si es necesario.
 * Los cálculos retornan números, el formateo se hace en el componente.
 */

/**
 * Formatea un número como porcentaje.
 */
export function formatPercentage(value: number, decimals: number = 1): string {
  return `${value.toFixed(decimals)}%`;
}
