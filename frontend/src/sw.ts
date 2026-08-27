/// <reference lib="webworker" />
declare let self: ServiceWorkerGlobalScope

import { precacheAndRoute } from 'workbox-precaching'
import { registerRoute } from 'workbox-routing'
import { CacheFirst, NetworkFirst } from 'workbox-strategies'
import { ExpirationPlugin } from 'workbox-expiration'
import { CacheableResponsePlugin } from 'workbox-cacheable-response'

// Precache assets built by Vite
precacheAndRoute(self.__WB_MANIFEST || [])

self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
})

// Cache attachment images
registerRoute(
    ({ url }) => url.pathname.startsWith('/api/attachments/') || url.pathname.includes('/header-image'),
    new CacheFirst({
        cacheName: 'snipsel-attachments',
        plugins: [
            new CacheableResponsePlugin({ statuses: [0, 200] }),
            new ExpirationPlugin({ maxEntries: 100, maxAgeSeconds: 30 * 24 * 60 * 60 })
        ]
    })
)

// Cache API GET requests
registerRoute(
    ({ url, request }) => url.pathname.startsWith('/api/') && request.method === 'GET',
    new NetworkFirst({
        cacheName: 'snipsel-api-fallback',
        networkTimeoutSeconds: 3,
        plugins: [
            new ExpirationPlugin({ maxEntries: 50, maxAgeSeconds: 24 * 60 * 60 })
        ]
    })
)

self.addEventListener('push', (event) => {
    console.log('[ServiceWorker] Push event received!', event);
    let data: any = {}
    try {
        data = event.data?.json() ?? {}
        console.log('[ServiceWorker] Push data:', data);
    } catch (err) {
        console.error('[ServiceWorker] Failed to parse push data', err)
    }

    const title = data.title || 'Snipsel Notification'
    const options = {
        body: data.body || '',
        icon: '/pwa-192x192.png',
        badge: '/pwa-192x192.png',
        data: data.url,
    }

    console.log('[ServiceWorker] Showing notification:', title, options);
    event.waitUntil(self.registration.showNotification(title, options))
})

self.addEventListener('notificationclick', (event) => {
    console.log('[ServiceWorker] Notification click received!', event);
    event.notification.close()
    if (event.notification.data) {
        console.log('[ServiceWorker] Opening URL:', event.notification.data);
        event.waitUntil(self.clients.openWindow(event.notification.data))
    }
})
