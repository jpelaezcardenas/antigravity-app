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
      {/* pt shrunk 2026-09-18 — ClientTopBar no longer hosts the JARVIS badge here either
          (moved in-flow, see the page's own JarvisFloatingBadgeV2); it's just the slim
          tenant-name/+/gear row now, same height on both breakpoints. */}
      <main className="flex-1 pt-20">{children}</main>
      <FloatingSignOutButton />
    </div>
  );
}
