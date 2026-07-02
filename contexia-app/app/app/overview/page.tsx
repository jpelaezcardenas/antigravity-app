import { pulsoMock } from "@/lib/mock/pulso";
import { NoteOfDayCard } from "@/components/pulso/NoteOfDayCard";
import { CashTodayCard } from "@/components/pulso/CashTodayCard";
import { HealthQuadrant } from "@/components/pulso/HealthQuadrant";
import { ActiveAlerts } from "@/components/pulso/ActiveAlerts";
import { StructuralBreakdownCTA } from "@/components/pulso/StructuralBreakdownCTA";

export default function OverviewPage() {
  return (
    <>
      <div className="px-container-margin-mobile md:px-container-margin-desktop flex flex-col gap-6 max-w-4xl mx-auto w-full mt-2">
        <NoteOfDayCard note={pulsoMock.note} />
        <CashTodayCard />
        <HealthQuadrant kpis={pulsoMock.health} />
        <StructuralBreakdownCTA />
        <ActiveAlerts alerts={pulsoMock.alerts} />
      </div>
      {/* Mobile logout: the desktop "Cerrar Sesión" button is hidden below md */}
      <a
        href="/logout"
        className="fixed bottom-24 right-4 z-50 inline-flex items-center gap-2 rounded-full border border-[#2DD4BF]/40 bg-[#020617]/90 px-4 py-2 text-[12px] font-bold text-[#2DD4BF] shadow-[0_0_20px_rgba(45,212,191,0.25)] backdrop-blur md:hidden"
      >
        Salir
      </a>
    </>
  );
}
