"use client";

type Status = "healthy" | "warning" | "local" | "info";

const STATUS_STYLES: Record<Status, string> = {
  healthy: "bg-status-success/10 text-status-success border-status-success/25",
  warning: "bg-status-warning/10 text-status-warning border-status-warning/25",
  local: "bg-secondary/10 text-secondary-fixed border-secondary/25",
  info: "bg-primary/10 text-primary-container border-primary/25",
};

function StatusBadge({ status, label }: { status: Status; label: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wide whitespace-nowrap ${STATUS_STYLES[status]}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {label}
    </span>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 mb-3.5">
      <span className="font-label-caps text-label-caps text-on-surface-variant whitespace-nowrap">
        {children}
      </span>
      <div className="flex-1 h-px bg-outline-variant/30" />
    </div>
  );
}

function Metric({
  label,
  value,
  tone = "default",
  full = false,
}: {
  label: string;
  value: string;
  tone?: "default" | "muted" | "success" | "warning" | "info";
  full?: boolean;
}) {
  const toneClass =
    tone === "muted"
      ? "text-on-surface-variant text-xs"
      : tone === "success"
        ? "text-status-success"
        : tone === "warning"
          ? "text-status-warning"
          : tone === "info"
            ? "text-primary-container"
            : "text-on-surface";
  return (
    <div className={`bg-surface-container rounded-lg px-3 py-2.5 ${full ? "col-span-2" : ""}`}>
      <div className="font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wide">
        {label}
      </div>
      <div className={`font-bold mt-0.5 ${tone === "muted" ? "text-xs" : "text-base"} ${toneClass}`}>
        {value}
      </div>
    </div>
  );
}

function ServiceCard({
  emoji,
  name,
  layer,
  status,
  statusLabel,
  cost,
  source,
  children,
}: {
  emoji: string;
  name: string;
  layer: string;
  status: Status;
  statusLabel: string;
  cost: string;
  source: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-surface-elevated rounded-xl p-5 border border-white/10">
      <div className="flex items-start justify-between mb-3.5">
        <div className="flex items-center gap-2.5">
          <span className="text-xl leading-none">{emoji}</span>
          <div>
            <div className="font-title-md text-body-md text-on-surface font-bold">
              {name}
            </div>
            <div className="text-[11px] text-on-surface-variant/70 mt-0.5">
              {layer}
            </div>
          </div>
        </div>
        <StatusBadge status={status} label={statusLabel} />
      </div>

      {children}

      <div className="border-t border-outline-variant/20 pt-3 mt-3.5 flex items-center justify-between">
        <div>
          <div className="text-[11px] text-on-surface-variant">Estimado mensual</div>
          <div className="text-sm font-bold text-on-surface">{cost}</div>
        </div>
        <span className="text-[10px] text-on-surface-variant/70 border border-outline-variant/30 rounded px-1.5 py-0.5">
          {source}
        </span>
      </div>
    </div>
  );
}

const SUMMARY_CARDS = [
  { label: "Gasto Cloud Mensual Est.", value: "~$75", sub: "USD/mes (sin AI variable)", icon: "payments" },
  { label: "Servicios en Producción", value: "15", sub: "Vercel × 10 · Supabase × 2 · Railway × 1", icon: "dns" },
  { label: "Capas de IA Activas", value: "4", sub: "GLM 5.2 · Groq · OpenRouter · Claude", icon: "smart_toy" },
  { label: "Agentes Locales (on-prem)", value: "9", sub: "Hermes Workspace — $0 cloud", icon: "home" },
];

const COST_BREAKDOWN = [
  { label: "Vercel", value: 20, tone: "text-primary" },
  { label: "Railway", value: 12, tone: "text-secondary-fixed" },
  { label: "Claude/Anthropic", value: 35, tone: "text-status-warning" },
  { label: "Groq + OpenRouter", value: 22, tone: "text-status-success" },
  { label: "GCP", value: 4, tone: "text-primary-container" },
];
const COST_MAX = Math.max(...COST_BREAKDOWN.map((c) => c.value));

const STACK_ROWS: {
  layer: string;
  tech: string;
  fn: string;
  cost: string;
  status: Status;
  statusLabel: string;
}[] = [
  { layer: "Frontend", tech: "Next.js · React · TypeScript", fn: "5 pantallas en producción (PWA)", cost: "~$20 USD (Vercel)", status: "healthy", statusLabel: "LIVE" },
  { layer: "Backend / API", tech: "Python · FastAPI", fn: "Lógica de negocio, ingesta, orquestación", cost: "~$5–20 USD (Railway)", status: "warning", statusLabel: "SIN MCP" },
  { layer: "Base de datos", tech: "Supabase · PostgreSQL 17", fn: "Datos financieros, auth, RLS multi-tenant", cost: "$0 USD (Free)", status: "healthy", statusLabel: "LIVE" },
  { layer: "IA Principal", tech: "GLM 5.2 (ZhipuAI)", fn: "Motor de los 9 agentes de Hermes", cost: "Variable (tokens)", status: "info", statusLabel: "ACTIVO" },
  { layer: "IA Fallback", tech: "Groq · OpenRouter", fn: "Respaldo en nube cuando GLM no disponible", cost: "~$10–35 USD", status: "info", statusLabel: "STANDBY" },
  { layer: "Copiloto Dev", tech: "Claude Code · Cowork", fn: "Desarrollo agent-first: spec → código → deploy", cost: "~$20–50 USD", status: "healthy", statusLabel: "ACTIVO" },
  { layer: "Orquestación IA", tech: "Hermes Workspace (on-prem)", fn: "Coordina los 9 agentes; datos financieros 100% local", cost: "$0 (hardware propio)", status: "local", statusLabel: "LOCAL" },
  { layer: "GCP", tech: "Google Cloud (VERDOLAGA)", fn: "Caricaturas IA — Atlético Nacional", cost: "COP ~55K/mes", status: "healthy", statusLabel: "ACTIVO" },
];

const ALERTS: { type: "danger" | "warn" | "ok"; icon: string; title: string; body: string }[] = [
  { type: "danger", icon: "key", title: "Railway API token expuesto", body: "El token quedó registrado en historial de chat. Rota el token en railway.com/account/tokens de inmediato." },
  { type: "warn", icon: "dns", title: "Railway sin MCP conectado", body: "El servidor MCP local ya está construido. Instálalo y configúralo en Claude Code." },
  { type: "warn", icon: "lock", title: "Auth de API pendiente", body: "La demo en contexia.online/app/overview es actualmente de acceso abierto. Hardening en curso." },
  { type: "ok", icon: "check_circle", title: "Supabase Free — límite: 2 proyectos", body: "Ocupas los 2 proyectos del plan gratuito. Un tercer proyecto requiere upgrade a Pro (~$25/mes)." },
];

const ALERT_STYLES: Record<string, string> = {
  danger: "bg-status-critical/8 border-status-critical/25",
  warn: "bg-status-warning/8 border-status-warning/25",
  ok: "bg-status-success/8 border-status-success/25",
};
const ALERT_TITLE_STYLES: Record<string, string> = {
  danger: "text-status-critical",
  warn: "text-status-warning",
  ok: "text-status-success",
};

export function InfrastructureDashboard() {
  return (
    <div className="w-full">
      <section className="mb-8 flex items-start justify-between flex-wrap gap-3">
        <div>
          <h2 className="font-headline-lg text-headline-lg text-primary-container mb-2">
            Infrastructure Dashboard
          </h2>
          <p className="text-on-surface-variant text-body-md">
            Consumo y costo de infraestructura de Contexia
          </p>
        </div>
        <span className="inline-flex items-center gap-1.5 rounded-full border border-status-success/30 bg-status-success/10 text-status-success text-xs font-semibold px-3 py-1">
          <span className="w-1.5 h-1.5 rounded-full bg-status-success" />
          Datos parcialmente en vivo
        </span>
      </section>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
        {SUMMARY_CARDS.map((c) => (
          <div
            key={c.label}
            className="bg-surface-elevated rounded-xl p-5 border border-white/10 relative overflow-hidden"
          >
            <span className="material-symbols-outlined absolute top-4 right-4 text-on-surface-variant/30 text-xl">
              {c.icon}
            </span>
            <div className="font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wide mb-2">
              {c.label}
            </div>
            <div className="font-headline-lg text-2xl text-primary-container font-extrabold">
              {c.value}
            </div>
            <div className="text-[11px] text-on-surface-variant mt-1">{c.sub}</div>
          </div>
        ))}
      </div>

      <SectionTitle>⚙️ Infraestructura Cloud</SectionTitle>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-10">
        <ServiceCard emoji="▲" name="Vercel" layer="Frontend · Auto-deploy" status="healthy" statusLabel="LIVE" cost="~$20 USD" source="🟢 Vercel MCP">
          <div className="grid grid-cols-2 gap-2 mb-1">
            <Metric label="Proyectos" value="10" tone="info" />
            <Metric label="Equipo" value="luna-del-cerro" tone="muted" />
          </div>
        </ServiceCard>

        <ServiceCard emoji="🚂" name="Railway" layer="Backend · FastAPI · Auto-deploy" status="warning" statusLabel="TOKEN VENCIDO" cost="~$5–20 USD" source="⚠️ Rotar token">
          <div className="grid grid-cols-2 gap-2 mb-1">
            <Metric label="Stack" value="Python · FastAPI" tone="muted" full />
            <Metric label="Función" value="Ingesta · Orquestación" tone="muted" full />
          </div>
        </ServiceCard>

        <ServiceCard emoji="🟢" name="Supabase" layer="Base de datos · Auth · RLS" status="healthy" statusLabel="LIVE" cost="Free (2 proyectos)" source="🟢 Supabase MCP">
          <div className="grid grid-cols-2 gap-2 mb-1">
            <Metric label="Proyectos activos" value="2" tone="success" />
            <Metric label="PostgreSQL" value="v17.6" tone="info" />
          </div>
        </ServiceCard>
      </div>

      <SectionTitle>🤖 Capa de Inteligencia Artificial</SectionTitle>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-10">
        <ServiceCard emoji="🧠" name="GLM 5.2 (ZhipuAI)" layer="Motor principal · Agentes interactivos" status="info" statusLabel="PRINCIPAL" cost="Variable" source="Informe técnico">
          <Metric label="Rol" value="Motor de los 9 agentes de Hermes" tone="muted" full />
        </ServiceCard>
        <ServiceCard emoji="⚡" name="Groq" layer="Fallback · Inferencia rápida" status="info" statusLabel="FALLBACK" cost="~$5–15 USD" source="Informe técnico">
          <Metric label="Rol" value="Respaldo cuando GLM no responde" tone="muted" full />
        </ServiceCard>
        <ServiceCard emoji="🔀" name="OpenRouter" layer="Fallback · Multi-modelo" status="info" statusLabel="FALLBACK" cost="~$5–20 USD" source="Informe técnico">
          <Metric label="Rol" value="Gateway multi-modelo de respaldo" tone="muted" full />
        </ServiceCard>
      </div>

      <SectionTitle>🛠️ Herramientas y Entorno Dev</SectionTitle>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-10">
        <ServiceCard emoji="🟠" name="Claude · Anthropic" layer="Claude Code · Cowork · API" status="healthy" statusLabel="ACTIVO" cost="~$20–50 USD" source="Pro plan + API">
          <Metric label="Uso" value="Copiloto principal de desarrollo" tone="muted" full />
        </ServiceCard>
        <ServiceCard emoji="☁️" name="Google Cloud (GCP)" layer="Pay-as-you-go · VERDOLAGA" status="healthy" statusLabel="ACTIVO" cost="COP ~55K" source="Facturas Gmail">
          <Metric label="Uso" value="Caricaturas IA" tone="muted" full />
        </ServiceCard>
        <ServiceCard emoji="🏠" name="Hermes Workspace" layer="On-prem · WSL/Ubuntu · Local" status="local" statusLabel="LOCAL" cost="$0 USD" source="Hardware propio">
          <Metric label="Agentes" value="9 activos" tone="success" full />
        </ServiceCard>
      </div>

      <SectionTitle>💸 Distribución de costos mensuales</SectionTitle>
      <div className="bg-surface-elevated rounded-xl p-5 border border-white/10 mb-10">
        <div className="flex flex-col gap-3">
          {COST_BREAKDOWN.map((c) => (
            <div key={c.label} className="flex items-center gap-3">
              <span className="w-40 shrink-0 text-sm text-on-surface-variant">
                {c.label}
              </span>
              <div className="flex-1 h-3 rounded-full bg-surface-container overflow-hidden">
                <div
                  className={`h-full rounded-full bg-current ${c.tone}`}
                  style={{ width: `${Math.max((c.value / COST_MAX) * 100, 4)}%` }}
                />
              </div>
              <span className="w-16 shrink-0 text-right text-sm font-bold text-on-surface">
                ${c.value}
              </span>
            </div>
          ))}
        </div>
      </div>

      <SectionTitle>📋 Stack técnico completo</SectionTitle>
      <div className="bg-surface-elevated rounded-xl border border-white/10 mb-10 overflow-x-auto">
        <table className="w-full border-collapse min-w-[640px]">
          <thead>
            <tr>
              {["Capa", "Tecnología", "Función", "Costo est./mes", "Estado"].map((h) => (
                <th
                  key={h}
                  className="text-left font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wide px-4 py-2.5 border-b border-outline-variant/20"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {STACK_ROWS.map((row, i) => (
              <tr key={row.layer} className={i < STACK_ROWS.length - 1 ? "border-b border-outline-variant/10" : ""}>
                <td className="px-4 py-2.5 text-[11px] text-on-surface-variant">{row.layer}</td>
                <td className="px-4 py-2.5 text-xs font-mono text-primary-container">{row.tech}</td>
                <td className="px-4 py-2.5 text-xs text-on-surface-variant">{row.fn}</td>
                <td className="px-4 py-2.5 text-xs font-bold text-on-surface whitespace-nowrap">{row.cost}</td>
                <td className="px-4 py-2.5">
                  <StatusBadge status={row.status} label={row.statusLabel} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <SectionTitle>🔔 Alertas y acciones pendientes</SectionTitle>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {ALERTS.map((a) => (
          <div
            key={a.title}
            className={`rounded-lg p-4 border flex gap-3 ${ALERT_STYLES[a.type]}`}
          >
            <span className="material-symbols-outlined text-lg shrink-0 mt-0.5 text-on-surface-variant">
              {a.icon}
            </span>
            <div>
              <div className={`text-sm font-bold mb-0.5 ${ALERT_TITLE_STYLES[a.type]}`}>
                {a.title}
              </div>
              <div className="text-xs text-on-surface-variant leading-relaxed">
                {a.body}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
