"use client";
// ============================================================
// lib/ecomStore.ts
// Zustand store for the 3-step express IVA diagnostic
// (wizard-iva-ecom-express-diagnostic, design.md D1).
//
// Deliberately separate from lib/store.ts's WizardStore: the data
// shapes don't overlap (this flow has no Paso1..7 fields at all), and
// WizardStore already persists to localStorage — extending it risks
// corrupting in-flight sessions of the existing 8-step flow. This
// store gets its own localStorage key instead.
// ============================================================
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export interface EcomNumeros {
  ventasMensuales?: number;
  gastoMetaAds?: number;
  margenBruto?: number;
}

export type TipoPersona = "persona_natural" | "sas";

export interface EcomFormalizacion {
  tipoPersona?: TipoPersona;
  facturaElectronicamente?: boolean;
}

interface EcomStore {
  pasoActual: 1 | 2 | 3;
  numeros: EcomNumeros;
  formalizacion: EcomFormalizacion;
  email?: string;
  setPasoActual: (paso: 1 | 2 | 3) => void;
  setNumeros: (data: EcomNumeros) => void;
  setFormalizacion: (data: EcomFormalizacion) => void;
  setEmail: (email: string) => void;
  reset: () => void;
}

const initialState = {
  pasoActual: 1 as const,
  numeros: {},
  formalizacion: {},
  email: undefined,
};

export const useEcomStore = create<EcomStore>()(
  persist(
    (set) => ({
      ...initialState,
      setPasoActual: (paso) => set({ pasoActual: paso }),
      setNumeros: (data) =>
        set((state) => ({ numeros: { ...state.numeros, ...data } })),
      setFormalizacion: (data) =>
        set((state) => ({ formalizacion: { ...state.formalizacion, ...data } })),
      setEmail: (email) => set({ email }),
      reset: () => set(initialState),
    }),
    {
      name: "contexia-wizard-ecom-store",
      storage: createJSONStorage(() => localStorage),
    }
  )
);
