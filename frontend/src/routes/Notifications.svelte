<script lang="ts">
  import Bell from '@animated-color-icons/lucide-svelte/Bell.svelte';
  import { api, type Notification } from '../lib/api';
  import { notificationsStore, currentView, collectionAnchor } from '../lib/stores';
  import { currentUser } from '../lib/session';
  import { computeHeaderColor, computeCardTileBg } from '../lib/colors';

  let viewMode: 'unread' | 'read' = $state('unread');
  let isBusy = $state(false);

  function getAccent(): string {
    return computeHeaderColor($currentUser?.default_collection_header_color);
  }

  function getAccentTint(): string {
    const isDark = typeof document !== 'undefined' && document.documentElement.classList.contains('dark');
    return computeCardTileBg(getAccent(), isDark);
  }

  let filteredNotifications = $derived(
    $notificationsStore.filter(n => (viewMode === 'unread' ? !n.is_read : n.is_read))
  );

  async function toggleReadStatus(n: Notification, e: Event) {
    e.stopPropagation(); // prevent clicking the card
    isBusy = true;
    try {
      if (!n.is_read) {
        await api.notifications.markRead(n.id);
        notificationsStore.update(store =>
          store.map(x => (x.id === n.id ? { ...x, is_read: true } : x))
        );
      }
    } finally {
      isBusy = false;
    }
  }

  async function openNotification(n: Notification) {
    if (!n.is_read) {
      await api.notifications.markRead(n.id);
      notificationsStore.update(store =>
        store.map(x => (x.id === n.id ? { ...x, is_read: true } : x))
      );
    }

    if (n.collection_id && n.snipsel_id) {
      collectionAnchor.set({ collectionId: n.collection_id, snipselId: n.snipsel_id });
      currentView.set({ type: 'collection', id: n.collection_id });
    } else if (n.snipsel_id) {
      currentView.set({ type: 'snipsel', id: n.snipsel_id });
    } else if (n.collection_id) {
      currentView.set({ type: 'collection', id: n.collection_id });
    }
  }

  async function markAllRead() {
    isBusy = true;
    try {
      await api.notifications.markAllRead();
      notificationsStore.update(store => store.map(x => ({ ...x, is_read: true })));
    } finally {
      isBusy = false;
    }
  }

  async function deleteAllRead() {
    isBusy = true;
    try {
      await api.notifications.deleteRead();
      notificationsStore.update(store => store.filter(x => !x.is_read));
    } finally {
      isBusy = false;
    }
  }

  function formatDate(iso: string) {
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }
</script>

<div class="space-y-4">
  <h2 class="flex items-center gap-2 text-2xl font-semibold dark:text-slate-100">
    <Bell label="" size={24} className="text-slate-700 dark:text-slate-300" />
    <span>Notifications</span>
  </h2>

  <div class="overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-900 dark:ring-white/10">
    <div class="grid grid-cols-2">
      <button
        class="px-4 py-3 text-sm font-medium transition-colors {viewMode === 'unread'
          ? 'text-slate-900'
          : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
        type="button"
        onclick={() => (viewMode = 'unread')}
        style={viewMode === 'unread' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
      >
        Unread
      </button>
      <button
        class="border-l border-black/5 px-4 py-3 text-sm font-medium transition-colors dark:border-white/5 {viewMode === 'read'
          ? 'text-slate-900'
          : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
        type="button"
        onclick={() => (viewMode = 'read')}
        style={viewMode === 'read' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
      >
        Read
      </button>
    </div>
  </div>

  {#if filteredNotifications.length === 0}
    <div class="py-8 text-center text-sm text-slate-500">No {viewMode} notifications</div>
  {:else}
    <div class="space-y-2">
      {#each filteredNotifications as n (n.id)}
        <div class="flex w-full items-center gap-3 px-1 py-2">
          <button class="min-w-0 flex flex-1 items-start gap-3 text-left" type="button" onclick={() => openNotification(n)}>
            <div class="min-w-0 flex-1">
              <div class="truncate text-lg font-medium text-slate-900 dark:text-slate-100">{n.message}</div>
              <div class="mt-0.5 flex flex-wrap items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
                <span>{formatDate(n.created_at)}</span>
              </div>
            </div>
          </button>
          
          {#if !n.is_read}
            <button
              class="grid h-8 w-8 shrink-0 place-items-center rounded-full border border-slate-300 bg-white transition-all hover:bg-slate-50 disabled:opacity-40 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
              type="button"
              aria-label="Mark as read"
              title="Mark as read"
              disabled={isBusy}
              style={`border-color: ${getAccent()}`}
              onclick={(e) => toggleReadStatus(n, e)}
            >
              <span class="text-sm font-semibold" style={`color: ${getAccent()}`}>✓</span>
            </button>
          {/if}
        </div>
      {/each}

      <div class="pt-6">
        {#if viewMode === 'unread'}
          <button
            class="w-full rounded-full border border-slate-200 bg-white px-4 py-3.5 text-base font-semibold shadow-sm ring-1 ring-black/5 transition-all hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-900 dark:ring-white/10 dark:hover:bg-white/5"
            style={`color: ${getAccent()}`}
            onclick={markAllRead}
            disabled={isBusy}
          >
            Mark all as read
          </button>
        {:else}
          <button
            class="w-full rounded-full border border-slate-200 bg-white px-4 py-3.5 text-base font-semibold text-red-600 shadow-sm ring-1 ring-black/5 transition-all hover:bg-red-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-900 dark:ring-white/10 dark:hover:bg-white/5"
            onclick={deleteAllRead}
            disabled={isBusy}
          >
            Delete all read
          </button>
        {/if}
      </div>
    </div>
  {/if}
</div>