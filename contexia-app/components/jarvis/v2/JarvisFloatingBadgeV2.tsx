import { JarvisBubble } from "@/components/jarvis/JarvisBubble";

/**
 * PWA V2 pilot — floats the real JarvisBubble in the page's own negative
 * space instead of the header/sidebar, per the founder's request (repositioned
 * to the center, equidistant between the hero and the content below — see
 * plan de migración, adenda de interacción). This is the SAME JarvisBubble
 * component used everywhere else, just placed differently — not a second
 * JARVIS. ClientTopBar/DesktopSidebar suppress their own badge on `-v2`
 * routes (pathname check) so there is still only one access point at a time.
 *
 * 2026-09-18 redesign: "JARVIS" + live status now sit INSIDE the badge's core,
 * under the pin (founder's reference design), with only the "Toca a JARVIS..."
 * caption below. That's why the size went 96 → 156: the core is 56/88 of the
 * diameter, and at 96px it can't fit pin + name + status legibly — the reference
 * mock's circle is deliberately this large.
 */
export function JarvisFloatingBadgeV2() {
  return (
    <div className="flex items-center justify-center py-10">
      <JarvisBubble size={156} panelAnchor="header" />
    </div>
  );
}
