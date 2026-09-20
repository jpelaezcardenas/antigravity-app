"use client";
import { useState } from "react";
import { useEcomStore } from "@/lib/ecomStore";
import EcomStepWrapper from "./EcomStepWrapper";

interface Props {
  onNext: () => void;
}

export default function Step1Numeros({ onNext }: Props) {
  const { numeros, setNumeros } = useEcomStore();
  const [ventasMensuales, setVentasMensuales] = useState(
    numeros.ventasMensuales?.toString() ?? ""
  );
  const [gastoMetaAds, setGastoMetaAds] = useState(
    numeros.gastoMetaAds?.toString() ?? ""
  );
  const [margenBruto, setMargenBruto] = useState(
    numeros.margenBruto?.toString() ?? ""
  );

  const parsed = {
    ventasMensuales: Number(ventasMensuales),
    gastoMetaAds: Number(gastoMetaAds),
    margenBruto: Number(margenBruto),
  };

  const isValid =
    ventasMensuales !== "" &&
    gastoMetaAds !== "" &&
    margenBruto !== "" &&
    parsed.ventasMensuales > 0 &&
    parsed.gastoMetaAds > 0 &&
    parsed.margenBruto > 0;

  const handleNext = () => {
    if (!isValid) return;
    setNumeros(parsed);
    onNext();
  };

  return (
    <EcomStepWrapper
      step={1}
      headline="Empecemos por tus números"
      subheadline="30 segundos. Solo necesitamos 3 datos para calcular tu diagnóstico."
      onNext={handleNext}
      nextDisabled={!isValid}
    >
      <div style={{ display: "grid", gap: "1.25rem" }}>
        <div>
          <label className="ctx-label">Ventas mensuales (COP) *</label>
          <input
            type="number"
            inputMode="numeric"
            min={0}
            className="ctx-input"
            placeholder="Ej. 15000000"
            value={ventasMensuales}
            onChange={(e) => setVentasMensuales(e.target.value)}
          />
        </div>

        <div>
          <label className="ctx-label">Gasto mensual en Meta Ads (COP) *</label>
          <input
            type="number"
            inputMode="numeric"
            min={0}
            className="ctx-input"
            placeholder="Ej. 2000000"
            value={gastoMetaAds}
            onChange={(e) => setGastoMetaAds(e.target.value)}
          />
        </div>

        <div>
          <label className="ctx-label">Margen bruto aproximado (%) *</label>
          <input
            type="number"
            inputMode="numeric"
            min={0}
            max={100}
            className="ctx-input"
            placeholder="Ej. 35"
            value={margenBruto}
            onChange={(e) => setMargenBruto(e.target.value)}
          />
        </div>
      </div>
    </EcomStepWrapper>
  );
}
