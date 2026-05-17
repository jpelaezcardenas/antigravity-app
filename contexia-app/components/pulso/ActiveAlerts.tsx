import type { ActiveAlert } from "@/lib/types/contexia";
import { SEVERITY_ICON_STYLES } from "@/lib/styles/statusStyles";

export function ActiveAlerts({ alerts }: { alerts: ActiveAlert[] }) {
  if (alerts.length === 0) return null;

  return (
    <section className="flex flex-col gap-3">
      <h3 className="font-title-md text-title-md text-primary-container mb-1">
        Alertas Activas
      </h3>
      {alerts.map((alert) => {
        const styles = SEVERITY_ICON_STYLES[alert.severity];
        return (
          <div
            key={alert.id}
            className={`bg-surface-elevated rounded-xl p-4 border flex items-start gap-4 ${styles.border}`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${styles.iconBg}`}
            >
              <span
                className={`material-symbols-outlined text-sm ${styles.iconColor}`}
              >
                {alert.icon}
              </span>
            </div>
            <div className="flex-1">
              <p className="font-body-md text-body-md text-on-surface">
                {alert.message}
              </p>
            </div>
            <button
              type="button"
              aria-label="Ver detalle"
              className="w-8 h-8 flex items-center justify-center text-on-surface-variant hover:text-primary transition-colors"
            >
              <span className="material-symbols-outlined">chevron_right</span>
            </button>
          </div>
        );
      })}
    </section>
  );
}
