/**
 * liveUpdates.ts
 *
 * Manages a long-lived Server-Sent Events connection that receives lightweight
 * "something changed" notifications from the backend.
 *
 * Each browser tab generates a stable random `CLIENT_ID` on startup. This ID is:
 *  1. Sent as a query-param when opening the SSE stream: /api/sse/events?client_id=<uuid>
 *  2. Sent as an `X-Client-Id` header on every mutating API request.
 *
 * The backend embeds the originating `client_id` in every SSE event it publishes.
 * This client ignores events whose `origin_client_id` matches its own — those
 * are mutations it triggered itself, which are already reflected via the
 * optimistic local update.
 *
 * When an event from another client arrives the module decides whether to re-fetch:
 *   - "collection_updated"      → refresh the affected collection if currently displayed
 *   - "snipsels_updated"        → refresh the snipsel list if the collection is open
 *   - "collection_list_changed" → refresh the full collection list in the sidebar
 */

import { get } from 'svelte/store';
import { currentView, collections, collectionItems, currentCollection, notificationsStore } from './stores';
import { idbSaveCollections, idbSaveCollectionItems, idbSaveCollection, idbGetSyncQueue } from './db';
import { requestJson, CLIENT_ID } from './api';
import type { Collection, CollectionItem } from './api';

// ---------------------------------------------------------------------------
// Stable per-tab client identity
// ---------------------------------------------------------------------------

// CLIENT_ID is defined in api.ts and shared across all modules via sessionStorage.
// It is sent as ?client_id= when opening the SSE stream so the backend can
// embed it as `origin_client_id` in every event we publish. This lets us skip
// events we ourselves triggered (the optimistic update is already applied).

// re-export so callers who only import from liveUpdates still have access
export { CLIENT_ID };

// ---------------------------------------------------------------------------
// EventSource management
// ---------------------------------------------------------------------------
let _es: EventSource | null = null;
let _reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let _active = false;
let _reconnectDelay = 2_000; // ms, doubles on failure up to 30 s
const MAX_RECONNECT_DELAY = 30_000;

export function initLiveUpdates(): void {
    _active = true;
    _connect();

    // Pause when tab is hidden, resume when visible again
    document.addEventListener('visibilitychange', _onVisibilityChange);
}

export function destroyLiveUpdates(): void {
    _active = false;
    document.removeEventListener('visibilitychange', _onVisibilityChange);
    _disconnect();
}

function _onVisibilityChange(): void {
    if (document.hidden) {
        _disconnect();
    } else if (_active) {
        _connect();
    }
}

function _connect(): void {
    if (_es) return; // already connected
    if (!navigator.onLine) {
        window.addEventListener('online', _connectOnce, { once: true });
        return;
    }

    // Pass our client_id so the server can embed it in events we publish,
    // allowing us to recognise and skip our own mutations.
    const url = `/api/sse/events?client_id=${encodeURIComponent(CLIENT_ID)}`;
    const es = new EventSource(url, { withCredentials: true });
    _es = es;

    es.onopen = () => {
        _reconnectDelay = 2_000; // reset backoff on successful connection
    };

    es.onmessage = (evt) => {
        try {
            const event = JSON.parse(evt.data);
            _handleEvent(event);
        } catch {
            // ignore malformed events
        }
    };

    es.onerror = () => {
        // EventSource enters CLOSED state on error; we clean up and reconnect
        es.close();
        _es = null;
        if (_active && !document.hidden) {
            _scheduleReconnect();
        }
    };
}

function _connectOnce(): void {
    if (_active && !document.hidden) _connect();
}

function _disconnect(): void {
    if (_reconnectTimer !== null) {
        clearTimeout(_reconnectTimer);
        _reconnectTimer = null;
    }
    if (_es) {
        _es.close();
        _es = null;
    }
}

function _scheduleReconnect(): void {
    if (_reconnectTimer !== null) return;
    _reconnectTimer = setTimeout(() => {
        _reconnectTimer = null;
        if (_active && !document.hidden) _connect();
    }, _reconnectDelay);
    _reconnectDelay = Math.min(_reconnectDelay * 2, MAX_RECONNECT_DELAY);
}

// ---------------------------------------------------------------------------
// Event handling
// ---------------------------------------------------------------------------

const _debounceTimers = new Map<string, ReturnType<typeof setTimeout>>();
function _debounce(key: string, fn: () => void, delayMs = 300) {
    if (_debounceTimers.has(key)) {
        clearTimeout(_debounceTimers.get(key)!);
    }
    _debounceTimers.set(key, setTimeout(() => {
        _debounceTimers.delete(key);
        fn();
    }, delayMs));
}

async function _handleEvent(event: {
    type: string;
    ids?: string[];
    collection_id?: string;
    origin_client_id?: string;
    notification_id?: string;
}): Promise<void> {
    // Ignore events that originated from this very tab – the optimistic
    // local update already reflects the change correctly.
    if (event.origin_client_id && event.origin_client_id === CLIENT_ID) return;

    try {
        if (event.type === 'notification_created') {
            _debounce('notifications', () => { void _refreshNotifications(); });

        } else if (event.type === 'collection_list_changed') {
            _debounce('collection_list', () => { void _refreshCollectionList(); });

        } else if (event.type === 'collection_updated' && event.ids?.length) {
            for (const id of event.ids) {
                _debounce(`collection_${id}`, () => { void _refreshCollection(id); });
            }

        } else if (event.type === 'snipsels_updated' && event.collection_id) {
            const cid = event.collection_id;
            _debounce(`snipsels_${cid}`, () => { void _refreshSnipsels(cid); });
        }
    } catch {
        // Never let a refresh error bubble up and crash the event listener
    }
}

async function _refreshNotifications(): Promise<void> {
    if (!navigator.onLine) return;
    try {
        const res = await requestJson<{ notifications: any[] }>('/api/notifications', { timeout: 10000, cache: 'no-store' });
        notificationsStore.set(res.notifications);
    } catch { /* silently ignore */ }
}

async function _refreshCollectionList(): Promise<void> {
    if (!navigator.onLine) return;
    try {
        const res = await requestJson<{ collections: Collection[] }>('/api/collections', { timeout: 10000, cache: 'no-store' });
        await idbSaveCollections(res.collections);
        collections.set(res.collections);
    } catch { /* silently ignore */ }
}

async function _refreshCollection(id: string): Promise<void> {
    if (!navigator.onLine) return;
    const view = get(currentView);
    const isVisible =
        (view.type === 'collection' && view.id === id) ||
        (view.type === 'collection_settings' && view.id === id);

    try {
        const res = await requestJson<{ collection: Collection }>(`/api/collections/${id}`, { timeout: 10000, cache: 'no-store' });
        await idbSaveCollection(res.collection);

        // Always update the sidebar list entry
        collections.update((cols) =>
            cols.map((c) => (c.id === id ? res.collection : c))
        );
        // Also update the active collection header if visible
        if (isVisible) {
            currentCollection.set(res.collection);
        }
    } catch { /* silently ignore */ }
}

async function _refreshSnipsels(collectionId: string): Promise<void> {
    if (!navigator.onLine) return;
    const view = get(currentView);
    const isVisible =
        (view.type === 'collection' && view.id === collectionId) ||
        (view.type === 'collection_settings' && view.id === collectionId);

    if (!isVisible) return; // don't load data we're not showing

    try {
        const syncQueue = await idbGetSyncQueue();
        if (syncQueue.length > 0) return; // Do not fetch from server and wipe local optimistic updates if local mutations are in flight

        const res = await requestJson<{ items: CollectionItem[] }>(
            `/api/collections/${collectionId}/snipsels`,
            { timeout: 10000, cache: 'no-store' }
        );
        await idbSaveCollectionItems(res.items);
        collectionItems.set(res.items);
    } catch { /* silently ignore */ }
}
