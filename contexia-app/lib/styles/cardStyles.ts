/**
 * Estilos centralizados para tarjetas y contenedores
 * Consolidado para normalizar espaciado, bordes y sombras en toda la app
 */

// === Card Shadows (Updated with Teal glow from landing design) ===
export const CARD_SHADOW = {
  // Shadow with Teal glow for primary cards
  base: "shadow-[0_4px_24px_rgba(45,212,191,0.15)]",
  // Subtle Teal glow for secondary elements
  subtle: "shadow-[0_4px_24px_rgba(45,212,191,0.08)]",
  // Strong glow for elevated/featured cards
  glow: "shadow-[0_0_20px_rgba(45,212,191,0.3)]",
  // Sin shadow (flat design)
  none: "shadow-none",
};

// === Card Base Classes ===
// Combinación recomendada para tarjetas estándar
export const CARD_BASE = `rounded-xl border border-white/10 p-5 flex flex-col gap-3 ${CARD_SHADOW.base}`;

// Para tarjetas elevadas con fondo especial
export const CARD_ELEVATED = `bg-surface-elevated rounded-xl border border-white/10 p-5 flex flex-col gap-3 ${CARD_SHADOW.base}`;

// === Spacing Standards ===
export const SPACING = {
  // Sección a sección (entre grandes bloques)
  sectionGap: "gap-4",
  // Ítem a ítem dentro de una sección
  itemGap: "gap-3",
  // Dentro de un ítem (sub-contenidos)
  contentGap: "gap-2",
  // Elementos muy cercanos (compacto)
  compactGap: "gap-1",
  // Espaciado generoso entre secciones
  largeGap: "gap-6",
};

// === Border Radius Standards ===
export const BORDER_RADIUS = {
  // Para tarjetas y contenedores principales
  card: "rounded-xl",
  // Para contenedores secundarios pequeños
  container: "rounded-lg",
  // Para badges, pills, botones circulares
  badge: "rounded-full",
  // Para elementos muy pequeños
  small: "rounded-md",
};

// === Responsive Grid Columns ===
export const RESPONSIVE_GRID = {
  // 1 columna en mobile, 2 en tablet+
  twoCol: "grid grid-cols-1 md:grid-cols-2 gap-4",
  // 1 columna en mobile, 3 en tablet+
  threeCol: "grid grid-cols-1 md:grid-cols-3 gap-4",
  // 1 columna en mobile, 2-3 en desktop
  adaptiveCol: "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4",
};

// === Container Padding Standards ===
export const CONTAINER_PADDING = {
  // Padding estándar para tarjetas
  card: "p-5",
  // Padding para contenedores interiores
  inner: "p-4",
  // Padding compacto
  compact: "p-3",
};
