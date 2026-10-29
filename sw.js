// Minimaler Service Worker: macht die App installierbar und hält die eigenen Seiten bei Funkloch bereit.
const CACHE = "rmt-v2";
const SHELL = ["./", "index.html", "karte.html", "impressum.html", "datenschutz.html", "legal.css", "i18n.js", "manifest.webmanifest", "icons/icon.svg", "icons/icon-192.png", "icons/icon-512.png",
               "vendor/fonts.css", "vendor/leaflet.css", "vendor/leaflet.js", "vendor/supabase.js"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)));
  self.skipWaiting();
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});
// Eigene Dateien: zuerst aus dem Netz (immer aktuell), ohne Netz aus dem Speicher.
// Fremde Anfragen (Kartenbilder, Datenbank) gehen unverändert ins Netz.
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  e.respondWith(
    fetch(e.request)
      .then(res => { const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); return res; })
      .catch(() => caches.match(e.request, { ignoreSearch: true }))
  );
});
