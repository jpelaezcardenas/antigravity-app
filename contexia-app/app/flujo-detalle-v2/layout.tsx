import { ClientTopBar } from "@/components/layout/ClientTopBar";
import { FloatingSignOutButton } from "@/components/layout/FloatingSignOutButton";

export default function FlujoDetalleV2Layout({
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
