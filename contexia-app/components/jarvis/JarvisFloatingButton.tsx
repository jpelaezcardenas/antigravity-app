import { JarvisBubble } from "@/components/jarvis/JarvisBubble";

/**
 * JARVIS as a small floating button — every V1 screen except Pulso (2026-09-18, founder:
 * "solo quiero ver jarvis en el pulso, en las demas queda al otro lado de apagado, tirado a
 * la izquierda como boton flotante"). Mirrors FloatingSignOutButton's placement on the
 * opposite edge: fixed bottom-left, same bottom offset (above BottomNav on mobile). Pulso
 * keeps the full in-flow badge (JarvisFloatingBadgeV2) instead.
 *
 * Same JarvisBubble component and chat panel — only the compact (pin-only) rendering, so
 * there's still one JARVIS, just a smaller door to it.
 */
export function JarvisFloatingButton() {
  return (
    <div className="fixed bottom-24 md:bottom-6 left-4 z-40">
      <JarvisBubble size={48} panelAnchor="header" />
    </div>
  );
}
