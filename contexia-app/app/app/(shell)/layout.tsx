import type { ReactNode } from "react";
import { ClientTopBar } from "@/components/layout/ClientTopBar";
import { BottomNav } from "@/components/layout/BottomNav";

// Jarvis lives in ClientTopBar's header now (2026-09-14, founder request) —
// no separate floating bubble here anymore.
export default function AppShellLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-bg-obsidian">
      <ClientTopBar />
      <main className="flex-1 pt-[150px] md:pt-[140px] pb-24 md:pb-8">{children}</main>
      <BottomNav />
    </div>
  );
}
