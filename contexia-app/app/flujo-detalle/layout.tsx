import { TopBar } from "@/components/layout/TopBar";

export default function FlujoDetalleLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="bg-bg-obsidian text-on-surface min-h-screen flex flex-col">
      <TopBar />
      <main className="flex-1 pt-24">{children}</main>
    </div>
  );
}
