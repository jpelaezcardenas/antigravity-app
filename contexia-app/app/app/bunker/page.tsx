"use client";

import { useState, useEffect } from "react";
import { BunkerSidebar, type BunkerSection } from "@/components/bunker/BunkerSidebar";
import { InfrastructureDashboard } from "@/components/bunker/InfrastructureDashboard";
import { CrmVentasSection } from "@/components/bunker/CrmVentasSection";
import { ComingSoonSection } from "@/components/bunker/ComingSoonSection";
import { SocialContentOpsSection } from "@/components/bunker/social-ops/SocialContentOpsSection";
import { OnboardingSection } from "@/components/bunker/onboarding/OnboardingSection";
import { SellMachineSection } from "@/components/bunker/sell-machine/SellMachineSection";
import { MetricsDashboardSection } from "@/components/bunker/metrics/MetricsDashboardSection";
import { AgenticOsSection } from "@/components/bunker/agentic-os/AgenticOsSection";

const PLACEHOLDER_LABELS: Partial<Record<BunkerSection, string>> = {
  "agentic-os": "Agentic OS",
  configuracion: "Configuración",
};

const PLACEHOLDER_SECTIONS: BunkerSection[] = ["configuracion"];

const ADMIN_ROLES = ["admin", "superadmin", "contexia_admin"];

const ADMIN_ONLY_SECTIONS: BunkerSection[] = [
  "crm-ventas",
  "social-content-ops",
  "onboarding",
  "sell-machine",
];

function readRoleFromJwt(): string {
  if (typeof document === "undefined") return "";
  const match = document.cookie
    .split("; ")
    .find((c) => c.startsWith("sb-access-token="));
  if (!match) return "";
  const token = match.split("=").slice(1).join("=");
  const parts = token.split(".");
  if (parts.length !== 3) return "";
  try {
    const payload = JSON.parse(atob(parts[1].replace(/-/g, "+").replace(/_/g, "/")));
    const appMeta = payload.app_metadata ?? {};
    const userMeta = payload.user_metadata ?? {};
    return String(
      appMeta.role ?? appMeta.account_role ?? userMeta.role ?? userMeta.account_role ?? ""
    ).toLowerCase();
  } catch {
    return "";
  }
}

export default function BunkerPage() {
  const [activeSection, setActiveSection] = useState<BunkerSection>("dashboard");
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    const role = readRoleFromJwt();
    setIsAdmin(ADMIN_ROLES.includes(role));
  }, []);

  function handleSelectSection(section: BunkerSection) {
    if (!isAdmin && ADMIN_ONLY_SECTIONS.includes(section)) {
      setActiveSection("dashboard");
      return;
    }
    setActiveSection(section);
  }

  return (
    <div
      className="min-h-screen bg-bg-obsidian text-on-surface flex"
      style={{
        backgroundImage: [
          "radial-gradient(1200px 600px at 12% -10%, rgba(45,212,191,0.10), transparent 60%)",
          "radial-gradient(1000px 520px at 100% 0%, rgba(139,92,246,0.10), transparent 55%)",
          "radial-gradient(900px 700px at 50% 120%, rgba(20,184,166,0.06), transparent 60%)",
        ].join(", "),
        backgroundAttachment: "fixed",
      }}
    >
      <BunkerSidebar
        activeSection={activeSection}
        onSelect={handleSelectSection}
        isAdmin={isAdmin}
      />

      <div className="flex-1 flex flex-col min-w-0">
        <header className="sticky top-0 z-40 bg-surface/80 backdrop-blur-xl border-b border-outline-variant/10 shadow-[0_0_20px_rgba(45,212,191,0.05)] flex justify-between items-center px-4 lg:px-8 h-16 lg:h-20">
          <h1 className="font-headline-lg text-headline-lg-mobile md:text-headline-lg font-bold text-gradient flex items-center">
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
          <div className="px-4 lg:px-8 max-w-6xl mx-auto w-full mt-6">
            {activeSection === "dashboard" && (
              <div className="flex flex-col gap-10">
                <InfrastructureDashboard />
                <MetricsDashboardSection />
              </div>
            )}
            {activeSection === "crm-ventas" && <CrmVentasSection />}
            {activeSection === "social-content-ops" && <SocialContentOpsSection />}
            {activeSection === "onboarding" && <OnboardingSection />}
            {activeSection === "sell-machine" && <SellMachineSection />}
            {activeSection === "agentic-os" && <AgenticOsSection />}
            {PLACEHOLDER_SECTIONS.includes(activeSection) && (
              <ComingSoonSection label={PLACEHOLDER_LABELS[activeSection] ?? ""} />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
