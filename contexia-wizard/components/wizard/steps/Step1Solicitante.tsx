"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { paso1Schema, type Paso1Data } from "@/lib/validations";
import { useWizardStore } from "@/lib/store";
import StepWrapper from "../StepWrapper";

const ROLES = [
  "Propietario / Emprendedor",
  "Independiente / Freelance",
  "Comerciante con Local",
  "Empleado",
  "Contador",
  "Financiero",
  "Administrador",
  "Manager",
  "Otro"
];

interface Props { onNext: () => void; }

export default function Step1Solicitante({ onNext }: Props) {
  const { paso1, setPaso1 } = useWizardStore();

  const { register, handleSubmit, formState: { errors } } = useForm<Paso1Data>({
    resolver: zodResolver(paso1Schema),
    defaultValues: { ...paso1 } as Paso1Data,
  });

  const onSubmit = async (data: Paso1Data) => {
    setPaso1(data);
    // Auto-save to Supabase
    try {
      await fetch("/wizard/api/leads/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ paso1: data }),
      });
    } catch (_) {}
    onNext();
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <StepWrapper
        step={1}
        headline="Empecemos por ti"
        subheadline="Esta info es confidencial. Solo la usamos para generar tu diagnóstico personalizado."
        onNext={handleSubmit(onSubmit)}
      >
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.25rem" }}>
          {/* Nombre */}
          <div style={{ gridColumn: "1 / -1" }}>
            <label className="ctx-label">Nombre completo *</label>
            <input className={`ctx-input ${errors.nombre ? "error" : ""}`} placeholder="Ej. María García López" {...register("nombre")} />
            {errors.nombre && <p className="ctx-error-msg">{errors.nombre.message}</p>}
          </div>

          {/* Cédula */}
          <div>
            <label className="ctx-label">Cédula de ciudadanía *</label>
            <input className={`ctx-input ${errors.cedula ? "error" : ""}`} placeholder="1234567890" {...register("cedula")} />
            {errors.cedula && <p className="ctx-error-msg">{errors.cedula.message}</p>}
          </div>

          {/* Email */}
          <div>
            <label className="ctx-label">Email *</label>
            <input type="email" className={`ctx-input ${errors.email ? "error" : ""}`} placeholder="tu@empresa.com" {...register("email")} />
            {errors.email && <p className="ctx-error-msg">{errors.email.message}</p>}
          </div>

          {/* WhatsApp with Country Code */}
          <div>
            <label className="ctx-label">WhatsApp *</label>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <select 
                className="ctx-input" 
                style={{ width: "90px", padding: "0.875rem 0.5rem", textAlign: "center" }}
                {...register("pais_codigo")}
                defaultValue="+57"
              >
                <option value="+57">🇨🇴 +57</option>
                <option value="+52">🇲🇽 +52</option>
                <option value="+56">🇨🇱 +56</option>
                <option value="+51">🇵🇪 +51</option>
                <option value="+1">🇺🇸 +1</option>
                <option value="+34">🇪🇸 +34</option>
                <option value="+58">🇻🇪 +58</option>
                <option value="+593">🇪🇨 +593</option>
                <option value="+507">🇵🇦 +507</option>
              </select>
              <input 
                className={`ctx-input ${errors.whatsapp ? "error" : ""}`} 
                placeholder="300 123 4567" 
                {...register("whatsapp")} 
                style={{ flex: 1 }}
              />
            </div>
            <span className="ctx-label-hint">Selecciona tu país y número sin prefijo</span>
            {errors.whatsapp && <p className="ctx-error-msg">{errors.whatsapp.message}</p>}
          </div>

          {/* Ciudad */}
          <div>
            <label className="ctx-label">Ciudad *</label>
            <input className={`ctx-input ${errors.ciudad ? "error" : ""}`} placeholder="Medellín, Antioquia" {...register("ciudad")} />
            {errors.ciudad && <p className="ctx-error-msg">{errors.ciudad.message}</p>}
          </div>

          {/* Rol */}
          <div style={{ gridColumn: "1 / -1" }}>
            <label className="ctx-label">Tu rol en la empresa *</label>
            <select className={`ctx-input ${errors.rol ? "error" : ""}`} {...register("rol")}>
              <option value="">Selecciona tu rol</option>
              {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
            {errors.rol && <p className="ctx-error-msg">{errors.rol.message}</p>}
          </div>
        </div>

        {/* Privacy note */}
        <p style={{ fontSize: "0.8125rem", color: "var(--ctx-text-muted)", marginTop: "1.25rem", display: "flex", alignItems: "center", gap: "0.375rem" }}>
          🔒 Tu información es 100% confidencial y nunca será compartida con terceros.
        </p>
      </StepWrapper>
    </form>
  );
}
