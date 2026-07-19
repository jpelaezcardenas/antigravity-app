"use client";

import { useState } from "react";
import { B2bRetainersTab } from "./crm/B2bRetainersTab";

type CrmTab = "b2b" | "b2c";

const TABS: { id: CrmTab; label: string }[] = [
  { id: "b2b", label: "B2B / Retainers" },
  { id: "b2c", label: "B2C / Renta Natural" },
];

export function CrmVentasSection() {
  const [activeTab, setActiveTab] = useState<CrmTab>("b2b");

  return (
    <div className="w-full">
      <section className="mb-6">
        <h2 className="font-headline-lg text-headline-lg text-primary-container mb-2">
          CRM / Ventas
        </h2>
        <p className="text-on-surface-variant text-body-md">
          Gestión centralizada de clientes B2B y del embudo B2C de Renta Natural
        </p>
      </section>

      <div className="mb-6 flex gap-1 overflow-x-auto rounded-2xl border border-outline-variant/20 bg-white/5 p-1.5">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`min-w-40 flex-1 rounded-xl px-4 py-2 text-sm font-semibold transition ${
              activeTab === tab.id
                ? "bg-primary/15 text-primary-container ring-1 ring-primary/30"
                : "text-on-surface-variant hover:bg-white/5 hover:text-on-surface"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "b2b" && <B2bRetainersTab />}
      {activeTab === "b2c" && (
        <div className="rounded-xl border border-outline-variant/30 bg-surface-container p-6 text-on-surface-variant">
          Próximamente: embudo Kanban de Renta Natural 2026.
        </div>
      )}
    </div>
  );
}
