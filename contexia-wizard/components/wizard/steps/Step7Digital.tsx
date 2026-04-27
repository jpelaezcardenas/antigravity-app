"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { paso7Schema, type Paso7Data } from "@/lib/validations";
import { useWizardStore } from "@/lib/store";
import StepWrapper from "../StepWrapper";

const REDES = ["Instagram", "Facebook", "TikTok", "YouTube", "LinkedIn", "X / Twitter"];

interface Props { onNext: () => void; onBack: () => void; }

export default function Step7Digital({ onNext, onBack }: Props) {
  const { paso7, setPaso7 } = useWizardStore();

  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<Paso7Data>({
    resolver: zodResolver(paso7Schema),
    defaultValues: { ...paso7, redes_sociales: paso7?.redes_sociales || [] } as Paso7Data,
  });

  const tieneEcommerce = watch("tiene_ecommerce");
  const redesActivas = watch("redes_sociales") || [];

  const toggleRed = (red: string) => {
    if (redesActivas.includes(red)) {
      setValue("redes_sociales", redesActivas.filter((r) => r !== red));
    } else {
      setValue("redes_sociales", [...redesActivas, red]);
    }
  };

  const onSubmit = (data: Paso7Data) => { setPaso7(data); onNext(); };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <StepWrapper step={7} headline="Tu presencia digital"
        subheadline="Estas plataformas pueden ser activos fiscales deducibles."
        onNext={handleSubmit(onSubmit)} onBack={onBack} nextLabel="Ir al Diagnóstico 🔍">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
          {/* E-commerce */}
          <div style={{ gridColumn: "1 / -1" }}>
            <label className="ctx-label">¿Tienes tienda en línea / e-commerce?</label>
            <div style={{ display: "flex", gap: "1rem", marginTop: "0.5rem" }}>
              {[{ val: "true", label: "Sí 🛒" }, { val: "false", label: "No" }].map(({ val, label }) => (
                <label key={val} style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer" }}>
                  <input type="radio" value={val}
                    {...register("tiene_ecommerce", { setValueAs: v => v === "true" })} />
                  {label}
                </label>
              ))}
            </div>
          </div>

          {tieneEcommerce && (
            <div>
              <label className="ctx-label">Plataforma de e-commerce</label>
              <input className="ctx-input" placeholder="Shopify, WooCommerce, Vtex..." {...register("plataforma_ecommerce")} />
            </div>
          )}

          {/* Software contable */}
          <div>
            <label className="ctx-label">Software contable usado <span style={{ color: "#94a3b8", fontWeight: 400 }}>(opcional)</span></label>
            <input className="ctx-input" placeholder="Siigo, Alegra, Helisa, Excel..." {...register("software_contable")} />
          </div>

          {/* Dominio */}
          <div>
            <label className="ctx-label">Dominio web <span style={{ color: "#94a3b8", fontWeight: 400 }}>(opcional)</span></label>
            <input className="ctx-input" placeholder="tuempresa.com" {...register("dominio_web")} />
          </div>

          {/* Redes sociales */}
          <div style={{ gridColumn: "1 / -1" }}>
            <label className="ctx-label">Redes sociales activas</label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginTop: "0.5rem" }}>
              {REDES.map((red) => {
                const selected = redesActivas.includes(red);
                return (
                  <button key={red} type="button" onClick={() => toggleRed(red)}
                    style={{
                      padding: "0.375rem 0.875rem", borderRadius: "999px",
                      border: `1.5px solid ${selected ? "#00a878" : "#e2e8f0"}`,
                      background: selected ? "#e8f7f3" : "#fff",
                      color: selected ? "#00a878" : "#64748b",
                      fontWeight: selected ? 600 : 400,
                      fontSize: "0.875rem", cursor: "pointer",
                    }}
                  >{red}</button>
                );
              })}
            </div>
          </div>
        </div>
      </StepWrapper>
    </form>
  );
}
