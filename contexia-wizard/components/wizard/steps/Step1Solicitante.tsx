"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { paso1Schema, type Paso1Data } from "@/lib/validations";
import { useWizardStore } from "@/lib/store";
import { isFeria, getFeriaConfig } from "@/lib/feriaConfig";
import StepWrapper from "../StepWrapper";

// ─── Normal roles ────────────────────────────────────────────
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

// ─── Extended feria schema (superset of paso1) ───────────────
const feriaLeadSchema = paso1Schema.extend({
  empresa: z.string().min(2, "Ingresa tu empresa o emprendimiento"),
  cargo: z.string().min(2, "Ingresa tu cargo"),
  expectativa: z.string().min(1, "Selecciona un tipo de expectativa"),
  servicio_interes: z.string().min(1, "Selecciona un servicio de interés"),
  como_conociste: z.string().min(1, "¿Cómo nos conociste?"),
  observaciones: z.string().optional(),
});
type FeriaLeadData = z.infer<typeof feriaLeadSchema>;

interface Props { onNext: () => void; }

// ─── FERIA version of Step 1 ─────────────────────────────────
function Step1Feria({ onNext }: Props) {
  const { paso1, setPaso1 } = useWizardStore();
  const config = getFeriaConfig()!;

  const { register, handleSubmit, formState: { errors } } = useForm<FeriaLeadData>({
    resolver: zodResolver(feriaLeadSchema),
    defaultValues: {
      ...paso1,
      pais_codigo: paso1.pais_codigo || "+57",
      empresa: "",
      cargo: "",
      expectativa: "",
      servicio_interes: "",
      como_conociste: "Rueda de Negocios Estud-IA",
      observaciones: "",
    } as FeriaLeadData,
  });

  const onSubmit = async (data: FeriaLeadData) => {
    // Save standard paso1 fields to store
    const { empresa, cargo, expectativa, servicio_interes, como_conociste, observaciones, ...paso1Fields } = data;
    setPaso1(paso1Fields);

    // Save to Supabase with feria source + extra fields
    try {
      await fetch("/wizard/api/leads/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          paso1: paso1Fields,
          source: config.leadSource,
          feria_data: {
            empresa,
            cargo,
            expectativa,
            servicio_interes,
            como_conociste,
            observaciones,
            evento: config.nombre,
            fecha_evento: config.fecha,
          },
        }),
      });
    } catch (_) {}
    onNext();
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <StepWrapper
        step={1}
        headline="Registro de Conexión Empresarial"
        subheadline={`${config.nombre} · Conéctate con Contexia y descubre cómo podemos potenciar tu empresa.`}
        onNext={handleSubmit(onSubmit)}
        nextLabel="Comenzar diagnóstico Estud-IA →"
      >
        {/* Feria badge */}
        <div
          style={{
            background: "linear-gradient(135deg, rgba(249,115,22,0.12), rgba(168,85,247,0.12))",
            border: "1px solid rgba(249,115,22,0.25)",
            borderRadius: "12px",
            padding: "0.875rem 1.25rem",
            marginBottom: "1.5rem",
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
            fontSize: "0.875rem",
          }}
        >
          <span style={{ fontSize: "1.25rem" }}>🚀</span>
          <div>
            <span style={{ color: "#fb923c", fontWeight: 700 }}>
              {config.nombre}
            </span>
            <span style={{ color: "var(--ctx-text-muted)" }}>
              {" "}— {config.fecha} · {config.lugar}
            </span>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.25rem" }}>
          {/* === DATOS PERSONALES === */}

          {/* Nombre */}
          <div style={{ gridColumn: "1 / -1" }}>
            <label className="ctx-label">Nombre completo *</label>
            <input className={`ctx-input ${errors.nombre ? "error" : ""}`} placeholder="Ej. María García López" {...register("nombre")} />
            {errors.nombre && <p className="ctx-error-msg">{errors.nombre.message}</p>}
          </div>

          {/* Empresa */}
          <div style={{ gridColumn: "1 / -1" }}>
            <label className="ctx-label">Empresa / Emprendimiento *</label>
            <input className={`ctx-input ${errors.empresa ? "error" : ""}`} placeholder="Nombre de tu empresa o proyecto" {...register("empresa")} />
            {errors.empresa && <p className="ctx-error-msg">{errors.empresa.message}</p>}
          </div>

          {/* Cargo */}
          <div>
            <label className="ctx-label">Cargo *</label>
            <input className={`ctx-input ${errors.cargo ? "error" : ""}`} placeholder="CEO, Gerente, Contador..." {...register("cargo")} />
            {errors.cargo && <p className="ctx-error-msg">{errors.cargo.message}</p>}
          </div>

          {/* Cédula */}
          <div>
            <label className="ctx-label">Cédula de ciudadanía *</label>
            <input className={`ctx-input ${errors.cedula ? "error" : ""}`} placeholder="1234567890" {...register("cedula")} />
            {errors.cedula && <p className="ctx-error-msg">{errors.cedula.message}</p>}
          </div>

          {/* Email */}
          <div>
            <label className="ctx-label">Email corporativo *</label>
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
            {errors.whatsapp && <p className="ctx-error-msg">{errors.whatsapp.message}</p>}
          </div>

          {/* Ciudad */}
          <div>
            <label className="ctx-label">Ciudad *</label>
            <input className={`ctx-input ${errors.ciudad ? "error" : ""}`} placeholder="Medellín, Antioquia" {...register("ciudad")} />
            {errors.ciudad && <p className="ctx-error-msg">{errors.ciudad.message}</p>}
          </div>

          {/* Rol */}
          <div>
            <label className="ctx-label">Tu rol en la empresa *</label>
            <select className={`ctx-input ${errors.rol ? "error" : ""}`} {...register("rol")}>
              <option value="">Selecciona tu rol</option>
              {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
            {errors.rol && <p className="ctx-error-msg">{errors.rol.message}</p>}
          </div>

          {/* === DATOS FERIA — Conexión Empresarial === */}

          <div style={{ gridColumn: "1 / -1", margin: "0.75rem 0 0.25rem" }}>
            <div style={{
              height: "1px",
              background: "linear-gradient(to right, transparent, rgba(249,115,22,0.3), transparent)",
              marginBottom: "1rem",
            }} />
            <p style={{
              color: "#fb923c",
              fontSize: "0.8125rem",
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              margin: 0,
            }}>
              📋 Registro de Conexión Empresarial
            </p>
          </div>

          {/* Expectativa */}
          <div>
            <label className="ctx-label">Tipo de expectativa *</label>
            <select className={`ctx-input ${errors.expectativa ? "error" : ""}`} {...register("expectativa")}>
              <option value="">Selecciona una opción</option>
              {config.expectativaOptions.map((o) => <option key={o} value={o}>{o}</option>)}
            </select>
            {errors.expectativa && <p className="ctx-error-msg">{errors.expectativa.message}</p>}
          </div>

          {/* Servicio de interés */}
          <div>
            <label className="ctx-label">Servicio o producto de interés *</label>
            <select className={`ctx-input ${errors.servicio_interes ? "error" : ""}`} {...register("servicio_interes")}>
              <option value="">¿Qué te interesa?</option>
              {config.servicioInteresOptions.map((o) => <option key={o} value={o}>{o}</option>)}
            </select>
            {errors.servicio_interes && <p className="ctx-error-msg">{errors.servicio_interes.message}</p>}
          </div>

          {/* Cómo nos conociste */}
          <div>
            <label className="ctx-label">¿Cómo nos conociste? *</label>
            <select className={`ctx-input ${errors.como_conociste ? "error" : ""}`} {...register("como_conociste")}>
              <option value="">Selecciona</option>
              {config.comoNosConocisteOptions.map((o) => <option key={o} value={o}>{o}</option>)}
            </select>
            {errors.como_conociste && <p className="ctx-error-msg">{errors.como_conociste.message}</p>}
          </div>

          {/* Observaciones */}
          <div>
            <label className="ctx-label">Observaciones</label>
            <textarea
              className="ctx-input"
              placeholder="Notas, proyección de ventas, comentarios..."
              rows={2}
              {...register("observaciones")}
              style={{ resize: "vertical", minHeight: "60px" }}
            />
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

// ─── NORMAL version of Step 1 ────────────────────────────────
function Step1Normal({ onNext }: Props) {
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

// ─── Export: auto-select version based on feria flag ──────────
export default function Step1Solicitante({ onNext }: Props) {
  return isFeria() ? <Step1Feria onNext={onNext} /> : <Step1Normal onNext={onNext} />;
}
