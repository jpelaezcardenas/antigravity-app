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
  accent?: "default" | "success" | "warning";
}

const ACCENT_TEXT: Record<NonNullable<MetricTile["accent"]>, string> = {
  default: "text-white",
  success: "text-status-success",
  warning: "text-status-warning",
};

export function MetricTileGrid({ tiles }: { tiles: MetricTile[] }) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {tiles.map((tile) => (
        <section
          key={tile.id}
          className="rounded-2xl border border-outline-variant/40 bg-surface-container/60 backdrop-blur-md p-4 flex flex-col gap-2"
        >
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium tracking-wide uppercase text-on-surface-variant">
              {tile.label}
            </span>
            <span className="material-symbols-outlined text-on-surface-variant/70 text-[18px]">
              {tile.icon}
            </span>
          </div>
          <p className={`text-lg font-semibold ${ACCENT_TEXT[tile.accent ?? "default"]}`}>
            {tile.value}
          </p>
        </section>
      ))}
    </div>
  );
}
