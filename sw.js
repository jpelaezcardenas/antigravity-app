// Service Worker para Contexia PWA
// Estrategia: Network-first para HTML, Cache-first para assets

const CACHE_VERSION = "v2-live-pulso";
const CACHE_NAME = `contexia-${CACHE_VERSION}`;

// Assets estáticos que cachear al instalar
const STATIC_ASSETS = [
  "/",
  "/app",
  "/app/overview",
  "/app/fiscal",
  "/app/radar",
  "/app/patrimonio",
  "/app/flujo-detalle",
  "/icons/icon-192x192.png",
  "/icons/icon-512x512.png",
];

// Extensiones de archivo que cacheamos agresivamente
const CACHE_FIRST_PATTERNS = [
  /\.(?:png|jpg|jpeg|svg|gif|webp)$/,
  /\.(?:woff2|woff|ttf|eot)$/,
  /\/_next\/static\//,
];

// Instalar: cachear assets estáticos mínimos
self.addEventListener("install", (event) => {
  console.log("[SW] Installing Contexia Service Worker");
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("[SW] Caching static assets");
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn("[SW] Some assets failed to cache (expected for dynamic routes)", err);
      });
    })
  );
  self.skipWaiting();
});

// Activar: limpiar caches viejos
self.addEventListener("activate", (event) => {
  console.log("[SW] Activating Contexia Service Worker");
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log("[SW] Deleting old cache:", cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch: Network-first para HTML, Cache-first para assets
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Ignorar solicitudes fuera de nuestro origen
  if (url.origin !== self.location.origin) {
    return;
  }

  // Cache-first para assets estáticos
  if (CACHE_FIRST_PATTERNS.some((pattern) => pattern.test(url.pathname))) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) {
          console.log("[SW] Cache hit:", url.pathname);
          return cached;
        }
        console.log("[SW] Fetching:", url.pathname);
        return fetch(request).then((response) => {
          // Solo cachear respuestas exitosas
          if (response.status === 200) {
            const cache = caches.open(CACHE_NAME).then((c) => {
              c.put(request, response.clone());
              return response;
            });
            return cache;
          }
          return response;
        });
      })
    );
    return;
  }

  // Network-first para HTML y rutas dinámicas
  event.respondWith(
    fetch(request)
      .then((response) => {
        // Cachear respuestas exitosas de HTML
        if (
          response.status === 200 &&
          (request.mode === "navigate" || request.destination === "document")
        ) {
          const cache = caches.open(CACHE_NAME).then((c) => {
            c.put(request, response.clone());
            return response;
          });
          return cache;
        }
        return response;
      })
      .catch(() => {
        // Fallback a cache si network falla
        console.log("[SW] Network failed, trying cache:", url.pathname);
        return caches.match(request).then((cached) => {
          if (cached) {
            return cached;
          }
          // Última opción: página de error offline simple
          return new Response("Offline - Por favor intenta de nuevo cuando tengas conexión", {
            status: 503,
            statusText: "Service Unavailable",
            headers: new Headers({
              "Content-Type": "text/plain; charset=utf-8",
            }),
          });
        });
      })
  );
});
