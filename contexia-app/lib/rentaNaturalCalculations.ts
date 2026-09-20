/**
 * Client-side "¿debo declarar renta?" mini-diagnostic for the public
 * /renta-natural landing. Mirrors DIAN's real quantitative criteria
 * (Art. 592 E.T.) so a visitor gets an instant, disclosed ESTIMATE
 * without leaving the page — the official DIAN tool
 * (consultarenta.dian.gov.co) is offered alongside as the authoritative
 * source, never replaced, since this quiz cannot see the visitor's real
 * tax records.
 *
 * UVT 2026 = $52.374 (Resolución DIAN 000238 de 2025) — verified against
 * the Contexia Knowledge Vault's DIAN-sourced figures during
 * wizard-iva-ecom-express-diagnostic. Two of DIAN's five criteria are
 * asked here (ingresos brutos, patrimonio bruto, consumos/consignaciones)
 * because they are the ones a visitor can self-report without needing
 * real transaction data.
 */

export const UVT_2026 = 52374;

export const UMBRAL_INGRESOS_UVT = 1400;
export const UMBRAL_PATRIMONIO_UVT = 4500;
export const UMBRAL_CONSUMOS_UVT = 1400;

export const UMBRAL_INGRESOS_COP = UMBRAL_INGRESOS_UVT * UVT_2026;
export const UMBRAL_PATRIMONIO_COP = UMBRAL_PATRIMONIO_UVT * UVT_2026;
export const UMBRAL_CONSUMOS_COP = UMBRAL_CONSUMOS_UVT * UVT_2026;

export interface DeclaranteInputs {
  ingresosAnuales: number;
  patrimonioBruto: number;
  superoConsumosOConsignaciones: boolean;
}

export interface DeclaranteResultado {
  probableDeclarante: boolean;
  criteriosSuperados: string[];
}

/**
 * Estimates whether the visitor likely must file Renta Natural, based on
 * whichever of DIAN's quantitative thresholds they exceed. Returns which
 * specific criteria were exceeded so the UI can be transparent about why.
 */
export function estimarDeclarante(inputs: DeclaranteInputs): DeclaranteResultado {
  const criteriosSuperados: string[] = [];

  if (inputs.ingresosAnuales > UMBRAL_INGRESOS_COP) {
    criteriosSuperados.push("ingresos brutos anuales");
  }
  if (inputs.patrimonioBruto > UMBRAL_PATRIMONIO_COP) {
    criteriosSuperados.push("patrimonio bruto");
  }
  if (inputs.superoConsumosOConsignaciones) {
    criteriosSuperados.push("consumos con tarjeta o consignaciones bancarias");
  }

  return {
    probableDeclarante: criteriosSuperados.length > 0,
    criteriosSuperados,
  };
}
