/* Automatisierbar Team PWA — service worker.
   Shell: cache-first (instant launch, offline shell).
   Appointments API: network-first with cached last-good fallback (offline queue view).
   Never touches non-GET (claim/unclaim POSTs pass straight through). */
const CACHE = 'ab-team-v1';
const SHELL = [
  '/team',
  '/team.webmanifest',
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
  if (e.request.method !== 'GET') return; // claim/unclaim/whoami POSTs: leave untouched
  const url = new URL(e.request.url);

  // Appointments queue: network-first, fall back to last-good cache when offline.
  if (url.pathname.startsWith('/api/team/appointments')) {
    e.respondWith(
      fetch(e.request)
        .then((r) => { const copy = r.clone(); caches.open(CACHE).then((c) => c.put(e.request, copy)); return r; })
        .catch(() => caches.match(e.request))
    );
    return;
  }

  // Shell assets: cache-first.
  if (url.pathname === '/team' || url.pathname === '/team.webmanifest'
      || url.pathname.startsWith('/static/team-icon')) {
    e.respondWith(caches.match(e.request).then((c) => c || fetch(e.request)));
  }
});
