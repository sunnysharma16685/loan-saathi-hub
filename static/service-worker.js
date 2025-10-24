const CACHE_NAME = "loan-saathi-hub-v1";
const urlsToCache = [
  "/",
  "/static/css/site.css",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
  "/static/icons/favicon.ico",
];

// ✅ Install event (pre-cache static assets)
self.addEventListener("install", (event) => {
  console.log("🟢 Service Worker: Installing...");
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("📦 Caching assets...");
      return cache.addAll(urlsToCache);
    })
  );
});

// ✅ Activate event (clean old caches)
self.addEventListener("activate", (event) => {
  console.log("🔵 Service Worker: Activated");
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log("🗑 Deleting old cache:", key);
            return caches.delete(key);
          }
        })
      );
    })
  );
});

// ✅ Fetch event (cache-first strategy)
self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      if (response) {
        // ✅ Return from cache
        return response;
      }

      // 🔄 Fetch from network
      return fetch(event.request)
        .then((networkResponse) => {
          if (
            !networkResponse ||
            networkResponse.status !== 200 ||
            networkResponse.type !== "basic"
          ) {
            return networkResponse;
          }

          // ✅ Clone response and store in cache
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });

          return networkResponse;
        })
.catch(() =>
  caches.match("/offline/") // Optional: serve offline page
);
    })
  );
});

// ✅ Optional: handle push notifications (future-ready)
self.addEventListener("push", (event) => {
  const data = event.data ? event.data.text() : "Loan Saathi Hub Notification";
  event.waitUntil(
    self.registration.showNotification("Loan Saathi Hub", {
      body: data,
      icon: "/static/icons/icon-192.png",
    })
  );
});
