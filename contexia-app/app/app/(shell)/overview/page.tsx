import { pulsoMock } from "@/lib/mock/pulso";
import { NoteOfDayCard } from "@/components/pulso/NoteOfDayCard";
import { CashTodayCard } from "@/components/pulso/CashTodayCard";
import { HealthQuadrant } from "@/components/pulso/HealthQuadrant";
import { ActiveAlerts } from "@/components/pulso/ActiveAlerts";
import { StructuralBreakdownCTA } from "@/components/pulso/StructuralBreakdownCTA";
import { JarvisFloatingBadgeV2 } from "@/components/jarvis/v2/JarvisFloatingBadgeV2";

// DataUploadCard (2026-09-18): no longer rendered inline here — the founder confirmed
// "Conectar mis datos" should ONLY be reachable via the "+" ClientTopBar now shows on every
// V1 screen (routes to /conectar-datos-v2), same single-access-point rule V2 already had.
export default function OverviewPage() {
  return (
    <div className="px-container-margin-mobile md:px-container-margin-desktop flex flex-col gap-6 max-w-4xl mx-auto w-full mt-2">
      <NoteOfDayCard note={pulsoMock.note} />
      <CashTodayCard />
      {/* JARVIS (2026-09-18): moved here, in-flow, from ClientTopBar's now-removed fixed-header
          badge — founder request, matching the -v2 pilots' own order (header, then this page's
          own hero/cash content, THEN JARVIS, scrolling away with the rest of the page instead
          of staying pinned). Same component every -v2 page already used. Mobile-only
          (`md:hidden`) — DesktopSidebar already hosts the single desktop access point on this
          `(shell)` layout; without this, desktop would get JARVIS twice. */}
      <div className="md:hidden">
        <JarvisFloatingBadgeV2 />
      </div>
      <HealthQuadrant kpis={pulsoMock.health} />
      <StructuralBreakdownCTA />
      <ActiveAlerts />
      {/* The floating mobile-only "Salir" button that used to live here (fixed bottom-24
          right-4, md:hidden) was removed 2026-09-15 — logout is FloatingSignOutButton's
          power icon everywhere now (rendered by the shell layout, both breakpoints). */}
    </div>
  );
}
