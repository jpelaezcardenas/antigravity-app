"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { toV2Path, useV2Preview } from "@/lib/v2-preview";

type NavItem = {
  path: string;
  icon: string;
  label: string;
};

// Patrimonio added 2026-09-15 — DesktopSidebar.tsx (desktop's equivalent of this nav) already
// has 5 items; mobile only had 4, and the founder noticed the mismatch ("no vi todas las
// opciones en la parte inferior"). Same route as the sidebar's, same icon.
const NAV_ITEMS: NavItem[] = [
  { path: "/app/overview", icon: "monitoring", label: "Pulso" },
  { path: "/app/fiscal", icon: "account_balance", label: "Fiscal" },
  { path: "/app/radar", icon: "insights", label: "Radar" },
  { path: "/app/patrimonio", icon: "account_balance_wallet", label: "Patrimonio" },
  { path: "/app/config", icon: "settings", label: "Config" },
];

export function BottomNav() {
  const pathname = usePathname();
  const v2Preview = useV2Preview();

  // Pulso-v2's own hero already has a gear icon -> /app/config (Stitch mockup's header
  // affordance) — founder caught the duplicate ("dos botones que llevan a lo mismo") when
  // both it and this bar's own "Config" tab were visible at once. Only overview-v2 has that
  // header gear (fiscal-v2/radar-v2/patrimonio-v2 don't), so this drops the tab there only —
  // dropping it from every -v2 route would leave those three pages with no way to reach
  // Config at all.
  const items = pathname === "/app/overview-v2" ? NAV_ITEMS.filter((i) => i.path !== "/app/config") : NAV_ITEMS;

  return (
    <nav className="md:hidden fixed bottom-0 w-full z-50 rounded-t-xl bg-surface-container/90 backdrop-blur-md border-t border-white/5 shadow-[0_-4px_24px_rgba(0,0,0,0.5)] flex justify-around items-center h-20 pb-safe px-4">
      {items.map((item) => {
        const href = toV2Path(item.path, v2Preview);
        const isActive = pathname === href;
        return (
          <Link
            key={item.path}
            href={href}
            className={`flex flex-col items-center justify-center h-full w-full rounded-xl transition-all ${
              isActive
                ? "text-primary-fixed-dim font-bold bg-primary/10 scale-90"
                : "text-on-surface-variant opacity-60 hover:bg-surface-variant/20"
            }`}
          >
            <span
              className={`material-symbols-outlined mb-1 ${
                isActive ? "icon-fill" : ""
              }`}
            >
              {item.icon}
            </span>
            <span className="font-label-caps text-label-caps">
              {item.label}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
