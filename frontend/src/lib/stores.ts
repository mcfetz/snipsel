import { writable, derived } from 'svelte/store';

import type { Collection, CollectionItem, SearchResponse } from './api';

export type View =
  | { type: 'loading' }
  | { type: 'collections' }
  | { type: 'collection'; id: string }
  | { type: 'collection_settings'; id: string }
  | { type: 'tags_mentions' }
  | { type: 'search' }
  | { type: 'todos' }
  | { type: 'calendar' }
  | { type: 'settings' }
  | { type: 'notifications' }
  | { type: 'importer' }
  | { type: 'recycle-bin' }
  | { type: 'public'; token: string }
  | { type: 'snipsel'; id: string; returnTo?: string };

export const currentView = writable<View>({ type: 'loading' });
export const collections = writable<Collection[]>([]);
export const currentCollection = writable<Collection | null>(null);
export const collectionItems = writable<CollectionItem[]>([]);
export const editingSnipselId = writable<string | null>(null);
export const isLoading = writable(false);
export const newSnipselRequest = writable(0);

export const pendingReference = writable<{ snipselIds: string[]; mode?: 'add' | 'move'; fromCollectionId?: string } | null>(null);

export type CollectionAnchor = { collectionId: string; pos?: number; snipselId?: string } | null;

export const collectionAnchor = writable<CollectionAnchor>(null);

export const searchQuery = writable('');
export const searchResults = writable<SearchResponse | null>(null);
export const searchError = writable<string | null>(null);
export const searchType = writable<string | undefined>(undefined);
export const searchScope = writable<'my' | 'shared' | 'all'>('all');

export const notificationsStore = writable<import('./api').Notification[]>([]);
export const recentCollectionsStore = writable<Array<{ id: string; title: string; icon: string }>>([]);

// Callback for creating snipsel with focus (for mobile keyboard support)
export const createSnipselCallback = writable<(() => Promise<void>) | null>(null);

// Flag to create snipsel after collection loads (for nav bar + button)
export const createSnipselOnLoad = writable(false);

export function requestNewSnipsel() {
  newSnipselRequest.update((n) => n + 1);
}

export function getTodayDate(): string {
  return toLocalIsoDay(new Date());
}

export function toLocalIsoDay(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export const sortedItems = derived(collectionItems, ($items) =>
  [...$items].sort((a, b) => a.position - b.position)
);

// Track if snipsels are selected in CollectionOutliner (for navbar/toolbox animation)
export const snipselsSelected = writable(0);

export const clearSelectionRequest = writable(0);
export const deleteSelectionRequest = writable(0);
export const moveSelectionRequest = writable<{ direction: 'up' | 'down' } | null>(null);
export const indentSelectionRequest = writable<{ direction: 'left' | 'right' } | null>(null);
export const aiAssistantRequest = writable(0);
export const toggleTypeRequest = writable(0);
export const toggleCardViewRequest = writable(0);
export const copySnipselsRequest = writable(0);
export const moveSnipselsRequest = writable(0);
export const infoSnipselsRequest = writable(0);
export const uploadAttachmentRequest = writable(0);
