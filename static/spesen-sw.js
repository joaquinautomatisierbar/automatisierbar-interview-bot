/* KnowSpesen PWA — service worker.
   Shell: cache-first (instant launch, offline shell).
   Never touches non-GET (OCR + beleg + month-close POSTs pass straight through —
   capture is online-only; a failed call surfaces a retry toast). */
const CACHE = 'knowspesen-v2';
const SHELL = [
  '/spesen',
  '/spesen.webmanifest',
  '/static/spesen-icon-192.png',
  '/static/spesen-icon-512.png',
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(SHELL).catch(() => {})).then(() => self.skipWaiting())
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
  if (e.request.method !== 'GET') return; // OCR/beleg/close POSTs: leave untouched
  const url = new URL(e.request.url);
  if (url.pathname === '/spesen' || url.pathname === '/spesen.webmanifest'
      || url.pathname.startsWith('/static/spesen-icon')) {
    e.respondWith(caches.match(e.request).then((c) => c || fetch(e.request)));
  }
});
