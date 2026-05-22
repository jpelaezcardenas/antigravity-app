import { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Contexia",
    short_name: "Contexia",
    description:
      "Plataforma inteligente de control financiero, fiscal y patrimonial para dueños de empresa",
    start_url: "/app",
    scope: "/app",
    display: "standalone",
    orientation: "portrait-primary",
    background_color: "#0A0A0A",
    theme_color: "#57F1DB",
    icons: [
      {
        src: "/icons/icon-192x192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icons/icon-192x192-maskable.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "maskable",
      },
      {
        src: "/icons/icon-512x512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icons/icon-512x512-maskable.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
    categories: ["business", "finance"],
    screenshots: [
      {
        src: "/screenshots/screenshot-540x720.png",
        sizes: "540x720",
        type: "image/png",
        form_factor: "narrow",
      },
      {
        src: "/screenshots/screenshot-1280x720.png",
        sizes: "1280x720",
        type: "image/png",
        form_factor: "wide",
      },
    ],
    shortcuts: [
      {
        name: "Visión General",
        short_name: "Pulso",
        description: "Accede al tablero de control",
        url: "/app/overview",
        icons: [
          {
            src: "/icons/icon-192x192.png",
            sizes: "192x192",
            type: "image/png",
          },
        ],
      },
      {
        name: "Desglose Fiscal",
        short_name: "Fiscal",
        description: "Revisa tu estado fiscal",
        url: "/app/fiscal",
        icons: [
          {
            src: "/icons/icon-192x192.png",
            sizes: "192x192",
            type: "image/png",
          },
        ],
      },
      {
        name: "Proyecciones",
        short_name: "Radar",
        description: "Analiza escenarios futuros",
        url: "/app/radar",
        icons: [
          {
            src: "/icons/icon-192x192.png",
            sizes: "192x192",
            type: "image/png",
          },
        ],
      },
    ],
    prefer_related_applications: false,
  };
}
