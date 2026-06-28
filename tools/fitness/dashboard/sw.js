// Comeback dashboard service worker — shell cache + offline-last-data.
const CACHE = 'comeback-v2';
const SHELL = ['./', './index.html', './manifest.webmanifest', './icon.svg', './icon-192.png'];
const DATA_KEY = './dashboard.json';   // normalized key (ignores ?ts= cache-buster)

self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL).catch(() => {})));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET') return;

  // data: network-first, store under a fixed key so the last good payload survives offline
  if (url.pathname.endsWith('/dashboard.json') || url.pathname.endsWith('dashboard.json')) {
    e.respondWith(
      fetch(e.request).then(r => {
        const copy = r.clone();
        caches.open(CACHE).then(c => c.put(DATA_KEY, copy)).catch(() => {});
        return r;
      }).catch(() => caches.match(DATA_KEY))
    );
    return;
  }

  // same-origin shell: cache-first
  if (url.origin === location.origin) {
    e.respondWith(caches.match(e.request).then(m => m || fetch(e.request)));
  }
});
