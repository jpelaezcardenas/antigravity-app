/**
 * Read-only HubSpot sync status badge (hubspot-sync-renta-natural).
 *
 * Shows "Sincronizado ✓" + a deep link only when `lastSyncedAt` is set — a lead/client with no
 * hubspot id yet gets a neutral "sin sincronizar" state instead, never a false-positive badge.
 * No write action to HubSpot exists anywhere in this component.
 */

// Confirmed live 2026-08-15 via HubSpot MCP (get_organization_details): accountId 51867201.
const HUBSPOT_PORTAL_ID =
  process.env.NEXT_PUBLIC_HUBSPOT_PORTAL_ID || "51867201";

const OBJECT_PATH: Record<"contact" | "deal" | "company", string> = {
  contact: "record/0-1",
  deal: "record/0-3",
  company: "record/0-2",
};

interface HubspotSyncBadgeProps {
  objectType: "contact" | "deal" | "company";
  hubspotId?: string | null;
  lastSyncedAt?: string | null;
}

export function HubspotSyncBadge({ objectType, hubspotId, lastSyncedAt }: HubspotSyncBadgeProps) {
  if (!lastSyncedAt || !hubspotId) {
    return (
      <span className="rounded-md border border-outline-variant/30 bg-white/5 px-2 py-0.5 text-[11px] text-on-surface-variant/70">
        sin sincronizar
      </span>
    );
  }

  const href = `https://app.hubspot.com/contacts/${HUBSPOT_PORTAL_ID}/${OBJECT_PATH[objectType]}/${hubspotId}`;

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="rounded-md border border-status-success/30 bg-status-success/10 px-2 py-0.5 text-[11px] text-status-success hover:bg-status-success/20"
    >
      Sincronizado ✓
    </a>
  );
}
