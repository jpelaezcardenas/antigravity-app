"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { paso4Schema, type Paso4Data } from "@/lib/validations";
import { useWizardStore } from "@/lib/store";
import StepWrapper from "../StepWrapper";

const MODELOS = [
  { value: "ecommerce", label: "📦 E-commerce / Ventas online" },
  { value: "manufactura", label: "🏭 Manufactura / Producción" },
  { value: "servicios", label: "💼 Servicios profesionales" },
  { value: "comercio_fisico", label: "🏪 Comercio físico" },
  { value: "mixto", label: "🔀 Mixto (varios canales)" },
];

const MEDIOS_PAGO = [
  "Transferencia bancaria", "Datafono", "Nequi", "Daviplata",
  "PayPal", "Wompi", "Bold", "Mercado Pago", "Contraentrega", "Efectivo",
];

interface Props { onNext: () => void; onBack: () => void; }

export default function Step4Financiera({ onNext, onBack }: Props) {
  const { paso4, setPaso4 } = useWizardStore();

  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<Paso4Data>({
    resolver: zodResolver(paso4Schema),
    defaultValues: { ...paso4, medios_pago: paso4?.medios_pago || [] } as Paso4Data,
  });

  const costosPct = watch("costos_pct") || 50;
  const tienePrevios = watch("tiene_ingresos_previos");
  const haDeclarado = watch("ha_declarado_renta");
  const mediosPago = watch("medios_pago") || [];

  const toggleMedio = (medio: string) => {
    if (mediosPago.includes(medio)) {
      setValue("medios_pago", mediosPago.filter((m) => m !== medio));
    } else {
      setValue("medios_pago", [...mediosPago, medio]);
    }
  };

  const onSubmit = (data: Paso4Data) => { setPaso4(data); onNext(); };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <StepWrapper step={4} headline="Tus números actuales (o proyectados)" onNext={handleSubmit(onSubmit)} onBack={onBack}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.25rem" }}>
          {/* Ingresos mensuales */}
          <div>
            <label className="ctx-label">Ingresos mensuales aproximados (COP) *</label>
            <input type="number" className={`ctx-input ${errors.ingresos_mensuales ? "error" : ""}`}
              placeholder="Ej. 8000000" {...register("ingresos_mensuales", { valueAsNumber: true })} />
            {errors.ingresos_mensuales && <p className="ctx-error-msg">{errors.ingresos_mensuales.message}</p>}
          </div>

          {/* Costos % */}
          <div>
            <label className="ctx-label">Costos + gastos como % de ingresos *</label>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <input
                type="range" min={0} max={100}
                {...register("costos_pct", { valueAsNumber: true })}
                style={{ flex: 1, accentColor: "#00a878" }}
              />
              <span style={{ fontWeight: 700, color: "#0a2540", minWidth: "40px", textAlign: "right" }}>{costosPct}%</span>
            </div>
            {costosPct > 70 && (
              <p style={{ fontSize: "0.8125rem", color: "#d97706", marginTop: "0.375rem" }}>
                ⚠️ Margen muy bajo. Optimización tributaria es clave.
              </p>
            )}
          </div>

          {/* Modelo negocio */}
          <div style={{ gridColumn: "1 / -1" }}>
            <label className="ctx-label">Modelo de negocio *</label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.625rem", marginTop: "0.5rem" }}>
              {MODELOS.map((m) => (
                <label key={m.value} style={{
                  display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer",
                  padding: "0.5rem 0.875rem", borderRadius: "8px", border: "1.5px solid #e2e8f0",
                  fontSize: "0.875rem", background: "#fff", transition: "all 0.15s",
                }}>
                  <input type="radio" value={m.value} {...register("modelo_negocio")} style={{ accentColor: "#00a878" }} />
                  {m.label}
                </label>
              ))}
            </div>
            {errors.modelo_negocio && <p className="ctx-error-msg">{errors.modelo_negocio.message}</p>}
          </div>

          {/* Medios de pago */}
          <div style={{ gridColumn: "1 / -1" }}>
            <label className="ctx-label">Pasarelas / medios de pago activas *</label>
            <span className="ctx-label-hint">Selecciona todos los que usas actualmente</span>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
              {MEDIOS_PAGO.map((m) => {
                const selected = mediosPago.includes(m);
                return (
                  <button key={m} type="button" onClick={() => toggleMedio(m)}
                    style={{
                      padding: "0.375rem 0.75rem", borderRadius: "999px",
                      border: `1.5px solid ${selected ? "#00a878" : "#e2e8f0"}`,
                      background: selected ? "#e8f7f3" : "#fff",
                      color: selected ? "#00a878" : "#64748b",
                      fontWeight: selected ? 600 : 400,
                      fontSize: "0.875rem", cursor: "pointer", transition: "all 0.15s",
                    }}
                  >{m}</button>
                );
              })}
            </div>
            {errors.medios_pago && <p className="ctx-error-msg">{errors.medios_pago.message}</p>}
          </div>

          {/* Ingresos previos */}
          <div>
            <label className="ctx-label">¿Tienes ingresos previos sin formalizar?</label>
            <div style={{ display: "flex", gap: "1rem", marginTop: "0.5rem" }}>
              {[{ val: "true", label: "Sí" }, { val: "false", label: "No" }].map(({ val, label }) => (
                <label key={label} style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer" }}>
                  <input type="radio" value={val} {...register("tiene_ingresos_previos", { setValueAs: v => v === "true" })} />
                  {label}
                </label>
              ))}
            </div>
          </div>

          {tienePrevios && (
            <div>
              <label className="ctx-label">Ingreso anual aprox. del último año</label>
              <input type="number" className="ctx-input" placeholder="Ej. 80000000"
                {...register("ingreso_anual_previo", { valueAsNumber: true })} />
            </div>
          )}

          {/* Ha declarado */}
          <div>
            <label className="ctx-label">¿Has declarado renta como persona natural?</label>
            <div style={{ display: "flex", gap: "1rem", marginTop: "0.5rem" }}>
              {[{ val: "true", label: "Sí" }, { val: "false", label: "No" }].map(({ val, label }) => (
                <label key={label} style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer" }}>
                  <input type="radio" value={val} {...register("ha_declarado_renta", { setValueAs: v => v === "true" })} />
                  {label}
                </label>
              ))}
            </div>
          </div>

          {haDeclarado && (
            <div>
              <label className="ctx-label">Último año declarado</label>
              <input className="ctx-input" placeholder="Ej. 2023" {...register("ultimo_año_declarado")} />
            </div>
          )}
        </div>
      </StepWrapper>
    </form>
  );
}
