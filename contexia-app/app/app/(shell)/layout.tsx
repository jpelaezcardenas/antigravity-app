"use client";

import type { ReactNode } from "react";
import { usePathname } from "next/navigation";
import { ClientTopBar } from "@/components/layout/ClientTopBar";
import { BottomNav } from "@/components/layout/BottomNav";
import { DesktopSidebar } from "@/components/layout/DesktopSidebar";
import { FloatingSignOutButton } from "@/components/layout/FloatingSignOutButton";

// Jarvis lives in the header on mobile, DesktopSidebar on desktop (2026-09-15, round 4 —
// see DesktopSidebar.tsx) — no separate floating bubble here.
export default function AppShellLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isV2Pilot = pathname?.endsWith("-v2") ?? false;

  return (
    <div className="min-h-screen flex flex-col bg-bg-obsidian">
      <ClientTopBar sidebarOffset />
      <DesktopSidebar />
      {/* md:pl-56 — DesktopSidebar (w-56) is fixed/left, content must not render underneath
          it; BottomNav covers mobile, DesktopSidebar is desktop's nav.
          2026-09-18: pt shrunk from 260px/8 to 20/8 — ClientTopBar no longer hosts the JARVIS
          badge (moved in-flow, see each page's own JarvisFloatingBadgeV2), so on V1 it's now
          just the slim tenant-name/+/gear row, not the tall badge header. On `-v2` pilot
          routes ClientTopBar renders nothing at all, so main needs only safe-area breathing
          room (founder: "elimina ese header o espacio vacío arriba"). */}
      <main
        className={`flex-1 pb-24 md:pb-8 md:pl-56 ${
          isV2Pilot ? "pt-4 md:pt-4" : "pt-20 md:pt-8"
        }`}
      >
        {children}
      </main>
      <FloatingSignOutButton />
      <BottomNav />
    </div>
  );
}
