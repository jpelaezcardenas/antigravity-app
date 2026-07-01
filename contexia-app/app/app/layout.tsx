import type { ReactNode } from "react";
import { ClientTopBar } from "@/components/layout/ClientTopBar";
import { BottomNav } from "@/components/layout/BottomNav";

export default function AppShellLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: "#020617" }}>
      <ClientTopBar />
      <main className="flex-1 pt-[150px] md:pt-[140px] pb-24 md:pb-8">{children}</main>
      <BottomNav />
    </div>
  );
}
