"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { paso2Schema, type Paso2Data } from "@/lib/validations";
import { useWizardStore } from "@/lib/store";
import StepWrapper from "../StepWrapper";

const CIIU_OPTIONS = [
  { value: "1090", label: "1090 — Elaboración de alimentos preparados para animales" },
  { value: "4631", label: "4631 — Comercio al por mayor de alimentos" },
  { value: "4791", label: "4791 — Comercio al por menor por internet" },
  { value: "4773", label: "4773 — Comercio al por menor especializado" },
  { value: "5611", label: "5611 — Restaurantes y establecimientos de comida" },
  { value: "6201", label: "6201 — Actividades de desarrollo de software" },
  { value: "7500", label: "7500 — Actividades veterinarias" },
  { value: "9609", label: "9609 — Otras actividades de servicios personales" },
  { value: "otro", label: "Otro (ingresa manualmente)" },
];

const TIPOS_SOCIEDAD = [
  { value: "SAS", label: "SAS — Sociedad por Acciones Simplificada (recomendada)" },
  { value: "Ltda", label: "Ltda — Sociedad de Responsabilidad Limitada" },
  { value: "persona_natural", label: "Persona Natural (sin constitución societaria)" },
];

interface Props { onNext: () => void; onBack: () => void; }

export default function Step2Empresa({ onNext, onBack }: Props) {
  const { paso2, setPaso2 } = useWizardStore();

  const { register, handleSubmit, watch, formState: { errors } } = useForm<Paso2Data>({
    resolver: zodResolver(paso2Schema),
    defaultValues: paso2 as Paso2Data,
  });

  const ciiu = watch("ciiu_principal");
  const tieneRut = watch("tiene_rut_actual");

  const onSubmit = (data: Paso2Data) => {
    setPaso2(data);
    onNext();
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <StepWrapper
        step={2}
        headline="Cuéntanos de tu empresa"
        onNext={handleSubmit(onSubmit)}
        onBack={onBack}
      >
        {/* Banner CIIU 1090 */}
        {ciiu === "1090" && (
          <div style={{
            background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: "10px",
            padding: "1rem 1.25rem", marginBottom: "1.5rem", display: "flex", gap: "0.75rem"
          }}>
            <span style={{ fontSize: "1.25rem", flexShrink: 0 }}>⚠️</span>
            <div>
              <h4 style={{ color: "#dc2626", fontWeight: 700, margin: "0 0 0.375rem", fontSize: "0.9375rem" }}>
                Tu actividad requiere registro ICA
              </h4>
              <p style={{ color: "#7f1d1d", fontSize: "0.875rem", margin: 0, lineHeight: 1.6 }}>
                La Resolución ICA 061252/2020 obliga a TODOS los fabricantes de alimento comercial para animales a registrarse en <strong>SimplifICA</strong>. Operar sin este registro expone a decomiso, cierre y multas hasta <strong>10.000 SMMLV (~$14.230 millones COP)</strong>. Contexia te acompaña en la ruta de cumplimiento.
              </p>
            </div>
          </div>
        )}

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.25rem" }}>
          {/* Nombres opciones */}
          <div style={{ gridColumn: "1 / -1" }}>
            <label className="ctx-label">Nombre deseado para tu empresa *</label>
            <input className={`ctx-input ${errors.nombre_opcion1 ? "error" : ""}`} placeholder="Opción 1 (principal)" {...register("nombre_opcion1")} />
            {errors.nombre_opcion1 && <p className="ctx-error-msg">{errors.nombre_opcion1.message}</p>}
          </div>
          <div>
            <label className="ctx-label">Nombre alternativo 2 <span style={{ color: "#94a3b8", fontWeight: 400 }}>(opcional)</span></label>
            <input className="ctx-input" placeholder="Opción 2" {...register("nombre_opcion2")} />
          </div>
          <div>
            <label className="ctx-label">Nombre alternativo 3 <span style={{ color: "#94a3b8", fontWeight: 400 }}>(opcional)</span></label>
            <input className="ctx-input" placeholder="Opción 3" {...register("nombre_opcion3")} />
          </div>

          {/* Tipo sociedad */}
          <div style={{ gridColumn: "1 / -1" }}>
            <label className="ctx-label">Tipo de sociedad *</label>
            <select className={`ctx-input ${errors.tipo_sociedad ? "error" : ""}`} {...register("tipo_sociedad")}>
              <option value="">Selecciona el tipo</option>
              {TIPOS_SOCIEDAD.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
            {errors.tipo_sociedad && <p className="ctx-error-msg">{errors.tipo_sociedad.message}</p>}
          </div>

          {/* Sector */}
          <div style={{ gridColumn: "1 / -1" }}>
            <label className="ctx-label">Sector / actividad económica *</label>
            <input className={`ctx-input ${errors.sector ? "error" : ""}`} placeholder="Ej. Fabricación de alimentos para mascotas" {...register("sector")} />
            {errors.sector && <p className="ctx-error-msg">{errors.sector.message}</p>}
          </div>

          {/* CIIU principal */}
          <div>
            <label className="ctx-label">CIIU principal *</label>
            <select className={`ctx-input ${errors.ciiu_principal ? "error" : ""}`} {...register("ciiu_principal")}>
              <option value="">Selecciona CIIU</option>
              {CIIU_OPTIONS.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
            {errors.ciiu_principal && <p className="ctx-error-msg">{errors.ciiu_principal.message}</p>}
          </div>

          {/* CIIU secundario */}
          <div>
            <label className="ctx-label">CIIU secundario <span style={{ color: "#94a3b8", fontWeight: 400 }}>(opcional)</span></label>
            <select className="ctx-input" {...register("ciiu_secundario")}>
              <option value="">Ninguno</option>
              {CIIU_OPTIONS.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
          </div>

          {/* Dirección */}
          <div style={{ gridColumn: "1 / -1" }}>
            <label className="ctx-label">Dirección de operación *</label>
            <input className={`ctx-input ${errors.direccion ? "error" : ""}`} placeholder="Calle, número, ciudad" {...register("direccion")} />
            {errors.direccion && <p className="ctx-error-msg">{errors.direccion.message}</p>}
          </div>

          {/* RUT actual */}
          <div>
            <label className="ctx-label">¿Ya tienes RUT como persona natural? *</label>
            <select className={`ctx-input ${errors.tiene_rut_actual ? "error" : ""}`} {...register("tiene_rut_actual")}>
              <option value="">Selecciona</option>
              <option value="si">Sí, tengo RUT activo</option>
              <option value="no">No, aún no tengo RUT</option>
            </select>
            {errors.tiene_rut_actual && <p className="ctx-error-msg">{errors.tiene_rut_actual.message}</p>}
          </div>

          {tieneRut === "si" && (
            <div>
              <label className="ctx-label">NIT / matrícula actual</label>
              <input className="ctx-input" placeholder="Ej. 1234567-1" {...register("nit_actual")} />
              <span className="ctx-label-hint">Para análisis de migración a la nueva SAS</span>
            </div>
          )}
        </div>
      </StepWrapper>
    </form>
  );
}
