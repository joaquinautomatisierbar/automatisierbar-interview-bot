/* Automatisierbar Walk-in PWA — service worker.
   Shell: cache-first (instant launch, offline shell).
   Never touches non-GET (lead-create + memo-upload POSTs pass straight through —
   Phase 1 is online-only; a failed upload surfaces a retry toast). */
const CACHE = 'ab-walkin-v2';
const SHELL = [
  '/walkin',
  '/walkin.webmanifest',
  '/static/team-icon-192.png',
  '/static/team-icon-512.png',
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return; // lead/memo POSTs: leave untouched
  const url = new URL(e.request.url);
  // Shell assets only: cache-first. Everything else hits the network normally.
  if (url.pathname === '/walkin' || url.pathname === '/walkin.webmanifest'
      || url.pathname.startsWith('/static/team-icon')) {
    e.respondWith(caches.match(e.request).then((c) => c || fetch(e.request)));
  }
});
