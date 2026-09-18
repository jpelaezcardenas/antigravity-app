"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { fetchTenantMe, type TenantMeSnapshot } from "@/lib/api-client";

// Note (superseded 2026-09-15 — see DesktopSidebar.tsx): removing the header's nav links
// assumed BottomNav already covered desktop navigation; it never did (BottomNav is
// `md:hidden`). DesktopSidebar.tsx now restores Pulso/Fiscal/Radar/Patrimonio/Config access on
// desktop as a real sidebar, not by reverting this header.

interface ClientTopBarProps {
  /** True only on the (shell) layout, which also renders <DesktopSidebar /> (w-56, fixed
   * left) — shifts this header's own centering container right by the same amount on desktop
   * so the badge stays centered in the content area next to the sidebar, not the full
   * viewport. flujo-detalle's layout has no sidebar, so it omits this and stays viewport-
   * centered. */
  sidebarOffset?: boolean;
}

/**
 * Branded header for the client app shell (/app/*) and detail screens.
 *
 * 2026-09-17 (PWA V2 pilot): promoted to a Client Component to read the
 * current pathname via `usePathname()` and suppress this header's own JARVIS
 * badge on the `-v2` pilot routes (overview-v2, fiscal-v2, radar-v2,
 * patrimonio-v2), which instead render JARVIS floating in the page content
 * per the Stitch-approved center composition. This does NOT reintroduce a
 * hydration mismatch: `usePathname()` resolves from the same URL on the
 * server and the client, so first-paint markup still matches. `JarvisBubble`
 * itself is a client child that renders null until its own effect resolves,
 * so it never diverges between server and first client paint either way.
 *
 * 2026-09-14 (design_handoff_jarvos_header_circle): a 3-column grid
 * (`left cluster / centered badge / right cluster`) replaces the old flex
 * layout — this is what makes the JARVIS badge sit at the true horizontal
 * center on BOTH breakpoints, instead of the previous per-breakpoint
 * absolute-position hack.
 *
 * The Taty WhatsApp card, the (unwired — no onClick) hamburger menu, and the
 * Contexia logo were removed earlier the same day — the header's only
 * identity mark used to be the JARVIS badge itself.
 *
 * 2026-09-15 (round 4, `sidebarOffset` layouts only): the desktop badge moved into
 * DesktopSidebar.tsx (below its nav items).
 *
 * 2026-09-18 (founder decision: V2 pilot retired as the migration target, V1 stays the
 * definitive PWA): every V1 screen this header covers (all of `(shell)` + flujo-detalle) gets
 * the same top row the -v2 pilots had — tenant name (left) / "+" / gear (right), same
 * destinations as V2 (`/conectar-datos-v2`, `/app/config`). BottomNav drops its own "Config"
 * tab everywhere now that the gear lives here.
 *
 * 2026-09-18 (same day, follow-up): the JARVIS badge that used to live INSIDE this fixed
 * header (mobile always, desktop on flujo-detalle only) is gone. Founder request, comparing
 * V1 against the -v2 pilots' own screenshots: "primero se vea el encabezado y despues jarvis,
 * para todas las pantallas" — V2 never put JARVIS in a sticky header at all, it's an in-flow
 * `JarvisFloatingBadgeV2` each page renders itself, right after that page's own header/hero
 * content, so it scrolls away with the rest of the page instead of staying pinned. V1's pages
 * (`overview`, `fiscal`, `radar`, `patrimonio`, `config`, `flujo-detalle`) now do the exact
 * same thing — this header is just the slim top row now, on every V1 screen, matching the
 * -v2 pilots' `isV2Pilot` branch structurally (this file just doesn't need a separate branch
 * for it anymore, since V1 no longer renders a badge here either).
 */
export function ClientTopBar({ sidebarOffset = false }: ClientTopBarProps) {
  const pathname = usePathname();
  const isV2Pilot = pathname?.endsWith("-v2") ?? false;
  const [tenant, setTenant] = useState<TenantMeSnapshot | null>(null);

  useEffect(() => {
    if (isV2Pilot) return;
    let cancelled = false;
    fetchTenantMe()
      .then((snapshot) => {
        if (!cancelled) setTenant(snapshot);
      })
      .catch(() => {
        // Fail silent — same "never alarm for identity" idiom as JarvisBubble/TenantInfoCard.
      });
    return () => {
      cancelled = true;
    };
  }, [isV2Pilot]);

  // 2026-09-18 (founder: "elimina ese header o espacio vacío arriba" — Stitch's mockup has
  // no header bar at all on -v2, content starts right at the top). Rendering nothing here
  // (not just an empty/collapsed bar) removes the border-bottom line and its own padding —
  // the page's own hero (PulsoHeroV2 etc.) now owns the top of the screen entirely.
  if (isV2Pilot) return null;

  const tenantLabel = tenant?.legal_name ?? "Contexia";

  return (
    <nav className="w-full border-b border-slate-800 bg-bg-obsidian/90 backdrop-blur-xl fixed top-0 z-50">
      <div
        className={`max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 ${sidebarOffset ? "md:pl-56" : ""}`}
      >
        <div className="flex items-center justify-between py-4 text-on-surface-variant">
          <span className="text-xs font-medium tracking-wide text-on-surface-variant/90">
            {tenantLabel}
          </span>
          <div className="flex items-center gap-4">
            <Link
              href="/conectar-datos-v2"
              aria-label="Conectar mis datos"
              className="hover:text-white transition-colors p-1 flex items-center justify-center"
            >
              <span className="material-symbols-outlined text-[21px]">add</span>
            </Link>
            <Link
              href="/app/config"
              aria-label="Configuración"
              className="hover:text-white transition-colors p-1 flex items-center justify-center"
            >
              <span className="material-symbols-outlined text-[20px]">settings</span>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
