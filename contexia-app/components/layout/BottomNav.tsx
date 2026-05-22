"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type NavItem = {
  path: string;
  icon: string;
  label: string;
};

const NAV_ITEMS: NavItem[] = [
  { path: "/app/overview", icon: "monitoring", label: "Pulso" },
  { path: "/app/fiscal", icon: "account_balance", label: "Fiscal" },
  { path: "/app/radar", icon: "insights", label: "Radar" },
  { path: "/app/config", icon: "settings", label: "Config" },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="md:hidden fixed bottom-0 w-full z-50 rounded-t-xl bg-surface-container/90 backdrop-blur-md border-t border-white/5 shadow-[0_-4px_24px_rgba(0,0,0,0.5)] flex justify-around items-center h-20 pb-safe px-4">
      {NAV_ITEMS.map((item) => {
        const isActive = pathname === item.path;
        return (
          <Link
            key={item.path}
            href={item.path}
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
