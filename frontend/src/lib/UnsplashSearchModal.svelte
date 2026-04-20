<script lang="ts">
  import Search from '@animated-color-icons/lucide-svelte/Search.svelte';
  import X from '@animated-color-icons/lucide-svelte/X.svelte';
  import { api } from './api';

  interface Props {
    initialQuery?: string;
    accentColor?: string;
    onSelect: (url: string) => void;
    onClose: () => void;
  }

  let { initialQuery = '', accentColor, onSelect, onClose }: Props = $props();

  const DEFAULT_ACCENT = '#4f46e5';
  const effectiveAccent = $derived(accentColor || DEFAULT_ACCENT);

  function isLightColor(color: string): boolean {
    const hex = color.replace('#', '');
    if (hex.length !== 6) return false;
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
    return brightness > 128;
  }

  function getContrastColor(bgColor: string): string {
    return isLightColor(bgColor) ? '#1e293b' : 'white';
  }

  function hexToRgba(hex: string, alpha: number): string {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  let query = $state(initialQuery);
  let results = $state<any[]>([]);
  let loading = $state(false);
  let page = $state(1);
  let totalPages = $state(0);
  let error = $state<string | null>(null);

  async function search(reset = true) {
    if (!query.trim()) return;
    if (reset) {
      page = 1;
      results = [];
    }
    loading = true;
    error = null;
    try {
      const res = await api.proxy.unsplashSearch(query, page);
      results = reset ? res.results : [...results, ...res.results];
      totalPages = res.total_pages;
    } catch (err: any) {
      error = err.error?.message || 'Failed to search Unsplash';
    } finally {
      loading = false;
    }
  }

  function handleSelect(photo: any) {
    onSelect(photo.urls.regular);
    onClose();
  }

  function loadMore() {
    if (page < totalPages) {
      page++;
      search(false);
    }
  }

  // Initial search
  if (initialQuery) {
    search();
  }
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div 
  class="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm dark:bg-black/60"
  onclick={(e) => { if (e.target === e.currentTarget) onClose(); }}
>
  <div class="flex h-full max-h-[80vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-900">
    <!-- Header -->
    <div class="flex items-center justify-between border-b border-slate-100 p-4 dark:border-white/5">
      <div class="flex items-center gap-3">
        <div 
          class="grid h-8 w-8 place-items-center rounded-lg"
          style={`background-color: ${hexToRgba(effectiveAccent, 0.1)}; color: ${effectiveAccent}`}
        >
          <Search label="" size={18} />
        </div>
        <h2 class="text-sm font-semibold text-slate-800 dark:text-slate-100">Search Unsplash</h2>
      </div>
      <button
        class="al-icon-wrapper grid h-8 w-8 place-items-center rounded-full text-slate-400 hover:bg-slate-100 dark:hover:bg-white/5"
        type="button"
        onclick={onClose}
      >
        <X label="" size={18} />
      </button>
    </div>

    <!-- Search Input -->
    <div class="border-b border-slate-100 p-4 dark:border-white/5">
      <form onsubmit={(e) => { e.preventDefault(); search(); }} class="flex gap-2">
        <input
          type="text"
          bind:value={query}
          placeholder="Search for images..."
          class="flex-1 rounded-lg border border-slate-200 bg-slate-50 px-4 py-2 text-sm focus:outline-none focus:ring-2 dark:border-white/10 dark:bg-slate-800 dark:text-slate-100"
          style={`--tw-ring-color: ${hexToRgba(effectiveAccent, 0.2)}`}
          autofocus
        />
        <button
          type="submit"
          class="rounded-lg px-4 py-2 text-sm font-medium text-white transition-colors disabled:opacity-50"
          style={`background-color: ${effectiveAccent}; color: ${getContrastColor(effectiveAccent)};`}
          disabled={loading}
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>
    </div>

    <!-- Results -->
    <div class="flex-1 overflow-y-auto p-4">
      {#if error}
        <div class="rounded-lg bg-red-50 p-3 text-xs text-red-600 dark:bg-red-900/20 dark:text-red-400">
          {error}
        </div>
      {:else if results.length === 0 && !loading}
        <div class="flex h-full flex-col items-center justify-center space-y-4 py-8 text-slate-400">
          <div class="opacity-20"><Search size={48} /></div>
          <p class="text-xs">No images found</p>
        </div>
      {:else}
        <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {#each results as photo (photo.id)}
            <button
              class="group relative aspect-video overflow-hidden rounded-lg bg-slate-100 transition-all hover:ring-2 dark:bg-slate-800"
              style={`--tw-ring-color: ${effectiveAccent}`}
              type="button"
              onclick={() => handleSelect(photo)}
            >

              <img
                src={photo.urls.thumb}
                alt={photo.alt_description || 'Unsplash photo'}
                class="h-full w-full object-cover transition-transform group-hover:scale-105"
              />
              <div class="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/60 to-transparent p-2 text-left opacity-0 transition-opacity group-hover:opacity-100">
                <div class="truncate text-[10px] text-white">
                  by {photo.user.name}
                </div>
              </div>
            </button>
          {/each}
        </div>

        {#if page < totalPages}
          <div class="mt-6 flex justify-center pb-4">
            <button
              class="rounded-full border border-slate-200 bg-white px-6 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50 dark:border-white/10 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
              type="button"
              onclick={loadMore}
              disabled={loading}
            >
              {loading ? 'Loading...' : 'Load more'}
            </button>
          </div>
        {/if}
      {/if}
    </div>

    <!-- Footer -->
    <div class="border-t border-slate-100 p-3 text-center dark:border-white/5">
      <span class="text-[10px] text-slate-400">
        Powered by <a href="https://unsplash.com/?utm_source=snipsel&utm_medium=referral" target="_blank" rel="noopener noreferrer" class="font-medium underline hover:text-slate-500">Unsplash</a>
      </span>
    </div>
  </div>
</div>
