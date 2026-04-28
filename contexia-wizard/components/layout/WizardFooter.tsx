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
    <footer style={{ background: "#020617", color: "var(--ctx-text-muted)", marginTop: "4rem", borderTop: "1px solid rgba(255,255,255,0.05)" }}>
      <div style={{ maxWidth: "1200px", margin: "0 auto", padding: "4rem 1.5rem 3rem" }}>
        {/* Top row */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "3rem", marginBottom: "3rem" }}>
          {/* Brand */}
          <div style={{ gridColumn: "span 1" }}>
            <Image
              src="https://www.contexia.online/assets/img/logo_official_transparent.png"
              alt="Contexia"
              width={160}
              height={48}
              style={{ objectFit: "contain", height: "40px", width: "auto", marginBottom: "1.5rem", filter: "brightness(0) invert(1)" }}
              unoptimized
            />
            <p style={{ fontSize: "0.875rem", lineHeight: 1.7, color: "var(--ctx-text-light)", maxWidth: "280px" }}>
              Liderando la transformación contable en Colombia con tecnología de vanguardia y especialistas de alto nivel.
            </p>
          </div>

          {/* Links */}
          {Object.entries(FOOTER_LINKS).map(([section, links]) => (
            <div key={section}>
              <h4 className="font-orbitron" style={{ color: "#fff", fontSize: "0.8125rem", fontWeight: 800, marginBottom: "1.25rem", textTransform: "uppercase", letterSpacing: "0.1em" }}>
                {section}
              </h4>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                {links.map((l) => (
                  <li key={l.label}>
                    <a
                      href={l.href}
                      style={{ color: "var(--ctx-text-muted)", fontSize: "0.875rem", textDecoration: "none", transition: "color 0.2s ease" }}
                      onMouseOver={(e) => (e.currentTarget.style.color = "var(--ctx-teal)")}
                      onMouseOut={(e) => (e.currentTarget.style.color = "var(--ctx-text-muted)")}
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
            borderTop: "1px solid rgba(255,255,255,0.05)",
            paddingTop: "2rem",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "1.5rem",
          }}
        >
          <div style={{ fontSize: "0.8125rem", color: "var(--ctx-text-light)" }}>
            <span>© 2026 Contexia SAS.</span>
            <span style={{ margin: "0 0.5rem" }}>·</span>
            <a href="mailto:growth@contexia.online" style={{ color: "inherit", textDecoration: "none" }}>
              growth@contexia.online
            </a>
            <span style={{ margin: "0 0.5rem" }}>·</span>
            <span>Antioquia, Colombia</span>
          </div>
          <div style={{ display: "flex", gap: "1.5rem", fontSize: "0.8125rem", alignItems: "center" }}>
            {["Términos", "Privacidad"].map((t) => (
              <a key={t} href="https://www.contexia.online/landing" style={{ color: "var(--ctx-text-light)", textDecoration: "none" }}>{t}</a>
            ))}
            <a
              href="https://wa.me/573018948151?text=Hola,%20me%20interesa%20Contexia"
              target="_blank"
              rel="noopener noreferrer"
              style={{ 
                color: "var(--ctx-teal)", 
                textDecoration: "none", 
                fontWeight: 700,
                padding: "0.5rem 1rem",
                borderRadius: "999px",
                background: "rgba(45, 212, 191, 0.05)",
                border: "1px solid rgba(45, 212, 191, 0.1)"
              }}
            >
              WhatsApp 24/7
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
