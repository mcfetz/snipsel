<script lang="ts">
  import X from '@animated-color-icons/lucide-svelte/X.svelte';
  import Search from '@animated-color-icons/lucide-svelte/Search.svelte';
  import Loader2 from '@animated-color-icons/lucide-svelte/Loader2.svelte';
  import { api, type SearchCollectionHit } from './api';
  import { onMount } from 'svelte';

  interface Props {
    title: string;
    onSelect: (collectionId: string) => void;
    onClose: () => void;
  }

  let { title, onSelect, onClose }: Props = $props();

  let query = $state('');
  let recentCollections = $state<SearchCollectionHit[]>([]);
  let searchResults = $state<SearchCollectionHit[]>([]);
  let loading = $state(false);
  let debounceTimer: ReturnType<typeof setTimeout> | null = null;
  let inputRef: HTMLInputElement | undefined = $state();

  let displayItems = $derived(query.trim() ? searchResults : recentCollections);

  $effect(() => {
    if (inputRef) {
      inputRef.focus();
    }
  });

  onMount(async () => {
    loading = true;
    try {
      const res = await api.collections.listRecent();
      recentCollections = res.collections.map(c => ({
        id: c.id,
        title: c.title,
        icon: c.icon,
        list_for_day: null // Not heavily used in autocomplete selection context
      }));
    } catch (err) {
      console.error('Failed to load recent collections', err);
    } finally {
      loading = false;
    }
  });

  function handleSearchInput() {
    if (debounceTimer) clearTimeout(debounceTimer);
    
    if (!query.trim()) {
      searchResults = [];
      return;
    }

    debounceTimer = setTimeout(async () => {
      loading = true;
      try {
        const res = await api.collections.autocomplete(query);
        searchResults = res.collections.map(c => ({
          id: c.id,
          title: c.title,
          icon: c.icon,
          list_for_day: null
        }));
      } catch (err) {
        console.error('Failed to search collections', err);
      } finally {
        loading = false;
      }
    }, 300);
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
    }
  }
</script>

<svelte:window onkeydown={handleKeydown} />

<div
  class="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm transition-all"
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
  tabindex="-1"
  onclick={(e) => e.target === e.currentTarget && onClose()}
  onkeydown={handleKeydown}
>
  <div class="w-full max-w-md overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-black/5 dark:bg-slate-900 dark:ring-white/10 flex flex-col max-h-[85vh]">
    <div class="border-b border-slate-100 bg-slate-50/50 px-6 py-4 dark:border-white/5 dark:bg-slate-800/50 flex items-center justify-between">
      <h2 id="modal-title" class="text-xl font-semibold text-slate-900 dark:text-slate-100">
        {title}
      </h2>
      <button
        class="al-icon-wrapper rounded-full p-2 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-white/5 dark:hover:text-slate-300"
        type="button"
        onclick={onClose}
        aria-label="Close"
      >
        <X label="" size={20} />
      </button>
    </div>

    <div class="p-6">
      <div class="relative">
        <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
          <Search label="" size={20} className="text-slate-400" />
        </div>
        <input
          bind:this={inputRef}
          type="text"
          class="block w-full rounded-xl border border-slate-200 bg-white py-3 pl-10 pr-3 text-sm placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-white/10 dark:bg-slate-800 dark:text-slate-100 dark:focus:border-indigo-400 dark:focus:ring-indigo-400 shadow-sm"
          placeholder="Search collections..."
          bind:value={query}
          oninput={handleSearchInput}
        />
      </div>
      
      {#if loading && !query && recentCollections.length === 0}
         <div class="mt-8 flex justify-center text-slate-400">
           <Loader2 label="" size={24} className="animate-spin" />
         </div>
      {/if}
    </div>

    <div class="flex-1 overflow-y-auto px-6 pb-6">
      
      {#if displayItems.length > 0}
        <div class="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          {query.trim() ? 'Search Results' : 'Recent Collections'}
        </div>
        <div class="space-y-1">
          {#each displayItems as c (c.id)}
            <button
              type="button"
              class="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left transition-colors hover:bg-slate-50 dark:hover:bg-white/5 group"
              onclick={() => onSelect(c.id)}
            >
              <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-white shadow-sm ring-1 ring-slate-200 dark:bg-slate-800 dark:ring-white/10 text-xl group-hover:scale-110 transition-transform">
                {c.icon || '📁'}
              </span>
              <span class="flex-1 truncate font-medium text-slate-700 dark:text-slate-200">
                {c.title}
              </span>
            </button>
          {/each}
        </div>
      {:else if query.trim() && !loading}
        <div class="py-8 text-center text-sm text-slate-500 dark:text-slate-400">
          No collections found matching "{query}"
        </div>
      {:else if !query.trim() && !loading && recentCollections.length === 0}
        <div class="py-8 text-center text-sm text-slate-500 dark:text-slate-400">
          No recent collections
        </div>
      {/if}
    </div>
  </div>
</div>
