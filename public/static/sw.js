/* Swastya Assist V11.1.8: cache only the generic offline capture shell and its assets.
   Never cache authenticated pages, session data, API responses, uploaded reports, or AI output. */
'use strict';
const CACHE_NAME = 'swastya-offline-shell-v118';
const PRECACHE = [
  '/offline-capture',
  '/static/offline_capture.css?v=1',
  '/static/offline_capture.js?v=1',
  '/static/swastya-assist-logo.jpg?v=35.0',
  '/static/favicon.ico?v=35.0'
];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith('swastya-offline-shell-') && k !== CACHE_NAME).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith('/api/') || ['/console','/','/login','/register','/admin','/patient','/logout'].includes(url.pathname)) return;
  if (url.pathname === '/offline-capture' || url.pathname.startsWith('/static/offline_capture.') || url.pathname === '/static/swastya-assist-logo.jpg' || url.pathname === '/static/favicon.ico') {
    event.respondWith(caches.match(request).then(cached => cached || fetch(request).then(response => {
      if (response.ok) caches.open(CACHE_NAME).then(cache => cache.put(request,response.clone()));
      return response;
    }).catch(() => caches.match('/offline-capture'))));
  }
});
