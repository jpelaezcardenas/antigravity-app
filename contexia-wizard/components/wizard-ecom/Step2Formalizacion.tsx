"use client";
import { useState } from "react";
import { useEcomStore, type TipoPersona } from "@/lib/ecomStore";
import EcomStepWrapper from "./EcomStepWrapper";

interface Props {
  onNext: () => void;
  onBack: () => void;
}

export default function Step2Formalizacion({ onNext, onBack }: Props) {
  const { formalizacion, setFormalizacion } = useEcomStore();
  const [tipoPersona, setTipoPersona] = useState<TipoPersona | undefined>(
    formalizacion.tipoPersona
  );
  const [facturaElectronicamente, setFacturaElectronicamente] = useState<
    boolean | undefined
  >(formalizacion.facturaElectronicamente);

  const isValid = tipoPersona !== undefined && facturaElectronicamente !== undefined;

  const handleNext = () => {
    if (!isValid) return;
    setFormalizacion({ tipoPersona, facturaElectronicamente });
    onNext();
  };

  return (
    <EcomStepWrapper
      step={2}
      headline="¿Cómo estás formalizado?"
      subheadline="Esto cambia si aplicas para reclamar el IVA."
      onNext={handleNext}
      onBack={onBack}
      nextDisabled={!isValid}
    >
      <div style={{ display: "grid", gap: "1.5rem" }}>
        <div>
          <label className="ctx-label">¿Persona Natural o SAS? *</label>
          <div style={{ display: "flex", gap: "0.75rem", marginTop: "0.5rem" }}>
            {(
              [
                { value: "persona_natural", label: "Persona Natural" },
                { value: "sas", label: "SAS" },
              ] as const
            ).map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setTipoPersona(opt.value)}
                className={tipoPersona === opt.value ? "ctx-btn-primary" : "ctx-btn-secondary"}
                style={{ flex: 1 }}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="ctx-label">¿Facturas electrónicamente? *</label>
          <div style={{ display: "flex", gap: "0.75rem", marginTop: "0.5rem" }}>
            {(
              [
                { value: true, label: "Sí" },
                { value: false, label: "No" },
              ] as const
            ).map((opt) => (
              <button
                key={String(opt.value)}
                type="button"
                onClick={() => setFacturaElectronicamente(opt.value)}
                className={
                  facturaElectronicamente === opt.value ? "ctx-btn-primary" : "ctx-btn-secondary"
                }
                style={{ flex: 1 }}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </EcomStepWrapper>
  );
}
