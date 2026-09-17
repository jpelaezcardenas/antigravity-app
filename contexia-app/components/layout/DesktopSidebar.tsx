"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { JarvisBubble } from "@/components/jarvis/JarvisBubble";

// Desktop-only navigation (2026-09-15) — restores access to every main screen on desktop.
// BottomNav (components/layout/BottomNav.tsx) is `md:hidden`, and the header's own nav links
// were removed earlier this session ("estas opciones elimínalas de arriba, solo quedan en la
// parte de abajo") on the assumption BottomNav already covered both breakpoints — it never
// did. This sidebar is the desktop equivalent of BottomNav, not a duplicate of the old header
// links: same 5 destinations (Patrimonio included on both since 2026-09-15 — the founder
// noticed the mobile/desktop mismatch when Patrimonio was sidebar-only).
//
// 2026-09-15 (round 4): also hosts the JARVIS badge itself, moved out of ClientTopBar's
// desktop header (founder request — one access point, not a second one with a new name/icon
// to invent: "usa el mismo badge... no crees otro acceso"). Same JarvisBubble component, just
// smaller (96 vs the header's 156) and placed right below the nav items — the header on this
// layout shrinks to a slim bar accordingly (see ClientTopBar's `sidebarOffset` branch).
type NavItem = {
  path: string;
  icon: string;
  label: string;
};

const NAV_ITEMS: NavItem[] = [
  { path: "/app/overview", icon: "monitoring", label: "Pulso" },
  { path: "/app/fiscal", icon: "account_balance", label: "Fiscal" },
  { path: "/app/radar", icon: "insights", label: "Radar" },
  { path: "/app/patrimonio", icon: "account_balance_wallet", label: "Patrimonio" },
  { path: "/app/config", icon: "settings", label: "Config" },
];

export function DesktopSidebar() {
  const pathname = usePathname();
  const isV2Pilot = pathname?.endsWith("-v2") ?? false;

  return (
    <nav className="hidden md:flex fixed left-0 top-0 bottom-0 z-40 w-56 flex-col border-r border-slate-800 bg-bg-obsidian/90 backdrop-blur-xl">
      {/* Top padding matches ClientTopBar's now-slim rendered height on this layout
          (sidebarOffset shrinks it to md:pt-4/md:pb-4 once the badge moves down here) so links
          start just below it, not underneath it. */}
      <div className="flex flex-col gap-1 pt-16 px-3">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.path;
          return (
            <Link
              key={item.path}
              href={item.path}
              className={`flex items-center gap-3 rounded-xl px-4 py-3 transition-all ${
                isActive
                  ? "text-primary-fixed-dim font-bold bg-primary/10"
                  : "text-on-surface-variant opacity-70 hover:bg-surface-variant/20 hover:opacity-100"
              }`}
            >
              <span className={`material-symbols-outlined ${isActive ? "icon-fill" : ""}`}>
                {item.icon}
              </span>
              <span className="font-label-caps text-label-caps">{item.label}</span>
            </Link>
          );
        })}
      </div>

      {/* JARVIS — moved here from the header (round 4). Sits right below the nav items, not
          pinned to the sidebar's bottom edge (viewport height varies; anchoring to the option
          list itself is the stable reference point the founder asked for).
          2026-09-17: skipped on `-v2` pilot routes, which render JARVIS floating in the page
          content instead (see JarvisFloatingBadgeV2) — avoids a second access point while both
          coexist. */}
      {!isV2Pilot && (
        <div className="flex justify-center pt-6 border-t border-slate-800/60 mx-3 mt-4">
          <JarvisBubble size={96} panelAnchor="sidebar" />
        </div>
      )}
    </nav>
  );
}
