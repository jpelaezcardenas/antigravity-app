"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/app/overview", label: "Pulso", icon: "📊" },
  { href: "/app/fiscal", label: "Fiscal", icon: "📋" },
  { href: "/app/radar", label: "Radar", icon: "🎯" },
  { href: "/app/patrimonio", label: "Patrimonio", icon: "💰" },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 md:relative bg-surface border-t border-outline-variant/10 px-container-margin-mobile md:px-container-margin-desktop">
      <div className="max-w-7xl mx-auto flex gap-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center justify-center gap-1 flex-1 h-touch-target-min text-center transition-all rounded-t-lg md:rounded-lg ${
                isActive
                  ? "bg-primary/10 border-t-2 border-primary md:border-t-0 md:bg-primary/20"
                  : "hover:bg-surface-variant/30"
              }`}
            >
              <span className="text-lg">{item.icon}</span>
              <span
                className={`font-label-caps text-label-caps text-xs line-clamp-1 ${
                  isActive ? "text-primary-container font-bold" : "text-on-surface-variant"
                }`}
              >
                {item.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
