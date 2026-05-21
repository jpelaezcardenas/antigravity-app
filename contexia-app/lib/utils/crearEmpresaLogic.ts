/**
 * Validaciones y helpers del wizard Crear Empresa
 */

import type {
  WizardStep,
  WizardState,
  AccionistaData,
} from "@/lib/types/crearEmpresa";

export interface ValidationResult {
  ok: boolean;
  error?: string;
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PHONE_RE = /^3\d{9}$/; // móvil Colombia: empieza en 3, 10 dígitos

export function validateStep(step: WizardStep, state: WizardState): ValidationResult {
  switch (step) {
    case 1: {
      const { nombre, telefono, email } = state.contacto;
      if (!nombre.trim() || nombre.trim().split(" ").length < 2) {
        return { ok: false, error: "Escribe tu nombre completo" };
      }
      if (!PHONE_RE.test(telefono.replace(/\s/g, ""))) {
        return { ok: false, error: "Teléfono debe tener 10 dígitos y empezar en 3" };
      }
      if (!EMAIL_RE.test(email)) {
        return { ok: false, error: "Correo no válido" };
      }
      return { ok: true };
    }
    case 2: {
      if (!state.tipoSociedad) {
        return { ok: false, error: "Elige el tipo de empresa" };
      }
      return { ok: true };
    }
    case 3: {
      if (state.nombreEmpresa.trim().length < 4) {
        return { ok: false, error: "El nombre debe tener al menos 4 letras" };
      }
      if (state.nombreDisponible === false) {
        return { ok: false, error: "Este nombre no está disponible, prueba con otro" };
      }
      return { ok: true };
    }
    case 4: {
      if (state.descripcion.actividad.trim().length < 20) {
        return {
          ok: false,
          error: "Cuéntanos un poco más qué hace tu empresa (mínimo 20 letras)",
        };
      }
      if (!state.descripcion.ciudad || !state.descripcion.direccion.trim()) {
        return { ok: false, error: "Falta la ciudad o la dirección" };
      }
      return { ok: true };
    }
    case 5: {
      if (state.accionistas.length === 0) {
        return { ok: false, error: "Agrega al menos un socio" };
      }
      const totalPct = state.accionistas.reduce((s, a) => s + (a.participacion || 0), 0);
      if (Math.abs(totalPct - 100) > 0.01) {
        return {
          ok: false,
          error: `La suma de participaciones debe ser 100% (ahora va en ${totalPct.toFixed(1)}%)`,
        };
      }
      for (const a of state.accionistas) {
        if (!a.nombre.trim() || !a.cedula.trim()) {
          return { ok: false, error: "Cada socio necesita nombre y cédula" };
        }
      }
      return { ok: true };
    }
    case 6: {
      if (state.capital.total < 400_000) {
        return {
          ok: false,
          error: "El capital mínimo recomendado es $400.000 COP",
        };
      }
      if (state.capital.total > 800_000) {
        return {
          ok: false,
          error: "Para arrancar lo recomendado es máximo $800.000 COP (puedes aumentarlo después)",
        };
      }
      if (state.capital.pagadoPct > state.capital.suscritoPct) {
        return { ok: false, error: "Lo pagado no puede ser mayor que lo suscrito" };
      }
      return { ok: true };
    }
    case 7: {
      const { origen, socioId, nombre, cedula, telefono, email } = state.representante;
      if (origen === "socio") {
        if (!socioId) return { ok: false, error: "Elige cuál socio firma" };
      } else {
        if (!nombre?.trim() || !cedula?.trim() || !telefono?.trim() || !email?.trim()) {
          return { ok: false, error: "Faltan datos del representante legal" };
        }
        if (!EMAIL_RE.test(email)) {
          return { ok: false, error: "Correo del representante no válido" };
        }
      }
      return { ok: true };
    }
    case 8: {
      if (!state.paymentMethod) {
        return { ok: false, error: "Elige cómo vas a pagar" };
      }
      if (!state.acceptedTerms) {
        return { ok: false, error: "Acepta los términos para continuar" };
      }
      return { ok: true };
    }
    default:
      return { ok: true };
  }
}

export function nextStep(step: WizardStep): WizardStep {
  return Math.min(step + 1, 8) as WizardStep;
}

export function prevStep(step: WizardStep): WizardStep {
  return Math.max(step - 1, 1) as WizardStep;
}

export function makeAccionistaId(): string {
  return `acc-${Math.random().toString(36).slice(2, 9)}-${Date.now().toString(36)}`;
}

export function createEmptyAccionista(): AccionistaData {
  return {
    id: makeAccionistaId(),
    nombre: "",
    cedula: "",
    participacion: 0,
  };
}

export function formatCedula(value: string): string {
  // Solo dígitos
  const digits = value.replace(/\D/g, "");
  return digits;
}

export function formatTelefono(value: string): string {
  // Solo dígitos, máximo 10
  const digits = value.replace(/\D/g, "").slice(0, 10);
  return digits;
}

export function formatNombreEmpresaConSufijo(
  nombre: string,
  tipo: string | null,
): string {
  const sufijo =
    tipo === "sas" || tipo === "sas-unipersonal" ? "S.A.S." : tipo === "ltda" ? "Ltda." : "";
  if (!nombre.trim()) return "";
  return `${nombre.trim()} ${sufijo}`.trim();
}
