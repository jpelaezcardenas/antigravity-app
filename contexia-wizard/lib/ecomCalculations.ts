// ============================================================
// lib/ecomCalculations.ts
// Client-side math for the 3-step express IVA diagnostic
// (wizard-iva-ecom-express-diagnostic, design.md D2/D4/D5).
// ============================================================
import { UVT_2026 } from "./calculations";

export const IVA_RATE = 0.19;

// `UVT_2026` (lib/calculations.ts) was mislabeled with the 2025 value
// ($49.799 instead of $52.374) until 2026-09-20 -- fixed at the source
// (see that file's header comment) after being caught during this change's
// founder review, cross-checked against the Contexia Knowledge Vault
// (DIAN normograma). Now safe to import directly instead of duplicating.

// Umbral de responsabilidad de IVA (Art. 437 ET) — distinto del umbral de
// 1.400 UVT para declarante de renta que ya usa el backend de
// antigravity-app (pricing_catalog.py). No mezclar los dos: este número
// responde "¿debo cobrar IVA?", no "¿debo declarar renta?".
export const UMBRAL_RESPONSABLE_IVA_UVT = 3500;

export type Tier = 1 | 2 | 3;

/**
 * Estimated monthly IVA that could be reclaimed on Meta Ads spend,
 * IF the business is IVA-responsible and isn't currently claiming it.
 * A flat-rate estimate, never presented as an unconditional fact
 * (design.md D4) — the disclosure lives in the UI copy, not here.
 */
export function calcularIvaPerdidoMensual(gastoMetaAdsMensual: number): number {
  if (!Number.isFinite(gastoMetaAdsMensual) || gastoMetaAdsMensual <= 0) return 0;
  return gastoMetaAdsMensual * IVA_RATE;
}

/**
 * Whether projected annual revenue exceeds the IVA-responsibility
 * threshold (3.500 UVT), using the same UVT_2026 constant the 8-step
 * flow already relies on.
 */
export function excedeUmbralResponsableIVA(ventasMensuales: number): boolean {
  if (!Number.isFinite(ventasMensuales) || ventasMensuales <= 0) return false;
  const ventasAnualesProyectadas = ventasMensuales * 12;
  return ventasAnualesProyectadas > UMBRAL_RESPONSABLE_IVA_UVT * UVT_2026;
}

/**
 * Frontend-only tier for CTA tone/urgency (design.md D5) — never persisted
 * as a CRM field, only shapes which WhatsApp message the button pre-fills.
 * Tier 1: high estimated loss AND over the IVA-responsibility threshold.
 * Tier 2: over the threshold, or a meaningful loss, but not both.
 * Tier 3: everything else (small spend, under threshold).
 */
export function calcularTier(
  ventasMensuales: number,
  gastoMetaAdsMensual: number
): Tier {
  const ivaPerdido = calcularIvaPerdidoMensual(gastoMetaAdsMensual);
  const excedeUmbral = excedeUmbralResponsableIVA(ventasMensuales);

  if (excedeUmbral && ivaPerdido >= 500_000) return 1;
  if (excedeUmbral || ivaPerdido >= 200_000) return 2;
  return 3;
}
