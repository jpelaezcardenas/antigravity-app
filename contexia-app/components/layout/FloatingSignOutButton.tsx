import Link from "next/link";

/**
 * The ONLY sign-out affordance in the client shell (2026-09-15, founder request) — a small
 * floating "power" icon, fixed bottom-right on every breakpoint. Replaced two earlier things
 * in the same tick: SignOutFooter (a text "Cerrar Sesión" button at the bottom of every page,
 * now deleted) and, before that, two page-specific duplicates (Config's own red button,
 * Overview's floating "Salir"). The Bunker admin panel (app/app/bunker/page.tsx) has its own
 * separate header-hosted logout button — same icon, different auth mechanism — kept in sync
 * by hand since it isn't part of this (shell) layout.
 *
 * Positioned above BottomNav on mobile (bottom-24, same offset the old per-page floating
 * "Salir" used) and clear of DesktopSidebar on desktop (fixed to the right edge, sidebar is
 * fixed to the left).
 *
 * Opacity/size tuned down (2026-09-17) after finding it obscuring card text on long
 * single-scroll pages (flujo-detalle, flujo-detalle-v2) — same fixed-position button on both
 * V1 and V2, not a V2-specific issue. Lower background opacity (still legible as a button,
 * via border + glow + blur) so text scrolling underneath it stays readable instead of hidden.
 */
export function FloatingSignOutButton() {
  return (
    <Link
      href="/logout"
      aria-label="Cerrar sesión"
      title="Cerrar sesión"
      className="fixed bottom-24 md:bottom-6 right-4 z-40 flex h-10 w-10 items-center justify-center rounded-full border border-[#2DD4BF]/40 bg-[#020617]/60 text-[#2DD4BF] shadow-[0_0_20px_rgba(45,212,191,0.25)] backdrop-blur transition-all hover:bg-[#020617]/90 hover:border-[#2DD4BF]/70"
    >
      <span className="material-symbols-outlined text-[20px]">power_settings_new</span>
    </Link>
  );
}
