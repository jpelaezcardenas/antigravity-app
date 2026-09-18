/**
 * PWA V2 — compact 2-column metric-tile grid (Weather UV/Humidity/Real Feel
 * pattern), approved in Stitch for Fiscal/Radar/Patrimonio. Every tile's
 * value must come from real/mock data already wired on the page — this
 * component only renders what it's given, it never invents a number.
 */
export interface MetricTile {
  id: string;
  icon: string; // Material Symbols Outlined ligature name
  label: string;
  value: string;
  accent?: "default" | "success" | "warning" | "critical";
  /** Makes the tile tappable (e.g. to expand its detail below the grid). */
  onClick?: () => void;
  /** Highlights the tile as the currently expanded/active one. */
  selected?: boolean;
}

const ACCENT_TEXT: Record<NonNullable<MetricTile["accent"]>, string> = {
  default: "text-white",
  success: "text-status-success",
  warning: "text-status-warning",
  critical: "text-status-critical",
};

const ACCENT_ICON: Record<NonNullable<MetricTile["accent"]>, string> = {
  default: "text-on-surface-variant/70",
  success: "text-status-success",
  warning: "text-status-warning",
  critical: "text-status-critical",
};

export interface MetricTileGridProps {
  tiles: MetricTile[];
  /**
   * "metric" (default): caps label + icon on top row, value below — the
   * Fiscal/Radar/Patrimonio pattern. "priority" (founder-approved reference,
   * 2026-09-18, Alertas Activas): plain-case label on its own row, then
   * value and icon together on the row below, sharing the accent color.
   */
  variant?: "metric" | "priority";
}

export function MetricTileGrid({ tiles, variant = "metric" }: MetricTileGridProps) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {tiles.map((tile) => {
        const Tag = tile.onClick ? "button" : "section";
        const accent = tile.accent ?? "default";
        return (
          <Tag
            key={tile.id}
            type={tile.onClick ? "button" : undefined}
            onClick={tile.onClick}
            className={`rounded-2xl border backdrop-blur-md p-4 flex flex-col gap-2 text-left transition-colors ${
              tile.selected
                ? "border-primary/60 bg-surface-container/90"
                : "border-outline-variant/40 bg-surface-container/60"
            } ${tile.onClick ? "hover:border-primary/40" : ""}`}
          >
            {variant === "priority" ? (
              <>
                <span className="text-[13px] font-normal text-on-surface-variant">
                  {tile.label}
                </span>
                <div className="flex items-center justify-between">
                  <p className={`text-lg font-semibold ${ACCENT_TEXT[accent]}`}>{tile.value}</p>
                  <span className={`material-symbols-outlined text-[18px] ${ACCENT_ICON[accent]}`}>
                    {tile.icon}
                  </span>
                </div>
              </>
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-medium tracking-wide uppercase text-on-surface-variant">
                    {tile.label}
                  </span>
                  <span className="material-symbols-outlined text-on-surface-variant/70 text-[18px]">
                    {tile.icon}
                  </span>
                </div>
                <p className={`text-lg font-semibold ${ACCENT_TEXT[accent]}`}>{tile.value}</p>
              </>
            )}
          </Tag>
        );
      })}
    </div>
  );
}
