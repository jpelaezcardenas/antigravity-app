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
      {/* Mobile pt (260px) matches ClientTopBar's tall mobile header (badge stays there, see
          ClientTopBar's comment) — unchanged since round 3. Desktop pt (round 4, tuned twice:
          24 then 8) matches DesktopSidebar's own pt-16 for its first nav link — founder
          feedback: the two columns' text should start at the same height, not just "close to
          the top". md:pl-56 — DesktopSidebar (w-56) is fixed/left, content must not render
          underneath it; BottomNav covers mobile, DesktopSidebar is desktop's nav.
          2026-09-18: this was hardcoded regardless of route — on `-v2` pilot routes
          ClientTopBar now renders nothing at all (see its own comment), so main needs only
          safe-area breathing room, not the 260px reserved for V1's tall badge header
          (founder: "elimina ese header o espacio vacío arriba" — Stitch's mockup has the
          hero content start right at the top of the screen). */}
      <main
        className={`flex-1 pb-24 md:pb-8 md:pl-56 ${
          isV2Pilot ? "pt-4 md:pt-4" : "pt-[260px] md:pt-8"
        }`}
      >
        {children}
      </main>
      <FloatingSignOutButton />
      <BottomNav />
    </div>
  );
}
