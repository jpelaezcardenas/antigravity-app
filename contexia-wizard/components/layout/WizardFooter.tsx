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
    <footer style={{ background: "#0a2540", color: "#94a3b8", marginTop: "4rem" }}>
      <div style={{ maxWidth: "1200px", margin: "0 auto", padding: "3rem 1.5rem 1.5rem" }}>
        {/* Top row */}
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr", gap: "2rem", marginBottom: "2.5rem" }}>
          {/* Brand */}
          <div>
            <Image
              src="https://www.contexia.online/assets/img/logo_official_transparent.png"
              alt="Contexia"
              width={160}
              height={48}
              style={{ objectFit: "contain", height: "48px", width: "auto", marginBottom: "1rem" }}
              unoptimized
            />
            <p style={{ fontSize: "0.875rem", lineHeight: 1.7, color: "#94a3b8", maxWidth: "280px" }}>
              El mejor equipo contable de Colombia. Contadores con experiencia con tecnología avanzada.
            </p>
          </div>

          {/* Links */}
          {Object.entries(FOOTER_LINKS).map(([section, links]) => (
            <div key={section}>
              <h4 style={{ color: "#fff", fontSize: "0.875rem", fontWeight: 700, marginBottom: "1rem", margin: "0 0 1rem" }}>
                {section}
              </h4>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                {links.map((l) => (
                  <li key={l.label}>
                    <a
                      href={l.href}
                      style={{ color: "#94a3b8", fontSize: "0.875rem", textDecoration: "none", transition: "color 0.15s" }}
                    >
                      {l.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom row */}
        <div
          style={{
            borderTop: "1px solid rgba(255,255,255,0.1)",
            paddingTop: "1.5rem",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "1rem",
          }}
        >
          <div style={{ fontSize: "0.8125rem" }}>
            <span>© 2026 Contexia SAS. Todos los derechos reservados.</span>
            <span style={{ margin: "0 0.5rem" }}>·</span>
            <a href="mailto:growth@contexia.online" style={{ color: "#94a3b8", textDecoration: "none" }}>
              growth@contexia.online
            </a>
            <span style={{ margin: "0 0.5rem" }}>·</span>
            <span>Antioquia, Colombia</span>
          </div>
          <div style={{ display: "flex", gap: "1rem", fontSize: "0.8125rem" }}>
            {["Términos", "Privacidad", "Seguridad"].map((t) => (
              <a key={t} href="https://www.contexia.online/landing" style={{ color: "#94a3b8", textDecoration: "none" }}>{t}</a>
            ))}
            <a
              href="https://wa.me/573018948151?text=Hola,%20me%20interesa%20Contexia"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "#00a878", textDecoration: "none", fontWeight: 600 }}
            >
              Hablemos por WhatsApp
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
