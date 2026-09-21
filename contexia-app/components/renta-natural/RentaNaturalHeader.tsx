"use client";

import { useState } from "react";

/**
 * Public marketing header for the /renta-natural landing (b2c-social-lead-capture).
 * Mirrors the navbar in root-level auditoria-sombra.html / landing.html so a visitor
 * who lands here from an ad or from the auditoria-sombra routing page sees the same
 * brand chrome and has a way back — this page previously had none.
 */
export function RentaNaturalHeader() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="w-full border-b border-slate-800 bg-[#020617]/90 backdrop-blur-xl fixed top-0 left-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between py-4 min-h-[96px] md:min-h-[120px]">
          <a href="/" className="flex items-center group">
            <div className="h-20 md:h-28 w-auto flex items-center justify-center flex-shrink-0">
              <img
                src="/assets/img/logo_official.png"
                alt="Contexia"
                fetchPriority="high"
                decoding="async"
                className="h-full w-auto object-contain transition-transform group-hover:scale-105 scale-110 translate-y-1 mix-blend-screen"
              />
            </div>
          </a>

          <div className="hidden md:flex items-center gap-8">
            <div className="flex items-center gap-6 text-sm font-bold uppercase tracking-widest">
              <a href="/#soluciones" className="text-slate-400 hover:text-white transition-colors">
                Soluciones
              </a>
              <a href="/#servicios" className="text-slate-400 hover:text-white transition-colors">
                Servicios
              </a>
              <a href="/crear-empresa.html" className="text-slate-400 hover:text-teal-300 transition-colors">
                Crear Empresa
              </a>
              <a href="/#faq" className="text-slate-400 hover:text-white transition-colors">
                FAQ
              </a>
            </div>

            <div className="h-8 w-px bg-slate-800 mx-2" />

            <div className="flex items-center gap-6">
              <a
                href="https://wa.me/573106229289"
                target="_blank"
                rel="noopener noreferrer"
                className="group relative flex items-center gap-4 bg-white/5 border border-white/10 rounded-2xl p-2 pr-6 hover:bg-white/10 hover:border-teal-400/50 transition-all duration-500 overflow-hidden"
                style={{ boxShadow: "0 0 20px rgba(20, 184, 166, 0.1)" }}
              >
                <div className="relative w-14 h-20 rounded-xl overflow-hidden border border-white/20 shadow-xl flex-shrink-0">
                  <img
                    src="/assets/img/profiles/tatiana_full.png"
                    alt="Taty"
                    decoding="async"
                    className="w-full h-full object-cover object-top group-hover:scale-110 transition-transform duration-700"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-[#020617]/80 via-transparent to-transparent" />
                </div>
                <div className="flex flex-col">
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75" />
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-teal-400" />
                    </span>
                    <span className="text-[10px] text-teal-300 font-black uppercase tracking-widest leading-none">
                      Online
                    </span>
                  </div>
                  <span className="text-sm text-white font-bold leading-tight">
                    Tu Amiga Contadora
                    <br />
                    <span className="text-teal-300">Taty</span>
                  </span>
                </div>
              </a>

              <a
                href="/app"
                className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-sm font-medium rounded-full text-[#020617] bg-teal-400 hover:bg-teal-300 shadow-[0_0_15px_rgba(20,184,166,0.3)] transition-all"
              >
                Acceso App
              </a>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setMobileOpen((open) => !open)}
            className="md:hidden text-slate-300 hover:text-white p-2"
            aria-label="Abrir menú"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="md:hidden border-t border-slate-800 px-4 py-6 space-y-4 bg-[#020617]/95 backdrop-blur-xl">
          <a href="/" className="block text-slate-300 hover:text-white py-2 text-sm font-semibold">
            ← Volver al inicio
          </a>
          <a href="/#soluciones" className="block text-slate-300 hover:text-white py-2 text-sm font-semibold">
            Soluciones
          </a>
          <a href="/#servicios" className="block text-slate-300 hover:text-white py-2 text-sm font-semibold">
            Servicios
          </a>
          <a href="/crear-empresa.html" className="block text-slate-300 hover:text-white py-2 text-sm font-semibold">
            Crear Empresa
          </a>
          <a href="/#faq" className="block text-slate-300 hover:text-white py-2 text-sm font-semibold">
            FAQ
          </a>
          <a
            href="/app"
            className="block bg-gradient-to-r from-teal-400 to-violet-500 text-white text-center py-3.5 rounded-xl text-sm font-bold mt-4 shadow-lg shadow-teal-400/20"
          >
            Acceso a Plataforma
          </a>
        </div>
      )}
    </nav>
  );
}
