import React from 'react';

export type AdminNavId = 'dashboard' | 'campaign' | 'content' | 'calendar' | 'editor' | 'operations' | 'config' | 'onboarding';

export default function AdminShell(props: {
  active: AdminNavId;
  onNavigate: (id: AdminNavId) => void;
  userEmail?: string;
  roleLabel?: string;
  children: React.ReactNode;
}) {
  const { active, onNavigate, userEmail = 'contexia.marketing@gmail.com', roleLabel = 'Administrador', children } = props;

  const nav: Array<{ id: AdminNavId; label: string }> = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'campaign', label: 'Campaña' },
    { id: 'content', label: 'Contenido' },
    { id: 'calendar', label: 'Calendario' },
    { id: 'editor', label: 'Editor' },
    { id: 'operations', label: 'Operaciones' },
    { id: 'config', label: 'Configuración' },
  ];

  const sidebar: Array<{ id: AdminNavId | 'crm' | 'onboarding' | 'social'; label: string }> = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'crm', label: 'CRM / Ventas' },
    { id: 'onboarding', label: 'Onboarding' },
    { id: 'social', label: 'Social Content Ops' },
    { id: 'config', label: 'Configuración' },
  ];

  return (
    <div className="min-h-screen text-ink flex">
      <aside className="hidden lg:flex w-72 border-r border-outline/40 bg-surface/60 backdrop-blur-xl flex-col p-6">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-primary/15 border border-primary/25 grid place-items-center glow-teal-soft">
            <span className="text-primary font-display font-bold">C</span>
          </div>
          <div>
            <p className="text-sm font-headline font-bold tracking-wide text-gradient">Admin</p>
            <p className="text-[10px] uppercase tracking-[0.2em] text-muted">Contexia</p>
          </div>
        </div>

        <nav className="space-y-2">
          {sidebar.map((item) => {
            const isActive = (item.id === 'social' && active === 'operations') || item.id === active;
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id === 'social' ? 'operations' : (item.id as AdminNavId))}
                className={`w-full text-left px-4 py-3 rounded-xl border transition ${
                  isActive
                    ? 'border-primary/30 bg-primary/10 text-primary glow-teal-soft'
                    : 'border-transparent hover:border-outline/40 hover:bg-white/5 text-muted'
                }`}
              >
                <span className="text-sm font-semibold">{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="mt-auto pt-6 text-[10px] uppercase tracking-[0.2em] text-outline">
          Powered by Contexia
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 lg:h-20 border-b border-outline/40 bg-surface/50 backdrop-blur-md flex items-center justify-between px-4 lg:px-8 sticky top-0 z-20">
          <div className="flex items-center gap-3 min-w-0">
            <div className="relative w-64 lg:w-96 max-w-full">
              <input
                type="text"
                placeholder="Buscar..."
                className="w-full bg-surface/50 border border-outline/40 rounded-xl py-2.5 pl-4 pr-4 text-sm text-ink placeholder:text-muted/60 focus:outline-none focus:border-primary/40"
              />
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden sm:block text-right">
              <p className="text-sm font-bold text-ink leading-none mb-1">{userEmail}</p>
              <p className="text-[10px] uppercase tracking-[0.2em] text-primary font-bold">{roleLabel}</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-white/5 border border-outline/40 grid place-items-center text-muted">
              <span className="text-xs font-bold font-display">AV</span>
            </div>
          </div>
        </header>

        <div className="border-b border-outline/40 bg-surface/40 backdrop-blur-md">
          <div className="px-4 lg:px-8">
            <div className="flex gap-2 overflow-x-auto">
              {nav.map((item) => (
                <button
                  key={item.id}
                  onClick={() => onNavigate(item.id)}
                  className={`px-4 py-4 text-sm font-semibold border-b-2 transition whitespace-nowrap ${
                    active === item.id
                      ? 'border-primary text-primary'
                      : 'border-transparent text-muted hover:text-ink'
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
