import { openDB, type DBSchema, type IDBPDatabase } from 'idb';
import type { Collection, CollectionItem, Snipsel } from './api';

export interface SyncOperation {
    id: string;
    method: 'POST' | 'PUT' | 'DELETE' | 'PATCH';
    endpoint: string;
    body?: any;
    createdAt: number;
}

export interface SnipselDB extends DBSchema {
    collections: {
        key: string;
        value: Collection;
    };
    collectionItems: {
        key: [string, string]; // [collection_id, snipsel_id]
        value: CollectionItem;
        indexes: {
            'by-collection': string;
        };
    };
    syncQueue: {
        key: string;
        value: SyncOperation;
    };
}

let dbPromise: Promise<IDBPDatabase<SnipselDB>> | null = null;

export async function getDB(): Promise<IDBPDatabase<SnipselDB>> {
    if (!dbPromise) {
        dbPromise = openDB<SnipselDB>('snipsel-db', 1, {
            upgrade(db) {
                if (!db.objectStoreNames.contains('collections')) {
                    db.createObjectStore('collections', { keyPath: 'id' });
                }
                if (!db.objectStoreNames.contains('collectionItems')) {
                    const store = db.createObjectStore('collectionItems', { keyPath: ['collection_id', 'snipsel_id'] });
                    store.createIndex('by-collection', 'collection_id');
                }
                if (!db.objectStoreNames.contains('syncQueue')) {
                    db.createObjectStore('syncQueue', { keyPath: 'id' });
                }
            },
        });
    }
    return dbPromise;
}

// -- Collections --
export async function idbSaveCollections(collections: Collection[]) {
    const queue = await idbGetSyncQueue();
    const hasPendingMutations = queue.some(op => op.endpoint.includes('/api/collections'));
    if (hasPendingMutations) return;

    const db = await getDB();
    const tx = db.transaction('collections', 'readwrite');
    await Promise.all(collections.map((c) => tx.store.put(c)));
    await tx.done;
}

export async function idbSaveCollection(collection: Collection) {
    const db = await getDB();
    await db.put('collections', collection);
}

export async function idbGetCollection(id: string): Promise<Collection | undefined> {
    const db = await getDB();
    return db.get('collections', id);
}

export async function idbGetAllCollections(): Promise<Collection[]> {
    const db = await getDB();
    return db.getAll('collections');
}

export async function idbDeleteCollection(id: string) {
    const db = await getDB();
    await db.delete('collections', id);
}

// -- Collection Items --
export async function idbSaveCollectionItems(items: CollectionItem[]) {
    if (items.length === 0) return;
    const collectionId = items[0].collection_id;
    
    // Protection against race conditions: Do not overwrite local IDB state
    // with server GET responses if we have pending optimistic mutations for this collection.
    const queue = await idbGetSyncQueue();
    const hasPendingMutations = queue.some(op => 
        op.endpoint.includes(`/api/collections/${collectionId}`) || 
        op.endpoint.includes(`/api/snipsels/`)
    );
    
    if (hasPendingMutations) return;

    const db = await getDB();
    const tx = db.transaction('collectionItems', 'readwrite');
    await Promise.all(items.map((item) => tx.store.put(item)));
    await tx.done;
}

export async function idbSaveCollectionItem(item: CollectionItem) {
    const db = await getDB();
    await db.put('collectionItems', item);
}

export async function idbGetCollectionItems(collectionId: string): Promise<CollectionItem[]> {
    const db = await getDB();
    const items = await db.getAllFromIndex('collectionItems', 'by-collection', collectionId);
    return items.sort((a, b) => a.position - b.position);
}

export async function idbDeleteCollectionItem(collectionId: string, snipselId: string) {
    const db = await getDB();
    await db.delete('collectionItems', [collectionId, snipselId]);
}

// Helper: If a snipsel text/done status is updated globally, we might want to update it in all collections
export async function idbUpdateSnipselData(snipselId: string, partialSnipsel: Partial<Snipsel>) {
    const db = await getDB();
    const tx = db.transaction('collectionItems', 'readwrite');
    const items = await tx.store.getAll();
    const matched = items.filter((item) => item.snipsel_id === snipselId);
    for (const item of matched) {
        item.snipsel = { ...item.snipsel, ...partialSnipsel } as Snipsel;
        await tx.store.put(item);
    }
    await tx.done;
}

// -- Sync Queue --
export async function idbEnqueueSync(method: SyncOperation['method'], endpoint: string, body?: any) {
    const db = await getDB();
    const op: SyncOperation = {
        id: crypto.randomUUID(),
        method,
        endpoint,
        body,
        createdAt: Date.now(),
    };
    await db.put('syncQueue', op);

    if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('snipsel-sync-queued'));
    }
}

export async function idbGetSyncQueue(): Promise<SyncOperation[]> {
    const db = await getDB();
    const all = await db.getAll('syncQueue');
    return all.sort((a, b) => a.createdAt - b.createdAt);
}

export async function idbRemoveSync(id: string) {
    const db = await getDB();
    await db.delete('syncQueue', id);
}

export async function idbReplaceTempCollection(tempId: string, realCollection: Collection): Promise<Collection> {
    const db = await getDB();
    const tx = db.transaction('collections', 'readwrite');
    const existing = await tx.store.get(tempId);
    await tx.store.delete(tempId);
    
    const finalCollection = existing ? {
        ...existing,
        id: realCollection.id,
        created_at: realCollection.created_at || existing.created_at
    } : realCollection;
    
    await tx.store.put(finalCollection);
    await tx.done;
    return finalCollection;
}

export async function idbReplaceTempCollectionItem(tempSnipselId: string, realItem: CollectionItem): Promise<CollectionItem> {
    const db = await getDB();
    const tx = db.transaction('collectionItems', 'readwrite');
    
    // An item is stored by [collection_id, snipsel_id]. 
    // We need to find all items that have this tempSnipselId.
    const all = await tx.store.getAll();
    const matches = all.filter(i => i.snipsel_id === tempSnipselId);
    
    let finalItem = realItem;

    for (const m of matches) {
        await tx.store.delete([m.collection_id, m.snipsel_id]);
        finalItem = {
            ...m,
            snipsel_id: realItem.snipsel_id,
            snipsel: {
                ...m.snipsel,
                id: realItem.snipsel_id,
                created_by_id: realItem.snipsel.created_by_id, // ensure user ownership is updated
                created_at: realItem.snipsel.created_at || m.snipsel.created_at
            }
        };
        await tx.store.put(finalItem);
    }
    
    // If no matches found, we just append the realItem
    if (matches.length === 0) {
        await tx.store.put(realItem);
    }

    await tx.done;
    return finalItem;
}
