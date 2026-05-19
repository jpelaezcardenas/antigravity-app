import Image from "next/image";

const FOOTER_LINKS = {
  Servicios: [
    { label: "Contabilidad", href: "https://www.contexia.online/landing#soluciones" },
    { label: "Impuestos", href: "https://www.contexia.online/landing#soluciones" },
    { label: "Nómina", href: "https://www.contexia.online/landing#soluciones" },
    { label: "Creación de Empresas", href: "https://www.contexia.online/crear-empresa.html" },
  ],
  Soluciones: [
    { label: "Startups & Tech", href: "https://www.contexia.online/landing#soluciones" },
    { label: "E-commerce", href: "https://www.contexia.online/landing#soluciones" },
    { label: "Comercio Minorista", href: "https://www.contexia.online/landing#soluciones" },
    { label: "Servicios", href: "https://www.contexia.online/landing#soluciones" },
  ],
  Recursos: [
    { label: "Blog", href: "https://www.contexia.online/landing" },
    { label: "Guías", href: "https://www.contexia.online/landing" },
    { label: "Calculadoras", href: "https://www.contexia.online/landing" },
    { label: "Calendario Tributario", href: "https://www.contexia.online/landing" },
  ],
  Empresa: [
    { label: "Por qué Contexia", href: "https://www.contexia.online/landing" },
    { label: "Nosotros", href: "https://www.contexia.online/landing" },
    { label: "Casos de éxito", href: "https://www.contexia.online/landing" },
    { label: "FAQ", href: "https://www.contexia.online/landing#faq" },
  ],
};

export default function WizardFooter() {
  return (
    <footer className="bg-[#0c1e30] border-t border-slate-800">
      <div className="mx-auto max-w-7xl px-6 pt-16 pb-8 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
          {/* Logo Column */}
          <div className="col-span-2 md:col-span-1">
            <a href="https://www.contexia.online/landing" className="flex items-center mb-6" title="Volver a la landing">
              <div className="h-32 w-auto flex items-center justify-start flex-shrink-0">
                <Image 
                  src="https://www.contexia.online/assets/img/logo_official.png" 
                  alt="Contexia"
                  width={200}
                  height={128}
                  className="h-full w-auto object-contain mix-blend-screen"
                  unoptimized
                />
              </div>
            </a>
            <p className="text-sm text-slate-400 mb-4">
              El mejor equipo contable de Colombia. Contadores con experiencia con tecnología avanzada.
            </p>
            <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-white transition-colors">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
              </svg>
            </a>
          </div>

          {/* Links Columns */}
          {Object.entries(FOOTER_LINKS).map(([section, links]) => (
            <div key={section}>
              <h3 className="text-sm font-bold text-white mb-4 uppercase tracking-wider">{section}</h3>
              <ul className="space-y-2 text-sm text-slate-400">
                {links.map((link) => (
                  <li key={link.label}>
                    <a href={link.href} className="hover:text-teal transition-colors">
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom Section */}
        <div className="border-t border-slate-800 pt-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-xs text-slate-500">© 2026 Contexia SAS. Todos los derechos reservados.</p>
          <p className="text-xs text-slate-500">growth@contexia.online · Antioquia, Colombia</p>
          <div className="flex items-center gap-4 text-xs text-slate-500">
            <a href="#" className="hover:text-slate-300 transition-colors">Términos</a>
            <a href="#" className="hover:text-slate-300 transition-colors">Privacidad</a>
            <a href="#" className="hover:text-slate-300 transition-colors">Seguridad</a>
            <a 
              href="https://wa.me/573018948151?text=Hola,%20me%20interesa%20Contexia" 
              className="text-teal hover:text-teal-dark transition-colors font-semibold"
            >
              Hablemos por WhatsApp
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
