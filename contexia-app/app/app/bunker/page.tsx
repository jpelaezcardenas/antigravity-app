"use client";

const clients = [
  {
    id: 1,
    name: "Contexia Marketing",
    email: "contexia.marketing",
    status: "activo",
    users: 5,
    plan: "Pro",
  },
  {
    id: 2,
    name: "Lavaderos L&D",
    email: "lavaderos@example.com",
    status: "activo",
    users: 3,
    plan: "Starter",
  },
  {
    id: 3,
    name: "Sion",
    email: "sion@example.com",
    status: "activo",
    users: 2,
    plan: "Starter",
  },
  {
    id: 4,
    name: "Repuestos Don Álvaro",
    email: "repuestos@example.com",
    status: "activo",
    users: 4,
    plan: "Pro",
  },
  {
    id: 5,
    name: "Studio 4",
    email: "studio4@example.com",
    status: "activo",
    users: 2,
    plan: "Starter",
  },
];

export default function BunkerPage() {
  return (
    <div className="min-h-screen bg-bg-obsidian text-on-surface">
      <header className="fixed top-0 w-full z-50 bg-surface/80 backdrop-blur-xl border-b border-outline-variant/10 shadow-[0_0_20px_rgba(45,212,191,0.05)] flex justify-between items-center px-container-margin-mobile md:px-container-margin-desktop h-touch-target-min">
        <div className="flex items-center gap-3">
          <a
            className="w-8 h-8 rounded-md bg-surface-variant flex items-center justify-center overflow-hidden border border-white/10 shrink-0"
            aria-label="Contexia — Admin"
            href="/app/bunker"
          >
            <img src="/logo.png" alt="Contexia" className="w-full h-full object-cover" />
          </a>
          <h1 className="font-headline-lg-mobile text-headline-lg-mobile md:font-headline-lg md:text-headline-lg font-bold text-primary-container flex items-center">
            Bunker Contexia
          </h1>
        </div>
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

      <main className="flex-1 pt-[80px] pb-24 md:pb-8">
        <div className="px-container-margin-mobile md:px-container-margin-desktop max-w-6xl mx-auto w-full mt-6">
          <section className="mb-8">
            <h2 className="font-headline-lg text-headline-lg text-primary-container mb-2">
              Clientes Activos
            </h2>
            <p className="text-on-surface-variant text-body-md">
              Gestión centralizada de empresas en Contexia
            </p>
          </section>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {clients.map((client) => (
              <div
                key={client.id}
                className="bg-surface-elevated rounded-xl p-6 border border-white/10 hover:border-primary/30 transition-all hover:shadow-[0_0_20px_rgba(45,212,191,0.15)] cursor-pointer group"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="font-title-md text-title-md text-primary-container mb-1">
                      {client.name}
                    </h3>
                    <p className="text-data-mono text-data-mono text-on-surface-variant text-sm">
                      {client.email}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-status-success shadow-[0_0_8px_rgba(45,212,191,0.6)]" />
                    <span className="text-[10px] text-status-success font-bold uppercase">
                      {client.status}
                    </span>
                  </div>
                </div>

                <div className="space-y-2 border-t border-outline-variant/30 pt-4">
                  <div className="flex justify-between items-center">
                    <span className="text-on-surface-variant text-body-md">Usuarios:</span>
                    <span className="font-headline-sm text-on-surface font-bold">
                      {client.users}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-on-surface-variant text-body-md">Plan:</span>
                    <span className="px-3 py-1 rounded-full bg-primary/10 text-primary-container text-label-caps text-label-caps font-bold">
                      {client.plan}
                    </span>
                  </div>
                </div>

                <button
                  type="button"
                  className="mt-4 w-full py-2 border border-primary-container/20 rounded-lg text-primary-container hover:bg-primary-container/10 transition-all text-label-caps text-label-caps font-bold group-hover:border-primary/50"
                >
                  Ver Detalles
                </button>
              </div>
            ))}
          </div>

          <section className="mt-12 bg-surface-elevated/50 rounded-xl p-6 border border-white/10">
            <h3 className="font-title-md text-title-md text-primary-container mb-4">
              Estadísticas del Bunker
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-surface-elevated rounded-lg p-4 text-center">
                <div className="font-headline-xl text-headline-xl text-primary-container">
                  {clients.length}
                </div>
                <p className="text-on-surface-variant text-body-md">Clientes Activos</p>
              </div>
              <div className="bg-surface-elevated rounded-lg p-4 text-center">
                <div className="font-headline-xl text-headline-xl text-status-success">
                  {clients.reduce((sum, c) => sum + c.users, 0)}
                </div>
                <p className="text-on-surface-variant text-body-md">Usuarios Totales</p>
              </div>
              <div className="bg-surface-elevated rounded-lg p-4 text-center">
                <div className="font-headline-xl text-headline-xl text-primary-container">
                  {clients.filter((c) => c.plan === "Pro").length}
                </div>
                <p className="text-on-surface-variant text-body-md">Planes Pro</p>
              </div>
              <div className="bg-surface-elevated rounded-lg p-4 text-center">
                <div className="font-headline-xl text-headline-xl text-status-success">
                  100%
                </div>
                <p className="text-on-surface-variant text-body-md">Uptime</p>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
