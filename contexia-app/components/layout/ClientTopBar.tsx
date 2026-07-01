"use client";

import Link from "next/link";

/**
 * Full-featured branded header for the client app shell (/app/app/*).
 * Renders: Contexia logo, nav (Pulso/Fiscal/Radar/Patrimonio),
 * AUDITORÍA SOMBRA CTA, Taty card, Cerrar Sesión button.
 * Simplified version optimized for stability (no complex animations).
 */
export function ClientTopBar() {
  return (
    <nav className="w-full border-b border-slate-800 bg-[#020617]/90 backdrop-blur-xl fixed top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="relative flex items-center justify-between py-3 min-h-[120px] md:min-h-[100px]">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <Link className="flex items-center group" title="Contexia" href="/app/overview">
              <div className="h-16 md:h-24 w-auto flex items-center justify-center flex-shrink-0">
                <img
                  src="/assets/img/logo_official.png"
                  alt="Contexia"
                  className="h-full w-auto object-contain mix-blend-screen"
                />
              </div>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            <div className="flex items-center gap-6 text-sm font-bold uppercase tracking-widest" style={{ fontFamily: "Rajdhani, sans-serif" }}>
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
              <Link
                className="px-8 py-3 bg-[#8B5CF6]/10 text-white border-2 border-[#8B5CF6] rounded-full hover:bg-[#8B5CF6]/20 transition-all text-base font-bold tracking-wide text-center inline-flex flex-col items-center leading-tight"
                href="/wizard"
              >
                <span>🔍 AUDITORÍA SOMBRA</span>
                <span className="text-[#8B5CF6] text-xs font-semibold">(SIMULACIÓN CON LA DIAN)</span>
              </Link>
            </div>

            <div className="h-8 w-[1px] bg-slate-800 mx-2"></div>

            <div className="flex items-center gap-6">
              <Link
                href="https://wa.me/573018948151"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-4 bg-white/5 border border-white/10 rounded-2xl p-2 pr-6 hover:bg-white/10 transition-all"
              >
                <div className="relative w-12 h-16 rounded-xl overflow-hidden border border-white/20 flex-shrink-0">
                  <img src="/assets/img/profiles/tatiana_full.png" alt="Taty" className="w-full h-full object-cover object-top" />
                </div>
                <div className="flex flex-col">
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="h-2 w-2 rounded-full bg-[#2DD4BF]"></span>
                    <span className="text-[10px] text-[#2DD4BF] font-black uppercase tracking-widest" style={{ fontFamily: "Rajdhani, sans-serif" }}>
                      Online
                    </span>
                  </div>
                  <span className="text-sm text-white font-bold leading-tight">
                    Tu Amiga Contadora
                    <br />
                    <span className="text-[#2DD4BF]">Taty</span>
                  </span>
                </div>
              </Link>

              <Link className="inline-flex items-center justify-center px-6 py-2 text-sm font-medium rounded-full text-[#020617] bg-[#2DD4BF] hover:bg-[#14B8A6] transition-all" href="/logout">
                Cerrar Sesión
              </Link>
            </div>
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden flex items-center gap-2">
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
