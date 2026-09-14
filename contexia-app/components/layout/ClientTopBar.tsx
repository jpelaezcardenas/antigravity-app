import Link from "next/link";
import { JarvisBubble } from "@/components/jarvis/JarvisBubble";

/**
 * Branded header for the client app shell (/app/*) and detail screens.
 * Server Component (no hooks) so SSR markup and client markup always match —
 * this is what prevents hydration mismatches (React error #418). `JarvisBubble`
 * is a client child component, which is fine — it renders null until its own
 * effect resolves, so it never diverges between server and first client paint.
 *
 * Desktop layout: nav links (left) · Jarvis circle + "Cerrar Sesión" (right).
 * Mobile: Jarvis circle (center).
 *
 * 2026-09-14 (founder request, hermes-jarvis-contexia D14): the Taty WhatsApp
 * card, the (unwired — no onClick) hamburger menu, and the Contexia logo were
 * all removed from here — the header's only identity mark is now the Jarvis
 * circle itself ("solo el círculo estilo Jarvis"). Already-won clients get
 * Jarvis instead of a generic WhatsApp link; the hamburger never did
 * anything. `JarvisBubble` itself stays hidden for a freemium/starter tenant
 * (no `jarvis_chat` feature) — the header shows nothing in that slot for
 * them, same as before this change added Jarvis.
 */
export function ClientTopBar() {
  return (
    <nav className="w-full border-b border-slate-800 bg-bg-obsidian/90 backdrop-blur-xl fixed top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="relative flex items-center justify-between py-3 min-h-[120px] md:min-h-[100px]">
          {/* Desktop nav links (left) */}
          <div
            className="hidden md:flex items-center gap-6 text-sm font-bold uppercase tracking-widest"
            style={{ fontFamily: "Rajdhani, sans-serif" }}
          >
            <Link className="text-slate-400 hover:text-white transition-colors" href="/app/overview">
              Pulso
            </Link>
            <Link className="text-slate-400 hover:text-white transition-colors" href="/app/fiscal">
              Fiscal
            </Link>
            <Link className="text-slate-400 hover:text-white transition-colors" href="/app/radar">
              Radar
            </Link>
            <Link className="text-slate-400 hover:text-[#2DD4BF] transition-colors" href="/app/patrimonio">
              Patrimonio
            </Link>
          </div>

          {/* Desktop right: Jarvis circle + logout */}
          <div className="hidden md:flex items-center gap-6">
            <JarvisBubble variant="desktop" />

            <Link
              className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-sm font-medium rounded-full text-[#020617] bg-[#2DD4BF] hover:bg-[#14B8A6] shadow-[0_0_15px_rgba(20,184,166,0.3)] transition-all"
              href="/logout"
            >
              Cerrar Sesión
            </Link>
          </div>

          {/* Jarvis circle (mobile, centered) */}
          <div className="md:hidden">
            <JarvisBubble variant="mobile" />
          </div>
        </div>
      </div>
    </nav>
  );
}
