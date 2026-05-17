import type { ReactNode } from "react";

/**
 * Base genérica para items en lista (milestones, movimientos, etc)
 * Reemplaza: UpcomingMilestonesCard items, EquityMovementHistoryCard items
 */
export function ListItemCard({
  icon,
  iconColor,
  title,
  subtitle,
  value,
  valueColor = "text-on-surface",
  onClick,
}: {
  icon: string;
  iconColor?: string;
  title: string;
  subtitle: string;
  value?: ReactNode;
  valueColor?: string;
  onClick?: () => void;
}) {
  return (
    <div
      onClick={onClick}
      className={`bg-surface-container border border-outline-variant/20 rounded-lg p-4 flex items-center gap-4 ${
        onClick ? "hover:border-primary/30 cursor-pointer transition-colors" : ""
      }`}
    >
      {/* Icon */}
      <div className="flex flex-col items-center justify-center bg-surface w-10 h-10 rounded border border-white/5 flex-shrink-0">
        <span className={`material-symbols-outlined text-sm ${iconColor || "text-on-surface-variant"}`}>
          {icon}
        </span>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <h4 className="font-body-md text-body-md font-semibold text-on-surface truncate">
          {title}
        </h4>
        <p className="font-label-caps text-label-caps text-on-surface-variant truncate">
          {subtitle}
        </p>
      </div>

      {/* Value (optional) */}
      {value && <div className={`font-data-mono text-data-mono text-right flex-shrink-0 font-bold ${valueColor}`}>{value}</div>}
    </div>
  );
}
