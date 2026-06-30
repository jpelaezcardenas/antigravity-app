import { pulsoMock } from "@/lib/mock/pulso";
import { NoteOfDayCard } from "@/components/pulso/NoteOfDayCard";
import { CashTodayCard } from "@/components/pulso/CashTodayCard";
import { HealthQuadrant } from "@/components/pulso/HealthQuadrant";
import { ActiveAlerts } from "@/components/pulso/ActiveAlerts";
import { StructuralBreakdownCTA } from "@/components/pulso/StructuralBreakdownCTA";
import { FAB } from "@/components/layout/FAB";

export default function OverviewPage() {
  return (
    <>
      <div className="px-container-margin-mobile md:px-container-margin-desktop flex flex-col gap-6 max-w-4xl mx-auto w-full mt-2">
        <NoteOfDayCard note={pulsoMock.note} />
        <CashTodayCard cash={pulsoMock.cash} />
        <HealthQuadrant kpis={pulsoMock.health} />
        <StructuralBreakdownCTA />
        <ActiveAlerts alerts={pulsoMock.alerts} />
      </div>
      <FAB />
    </>
  );
}
