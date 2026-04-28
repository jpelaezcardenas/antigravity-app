import Link from "next/link";
import Image from "next/image";

const NAV_LINKS = [
  { label: "Soluciones", href: "https://www.contexia.online/landing#soluciones" },
  { label: "Servicios", href: "https://www.contexia.online/landing#servicios" },
  { label: "Crear Empresa", href: "https://www.contexia.online/crear-empresa.html" },
  { label: "FAQ", href: "https://www.contexia.online/landing#faq" },
];

const WA_URL =
  "https://wa.me/573018948151?text=Hola,%20completé%20el%20Shadow%20Audit%20y%20quiero%20agendar%20asesoría";

export default function WizardHeader() {
  return (
    <header
      className="ctx-force-dark-bg"
      style={{
        background: "rgba(2, 6, 23, 0.8)",
        backdropFilter: "blur(12px)",
        borderBottom: "1px solid rgba(255,255,255,0.05)",
        position: "sticky",
        top: 0,
        zIndex: 40,
      }}
    >
      <div
        style={{
          maxWidth: "1200px",
          margin: "0 auto",
          padding: "0 1.5rem",
          height: "68px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "1.5rem",
        }}
      >
        {/* Logo */}
        <a href="https://www.contexia.online/landing" style={{ display: "flex", alignItems: "center", flexShrink: 0 }}>
          <Image
            src="https://www.contexia.online/assets/img/logo_official.png"
            alt="Contexia"
            width={140}
            height={40}
            style={{ objectFit: "contain", height: "40px", width: "auto" }}
            unoptimized
          />
        </a>

        {/* Nav desktop */}
        <nav
          style={{ display: "flex", gap: "1.5rem", alignItems: "center" }}
          className="hidden-mobile"
        >
          {NAV_LINKS.map((l) => (
            <a
              key={l.label}
              href={l.href}
              className="ctx-force-white"
              style={{
                fontSize: "0.9375rem",
                textDecoration: "none",
                fontWeight: 500,
                transition: "color 0.15s",
              }}
              onMouseEnter={(e) => ((e.target as HTMLElement).style.color = "var(--ctx-teal)")}
              onMouseLeave={(e) => ((e.target as HTMLElement).style.color = "white")}
            >
              {l.label}
            </a>
          ))}
        </nav>

        {/* CTAs */}
        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", flexShrink: 0 }}>
          <a
            href="https://www.contexia.online/app"
            style={{
              fontSize: "0.875rem",
              color: "white",
              textDecoration: "none",
              fontWeight: 600,
              padding: "0.5rem 1.25rem",
              border: "1.5px solid rgba(255,255,255,0.1)",
              borderRadius: "10px",
              transition: "all 0.15s",
              background: "rgba(255,255,255,0.05)",
              backdropFilter: "blur(8px)",
            }}
          >
            Acceso App
          </a>
          <a
            href={WA_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="ctx-btn-primary"
            style={{ fontSize: "0.875rem", padding: "0.5rem 1rem" }}
          >
            <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path d="M13.601 2.326A7.85 7.85 0 0 0 7.994 0C3.627 0 .068 3.558.064 7.926c0 1.399.366 2.76 1.057 3.965L0 16l4.204-1.102a7.9 7.9 0 0 0 3.79.965h.004c4.368 0 7.926-3.558 7.93-7.93A7.9 7.9 0 0 0 13.6 2.326zM7.994 14.521a6.6 6.6 0 0 1-3.356-.92l-.24-.144-2.494.654.666-2.433-.156-.251a6.56 6.56 0 0 1-1.007-3.505c0-3.626 2.957-6.584 6.591-6.584a6.56 6.56 0 0 1 4.66 1.931 6.56 6.56 0 0 1 1.928 4.66c-.004 3.639-2.961 6.592-6.592 6.592m3.615-4.934c-.197-.099-1.17-.578-1.353-.646-.182-.065-.315-.099-.445.099-.133.197-.513.646-.627.775-.114.133-.232.148-.43.05-.197-.1-.836-.308-1.592-.985-.59-.525-.985-1.175-1.103-1.372-.114-.198-.011-.304.088-.403.087-.088.197-.232.296-.346.1-.114.133-.198.198-.33.065-.134.034-.248-.015-.347-.05-.099-.445-1.076-.612-1.47-.16-.389-.323-.335-.445-.34-.114-.007-.247-.007-.38-.007a.73.73 0 0 0-.529.247c-.182.198-.691.677-.691 1.654s.71 1.916.81 2.049c.098.133 1.394 2.132 3.383 2.992.47.205.84.326 1.129.418.475.152.904.129 1.246.08.38-.058 1.171-.48 1.338-.943.164-.464.164-.86.114-.943-.049-.084-.182-.133-.38-.232z" />
            </svg>
            Taty
          </a>
        </div>
      </div>
    </header>
  );
}
