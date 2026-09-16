import { ClientTopBar } from "@/components/layout/ClientTopBar";
import { FloatingSignOutButton } from "@/components/layout/FloatingSignOutButton";

export default function FlujoDetalleLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="bg-bg-obsidian text-on-surface min-h-screen flex flex-col">
      <ClientTopBar />
      {/* pt bumped 2026-09-15 (three times — see the shell layout's comment) to match
          ClientTopBar's current rendered height. */}
      <main className="flex-1 pt-[260px] md:pt-[300px]">{children}</main>
      <FloatingSignOutButton />
    </div>
  );
}
