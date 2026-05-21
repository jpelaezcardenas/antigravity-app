/**
 * Tipos del Wizard de Crear Empresa (constitución de SAS/Ltda en Colombia)
 * Mock-first: sin backend, todo el estado vive en useState + localStorage.
 */

export type WizardStep = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8;

export type TipoSociedad = "sas" | "sas-unipersonal" | "ltda";

export type RepresentanteOrigen = "socio" | "otro";

export type PaymentMethod =
  | "transferencia"
  | "tarjeta"
  | "pse"
  | "bancolombia"
  | "daviplata"
  | "nequi";

export interface ContactoData {
  nombre: string;
  telefono: string; // sin +57, solo dígitos
  email: string;
}

export interface AccionistaData {
  id: string; // uuid local
  nombre: string;
  cedula: string;
  participacion: number; // porcentaje 0-100
  esRepresentanteLegal?: boolean;
}

export interface CapitalData {
  total: number; // COP
  suscritoPct: number; // 0-100
  pagadoPct: number; // 0-100
}

export interface RepresentanteData {
  origen: RepresentanteOrigen;
  // si origen === "socio"
  socioId?: string;
  // si origen === "otro"
  nombre?: string;
  cedula?: string;
  telefono?: string;
  email?: string;
}

export interface EmpresaDescripcion {
  actividad: string; // texto largo
  ciiu?: string; // código CIIU
  direccion: string;
  ciudad: string;
  departamento: string;
}

export interface WizardState {
  step: WizardStep;
  contacto: ContactoData;
  tipoSociedad: TipoSociedad | null;
  nombreEmpresa: string;
  nombreDisponible: boolean | null; // null = no checked
  descripcion: EmpresaDescripcion;
  accionistas: AccionistaData[];
  capital: CapitalData;
  representante: RepresentanteData;
  paymentMethod: PaymentMethod | null;
  acceptedTerms: boolean;
}

export const INITIAL_WIZARD_STATE: WizardState = {
  step: 1,
  contacto: {
    nombre: "",
    telefono: "",
    email: "",
  },
  tipoSociedad: null,
  nombreEmpresa: "",
  nombreDisponible: null,
  descripcion: {
    actividad: "",
    ciiu: "",
    direccion: "",
    ciudad: "",
    departamento: "",
  },
  accionistas: [],
  capital: {
    total: 500_000,
    suscritoPct: 100,
    pagadoPct: 100,
  },
  representante: {
    origen: "socio",
  },
  paymentMethod: null,
  acceptedTerms: false,
};

export const WIZARD_STORAGE_KEY = "contexia_crear_empresa_wizard_v1";

export const PRICE_CREAR_EMPRESA = 399_000; // COP

export const WIZARD_STEPS_LABELS: Record<WizardStep, { short: string; long: string }> = {
  1: { short: "Contacto", long: "Tus datos" },
  2: { short: "Estructura", long: "Tipo de empresa" },
  3: { short: "Nombre", long: "Nombre de la empresa" },
  4: { short: "Actividad", long: "Qué hace la empresa" },
  5: { short: "Socios", long: "Quién participa" },
  6: { short: "Capital", long: "Con cuánto arrancan" },
  7: { short: "Firma", long: "Representante legal" },
  8: { short: "Pago", long: "Resumen y pago" },
};
