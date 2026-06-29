// Contexia Service Worker — KILL-SWITCH (recovery)
//
// The previous SW (cache "contexia-v1") precached the navigation routes and used
// a cache-first strategy for /_next/static/ assets, while CACHE_VERSION was never
// bumped between deploys. After a deploy the cached HTML shell + stale chunks
// poisoned navigation ("[SW] Network failed, trying cache: /app/overview"),
// causing the PWA to flicker and fail to load.
//
// This replacement self-destructs: it skips waiting, deletes every cache,
// unregisters itself, and reloads open windows so clients return to plain network
// (Vercel serves /app/* with no-store, so fresh content is guaranteed).
// A correctly-versioned SW will ship with the rebuilt PWA.

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const cacheNames = await caches.keys();
      await Promise.all(cacheNames.map((name) => caches.delete(name)));
      await self.registration.unregister();
      const clients = await self.clients.matchAll({ type: "window" });
      for (const client of clients) {
        client.navigate(client.url);
      }
    })()
  );
});

// While tearing down, never serve from cache — always hit the network.
self.addEventListener("fetch", (event) => {
  event.respondWith(fetch(event.request));
});
