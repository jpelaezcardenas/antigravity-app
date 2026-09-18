import Link from "next/link";

/**
 * Single header gear icon -> /app/config, for every -v2 route that isn't
 * Pulso-v2 (which already has its own header gear in PulsoHeroV2). Founder
 * caught BottomNav's "Config" tab duplicating this same destination on
 * overview-v2 (2026-09-18) — the fix was scoped to that one route because
 * fiscal-v2/radar-v2/patrimonio-v2 had no header gear of their own yet. This
 * component closes that gap so BottomNav can drop "Config" everywhere under
 * "-v2" (one access point, matching the Stitch mock), not just on Pulso.
 */
export function V2ConfigGearHeader() {
  return (
    <div className="flex items-center justify-end text-on-surface-variant">
      <Link
        href="/app/config"
        aria-label="Configuración"
        className="hover:text-white transition-colors p-1 flex items-center justify-center"
      >
        <span className="material-symbols-outlined text-[20px]">settings</span>
      </Link>
    </div>
  );
}
