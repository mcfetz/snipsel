<script lang="ts">
  import ArrowLeft from '@animated-color-icons/lucide-svelte/ArrowLeft.svelte';
  import Trash2 from '@animated-color-icons/lucide-svelte/Trash2.svelte';
  import Trash from '@animated-color-icons/lucide-svelte/Trash.svelte';
  import Undo from '@animated-color-icons/lucide-svelte/Undo.svelte';
  import { api, type Collection, type Snipsel } from '../lib/api';
  import { currentView } from '../lib/stores';
  import { currentUser } from '../lib/session';
  import DeleteConfirmModal from '../lib/DeleteConfirmModal.svelte';

  const DEFAULT_ACCENT = '#4f46e5';
  type Rgb = { r: number; g: number; b: number };

  function clampByte(n: number): number {
    return Math.max(0, Math.min(255, Math.round(n)));
  }

  function hexToRgb(hex: string): Rgb | null {
    const h = (hex || '').trim();
    const m = /^#([0-9a-fA-F]{6})$/.exec(h);
    if (!m) return null;
    const v = m[1];
    return {
      r: parseInt(v.slice(0, 2), 16),
      g: parseInt(v.slice(2, 4), 16),
      b: parseInt(v.slice(4, 6), 16),
    };
  }

  function mixRgb(a: Rgb, b: Rgb, t: number): Rgb {
    const tt = Math.max(0, Math.min(1, t));
    return {
      r: clampByte(a.r + (b.r - a.r) * tt),
      g: clampByte(a.g + (b.g - a.g) * tt),
      b: clampByte(a.b + (b.b - a.b) * tt),
    };
  }

  function rgba(c: Rgb, alpha: number): string {
    const a = Math.max(0, Math.min(1, alpha));
    return `rgba(${c.r}, ${c.g}, ${c.b}, ${a})`;
  }

  function getAccent(): string {
    const raw = ($currentUser?.default_collection_header_color || '').trim() || DEFAULT_ACCENT;
    return /^#[0-9a-fA-F]{6}$/.test(raw) ? raw : DEFAULT_ACCENT;
  }

  function getAccentTint(): string {
    const isDark = document.documentElement.classList.contains('dark');
    const baseColor = isDark ? '#1e293b' : '#ffffff';
    const base = hexToRgb(baseColor) ?? { r: 255, g: 255, b: 255 };
    const accent = hexToRgb(getAccent());
    const mixed = accent ? mixRgb(base, accent, 0.14) : base;
    return rgba(mixed, 0.96);
  }

  let deletedCollections = $state<Collection[]>([]);
  let deletedSnipsels = $state<Snipsel[]>([]);
  let isBusy = $state(false);
  let errorMsg = $state('');
  let showEmptyConfirm = $state(false);
  let showDeleteConfirmId = $state<string | null>(null);
  
  let activeTab: 'collections' | 'snipsels' = $state('collections');

  async function loadTrash() {
    isBusy = true;
    errorMsg = '';
    try {
      const [colRes, snipRes] = await Promise.all([
        api.collections.trash(),
        api.snipsels.trash()
      ]);
      deletedCollections = colRes.collections;
      deletedSnipsels = snipRes.snipsels;
    } catch (err: any) {
      errorMsg = err.error?.message || 'Failed to load deleted items';
    } finally {
      isBusy = false;
    }
  }

  async function restoreCollection(id: string) {
    isBusy = true;
    errorMsg = '';
    try {
      await api.collections.restore(id);
      deletedCollections = deletedCollections.filter(c => c.id !== id);
    } catch (err: any) {
      errorMsg = err.error?.message || 'Failed to restore collection';
    } finally {
      isBusy = false;
    }
  }

  async function restoreSnipsel(id: string) {
    isBusy = true;
    errorMsg = '';
    try {
      // Find today's collection ID to restore snipsel into
      const res = await api.collections.today();
      await api.snipsels.restore(id, res.collection.id);
      deletedSnipsels = deletedSnipsels.filter(s => s.id !== id);
    } catch (err: any) {
      errorMsg = err.error?.message || 'Failed to restore snipsel';
    } finally {
      isBusy = false;
    }
  }

  async function emptyTrash() {
    isBusy = true;
    errorMsg = '';
    showEmptyConfirm = false;
    try {
      if (activeTab === 'collections') {
        await api.collections.emptyTrash();
        deletedCollections = [];
      } else {
        await api.snipsels.emptyTrash();
        deletedSnipsels = [];
      }
    } catch (err: any) {
      errorMsg = err.error?.message || `Failed to empty ${activeTab}`;
    } finally {
      isBusy = false;
    }
  }

  async function deleteTrashItem() {
    if (!showDeleteConfirmId) return;
    
    isBusy = true;
    errorMsg = '';
    const targetId = showDeleteConfirmId;
    showDeleteConfirmId = null;
    
    try {
      if (activeTab === 'collections') {
        await api.collections.deleteTrashItem(targetId);
        deletedCollections = deletedCollections.filter(c => c.id !== targetId);
      } else {
        await api.snipsels.deleteTrashItem(targetId);
        deletedSnipsels = deletedSnipsels.filter(s => s.id !== targetId);
      }
    } catch (err: any) {
      errorMsg = err.error?.message || `Failed to permanently delete item`;
    } finally {
      isBusy = false;
    }
  }

  function formatDate(dateString: string | null | undefined) {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleString(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short'
    });
  }

  $effect(() => {
    loadTrash();
  });
</script>

<div class="space-y-4">
  <div class="flex items-center gap-2">
    <button
      class="al-icon-wrapper rounded-full p-2 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors"
      onclick={() => currentView.set({ type: 'settings' })}
      title="Back to Settings"
      aria-label="Back to Settings"
    >
      <ArrowLeft label="" size={20} />
    </button>
    <h2 class="flex items-center gap-2 text-2xl font-semibold">
      <Trash2 label="" size={24} className="text-slate-700 dark:text-slate-300" />
      <span>Recycle Bin</span>
    </h2>
  </div>

  {#if errorMsg}
    <div class="rounded-lg bg-red-50 p-3 text-sm text-red-600 dark:bg-red-900/30 dark:text-red-400">
      {errorMsg}
    </div>
  {/if}

  <div class="flex items-center justify-between gap-4">
    <div class="flex items-center gap-2 flex-1">
      <div class="flex flex-1 overflow-hidden rounded-full border border-slate-200 bg-white dark:border-white/10 dark:bg-slate-900" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'collections'}
          class="flex-1 px-4 py-3 text-base font-medium transition-colors {activeTab === 'collections'
            ? 'text-slate-900'
            : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
          style={activeTab === 'collections' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          onclick={() => activeTab = 'collections'}
        >
          Collections ({deletedCollections.length})
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'snipsels'}
          class="flex-1 border-l border-black/5 px-4 py-3 text-base font-medium transition-colors dark:border-white/5 {activeTab === 'snipsels'
            ? 'text-slate-900'
            : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
          style={activeTab === 'snipsels' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          onclick={() => activeTab = 'snipsels'}
        >
          Snipsels ({deletedSnipsels.length})
        </button>
      </div>
    </div>
    
    {#if (activeTab === 'collections' && deletedCollections.length > 0) || (activeTab === 'snipsels' && deletedSnipsels.length > 0)}
      <button
        class="al-icon-wrapper flex shrink-0 h-12 w-12 sm:w-auto sm:px-4 items-center justify-center gap-2 rounded-full border border-red-200 bg-white text-sm font-medium text-red-600 shadow-sm hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 dark:border-red-900/30 dark:bg-slate-900 dark:text-red-400 dark:hover:bg-red-900/20"
        onclick={() => showEmptyConfirm = true}
        disabled={isBusy}
        title="Empty {activeTab}"
      >
        <Trash label="" size={20} />
        <span class="hidden sm:inline">Empty {activeTab === 'collections' ? 'Collections' : 'Snipsels'}</span>
      </button>
    {/if}
  </div>

  <div class="mt-4">
    {#if activeTab === 'collections'}
      {#if deletedCollections.length === 0}
        <div class="py-8 text-center text-sm text-slate-500 dark:text-slate-400">No deleted collections found.</div>
      {:else}
        <div class="grid gap-3 sm:grid-cols-2">
          {#each deletedCollections as col (col.id)}
            <div class="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div class="min-w-0 flex-1 pl-2">
                <div class="flex items-center gap-2">
                  <span class="text-xl">{col.icon}</span>
                  <span class="truncate font-medium text-slate-900 dark:text-slate-100">{col.title}</span>
                </div>
                <div class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  Deleted: {formatDate((col as any).deleted_at)}
                </div>
              </div>
              <div class="ml-3 flex items-center gap-1 shrink-0">
                <button
                  class="al-icon-wrapper flex h-8 w-8 items-center justify-center rounded-full text-slate-500 hover:bg-slate-100 hover:text-slate-900 disabled:opacity-50 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100 transition-colors"
                  onclick={() => restoreCollection(col.id)}
                  disabled={isBusy}
                  title="Restore Collection"
                >
                  <Undo label="" size={16} />
                </button>
                <button
                  class="al-icon-wrapper flex h-8 w-8 items-center justify-center rounded-full text-red-500 hover:bg-red-50 hover:text-red-600 disabled:opacity-50 dark:text-red-400 dark:hover:bg-red-900/30 dark:hover:text-red-300 transition-colors"
                  onclick={() => showDeleteConfirmId = col.id}
                  disabled={isBusy}
                  title="Permanently Delete"
                >
                  <Trash label="" size={16} />
                </button>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    {:else}
      {#if deletedSnipsels.length === 0}
        <div class="py-8 text-center text-sm text-slate-500 dark:text-slate-400">No deleted snipsels found.</div>
      {:else}
        <div class="grid gap-3 sm:grid-cols-2">
          {#each deletedSnipsels as snip (snip.id)}
            <div class="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div class="min-w-0 flex-1 pl-2">
                <div class="line-clamp-2 text-sm text-slate-900 dark:text-slate-100">
                  {snip.content_markdown || '(Empty)'}
                </div>
                <div class="mt-1 flex gap-2 text-xs text-slate-500 dark:text-slate-400">
                  <span class="uppercase tracking-wide">[{snip.type}]</span>
                  <span>Deleted: {formatDate((snip as any).deleted_at)}</span>
                </div>
              </div>
              <div class="ml-3 flex items-center gap-1 shrink-0">
                <button
                  class="al-icon-wrapper flex h-8 w-8 items-center justify-center rounded-full text-slate-500 hover:bg-slate-100 hover:text-slate-900 disabled:opacity-50 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100 transition-colors"
                  onclick={() => restoreSnipsel(snip.id)}
                  disabled={isBusy}
                  title="Restores to Today's collection"
                >
                  <Undo label="" size={16} />
                </button>
                <button
                  class="al-icon-wrapper flex h-8 w-8 items-center justify-center rounded-full text-red-500 hover:bg-red-50 hover:text-red-600 disabled:opacity-50 dark:text-red-400 dark:hover:bg-red-900/30 dark:hover:text-red-300 transition-colors"
                  onclick={() => showDeleteConfirmId = snip.id}
                  disabled={isBusy}
                  title="Permanently Delete"
                >
                  <Trash label="" size={16} />
                </button>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    {/if}
  </div>
</div>

{#if showEmptyConfirm}
  <DeleteConfirmModal
    title={`Empty ${activeTab === 'collections' ? 'Collections' : 'Snipsels'} Trash`}
    message={`Are you sure you want to permanently delete all ${activeTab}? This action cannot be undone.`}
    confirmLabel="Permanently Delete"
    onConfirm={emptyTrash}
    onCancel={() => showEmptyConfirm = false}
  />
{/if}

{#if showDeleteConfirmId}
  <DeleteConfirmModal
    title={`Delete ${activeTab === 'collections' ? 'Collection' : 'Snipsel'}`}
    message={`Are you sure you want to permanently delete this item? This action cannot be undone.`}
    confirmLabel="Permanently Delete"
    onConfirm={deleteTrashItem}
    onCancel={() => showDeleteConfirmId = null}
  />
{/if}
