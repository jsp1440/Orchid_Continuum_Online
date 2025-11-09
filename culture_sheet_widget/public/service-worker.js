const CACHE_NAME = 'orchid-culture-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request)
        .then(fetchResponse => {
          return caches.open(CACHE_NAME).then(cache => {
            if (event.request.method === 'GET') {
              cache.put(event.request, fetchResponse.clone());
            }
            return fetchResponse;
          });
        })
      )
      .catch(() => caches.match('/'))
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
