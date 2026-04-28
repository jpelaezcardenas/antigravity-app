"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { paso6Schema } from "@/lib/validations";
import { useWizardStore } from "@/lib/store";
import StepWrapper from "../StepWrapper";
import { z } from "zod";

type Step6Form = z.infer<typeof paso6Schema>;

const VINCULACION_TIPOS = [
  "Contrato indefinido", "Término fijo", "Prestación de servicios", "Aprendices SENA",
];

interface Props { onNext: () => void; onBack: () => void; }

export default function Step6Administrativa({ onNext, onBack }: Props) {
  const { paso6, setPaso6, paso2 } = useWizardStore();
  const isManufactura = paso2?.ciiu_principal === "1090" || paso2?.ciiu_principal === "5611";

  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<Step6Form>({
    resolver: zodResolver(paso6Schema),
    defaultValues: {
      empleados: 0,
      tipos_vinculacion: [],
      salario_promedio: 0,
      requiere_nomina: false,
      contratos_proveedores: false,
      tiene_bpa: false,
      ...paso6,
    } as Step6Form,
  });

  const tiposVinculacion = (watch("tipos_vinculacion") || []) as string[];

  const toggleTipo = (tipo: string) => {
    if (tiposVinculacion.includes(tipo)) {
      setValue("tipos_vinculacion", tiposVinculacion.filter((t) => t !== tipo));
    } else {
      setValue("tipos_vinculacion", [...tiposVinculacion, tipo]);
    }
  };

  const onSubmit = (data: Step6Form) => { setPaso6(data as any); onNext(); };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <StepWrapper step={6} headline="Tu equipo y operaciones" onNext={handleSubmit(onSubmit)} onBack={onBack}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
          {/* Empleados */}
          <div>
            <label className="ctx-label">Empleados directos</label>
            <input type="number" min={0} className="ctx-input"
              {...register("empleados", { valueAsNumber: true })} placeholder="0" />
          </div>

          {/* Salario promedio */}
          <div>
            <label className="ctx-label">Salario promedio mensual (COP)</label>
            <input type="number" className="ctx-input" placeholder="Ej. 1500000"
              {...register("salario_promedio", { valueAsNumber: true })} />
          </div>

          {/* Tipos de vinculación */}
          <div style={{ gridColumn: "1 / -1" }}>
            <label className="ctx-label">Tipos de vinculación laboral</label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.625rem", marginTop: "0.5rem" }}>
              {VINCULACION_TIPOS.map((tipo) => {
                const selected = tiposVinculacion.includes(tipo);
                return (
                  <button key={tipo} type="button" onClick={() => toggleTipo(tipo)}
                    style={{
                      padding: "0.5rem 1rem", borderRadius: "999px",
                      border: `1px solid ${selected ? "var(--ctx-teal)" : "rgba(255,255,255,0.1)"}`,
                      background: selected ? "rgba(45, 212, 191, 0.1)" : "rgba(255,255,255,0.03)",
                      color: selected ? "var(--ctx-teal)" : "var(--ctx-text-muted)",
                      fontWeight: selected ? 700 : 500,
                      fontSize: "0.8125rem", cursor: "pointer", transition: "all 0.2s",
                    }}
                  >{tipo}</button>
                );
              })}
            </div>
          </div>

          {/* Nómina formal */}
          <div>
            <label className="ctx-label">¿Requieres nómina formal con prestaciones?</label>
            <div style={{ display: "flex", gap: "1.5rem", marginTop: "0.5rem" }}>
              {[{ val: "true", label: "Sí" }, { val: "false", label: "No" }].map(({ val, label }) => (
                <label key={val} style={{ display: "flex", alignItems: "center", gap: "0.625rem", cursor: "pointer", color: "white", fontSize: "0.9375rem" }}>
                  <input type="radio" value={val} {...register("requiere_nomina", { setValueAs: v => v === "true" })} 
                    style={{ accentColor: "var(--ctx-teal)" }}
                  />
                  {label}
                </label>
              ))}
            </div>
          </div>

          {/* Contratos proveedores */}
          <div>
            <label className="ctx-label">¿Tienes contratos formales con proveedores clave?</label>
            <div style={{ display: "flex", gap: "1.5rem", marginTop: "0.5rem" }}>
              {[{ val: "true", label: "Sí" }, { val: "false", label: "No" }].map(({ val, label }) => (
                <label key={val} style={{ display: "flex", alignItems: "center", gap: "0.625rem", cursor: "pointer", color: "white", fontSize: "0.9375rem" }}>
                  <input type="radio" value={val} {...register("contratos_proveedores", { setValueAs: v => v === "true" })} 
                    style={{ accentColor: "var(--ctx-teal)" }}
                  />
                  {label}
                </label>
              ))}
            </div>
          </div>

          {/* BPA — solo si es manufactura/alimentos */}
          {isManufactura && (
            <div style={{ gridColumn: "1 / -1", background: "rgba(217, 119, 6, 0.05)", border: "1px solid rgba(217, 119, 6, 0.2)", borderRadius: "12px", padding: "1.25rem" }}>
              <label className="ctx-label" style={{ color: "#fbbf24" }}>¿Tienes Buenas Prácticas (BPA/BPM) implementadas?</label>
              <span className="ctx-label-hint">Importante para el proceso de registro ICA/sanitario</span>
              <div style={{ display: "flex", gap: "1.5rem", marginTop: "0.5rem" }}>
                {[{ val: "true", label: "Sí ✅" }, { val: "false", label: "No ❌" }].map(({ val, label }) => (
                  <label key={val} style={{ display: "flex", alignItems: "center", gap: "0.625rem", cursor: "pointer", color: "white", fontSize: "0.9375rem" }}>
                    <input type="radio" value={val} {...register("tiene_bpa", { setValueAs: v => v === "true" })} 
                      style={{ accentColor: "var(--ctx-teal)" }}
                    />
                    {label}
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>
      </StepWrapper>
    </form>
  );
}
