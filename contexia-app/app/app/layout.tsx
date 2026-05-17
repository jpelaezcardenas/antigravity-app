import type { ReactNode } from "react";
import { TopBar } from "@/components/layout/TopBar";
import { BottomNav } from "@/components/layout/BottomNav";

export default function AppShellLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <TopBar />
      <main className="flex-1 pt-[80px] pb-24 md:pb-8">{children}</main>
      <BottomNav />
    </div>
  );
}
