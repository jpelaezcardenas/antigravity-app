"use client";
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { paso3Schema, type Paso3Data } from "@/lib/validations";
import { useWizardStore } from "@/lib/store";
import StepWrapper from "../StepWrapper";
import { Plus, Trash2 } from "lucide-react";

interface Props { onNext: () => void; onBack: () => void; }

export default function Step3Sociedad({ onNext, onBack }: Props) {
  const { paso3, setPaso3 } = useWizardStore();

  const { register, handleSubmit, watch, control, formState: { errors } } = useForm<Paso3Data>({
    resolver: zodResolver(paso3Schema),
    defaultValues: paso3 as Paso3Data || {
      num_socios: 1,
      socios: [{ nombre: "", cedula: "", participacion: 100, rol: "Accionista" }],
      capital_suscrito: 20000000,
      aportes_en_especie: false,
    },
  });

  const { fields, append, remove } = useFieldArray({ control, name: "socios" });
  const aportesEspecie = watch("aportes_en_especie");

  const onSubmit = (data: Paso3Data) => { setPaso3(data); onNext(); };

  const formatCOP = (v: number) =>
    new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(v);

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <StepWrapper step={3} headline="Quiénes son los socios" onNext={handleSubmit(onSubmit)} onBack={onBack}>
        {/* Socios dinámicos */}
        <div style={{ marginBottom: "1.5rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
            <label className="ctx-label" style={{ margin: 0 }}>Socios / accionistas *</label>
            <button
              type="button"
              onClick={() => append({ nombre: "", cedula: "", participacion: 0, rol: "Socio" })}
              style={{ display: "flex", alignItems: "center", gap: "0.375rem", background: "#e8f7f3", color: "#00a878", border: "none", borderRadius: "8px", padding: "0.5rem 0.875rem", cursor: "pointer", fontWeight: 600, fontSize: "0.875rem" }}
            >
              <Plus size={14} /> Agregar socio
            </button>
          </div>

          {fields.map((field, idx) => (
            <div key={field.id} style={{ background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "10px", padding: "1rem", marginBottom: "0.75rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.75rem" }}>
                <span style={{ fontWeight: 600, fontSize: "0.875rem", color: "#0a2540" }}>Socio {idx + 1}</span>
                {idx > 0 && (
                  <button type="button" onClick={() => remove(idx)} style={{ background: "none", border: "none", color: "#dc2626", cursor: "pointer" }}>
                    <Trash2 size={16} />
                  </button>
                )}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: "0.75rem" }}>
                <div>
                  <label className="ctx-label" style={{ fontSize: "0.8125rem" }}>Nombre</label>
                  <input className="ctx-input" {...register(`socios.${idx}.nombre`)} placeholder="Nombre completo" />
                </div>
                <div>
                  <label className="ctx-label" style={{ fontSize: "0.8125rem" }}>Cédula</label>
                  <input className="ctx-input" {...register(`socios.${idx}.cedula`)} placeholder="Cédula" />
                </div>
                <div>
                  <label className="ctx-label" style={{ fontSize: "0.8125rem" }}>Participación %</label>
                  <input type="number" min={0} max={100} className="ctx-input" {...register(`socios.${idx}.participacion`, { valueAsNumber: true })} />
                </div>
                <div>
                  <label className="ctx-label" style={{ fontSize: "0.8125rem" }}>Rol</label>
                  <input className="ctx-input" {...register(`socios.${idx}.rol`)} placeholder="Gerente, Socio..." />
                </div>
              </div>
            </div>
          ))}
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.25rem" }}>
          {/* Representante legal */}
          <div style={{ gridColumn: "1 / -1" }}>
            <label className="ctx-label">Representante legal *</label>
            <input className={`ctx-input ${errors.representante_legal ? "error" : ""}`} placeholder="Nombre del representante" {...register("representante_legal")} />
            {errors.representante_legal && <p className="ctx-error-msg">{errors.representante_legal.message}</p>}
          </div>

          {/* Capital */}
          <div>
            <label className="ctx-label">Capital suscrito y pagado (COP) *</label>
            <input type="number" className="ctx-input" placeholder="20000000" {...register("capital_suscrito", { valueAsNumber: true })} />
            <span className="ctx-label-hint">Sugerido: $20.000.000 (protección mínima)</span>
          </div>

          {/* Aportes en especie */}
          <div>
            <label className="ctx-label">¿Aportes en especie?</label>
            <div style={{ display: "flex", gap: "1rem", marginTop: "0.5rem" }}>
              {[{ val: true, label: "Sí" }, { val: false, label: "No" }].map(({ val, label }) => (
                <label key={label} style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer" }}>
                  <input type="radio" value={String(val)} {...register("aportes_en_especie", { setValueAs: v => v === "true" })} />
                  {label}
                </label>
              ))}
            </div>
          </div>

          {aportesEspecie && (
            <div style={{ gridColumn: "1 / -1" }}>
              <label className="ctx-label">Descripción de los aportes en especie</label>
              <textarea
                className="ctx-input"
                rows={3}
                placeholder="Ej. Equipos de producción, inventario, dominio web..."
                {...register("descripcion_aportes")}
                style={{ resize: "vertical" }}
              />
            </div>
          )}
        </div>
      </StepWrapper>
    </form>
  );
}
