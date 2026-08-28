<script lang="ts">
  import Upload from '@animated-color-icons/lucide-svelte/Upload.svelte';
  import Trash2 from '@animated-color-icons/lucide-svelte/Trash2.svelte';
  import SquareCheck from '@animated-color-icons/lucide-svelte/SquareCheck.svelte';
  import ChevronRight from '@animated-color-icons/lucide-svelte/ChevronRight.svelte';
  import { api } from '../api';
  import { currentView } from '../stores';
  import { idbSaveBulkSync, idbClearAllCollections, idbClearAllCollectionItems } from '../db';

  interface Props {
    accent: string;
    isBusy: boolean;
  }

  let { accent, isBusy }: Props = $props();

  let syncStatus = $state<'idle' | 'syncing' | 'success' | 'error'>('idle');
  let syncProgress = $state(0);
  let syncStage = $state('');
  let syncError = $state('');
  let lastFullSync = $state<string | null>(null);

  $effect(() => {
    if (typeof localStorage !== 'undefined') {
      lastFullSync = localStorage.getItem('last_full_offline_sync');
    }
  });

  async function performFullSync() {
    syncStatus = 'syncing';
    syncProgress = 10;
    syncStage = 'Fetching all collections & snipsels...';
    syncError = '';

    try {
      const res = await api.collections.fullSync();
      syncProgress = 50;
      syncStage = 'Storing offline data in database...';

      await idbClearAllCollectionItems();
      await idbClearAllCollections();
      await idbSaveBulkSync(res.collections, res.items);

      syncProgress = 100;
      syncStage = 'Complete';
      syncStatus = 'success';
      const now = new Date().toISOString();
      lastFullSync = now;
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem('last_full_offline_sync', now);
      }
      setTimeout(() => {
        if (syncStatus === 'success') syncStatus = 'idle';
      }, 3000);
    } catch (err: any) {
      console.error('Full sync failed:', err);
      syncStatus = 'error';
      syncError = err?.message || 'Failed to complete offline sync.';
    }
  }
</script>

<div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
  <div class="text-xs uppercase text-slate-500">Data & Migration</div>
  <div class="mt-3 space-y-3">
    <button
      class="al-icon-wrapper flex w-full items-center gap-4 rounded-xl border border-dashed border-slate-200 p-3 text-left transition-all hover:border-slate-300 hover:bg-slate-50/50 dark:border-white/10 dark:hover:bg-white/5"
      onclick={() => currentView.set({ type: 'importer' })}
      type="button"
    >
      <div class="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400">
        <Upload label="" size={20} />
      </div>
      <div class="flex-1">
        <div class="font-medium text-slate-900 dark:text-slate-100">Import from TwoS</div>
        <div class="text-xs text-slate-500 dark:text-slate-400">Bring your lists and things into snipsel</div>
      </div>
      <ChevronRight label="" size={20} className="text-slate-400" />
    </button>

    <button
      class="al-icon-wrapper flex w-full items-center gap-4 rounded-xl border border-dashed border-slate-200 p-3 text-left transition-all hover:border-slate-300 hover:bg-slate-50/50 dark:border-white/10 dark:hover:bg-white/5"
      onclick={() => currentView.set({ type: 'recycle-bin' })}
      type="button"
    >
      <div class="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-red-50 text-red-600 dark:bg-red-900/20 dark:text-red-400">
        <Trash2 label="" size={20} />
      </div>
      <div class="flex-1">
        <div class="font-medium text-slate-900 dark:text-slate-100">Recycle Bin</div>
        <div class="text-xs text-slate-500 dark:text-slate-400">Restore deleted collections and snipsels</div>
      </div>
      <ChevronRight label="" size={20} className="text-slate-400" />
    </button>

    <div class="mt-6 border-t border-slate-100 pt-6 dark:border-white/5">
      <div class="flex items-center justify-between gap-4">
        <div class="flex-1">
          <div class="flex items-center gap-2 font-medium text-slate-900 dark:text-slate-100">
            <div class="grid h-8 w-8 place-items-center rounded-full bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400">
              <SquareCheck label="" size={16} />
            </div>
            Full Offline Sync
          </div>
          <div class="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Download all collections and snipsels to your device for offline use.
            {#if lastFullSync}
              <div class="mt-1 font-medium text-blue-600 dark:text-blue-400">Last sync: {new Date(lastFullSync).toLocaleString()}</div>
            {/if}
          </div>
        </div>
        <button
          class="rounded-full border border-slate-200 bg-white px-6 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
          style={`color: ${accent}`}
          type="button"
          onclick={performFullSync}
          disabled={isBusy || syncStatus === 'syncing'}
        >
          {#if syncStatus === 'syncing'}
            Syncing...
          {:else}
            Sync Now
          {/if}
        </button>
      </div>

      {#if syncStatus === 'syncing'}
        <div class="mt-4 space-y-2">
          <div class="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-slate-400">
            <span>{syncStage}</span>
            <span>{Math.round(syncProgress)}%</span>
          </div>
          <div class="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-white/5">
            <div 
              class="h-full transition-all duration-500 ease-out"
              style={`width: ${syncProgress}%; background-color: ${accent}; box-shadow: 0 0 10px ${accent}40`}
            ></div>
          </div>
        </div>
      {/if}

      {#if syncStatus === 'error'}
        <div class="mt-2 text-xs font-medium text-red-600 dark:text-red-400">{syncError}</div>
      {/if}
      {#if syncStatus === 'success'}
        <div class="mt-2 text-xs font-medium text-green-600 dark:text-green-400">Sync completed successfully!</div>
      {/if}
    </div>
  </div>
</div>
