"use client";
// ============================================================
// lib/store.ts
// Zustand store con persistencia localStorage
// ============================================================
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type {
  Paso1Data, Paso2Data, Paso3Data, Paso4Data,
  Paso5Data, Paso6Data, Paso7Data
} from "./validations";

export interface AuditResult {
  recomendacion: "simple" | "ordinario";
  ingresosAnuales: number;
  costosTotales: number;
  utilidadBruta: number;
  margenPct: number;
  impuestoSimple: number;
  impuestoOrdinario: number;
  ahorroPotencial: number;
  readinessScore: number;
  readinessBand: "verde" | "ambar" | "rojo";
  riesgos: Array<{ nivel: string; titulo: string; descripcion: string; accion: string; esBannerCIIU1090?: boolean }>;
  oportunidades: Array<{ titulo: string; descripcion: string; impactoEstimado?: string }>;
}

interface WizardStore {
  pasoActual: number;
  leadId: string | null;
  paso1: Partial<Paso1Data>;
  paso2: Partial<Paso2Data>;
  paso3: Partial<Paso3Data>;
  paso4: Partial<Paso4Data>;
  paso5: Partial<Paso5Data>;
  paso6: Partial<Paso6Data>;
  paso7: Partial<Paso7Data>;
  auditResult: AuditResult | null;
  // Actions
  setPasoActual: (paso: number) => void;
  setLeadId: (id: string) => void;
  setPaso1: (data: Partial<Paso1Data>) => void;
  setPaso2: (data: Partial<Paso2Data>) => void;
  setPaso3: (data: Partial<Paso3Data>) => void;
  setPaso4: (data: Partial<Paso4Data>) => void;
  setPaso5: (data: Partial<Paso5Data>) => void;
  setPaso6: (data: Partial<Paso6Data>) => void;
  setPaso7: (data: Partial<Paso7Data>) => void;
  setAuditResult: (result: AuditResult) => void;
  setPrefillConnatural: () => void;
  reset: () => void;
}

const CONNATURAL_DATA = {
  paso1: {
    nombre: "Juan Esteban Gutiérrez Caicedo",
    cedula: "1216729372",
    email: "estebancaicedo66@outlook.es",
    pais_codigo: "+57",
    whatsapp: "3165693970",
    ciudad: "Medellín, Antioquia",
    rol: "Propietario / Emprendedor",
  } as Paso1Data,
  paso2: {
    nombre_opcion1: "Connatural Dieta BARF S.A.S.",
    tipo_sociedad: "SAS" as const,
    sector: "Manufactura de alimentos para mascotas (BARF — Biologically Appropriate Raw Food)",
    ciiu_principal: "1090",
    ciiu_secundario: "4791",
    direccion: "Calle 104A #84D-78, Medellín, Antioquia",
    tiene_rut_actual: "si" as const,
    nit_actual: "Mat. 21-805311-01",
  } as Paso2Data,
  paso3: {
    num_socios: 1,
    socios: [{ nombre: "Juan Esteban Gutiérrez Caicedo", cedula: "1216729372", participacion: 100, rol: "Accionista único" }],
    representante_legal: "Juan Esteban Gutiérrez Caicedo",
    capital_suscrito: 20000000,
    aportes_en_especie: true,
    descripcion_aportes: "Equipos de planta BARF, inventario, dominio web naturalbarf.com y derechos sobre redes sociales",
  } as Paso3Data,
  paso4: {
    ingresos_mensuales: 8000000,
    costos_pct: 65,
    modelo_negocio: "manufactura" as const,
    medios_pago: ["Transferencia", "Nequi", "Daviplata"],
    tiene_ingresos_previos: true,
    ingreso_anual_previo: 80000000,
    ha_declarado_renta: false,
  } as Paso4Data,
  paso5: {
    tiene_contador: false,
    maneja_inventarios: true,
    facturacion_electronica: "no" as const,
    regimen_preferido: "analisis" as const,
    registros_actuales: "excel" as const,
  } as Paso5Data,
  paso6: {
    empleados: 0,
    tipos_vinculacion: [],
    salario_promedio: 0,
    requiere_nomina: false,
    contratos_proveedores: false,
    tiene_bpa: true,
  } as Paso6Data,
  paso7: {
    tiene_ecommerce: false,
    dominio_web: "naturalbarf.com",
    redes_sociales: ["Instagram", "YouTube"],
  } as Paso7Data,
};

export const useWizardStore = create<WizardStore>()(
  persist(
    (set) => ({
      pasoActual: 1,
      leadId: null,
      paso1: {},
      paso2: {},
      paso3: {},
      paso4: {},
      paso5: {},
      paso6: {},
      paso7: {},
      auditResult: null,
      setPasoActual: (paso) => set({ pasoActual: paso }),
      setLeadId: (id) => set({ leadId: id }),
      setPaso1: (data) => set((s) => ({ paso1: { ...s.paso1, ...data } })),
      setPaso2: (data) => set((s) => ({ paso2: { ...s.paso2, ...data } })),
      setPaso3: (data) => set((s) => ({ paso3: { ...s.paso3, ...data } })),
      setPaso4: (data) => set((s) => ({ paso4: { ...s.paso4, ...data } })),
      setPaso5: (data) => set((s) => ({ paso5: { ...s.paso5, ...data } })),
      setPaso6: (data) => set((s) => ({ paso6: { ...s.paso6, ...data } })),
      setPaso7: (data) => set((s) => ({ paso7: { ...s.paso7, ...data } })),
      setAuditResult: (result) => set({ auditResult: result }),
      setPrefillConnatural: () => set({ ...CONNATURAL_DATA, pasoActual: 1 }),
      reset: () => set({
        pasoActual: 1, leadId: null,
        paso1: {}, paso2: {}, paso3: {}, paso4: {}, paso5: {}, paso6: {}, paso7: {},
        auditResult: null,
      }),
    }),
    {
      name: "contexia-wizard-storage",
      storage: createJSONStorage(() =>
        typeof window !== "undefined" ? localStorage : {
          getItem: () => null, setItem: () => {}, removeItem: () => {}
        }
      ),
    }
  )
);
