import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";

export const metadata: Metadata = {
  title: "Shadow Audit Gratuito — Contexia",
  description:
    "Analiza tu empresa en 5 minutos. Descubre cuánto pagarías en Régimen Simple vs Ordinario, tus riesgos DIAN y tu plan de acción 30-60-90 días.",
  openGraph: {
    title: "Shadow Audit Gratuito — Contexia",
    description:
      "Tu diagnóstico tributario personalizado. Gratis. Sin compromiso.",
    url: "https://www.contexia.online/wizard",
    siteName: "Contexia",
    images: [{ url: "https://www.contexia.online/assets/img/logo_official.png" }],
  },
};

const GA_ID = "G-Q03PYP6RBH";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" style={{ backgroundColor: "#020617" }}>
      <head>
        <link rel="icon" href="https://www.contexia.online/assets/img/logo_official.png" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&family=Orbitron:wght@400;500;600;700;800;900&display=swap" rel="stylesheet" />
        {/* Google Analytics GA4 */}
        <Script
          src={`https://www.googletagmanager.com/gtag/js?id=${GA_ID}`}
          strategy="afterInteractive"
        />
        <Script id="google-analytics" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', '${GA_ID}');
          `}
        </Script>
        <style>
          {`
            :root {
              --ctx-navy-dark: #020617;
              --ctx-teal: #2dd4bf;
              --ctx-text: #f8fafc;
            }
            body {
              background-color: #020617 !important;
              color: #f8fafc !important;
              margin: 0;
              font-family: sans-serif;
            }
            a { color: #f8fafc; text-decoration: none; }
            .ctx-btn-primary {
              background: #2dd4bf !important;
              color: #020617 !important;
            }
          `}
        </style>
      </head>
      <body style={{ backgroundColor: "#020617", color: "#f8fafc", margin: 0 }}>{children}</body>
    </html>
  );
}
