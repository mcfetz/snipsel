<script lang="ts">
  import ArrowLeft from '@animated-color-icons/lucide-svelte/ArrowLeft.svelte';
  import Trash2 from '@animated-color-icons/lucide-svelte/Trash2.svelte';
  import Trash from '@animated-color-icons/lucide-svelte/Trash.svelte';
  import Undo from '@animated-color-icons/lucide-svelte/Undo.svelte';
  import Check from '@animated-color-icons/lucide-svelte/Check.svelte';
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

  function isLightColor(color: string): boolean {
    const hex = color.replace('#', '');
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
    return brightness > 155;
  }

  function getContrastColor(bgColor: string): string {
    return isLightColor(bgColor) ? '#1e293b' : 'white';
  }

  let deletedCollections = $state<Collection[]>([]);
  let deletedSnipsels = $state<Snipsel[]>([]);
  let isBusy = $state(false);
  let errorMsg = $state('');
  let showEmptyConfirm = $state(false);
  let showDeleteConfirmId = $state<string | null>(null);
  let showRestoreSuccess = $state(false);
  let showEmptySuccess = $state(false);
  
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
      showRestoreSuccess = true;
      setTimeout(() => showRestoreSuccess = false, 2000);
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
      const res = await api.collections.today();
      await api.snipsels.restore(id, res.collection.id);
      deletedSnipsels = deletedSnipsels.filter(s => s.id !== id);
      showRestoreSuccess = true;
      setTimeout(() => showRestoreSuccess = false, 2000);
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
      showEmptySuccess = true;
      setTimeout(() => showEmptySuccess = false, 2000);
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

<div class="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-6 pb-20">
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-4">
      <button
        class="al-icon-wrapper grid h-10 w-10 place-items-center rounded-full bg-slate-100/80 text-slate-600 shadow-sm ring-1 ring-black/5 backdrop-blur-sm transition-all hover:bg-slate-200 dark:bg-slate-800/80 dark:text-slate-400 dark:ring-white/10 dark:hover:bg-slate-700"
        onclick={() => currentView.set({ type: 'settings' })}
        title="Back to Settings"
      >
        <ArrowLeft label="" size={20} strokeWidth={2.5} />
      </button>
      <div>
        <h2 class="text-2xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <Trash2 label="" size={24} className="text-slate-500" />
          Recycle Bin
        </h2>
        <p class="text-xs text-slate-500 dark:text-slate-400">Permanently delete or restore your content</p>
      </div>
    </div>

    {#if showRestoreSuccess || showEmptySuccess}
      <div class="flex items-center gap-2 rounded-full bg-green-500/10 px-4 py-2 text-sm font-bold text-green-600 animate-in fade-in zoom-in duration-300 dark:bg-green-500/20 dark:text-green-400">
        <Check size={18} strokeWidth={3} />
        <span>Action Successful!</span>
      </div>
    {/if}
  </div>

  {#if errorMsg}
    <div class="rounded-xl border border-red-200 bg-red-50 p-4 text-sm font-medium text-red-600 shadow-sm dark:border-red-900/30 dark:bg-red-950/20 dark:text-red-400">
      {errorMsg}
    </div>
  {/if}

  <div class="sticky top-0 z-10 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between py-2 bg-slate-50/50 backdrop-blur-md dark:bg-slate-950/50">
    <div class="flex flex-1 overflow-hidden rounded-full border border-slate-200 bg-white/50 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/50 dark:ring-white/10 w-full sm:max-w-xs" role="tablist">
      <button
        type="button"
        role="tab"
        aria-selected={activeTab === 'collections'}
        class="flex-1 px-4 py-3 text-sm font-bold transition-all duration-300 {activeTab === 'collections'
          ? ''
          : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
        style={activeTab === 'collections' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        onclick={() => activeTab = 'collections'}
      >
        Collections <span class="ml-1 opacity-70">({deletedCollections.length})</span>
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={activeTab === 'snipsels'}
        class="flex-1 border-l border-black/5 px-4 py-3 text-sm font-bold transition-all duration-300 dark:border-white/5 {activeTab === 'snipsels'
          ? ''
          : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
        style={activeTab === 'snipsels' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        onclick={() => activeTab = 'snipsels'}
      >
        Snipsels <span class="ml-1 opacity-70">({deletedSnipsels.length})</span>
      </button>
    </div>
    
    {#if (activeTab === 'collections' && deletedCollections.length > 0) || (activeTab === 'snipsels' && deletedSnipsels.length > 0)}
      <button
        class="flex items-center justify-center gap-2 rounded-full border border-red-200 bg-white/80 px-6 py-2.5 text-sm font-bold text-red-600 shadow-sm ring-1 ring-black/5 transition-all hover:bg-red-600 hover:text-white disabled:opacity-50 dark:border-red-900/30 dark:bg-slate-900/80 dark:text-red-400 dark:hover:bg-red-600 dark:hover:text-white"
        onclick={() => showEmptyConfirm = true}
        disabled={isBusy}
      >
        <Trash label="" size={18} strokeWidth={2.5} />
        <span class="hidden sm:inline">Empty All {activeTab === 'collections' ? 'Collections' : 'Snipsels'}</span>
        <span class="sm:hidden">Empty All</span>
      </button>
    {/if}
  </div>

  <div class="mt-4">
    {#if activeTab === 'collections'}
      {#if deletedCollections.length === 0}
        <div class="flex flex-col items-center justify-center py-20 text-center animate-in fade-in zoom-in duration-500">
          <div class="mb-4 grid h-16 w-16 place-items-center rounded-2xl bg-slate-50 text-slate-300 dark:bg-white/5 dark:text-slate-700">
            <Trash2 size={32} />
          </div>
          <p class="text-sm font-medium text-slate-500 dark:text-slate-400">No deleted collections found.</p>
        </div>
      {:else}
        <div class="grid gap-4 sm:grid-cols-2">
          {#each deletedCollections as col (col.id)}
            <div class="group flex items-center justify-between rounded-2xl border border-slate-200 bg-white/70 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md transition-all hover:scale-[1.01] hover:bg-white/90 dark:border-white/10 dark:bg-slate-900/70 dark:ring-white/10 dark:hover:bg-slate-900/90">
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-3">
                  <span class="text-2xl transition-transform group-hover:scale-110">{col.icon}</span>
                  <div class="min-w-0 flex-1">
                    <span class="block truncate text-sm font-bold text-slate-900 dark:text-slate-100">{col.title}</span>
                    <span class="mt-0.5 block text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Deleted: {formatDate((col as any).deleted_at)}
                    </span>
                  </div>
                </div>
              </div>
              <div class="ml-4 flex items-center gap-2 shrink-0">
                <button
                  class="al-icon-wrapper flex h-9 w-9 items-center justify-center rounded-full bg-slate-100/50 text-slate-600 shadow-sm ring-1 ring-black/5 transition-all hover:bg-white hover:text-slate-900 dark:bg-white/5 dark:text-slate-400 dark:ring-white/10 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                  onclick={() => restoreCollection(col.id)}
                  disabled={isBusy}
                  title="Restore Collection"
                >
                  <Undo size={18} strokeWidth={2.5} />
                </button>
                <button
                  class="al-icon-wrapper flex h-9 w-9 items-center justify-center rounded-full bg-red-500/10 text-red-600 shadow-sm ring-1 ring-black/5 transition-all hover:bg-red-600 hover:text-white dark:bg-red-500/20 dark:text-red-400 dark:hover:bg-red-600 dark:hover:text-white"
                  onclick={() => showDeleteConfirmId = col.id}
                  disabled={isBusy}
                  title="Permanently Delete"
                >
                  <Trash size={18} strokeWidth={2.5} />
                </button>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    {:else}
      {#if deletedSnipsels.length === 0}
        <div class="flex flex-col items-center justify-center py-20 text-center animate-in fade-in zoom-in duration-500">
          <div class="mb-4 grid h-16 w-16 place-items-center rounded-2xl bg-slate-50 text-slate-300 dark:bg-white/5 dark:text-slate-700">
            <Trash2 size={32} />
          </div>
          <p class="text-sm font-medium text-slate-500 dark:text-slate-400">No deleted snipsels found.</p>
        </div>
      {:else}
        <div class="grid gap-4 sm:grid-cols-2">
          {#each deletedSnipsels as snip (snip.id)}
            <div class="group flex items-center justify-between rounded-2xl border border-slate-200 bg-white/70 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md transition-all hover:scale-[1.01] hover:bg-white/90 dark:border-white/10 dark:bg-slate-900/70 dark:ring-white/10 dark:hover:bg-slate-900/90">
              <div class="min-w-0 flex-1">
                <div class="line-clamp-2 text-sm font-medium text-slate-900 dark:text-slate-100">
                  {snip.content_markdown || '(Empty Snipsel)'}
                </div>
                <div class="mt-2 flex items-center gap-2">
                  <span class="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:bg-slate-800 dark:text-slate-400">{snip.type}</span>
                  <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Deleted: {formatDate((snip as any).deleted_at)}
                  </span>
                </div>
              </div>
              <div class="ml-4 flex items-center gap-2 shrink-0">
                <button
                  class="al-icon-wrapper flex h-9 w-9 items-center justify-center rounded-full bg-slate-100/50 text-slate-600 shadow-sm ring-1 ring-black/5 transition-all hover:bg-white hover:text-slate-900 dark:bg-white/5 dark:text-slate-400 dark:ring-white/10 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                  onclick={() => restoreSnipsel(snip.id)}
                  disabled={isBusy}
                  title="Restores to Today's collection"
                >
                  <Undo size={18} strokeWidth={2.5} />
                </button>
                <button
                  class="al-icon-wrapper flex h-9 w-9 items-center justify-center rounded-full bg-red-500/10 text-red-600 shadow-sm ring-1 ring-black/5 transition-all hover:bg-red-600 hover:text-white dark:bg-red-500/20 dark:text-red-400 dark:hover:bg-red-600 dark:hover:text-white"
                  onclick={() => showDeleteConfirmId = snip.id}
                  disabled={isBusy}
                  title="Permanently Delete"
                >
                  <Trash size={18} strokeWidth={2.5} />
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
