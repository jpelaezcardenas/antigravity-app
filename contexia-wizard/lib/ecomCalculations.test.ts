import {
  calcularIvaPerdidoMensual,
  excedeUmbralResponsableIVA,
  calcularTier,
  UMBRAL_RESPONSABLE_IVA_UVT,
  IVA_RATE,
} from "./ecomCalculations";
import { UVT_2026 } from "./calculations";

describe("calcularIvaPerdidoMensual", () => {
  it("returns 19% of the monthly Meta Ads spend", () => {
    expect(calcularIvaPerdidoMensual(1_000_000)).toBe(1_000_000 * IVA_RATE);
  });

  it("returns 0 for zero or negative spend", () => {
    expect(calcularIvaPerdidoMensual(0)).toBe(0);
    expect(calcularIvaPerdidoMensual(-500)).toBe(0);
  });

  it("returns 0 for non-finite input", () => {
    expect(calcularIvaPerdidoMensual(NaN)).toBe(0);
  });
});

describe("excedeUmbralResponsableIVA", () => {
  const umbralAnual = UMBRAL_RESPONSABLE_IVA_UVT * UVT_2026;

  it("is false when annualized revenue is under the 3,500 UVT threshold", () => {
    const ventasMensuales = umbralAnual / 12 - 1000;
    expect(excedeUmbralResponsableIVA(ventasMensuales)).toBe(false);
  });

  it("is true when annualized revenue exceeds the 3,500 UVT threshold", () => {
    const ventasMensuales = umbralAnual / 12 + 1000;
    expect(excedeUmbralResponsableIVA(ventasMensuales)).toBe(true);
  });

  it("is false for zero or negative revenue", () => {
    expect(excedeUmbralResponsableIVA(0)).toBe(false);
    expect(excedeUmbralResponsableIVA(-100)).toBe(false);
  });
});

describe("calcularTier", () => {
  const umbralAnual = UMBRAL_RESPONSABLE_IVA_UVT * UVT_2026;
  const ventasBajoUmbral = umbralAnual / 12 - 1000;
  const ventasSobreUmbral = umbralAnual / 12 + 1000;

  it("assigns tier 1 when over the threshold with high estimated loss", () => {
    expect(calcularTier(ventasSobreUmbral, 3_000_000)).toBe(1);
  });

  it("assigns tier 2 when over the threshold but loss is moderate", () => {
    expect(calcularTier(ventasSobreUmbral, 100_000)).toBe(2);
  });

  it("assigns tier 2 when under the threshold but loss is meaningful", () => {
    expect(calcularTier(ventasBajoUmbral, 1_500_000)).toBe(2);
  });

  it("assigns tier 3 for small spend under the threshold", () => {
    expect(calcularTier(ventasBajoUmbral, 50_000)).toBe(3);
  });
});
