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
    <html lang="es">
      <head>
        <link rel="icon" href="https://www.contexia.online/assets/img/logo_official.png" />
        {/* Google Analytics GA4 */}
        <Script
          src={`https://www.googletagmanager.com/gtag/js?id=${GA_ID}`}
          strategy="afterInteractive"
        />
        <Script id="ga4-init" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', '${GA_ID}');
          `}
        </Script>
      </head>
      <body>{children}</body>
    </html>
  );
}
