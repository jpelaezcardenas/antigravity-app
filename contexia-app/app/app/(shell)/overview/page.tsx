import { pulsoMock } from "@/lib/mock/pulso";
import { NoteOfDayCard } from "@/components/pulso/NoteOfDayCard";
import { CashTodayCard } from "@/components/pulso/CashTodayCard";
import { DataUploadCard } from "@/components/pulso/DataUploadCard";
import { HealthQuadrant } from "@/components/pulso/HealthQuadrant";
import { ActiveAlerts } from "@/components/pulso/ActiveAlerts";
import { StructuralBreakdownCTA } from "@/components/pulso/StructuralBreakdownCTA";

export default function OverviewPage() {
  return (
    <div className="px-container-margin-mobile md:px-container-margin-desktop flex flex-col gap-6 max-w-4xl mx-auto w-full mt-2">
      <NoteOfDayCard note={pulsoMock.note} />
      <CashTodayCard />
      <DataUploadCard />
      <HealthQuadrant kpis={pulsoMock.health} />
      <StructuralBreakdownCTA />
      <ActiveAlerts />
      {/* The floating mobile-only "Salir" button that used to live here (fixed bottom-24
          right-4, md:hidden) was removed 2026-09-15 — logout is FloatingSignOutButton's
          power icon everywhere now (rendered by the shell layout, both breakpoints). */}
    </div>
  );
}
