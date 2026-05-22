"use client";

/**
 * Register Service Worker para Contexia PWA
 * Encapsulado y simple: sin dependencias, solo API nativa
 */

export function registerServiceWorker() {
  if (typeof window === "undefined") {
    return;
  }

  // Solo en HTTPS o localhost (requisito de SW)
  const isLocalhost = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
  const isHttps = window.location.protocol === "https:";

  if (!isLocalhost && !isHttps) {
    console.warn("[PWA] Service Worker requiere HTTPS o localhost");
    return;
  }

  if (!("serviceWorker" in navigator)) {
    console.warn("[PWA] Service Worker no soportado en este navegador");
    return;
  }

  // Registrar el SW
  navigator.serviceWorker
    .register("/sw.js", {
      scope: "/",
      updateViaCache: "none",
    })
    .then((registration) => {
      console.log("[PWA] Service Worker registrado:", registration);

      // Verificar actualizaciones cada vez que la página se enfoca
      window.addEventListener("focus", () => {
        registration.update().catch((err) => {
          console.error("[PWA] Error actualizando SW:", err);
        });
      });
    })
    .catch((err) => {
      console.error("[PWA] Error registrando Service Worker:", err);
    });
}
