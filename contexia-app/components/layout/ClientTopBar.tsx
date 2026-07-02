import Link from "next/link";

/**
 * Branded header for the client app shell (/app/*) and detail screens.
 * Server Component (no hooks) so SSR markup and client markup always match —
 * this is what prevents hydration mismatches (React error #418).
 * Desktop layout: nav links (left) · official logo with slogan (center) ·
 * Taty card + "Cerrar Sesión" (right). Mobile: logo (left) · Taty card
 * (center) · menu button (right).
 */
export function ClientTopBar() {
  return (
    <nav className="w-full border-b border-slate-800 bg-[#020617]/90 backdrop-blur-xl fixed top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="relative flex items-center justify-between py-3 min-h-[120px] md:min-h-[100px]">
          {/* Logo (mobile, left) */}
          <div className="flex items-center gap-2 md:hidden">
            <Link className="flex items-center group" title="Contexia" href="/app/overview">
              <div className="h-16 w-auto flex items-center justify-center flex-shrink-0">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src="/assets/img/logo_official.png"
                  alt="Contexia"
                  className="h-full w-auto object-contain transition-transform group-hover:scale-105 scale-110 mix-blend-screen"
                />
              </div>
            </Link>
          </div>

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

          {/* Official logo with slogan (desktop, centered) */}
          <Link
            className="hidden md:flex absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 items-center group"
            title="Contexia"
            href="/app/overview"
          >
            <div className="h-24 w-auto flex items-center justify-center flex-shrink-0">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/assets/img/logo_official.png"
                alt="Contexia — GPS for cash flow & tax risk"
                className="h-full w-auto object-contain transition-transform group-hover:scale-105 scale-110 mix-blend-screen"
              />
            </div>
          </Link>

          {/* Desktop right: Taty card + logout */}
          <div className="hidden md:flex items-center gap-6">
            <a
              href="https://wa.me/573018948151"
              target="_blank"
              rel="noopener noreferrer"
              className="group relative flex items-center gap-4 bg-white/5 border border-white/10 rounded-2xl p-2 pr-6 hover:bg-white/10 hover:border-[#2DD4BF]/50 transition-all duration-500 overflow-hidden"
              style={{ boxShadow: "0 0 20px rgba(20, 184, 166, 0.1)" }}
            >
              <div className="relative w-12 h-16 rounded-xl overflow-hidden border border-white/20 shadow-xl flex-shrink-0">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src="/assets/img/profiles/tatiana_full.png"
                  alt="Taty"
                  className="w-full h-full object-cover object-top group-hover:scale-110 transition-transform duration-700"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#020617]/80 via-transparent to-transparent"></div>
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-1.5 mb-1">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#2DD4BF] opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-[#2DD4BF]"></span>
                  </span>
                  <span
                    className="text-[10px] text-[#2DD4BF] font-black uppercase tracking-widest leading-none"
                    style={{ fontFamily: "Rajdhani, sans-serif" }}
                  >
                    Online
                  </span>
                </div>
                <span className="text-sm text-white font-bold leading-tight">
                  Tu Amiga Contadora
                  <br />
                  <span className="text-[#2DD4BF]">Taty</span>
                </span>
              </div>
            </a>

            <Link
              className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-sm font-medium rounded-full text-[#020617] bg-[#2DD4BF] hover:bg-[#14B8A6] shadow-[0_0_15px_rgba(20,184,166,0.3)] transition-all"
              href="/logout"
            >
              Cerrar Sesión
            </Link>
          </div>

          {/* Taty card (mobile, centered) */}
          <a
            href="https://wa.me/573018948151?text=Hola%20Taty%2C%20necesito%20ayuda"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Chat con Taty - Tu Amiga Contadora 24/7"
            className="md:hidden absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-10 group flex items-center gap-2.5 bg-white/5 border border-[#2DD4BF]/30 rounded-2xl p-1.5 pr-3 backdrop-blur-xl hover:bg-white/10 hover:border-[#2DD4BF]/60 transition-all"
            style={{ boxShadow: "0 0 20px rgba(45, 212, 191, 0.3)" }}
          >
            <div className="relative w-14 h-16 rounded-xl overflow-hidden border border-white/20 shadow-md flex-shrink-0">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/assets/img/profiles/tatiana_full.png"
                alt="Taty"
                className="w-full h-full object-cover object-top group-hover:scale-110 transition-transform duration-500"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-[#020617]/70 via-transparent to-transparent"></div>
            </div>
            <div className="flex flex-col items-start">
              <div className="flex items-center gap-1 mb-0.5">
                <span className="relative flex h-1.5 w-1.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#2DD4BF] opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-[#2DD4BF]"></span>
                </span>
                <span
                  className="text-[9px] text-[#2DD4BF] font-black uppercase tracking-widest leading-none"
                  style={{ fontFamily: "Rajdhani, sans-serif" }}
                >
                  Online · 24/7
                </span>
              </div>
              <span className="text-[11px] text-white font-bold leading-tight whitespace-nowrap">
                Taty
                <br />
                <span className="text-[#2DD4BF] text-[10px]">Tu Contadora</span>
              </span>
              <div className="flex items-center gap-1 mt-1 bg-[#25D366]/15 border border-[#25D366]/40 rounded-full px-1.5 py-0.5">
                <svg
                  className="w-2.5 h-2.5 fill-[#25D366]"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"></path>
                </svg>
                <span
                  className="text-[7px] text-[#25D366] font-bold uppercase tracking-widest leading-none"
                  style={{ fontFamily: "Rajdhani, sans-serif" }}
                >
                  WhatsApp
                </span>
              </div>
            </div>
          </a>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center gap-2 flex-shrink-0">
            <button className="text-slate-300 hover:text-white p-2" aria-label="Abrir menú">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
