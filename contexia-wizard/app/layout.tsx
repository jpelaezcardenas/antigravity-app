import type { Metadata } from "next";
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

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <head>
        <link rel="icon" href="https://www.contexia.online/assets/img/logo_official.png" />
      </head>
      <body>{children}</body>
    </html>
  );
}
