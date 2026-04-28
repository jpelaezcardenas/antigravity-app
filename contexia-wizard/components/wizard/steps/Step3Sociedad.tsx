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
    defaultValues: {
      num_socios: 1,
      socios: [{ nombre: "", cedula: "", participacion: 100, rol: "Accionista" }],
      representante_legal: "",
      capital_suscrito: 20000000,
      aportes_en_especie: false,
      ...paso3,
    } as Paso3Data,
  });

  const { fields, append, remove } = useFieldArray({ control, name: "socios" });
  const aportesEspecie = watch("aportes_en_especie");

  const onSubmit = (data: Paso3Data) => {
    const finalData = { ...data, num_socios: data.socios.length };
    setPaso3(finalData);
    onNext();
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <StepWrapper step={3} headline="Quiénes son los socios" onNext={handleSubmit(onSubmit)} onBack={onBack}>
        <div style={{ marginBottom: "1.5rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
            <label className="ctx-label" style={{ margin: 0 }}>Socios / accionistas *</label>
            <button
              type="button"
              onClick={() => append({ nombre: "", cedula: "", participacion: 0, rol: "Socio" })}
              className="ctx-btn-secondary"
              style={{ padding: "0.5rem 1rem", fontSize: "0.875rem", gap: "0.375rem" }}
            >
              <Plus size={14} /> Agregar socio
            </button>
          </div>

          {fields.map((field, idx) => (
            <div key={field.id} style={{ background: "rgba(255, 255, 255, 0.03)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "12px", padding: "1.25rem", marginBottom: "0.75rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "1rem" }}>
                <span style={{ fontWeight: 700, fontSize: "0.875rem", color: "white" }}>Socio {idx + 1}</span>
                {idx > 0 && (
                  <button type="button" onClick={() => remove(idx)} style={{ background: "none", border: "none", color: "#ef4444", cursor: "pointer", opacity: 0.8 }}>
                    <Trash2 size={16} />
                  </button>
                )}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: "0.75rem" }}>
                <div>
                  <label className="ctx-label" style={{ fontSize: "0.8125rem" }}>Nombre</label>
                  <input className={`ctx-input ${errors.socios?.[idx]?.nombre ? "error" : ""}`} {...register(`socios.${idx}.nombre`)} placeholder="Nombre" />
                  {errors.socios?.[idx]?.nombre && <p className="ctx-error-msg">Min 2</p>}
                </div>
                <div>
                  <label className="ctx-label" style={{ fontSize: "0.8125rem" }}>Cédula</label>
                  <input className={`ctx-input ${errors.socios?.[idx]?.cedula ? "error" : ""}`} {...register(`socios.${idx}.cedula`)} placeholder="Cédula" />
                  {errors.socios?.[idx]?.cedula && <p className="ctx-error-msg">8-10 dig</p>}
                </div>
                <div>
                  <label className="ctx-label" style={{ fontSize: "0.8125rem" }}>%</label>
                  <input type="number" min={0} max={100} className={`ctx-input ${errors.socios?.[idx]?.participacion ? "error" : ""}`} {...register(`socios.${idx}.participacion`, { valueAsNumber: true })} />
                </div>
                <div>
                  <label className="ctx-label" style={{ fontSize: "0.8125rem" }}>Rol</label>
                  <input className={`ctx-input ${errors.socios?.[idx]?.rol ? "error" : ""}`} {...register(`socios.${idx}.rol`)} placeholder="Rol" />
                </div>
              </div>
            </div>
          ))}
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.25rem" }}>
          <div style={{ gridColumn: "1 / -1" }}>
            <label className="ctx-label">Representante legal *</label>
            <input className={`ctx-input ${errors.representante_legal ? "error" : ""}`} placeholder="Nombre del representante" {...register("representante_legal")} />
            {errors.representante_legal && <p className="ctx-error-msg">{errors.representante_legal.message}</p>}
          </div>

          <div>
            <label className="ctx-label">Capital suscrito (COP) *</label>
            <input type="number" className="ctx-input" placeholder="20000000" {...register("capital_suscrito", { valueAsNumber: true })} />
            <span className="ctx-label-hint">Sugerido: $20M</span>
          </div>

          <div>
            <label className="ctx-label">¿Aportes en especie?</label>
            <div style={{ display: "flex", gap: "1.5rem", marginTop: "0.5rem" }}>
              {[{ val: true, label: "Sí" }, { val: false, label: "No" }].map(({ val, label }) => (
                <label key={label} style={{ display: "flex", alignItems: "center", gap: "0.625rem", cursor: "pointer", color: "white", fontSize: "0.9375rem" }}>
                  <input type="radio" value={String(val)} {...register("aportes_en_especie", { setValueAs: v => v === "true" })} 
                    style={{ accentColor: "var(--ctx-teal)" }}
                  />
                  {label}
                </label>
              ))}
            </div>
          </div>

          {aportesEspecie && (
            <div style={{ gridColumn: "1 / -1" }}>
              <label className="ctx-label">Descripción aportes</label>
              <textarea
                className="ctx-input"
                rows={3}
                placeholder="Ej. Equipos..."
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
