import { idbGetSyncQueue, idbRemoveSync, idbReplaceTempCollection, idbReplaceTempCollectionItem } from './db';
import { requestJson } from './api';

let syncInProgress = false;

export async function processSyncQueue() {
    if (syncInProgress) return;
    if (!navigator.onLine) return; // Only process if online

    syncInProgress = true;
    try {
        const queue = await idbGetSyncQueue();
        const idMap: Record<string, string> = {}; // Maps temp IDs to real server IDs

        for (const op of queue) {
            if (!navigator.onLine) break; // Network went down during sync

            try {
                // Apply ID translations to endpoint and body
                let endpoint = op.endpoint;
                let bodyStr = op.body ? JSON.stringify(op.body) : undefined;

                for (const [tempId, realId] of Object.entries(idMap)) {
                    endpoint = endpoint.replace(tempId, realId);
                    if (bodyStr) {
                        bodyStr = bodyStr.replace(new RegExp(tempId, 'g'), realId);
                    }
                }

                const res = await requestJson<any>(endpoint, {
                    method: op.method,
                    body: bodyStr,
                });

                // If this was a collection creation endpoint, map its ID and replace temp local record
                if (op.method === 'POST' && res?.collection?.id && op.endpoint === '/api/collections') {
                    if (op.body && (op.body as any)._tempId) {
                        const tempId = (op.body as any)._tempId;
                        idMap[tempId] = res.collection.id;
                        await idbReplaceTempCollection(tempId, res.collection);
                        if (typeof window !== 'undefined') {
                            window.dispatchEvent(new CustomEvent('snipsel-data-refreshed', { detail: { type: 'collection', id: res.collection.id } }));
                        }
                    }
                }

                // If this was a snipsel creation endpoint, map its ID and replace temp local record
                if (op.method === 'POST' && res?.item?.snipsel_id && op.endpoint.endsWith('/snipsels')) {
                    if (op.body && (op.body as any)._tempId) {
                        const tempId = (op.body as any)._tempId;
                        idMap[tempId] = res.item.snipsel_id;
                        await idbReplaceTempCollectionItem(tempId, res.item);
                        if (typeof window !== 'undefined') {
                            window.dispatchEvent(new CustomEvent('snipsel-data-refreshed', { detail: { type: 'snipsels', collectionId: res.item.collection_id } }));
                        }
                    }
                }

                // Success -> remove from queue
                await idbRemoveSync(op.id);
            } catch (err: any) {
                // If the error is a controlled ApiError (400, 403, 404), drop it to unblock queue.
                if (err?.error?.code && err.error.code !== 'network_error' && err.error.code !== 'unknown_error') {
                    console.warn('[Sync Queue] Dropping failed operation (client error)', op, err);
                    await idbRemoveSync(op.id);
                } else {
                    // Network error or 500, we keep it to retry later
                    console.error('[Sync Queue] Transient error, stopping queue processing', op, err);
                    break;
                }
            }
        }
    } finally {
        syncInProgress = false;
    }
}

export function initSyncManager() {
    if (typeof window !== 'undefined') {
        window.addEventListener('online', () => {
            processSyncQueue();
        });
        window.addEventListener('snipsel-sync-queued', () => {
            processSyncQueue();
        });

        // Initial run
        setTimeout(processSyncQueue, 1000);
    }
}
