// ============================================================
// lib/feriaConfig.ts
// Feature-flag + configuración centralizada para ferias/eventos
// 
// Activar:   NEXT_PUBLIC_FERIA_MODE=estudia-2026-06-17  (en Vercel env vars)
// Desactivar: borrar o vaciar esa env var → redeploy automático
// ============================================================

export interface FeriaConfig {
  id: string;
  nombre: string;
  nombreCorto: string;
  fecha: string;
  lugar: string;
  direccion: string;
  horario: string;
  organizador: string;
  apoya: string;
  // Copy del Hero
  heroBadge: string;
  heroTitle: string;
  heroTitleGradient: string;
  heroSubtitle: string;
  heroCTA: string;
  heroSubCTA: string;
  // Proof points
  proofPoints: Array<{ icon: string; text: string }>;
  // Trust logos / badges
  trustBadges: string[];
  // Lead source tag para Supabase
  leadSource: string;
  // Campos extra de lead capture para la feria
  expectativaOptions: string[];
  servicioInteresOptions: string[];
  comoNosConocisteOptions: string[];
}

const FERIAS: Record<string, FeriaConfig> = {
  "estudia-2026-06-17": {
    id: "estudia-2026-06-17",
    nombre: "Rueda de Negocios Estud-IA",
    nombreCorto: "Estud-IA",
    fecha: "Miércoles 17 de junio, 2026",
    lugar: "Ruta N — Centro de Innovación y Negocios",
    direccion: "Calle 67 #52-20, Medellín",
    horario: "7:30 a.m. a 1:00 p.m.",
    organizador: "Alcaldía de Medellín — Ciencia, Tecnología e Innovación",
    apoya: "Cymetria · El futuro es digital",

    heroBadge: "🚀 Rueda de Negocios Estud-IA × Contexia",
    heroTitle: "Inteligencia fiscal",
    heroTitleGradient: "para empresas que escalan",
    heroSubtitle:
      "Contexia combina IA + equipo contable experto para optimizar tu carga tributaria. Descubre en 5 minutos si tu empresa está dejando dinero en la mesa — gratis, sin compromiso.",
    heroCTA: "Hacer mi diagnóstico Estud-IA →",
    heroSubCTA: "Exclusivo para asistentes de la Rueda de Negocios. 100% gratuito.",

    proofPoints: [
      { icon: "🏢", text: "Aliados Ruta N" },
      { icon: "🤖", text: "IA + Contadores" },
      { icon: "📊", text: "+200 diagnósticos" },
      { icon: "🎯", text: "Plan 30-60-90 días" },
    ],

    trustBadges: [
      "Estud-IA",
      "Ruta N Medellín",
      "Alcaldía de Medellín",
      "Cymetria",
    ],

    leadSource: "feria-estudia-2026-06-17",

    expectativaOptions: [
      "Alianza estratégica",
      "Compra de servicios",
      "Canje / Intercambio",
      "Inversión",
      "Mentoría / Asesoría",
      "Networking",
      "Otro",
    ],
    servicioInteresOptions: [
      "Contabilidad con IA",
      "Creación de Empresa SAS",
      "Shadow Audit (Diagnóstico Tributario)",
      "Nómina electrónica",
      "Facturación electrónica",
      "Growth / Marketing digital",
      "Consultoría fiscal",
      "Otro",
    ],
    comoNosConocisteOptions: [
      "Rueda de Negocios Estud-IA",
      "Ruta N / Ruta Emprender",
      "Secretaría de Desarrollo",
      "Referido / Contacto directo",
      "Redes sociales",
      "Google",
      "Otro",
    ],
  },
};

// ─── Public helpers ──────────────────────────────────────────

/** Is feria mode active? */
export function isFeria(): boolean {
  const mode = process.env.NEXT_PUBLIC_FERIA_MODE || "";
  return mode !== "" && mode in FERIAS;
}

/** Get current feria config (or null) */
export function getFeriaConfig(): FeriaConfig | null {
  const mode = process.env.NEXT_PUBLIC_FERIA_MODE || "";
  return FERIAS[mode] || null;
}
