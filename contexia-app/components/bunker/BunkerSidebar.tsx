"use client";

export type BunkerSection =
  | "dashboard"
  | "crm-ventas"
  | "onboarding"
  | "social-content-ops"
  | "agentic-os"
  | "configuracion";

const NAV_ITEMS: { id: BunkerSection; label: string }[] = [
  { id: "dashboard", label: "Dashboard" },
  { id: "crm-ventas", label: "CRM / Ventas" },
  { id: "onboarding", label: "Onboarding" },
  { id: "social-content-ops", label: "Social Content Ops" },
  { id: "agentic-os", label: "Agentic OS" },
  { id: "configuracion", label: "Configuración" },
];

export function BunkerSidebar({
  activeSection,
  onSelect,
}: {
  activeSection: BunkerSection;
  onSelect: (section: BunkerSection) => void;
}) {
  return (
    <aside className="w-64 shrink-0 bg-surface-container border-r border-outline-variant/20 flex flex-col h-screen sticky top-0">
      <div className="flex items-center gap-3 px-6 py-6">
        <div className="w-9 h-9 rounded-md bg-primary/10 border border-primary/30 flex items-center justify-center shrink-0">
          <span className="font-headline-lg text-title-md text-primary-container font-bold">
            C
          </span>
        </div>
        <div>
          <div className="font-title-md text-body-md text-on-surface font-bold leading-tight">
            Admin
          </div>
          <div className="font-label-caps text-label-caps text-on-surface-variant tracking-wide">
            CONTEXIA
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3 flex flex-col gap-1">
        {NAV_ITEMS.map((item) => {
          const isActive = item.id === activeSection;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelect(item.id)}
              className={`text-left px-4 py-2.5 rounded-full font-body-md text-body-md transition-colors ${
                isActive
                  ? "bg-primary/15 text-primary-container font-semibold"
                  : "text-on-surface-variant hover:text-on-surface hover:bg-white/5"
              }`}
              aria-current={isActive ? "page" : undefined}
            >
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="px-6 py-4">
        <p className="font-label-caps text-label-caps text-on-surface-variant/60 tracking-wide">
          POWERED BY CONTEXIA
        </p>
      </div>
    </aside>
  );
}
