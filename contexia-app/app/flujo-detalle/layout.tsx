import { ClientTopBar } from "@/components/layout/ClientTopBar";

export default function FlujoDetalleLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="bg-background text-on-surface min-h-screen flex flex-col">
      <ClientTopBar />
      <main className="flex-1 pt-[150px] md:pt-[140px]">{children}</main>
    </div>
  );
}
