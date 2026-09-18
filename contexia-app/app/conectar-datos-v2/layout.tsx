import { ClientTopBar } from "@/components/layout/ClientTopBar";
import { FloatingSignOutButton } from "@/components/layout/FloatingSignOutButton";

/**
 * Same shape as flujo-detalle-v2/layout.tsx — a "detail screen" outside the
 * (shell) route group: no BottomNav, browser back to return. ClientTopBar
 * renders null on this `-v2` path (see its own isV2Pilot check), same as
 * every other -v2 route.
 */
export default function ConectarDatosV2Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="bg-bg-obsidian text-on-surface min-h-screen flex flex-col">
      <ClientTopBar />
      <main className="flex-1 pt-[100px] md:pt-[120px]">{children}</main>
      <FloatingSignOutButton />
    </div>
  );
}
