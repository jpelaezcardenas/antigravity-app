import { JarvisBubble } from "@/components/jarvis/JarvisBubble";

/**
 * PWA V2 pilot — floats the real JarvisBubble in the page's own negative
 * space instead of the header/sidebar, per the founder's request (repositioned
 * to the center, equidistant between the hero and the content below — see
 * plan de migración, adenda de interacción). This is the SAME JarvisBubble
 * component used everywhere else, just placed differently — not a second
 * JARVIS. ClientTopBar/DesktopSidebar suppress their own badge on `-v2`
 * routes (pathname check) so there is still only one access point at a time.
 */
export function JarvisFloatingBadgeV2() {
  return (
    <div className="flex items-center justify-center py-10">
      <JarvisBubble size={96} panelAnchor="header" />
    </div>
  );
}
