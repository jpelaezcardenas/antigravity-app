"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { paso5Schema } from "@/lib/validations";
import { useWizardStore } from "@/lib/store";
import StepWrapper from "../StepWrapper";
import { z } from "zod";

// Use the inferred type directly from the schema to avoid resolver mismatch
type Step5Form = z.infer<typeof paso5Schema>;

interface Props { onNext: () => void; onBack: () => void; }

export default function Step5Contable({ onNext, onBack }: Props) {
  const { paso5, setPaso5 } = useWizardStore();

  const { register, handleSubmit, watch, formState: { errors } } = useForm<Step5Form>({
    resolver: zodResolver(paso5Schema),
    defaultValues: {
      tiene_contador: false,
      maneja_inventarios: false,
      facturacion_electronica: "no",
      regimen_preferido: "analisis",
      registros_actuales: "excel",
      ...paso5,
    } as Step5Form,
  });

  const tieneContador = watch("tiene_contador");
  const onSubmit = (data: Step5Form) => { setPaso5(data as any); onNext(); };

  const RadioGroup = ({ name, options }: { name: any; options: { val: string; label: string }[] }) => (
    <div style={{ display: "flex", gap: "1.25rem", marginTop: "0.5rem", flexWrap: "wrap" }}>
      {options.map(({ val, label }) => (
        <label key={val} style={{ display: "flex", alignItems: "center", gap: "0.625rem", cursor: "pointer", color: "white", fontSize: "0.9375rem" }}>
          <input type="radio" value={val} {...register(name, { setValueAs: (v) => (v === "true" ? true : v === "false" ? false : v) })} style={{ accentColor: "var(--ctx-teal)" }} />
          {label}
        </label>
      ))}
    </div>
  );

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <StepWrapper step={5} headline="Cómo manejas hoy tu contabilidad" onNext={handleSubmit(onSubmit)} onBack={onBack}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
          {/* Tiene contador */}
          <div style={{ gridColumn: "1 / -1" }}>
            <label className="ctx-label">¿Tienes contador actual? *</label>
            <RadioGroup name="tiene_contador" options={[
              { val: "true", label: "Sí, tengo contador" },
              { val: "false", label: "No tengo contador" },
            ]} />
          </div>

          {tieneContador && (
            <>
              <div>
                <label className="ctx-label">Nombre del contador</label>
                <input className="ctx-input" placeholder="Nombre completo" {...register("nombre_contador")} />
              </div>
              <div>
                <label className="ctx-label">Email del contador</label>
                <input type="email" className="ctx-input" placeholder="contador@firma.com" {...register("email_contador")} />
                <span className="ctx-label-hint">Para coordinar el handoff de información</span>
              </div>
            </>
          )}

          {/* Inventarios */}
          <div>
            <label className="ctx-label">¿Manejas inventarios físicos? *</label>
            <RadioGroup name="maneja_inventarios" options={[
              { val: "true", label: "Sí" },
              { val: "false", label: "No" },
            ]} />
          </div>

          {/* Facturación electrónica */}
          <div>
            <label className="ctx-label">¿Tienes facturación electrónica habilitada con DIAN? *</label>
            <RadioGroup name="facturacion_electronica" options={[
              { val: "si", label: "Sí ✅" },
              { val: "no", label: "No ❌" },
              { val: "no_se", label: "No sé 🤷" },
            ]} />
            {errors.facturacion_electronica && <p className="ctx-error-msg">{errors.facturacion_electronica.message}</p>}
          </div>

          {/* Régimen preferido */}
          <div style={{ gridColumn: "1 / -1" }}>
            <label className="ctx-label">Régimen tributario preferido</label>
            <span className="ctx-label-hint">Si no estás seguro, selecciona "Análisis" y te recomendaremos el mejor</span>
            <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", marginTop: "0.5rem" }}>
              {[
                { val: "simple", label: "🟢 Régimen Simple" },
                { val: "ordinario", label: "🔵 Régimen Ordinario" },
                { val: "analisis", label: "🔍 Quiero el análisis" },
              ].map(({ val, label }) => {
                return (
                  <label key={val} style={{
                    display: "flex", alignItems: "center", gap: "0.625rem", cursor: "pointer",
                    padding: "0.625rem 1rem", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.1)",
                    fontSize: "0.875rem", background: "rgba(255,255,255,0.03)", color: "white",
                  }}>
                    <input type="radio" value={val} {...register("regimen_preferido")} style={{ accentColor: "var(--ctx-teal)" }} />
                    {label}
                  </label>
                );
              })}
            </div>
          </div>

          {/* Registros actuales */}
          <div style={{ gridColumn: "1 / -1" }}>
            <label className="ctx-label">¿Cómo llevas tus registros hoy? *</label>
            <select className={`ctx-input ${errors.registros_actuales ? "error" : ""}`} {...register("registros_actuales")}>
              <option value="">Selecciona</option>
              <option value="manual">📝 Manual (papel)</option>
              <option value="excel">📊 Excel</option>
              <option value="software">💻 Software contable (Siigo, Alegra, Helisa...)</option>
              <option value="ninguno">❌ No llevo registros</option>
            </select>
            {errors.registros_actuales && <p className="ctx-error-msg">{errors.registros_actuales.message}</p>}
          </div>
        </div>
      </StepWrapper>
    </form>
  );
}
