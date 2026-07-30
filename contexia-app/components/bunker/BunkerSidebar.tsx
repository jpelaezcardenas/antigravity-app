"use client";

export type BunkerSection =
  | "dashboard"
  | "crm-ventas"
  | "onboarding"
  | "social-content-ops"
  | "sell-machine"
  | "agentic-os"
  | "configuracion";

const NAV_ITEMS: { id: BunkerSection; label: string }[] = [
  { id: "dashboard", label: "Dashboard" },
  { id: "crm-ventas", label: "CRM / Ventas" },
  { id: "onboarding", label: "Onboarding" },
  { id: "social-content-ops", label: "Social Content Ops" },
  { id: "sell-machine", label: "Sell Machine" },
  { id: "agentic-os", label: "Agentic OS" },
  { id: "configuracion", label: "Configuración" },
];

const ADMIN_ONLY_SECTIONS: BunkerSection[] = [
  "crm-ventas",
  "social-content-ops",
  "onboarding",
  "sell-machine",
];

export function BunkerSidebar({
  activeSection,
  onSelect,
  isAdmin = false,
}: {
  activeSection: BunkerSection;
  onSelect: (section: BunkerSection) => void;
  isAdmin?: boolean;
}) {
  const visibleItems = isAdmin
    ? NAV_ITEMS
    : NAV_ITEMS.filter((item) => !ADMIN_ONLY_SECTIONS.includes(item.id));

  return (
    <aside className="hidden lg:flex w-72 border-r border-outline-variant/40 bg-surface/60 backdrop-blur-xl flex-col h-screen sticky top-0 p-6">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-xl bg-primary/15 border border-primary/25 grid place-items-center glow-teal-soft">
          <span className="font-headline-lg text-title-md text-primary font-bold">
            C
          </span>
        </div>
        <div>
          <p className="text-sm font-bold tracking-wide text-gradient">
            Admin
          </p>
          <p className="text-[10px] uppercase tracking-[0.2em] text-on-surface-variant">
            CONTEXIA
          </p>
        </div>
      </div>

      <nav className="flex-1 flex flex-col gap-1">
        {visibleItems.map((item) => {
          const isActive = item.id === activeSection;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelect(item.id)}
              className={`w-full text-left px-4 py-3 rounded-xl border transition ${
                isActive
                  ? "border-primary/30 bg-primary/10 text-primary glow-teal-soft"
                  : "border-transparent hover:border-outline-variant/40 hover:bg-white/5 text-on-surface-variant"
              }`}
              aria-current={isActive ? "page" : undefined}
            >
              <span className="text-sm font-semibold">{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="mt-auto pt-6 text-[10px] uppercase tracking-[0.2em] text-outline-variant">
        Powered by Contexia
      </div>
    </aside>
  );
}
