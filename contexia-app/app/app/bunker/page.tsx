"use client";

import { useState } from "react";
import { BunkerSidebar, type BunkerSection } from "@/components/bunker/BunkerSidebar";
import { InfrastructureDashboard } from "@/components/bunker/InfrastructureDashboard";
import { CrmVentasSection } from "@/components/bunker/CrmVentasSection";
import { ComingSoonSection } from "@/components/bunker/ComingSoonSection";
import { SocialContentOpsSection } from "@/components/bunker/social-ops/SocialContentOpsSection";
import { OnboardingSection } from "@/components/bunker/onboarding/OnboardingSection";
import { SellMachineSection } from "@/components/bunker/sell-machine/SellMachineSection";

const PLACEHOLDER_LABELS: Partial<Record<BunkerSection, string>> = {
  "agentic-os": "Agentic OS",
  configuracion: "Configuración",
};

const PLACEHOLDER_SECTIONS: BunkerSection[] = ["agentic-os", "configuracion"];

export default function BunkerPage() {
  const [activeSection, setActiveSection] = useState<BunkerSection>("dashboard");

  return (
    <div className="min-h-screen bg-bg-obsidian text-on-surface flex">
      <BunkerSidebar activeSection={activeSection} onSelect={setActiveSection} />

      <div className="flex-1 flex flex-col min-w-0">
        <header className="sticky top-0 z-40 bg-surface/80 backdrop-blur-xl border-b border-outline-variant/10 shadow-[0_0_20px_rgba(45,212,191,0.05)] flex justify-between items-center px-container-margin-mobile md:px-container-margin-desktop h-touch-target-min">
          <h1 className="font-headline-lg-mobile text-headline-lg-mobile md:font-headline-lg md:text-headline-lg font-bold text-primary-container flex items-center">
            Bunker Contexia
          </h1>
          <button
            type="button"
            onClick={() => {
              localStorage.removeItem("token");
              localStorage.removeItem("cx_user");
              location.href = "/login";
            }}
            className="px-4 py-2 text-on-surface-variant hover:text-on-surface text-sm font-medium transition-colors"
          >
            Cerrar Sesión
          </button>
        </header>

        <main className="flex-1 pb-24 md:pb-8">
          <div className="px-container-margin-mobile md:px-container-margin-desktop max-w-6xl mx-auto w-full mt-6">
            {activeSection === "dashboard" && <InfrastructureDashboard />}
            {activeSection === "crm-ventas" && <CrmVentasSection />}
            {activeSection === "social-content-ops" && <SocialContentOpsSection />}
            {activeSection === "onboarding" && <OnboardingSection />}
            {activeSection === "sell-machine" && <SellMachineSection />}
            {PLACEHOLDER_SECTIONS.includes(activeSection) && (
              <ComingSoonSection label={PLACEHOLDER_LABELS[activeSection] ?? ""} />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
