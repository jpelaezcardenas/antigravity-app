import Link from "next/link";

/**
 * "Cerrar Sesión" moved out of the header (2026-09-15, founder request) — now sits at the
 * bottom of the page content on both mobile and desktop, instead of the header's right
 * cluster. Rendered inside `<main>` in the shell layout, right after the page's own content
 * and before `BottomNav`, so it scrolls with the page and never overlaps the fixed mobile nav.
 */
export function SignOutFooter() {
  return (
    <div className="flex justify-center pt-10 pb-4">
      {/* 2026-09-15: restyled to match the app's existing mobile "Salir" button
          (overview/page.tsx) — teal text + teal border on a dark pill, instead of the original
          dark-on-teal fill (founder feedback: dark-on-bright text read as "black letters"). */}
      <Link
        className="inline-flex items-center justify-center gap-2 rounded-full border border-[#2DD4BF]/40 bg-[#020617]/90 px-6 py-2 text-sm font-bold text-[#2DD4BF] shadow-[0_0_20px_rgba(45,212,191,0.25)] backdrop-blur transition-all hover:bg-[#020617] hover:border-[#2DD4BF]/70"
        href="/logout"
      >
        Cerrar Sesión
      </Link>
    </div>
  );
}
