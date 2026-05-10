// ============================================================
// lib/validations.ts
// Zod schemas para cada paso del wizard
// ============================================================
import { z } from "zod";

// ── Paso 1 — Solicitante ─────────────────────────────────────
export const paso1Schema = z.object({
  nombre: z.string().min(3, "Ingresa tu nombre completo"),
  cedula: z
    .string()
    .regex(/^\d{8,10}$/, "La cédula debe tener entre 8 y 10 dígitos"),
  email: z.string().email("Ingresa un email válido"),
  pais_codigo: z.string().min(1),
  whatsapp: z
    .string()
    .min(7, "Ingresa un número válido")
    .regex(/^\d+$/, "Solo números sin espacios"),
  ciudad: z.string().min(2, "Ingresa tu ciudad"),
  rol: z.string().min(1, "Selecciona tu rol"),
});
export type Paso1Data = z.infer<typeof paso1Schema>;

// ── Paso 2 — Empresa ─────────────────────────────────────────
export const paso2Schema = z.object({
  nombre_opcion1: z.string().min(3, "Ingresa el nombre deseado para tu empresa"),
  nombre_opcion2: z.string().optional(),
  nombre_opcion3: z.string().optional(),
  tipo_sociedad: z.enum(["SAS", "Ltda", "persona_natural_comercio", "persona_natural_servicios", "otro"]),
  sector: z.string().min(3, "Describe la actividad económica"),
  ciiu_principal: z.string().min(4, "Selecciona el CIIU principal"),
  ciiu_secundario: z.string().optional(),
  direccion: z.string().min(5, "Ingresa la dirección de operación"),
  tiene_rut_actual: z.enum(["si", "no"]),
  nit_actual: z.string().optional(),
});
export type Paso2Data = z.infer<typeof paso2Schema>;

// ── Paso 3 — Sociedad ────────────────────────────────────────
const socioSchema = z.object({
  nombre: z.string().min(2),
  cedula: z.string(),
  participacion: z.number().min(1).max(100),
  rol: z.string().min(2),
});

export const paso3Schema = z.object({
  num_socios: z.number().min(1).max(10),
  socios: z.array(socioSchema).min(1),
  representante_legal: z.string().min(2),
  capital_suscrito: z.number().min(0),
  aportes_en_especie: z.boolean(),
  descripcion_aportes: z.string().optional(),
});
export type Paso3Data = z.infer<typeof paso3Schema>;

// ── Paso 4 — Financiero ──────────────────────────────────────
export const paso4Schema = z.object({
  ingresos_mensuales: z.number().min(1, "Ingresa los ingresos mensuales"),
  costos_pct: z.number().min(0).max(100),
  modelo_negocio: z.enum([
    "ecommerce",
    "manufactura",
    "servicios",
    "comercio_fisico",
    "mixto",
  ]),
  medios_pago: z.array(z.string()).min(1, "Selecciona al menos un medio de pago"),
  tiene_ingresos_previos: z.boolean(),
  ingreso_anual_previo: z.number().optional(),
  ha_declarado_renta: z.boolean(),
  ultimo_año_declarado: z.string().optional(),
});
export type Paso4Data = z.infer<typeof paso4Schema>;

// ── Paso 5 — Contable ────────────────────────────────────────
export const paso5Schema = z.object({
  tiene_contador: z.boolean(),
  nombre_contador: z.string().optional(),
  email_contador: z.string().email().optional().or(z.literal("")),
  maneja_inventarios: z.boolean(),
  facturacion_electronica: z.enum(["si", "no", "no_se"]),
  regimen_preferido: z.enum(["simple", "ordinario", "analisis"]).optional(),
  registros_actuales: z.enum([
    "manual",
    "excel",
    "software",
    "ninguno",
  ]),
});
export type Paso5Data = z.infer<typeof paso5Schema>;

// ── Paso 6 — Administrativa ──────────────────────────────────
export const paso6Schema = z.object({
  empleados: z.number().min(0).optional(),
  tipos_vinculacion: z.array(z.string()),
  salario_promedio: z.number().min(0).optional(),
  requiere_nomina: z.boolean(),
  contratos_proveedores: z.boolean(),
  tiene_bpa: z.boolean().optional(),
});
export type Paso6Data = z.infer<typeof paso6Schema>;

// ── Paso 7 — Digital ─────────────────────────────────────────
export const paso7Schema = z.object({
  tiene_ecommerce: z.boolean(),
  plataforma_ecommerce: z.string().optional(),
  software_contable: z.string().optional(),
  dominio_web: z.string().optional(),
  redes_sociales: z.array(z.string()),
});
export type Paso7Data = z.infer<typeof paso7Schema>;

// ── Tipo completo del wizard ──────────────────────────────────
export interface WizardData {
  paso1?: Paso1Data;
  paso2?: Paso2Data;
  paso3?: Paso3Data;
  paso4?: Paso4Data;
  paso5?: Paso5Data;
  paso6?: Paso6Data;
  paso7?: Paso7Data;
}
