import Link from "next/link";
import Image from "next/image";

const NAV_LINKS = [
  { label: "Soluciones", href: "https://www.contexia.online/landing#soluciones" },
  { label: "Servicios", href: "https://www.contexia.online/landing#servicios" },
  { label: "Crear Empresa", href: "https://www.contexia.online/crear-empresa.html" },
  { label: "FAQ", href: "https://www.contexia.online/landing#faq" },
];

export default function WizardHeader() {
  return (
    <nav 
      className="w-full border-b border-slate-800 bg-[#020617]/90 backdrop-blur-xl fixed top-0 z-50"
      style={{ borderBottom: "1px solid rgba(100, 116, 139, 0.2)" }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between py-4 min-h-[120px]">
          {/* Logo Section */}
          <a href="https://www.contexia.online/landing" className="flex items-center group" title="Volver a la landing">
            <div className="h-32 md:h-40 w-auto flex items-center justify-center flex-shrink-0">
              <Image 
                src="https://www.contexia.online/assets/img/logo_official.png" 
                alt="Contexia"
                width={200}
                height={160}
                className="h-full w-auto object-contain transition-transform group-hover:scale-105 scale-110 translate-y-1 mix-blend-screen"
                unoptimized
              />
            </div>
          </a>
          
          <div className="hidden md:flex items-center gap-8">
            <div className="flex items-center gap-6 text-sm font-bold uppercase tracking-widest">
              {NAV_LINKS.map((link) => (
                <a 
                  key={link.label}
                  href={link.href} 
                  className="text-slate-400 hover:text-white transition-colors"
                >
                  {link.label}
                </a>
              ))}
              
              <Link 
                href="/" 
                className="px-8 py-3 bg-ctx-violet/10 text-white border-2 border-ctx-violet rounded-full hover:bg-ctx-violet/20 hover:shadow-[0_0_30px_-5px_rgba(139,92,246,0.6)] transition-all text-base font-bold tracking-wide shadow-[0_0_15px_-5px_rgba(139,92,246,0.4)] text-center inline-flex flex-col items-center leading-tight"
                title="Auditoría tributaria gratuita y 100% anónima"
              >
                <span>🔍 AUDITORÍA SOMBRA</span>
                <span className="text-ctx-violet text-xs font-semibold">(SIMULACIÓN CON LA DIAN)</span>
              </Link>
            </div>

            <div className="h-8 w-[1px] bg-slate-800 mx-2"></div>

            <div className="flex items-center gap-6">
              {/* Taty Button */}
              <a 
                href="https://wa.me/573018948151?text=Hola,%20completé%20el%20Shadow%20Audit%20y%20quiero%20agendar%20asesoría" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="group relative flex items-center gap-4 bg-white/5 border border-white/10 rounded-2xl p-2 pr-6 hover:bg-white/10 hover:border-ctx-teal/50 transition-all duration-500 overflow-hidden" 
                style={{ boxShadow: "0 0 20px rgba(20, 184, 166, 0.1)" }}
              >
                {/* Photo Section */}
                <div className="relative w-14 h-20 rounded-xl overflow-hidden border border-white/20 shadow-xl flex-shrink-0">
                  <Image 
                    src="https://www.contexia.online/assets/img/profiles/tatiana_full.png" 
                    alt="Taty" 
                    width={56}
                    height={80}
                    className="w-full h-full object-cover object-top group-hover:scale-110 transition-transform duration-700"
                    unoptimized
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-[#020617]/80 via-transparent to-transparent"></div>
                </div>
                {/* Text Section */}
                <div className="flex flex-col">
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-ctx-teal opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-ctx-teal"></span>
                    </span>
                    <span className="text-[10px] text-ctx-teal font-black uppercase tracking-widest leading-none">Online</span>
                  </div>
                  <span className="text-sm text-white font-bold leading-tight">Tu Amiga Contadora<br/><span className="text-ctx-teal">Taty</span></span>
                </div>
              </a>

              <a 
                href="https://www.contexia.online/app" 
                className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-sm font-medium rounded-full text-[#020617] bg-ctx-teal hover:bg-ctx-teal-dark shadow-[0_0_15px_rgba(20,184,166,0.3)] transition-all"
              >
                Acceso App
              </a>
            </div>
          </div>

          {/* Mobile menu button could go here if needed, but keeping it simple for now */}
        </div>
      </div>
    </nav>
  );
}
