"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { JarvisBubble } from "@/components/jarvis/JarvisBubble";
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
 * DesktopSidebar.tsx (below its nav items) — there's no more DesktopSidebar-side content to
 * center on desktop, so this header shrinks to a slim bar there (`md:pt-4 md:min-h-0`) instead
 * of the tall one still sized for the badge. flujo-detalle's layout doesn't set
 * `sidebarOffset` (it has no sidebar to move the badge into), so it keeps the original
 * badge-in-header behavior on both breakpoints, unchanged.
 *
 * 2026-09-18 (founder decision: V2 pilot retired as the migration target, V1 stays the
 * definitive PWA): every V1 screen this header covers (all of `(shell)` + flujo-detalle) gets
 * the same top row the -v2 pilots had — tenant name (left) / "+" / gear (right), same
 * destinations as V2 (`/conectar-datos-v2`, `/app/config`). BottomNav drops its own "Config"
 * tab everywhere now that the gear lives here — one access point, matching V2's pattern.
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
        <div className="flex items-center justify-between pt-4 text-on-surface-variant">
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

        <div
          className={`grid grid-cols-[1fr_auto_1fr] items-start pt-10 pb-6 ${
            isV2Pilot ? "min-h-0 pt-4 pb-4" : "min-h-[220px]"
          } ${
            isV2Pilot || sidebarOffset
              ? "md:pt-4 md:pb-4 md:min-h-0"
              : "md:pt-12 md:min-h-[260px]"
          }`}
        >
          {/* Left cluster: intentionally empty — kept as a grid track (not removed) so the
              center column stays mathematically centered against the right cluster below. */}
          <div />

          {/* Center: the JARVIS badge on mobile always; on desktop only when this header is
              still the badge's home (sidebarOffset false, i.e. flujo-detalle). 2026-09-15
              (founder request, round 2): the header itself grew (152/168 → 220/260px) to give
              the badge more room — 96/120 → 128/156. Switched from `items-center` to
              `items-start` + explicit pt (founder feedback: centering put the badge's own
              decorative rings — which extend ~20-25px past its box via overflow-visible —
              right up against the header's top border). Everything below the header (main
              content, via its own pt-*) shifts down to match; see the shell layouts that
              render <ClientTopBar />.
              2026-09-17: skipped entirely on `-v2` pilot routes — those render JARVIS floating
              in the page content instead (see JarvisFloatingBadgeV2).
              2026-09-18: `hideLabel` — this header's own top row (added the same day) already
              shows the tenant name, so JarvisBubble's own company-name label underneath would
              just repeat it, same reasoning as JarvisFloatingBadgeV2 on the -v2 pilots. */}
          {!isV2Pilot && (
            <div className="col-start-2 justify-self-center">
              <div className="md:hidden">
                <JarvisBubble size={128} hideLabel />
              </div>
              {!sidebarOffset && (
                <div className="hidden md:block">
                  <JarvisBubble size={156} hideLabel />
                </div>
              )}
            </div>
          )}

          {/* Right cluster: intentionally empty — the logout affordance moved out of the header
              entirely on 2026-09-15 (first to a text SignOutFooter, later replaced by
              FloatingSignOutButton's power icon — see that component). Kept as a grid track
              (not removed) for the same centering reason as the left one. */}
          <div />
        </div>
      </div>
    </nav>
  );
}
