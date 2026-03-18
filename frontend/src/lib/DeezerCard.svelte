<script lang="ts">
  import CirclePlay from '@animated-color-icons/lucide-svelte/CirclePlay.svelte';
  import Disc from '@animated-color-icons/lucide-svelte/Disc.svelte';
  import ExternalLink from '@animated-color-icons/lucide-svelte/ExternalLink.svelte';
  import { onMount } from 'svelte';
  import { api } from './api';

  interface Props {
    type: 'track' | 'album' | 'artist' | null;
    id: string | null;
    url: string;
  }

  let { type, id, url }: Props = $props();

  let data = $state<any>(null);
  let loading = $state(true);
  let error = $state(false);

  async function fetchData() {
    loading = true;
    error = false;
    try {
      // Use the new backend proxy
      let query = '';
      if (type && id) {
        query = `type=${type}&id=${id}`;
      } else if (url) {
        query = `url=${encodeURIComponent(url)}`;
      }

      if (!query) throw new Error('Missing parameters');

      const res = await fetch(`/api/proxy/deezer?${query}`, {
        credentials: 'include'
      });
      if (!res.ok) throw new Error('Failed to fetch');
      const json = await res.json();
      data = json;
      
      // If we got type/id back from resolving a short URL, we can use them
      // although deriving from data is safer.
    } catch (e) {
      console.error('Deezer fetch error:', e);
      error = true;
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    fetchData();
  });

  const title = $derived.by(() => {
    if (!data) return '';
    const activeType = data.type || type;
    if (activeType === 'track') return data.title || data.name || 'Unknown Track';
    if (activeType === 'album') return data.title || data.name || 'Unknown Album';
    if (activeType === 'artist') return data.name || data.title || 'Unknown Artist';
    // Fallback to any available name/title
    return data.title || data.name || 'Deezer Media';
  });

  const subtitle = $derived.by(() => {
    if (!data) return '';
    const activeType = data.type || type;
    if (activeType === 'track') return data.artist?.name || 'Unknown Artist';
    if (activeType === 'album') return data.artist?.name || 'Unknown Artist';
    if (activeType === 'artist') return 'Artist';
    return data.artist?.name || '';
  });

  const coverUrl = $derived.by(() => {
    if (!data) return '';
    const activeType = data.type || type;
    return (
      data.album?.cover_medium || 
      data.cover_medium || 
      data.picture_medium || 
      data.artist?.picture_medium || 
      ''
    );
  });
</script>

{#if loading}
  <div class="mt-4 flex animate-pulse items-center gap-4 rounded-2xl border border-slate-200 bg-white/50 p-4 dark:border-white/10 dark:bg-slate-900/50">
    <div class="h-20 w-20 flex-shrink-0 rounded-xl bg-slate-200 dark:bg-white/10"></div>
    <div class="flex-1 space-y-2">
      <div class="h-4 w-3/4 rounded bg-slate-200 dark:bg-white/10"></div>
      <div class="h-3 w-1/2 rounded bg-slate-200 dark:bg-white/10"></div>
    </div>
  </div>
{:else if error || !data || data.error}
  <!-- Silently fail or minimal fallback -->
{:else}
  <div class="group relative mt-4 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all hover:shadow-md dark:border-white/10 dark:bg-slate-900">
    <!-- Glassmorphic background effect -->
    <div class="absolute inset-0 z-0 bg-gradient-to-br from-indigo-500/5 to-purple-500/5 opacity-0 transition-opacity group-hover:opacity-100"></div>
    
    <div class="relative z-10 flex items-center gap-4 p-4">
      <a 
        href={url} 
        target="_blank" 
        rel="noopener noreferrer"
        class="relative h-20 w-20 flex-shrink-0 overflow-hidden rounded-xl bg-slate-100 shadow-sm transition-transform hover:scale-105 active:scale-95 dark:bg-white/5"
        onclick={(e) => e.stopPropagation()}
      >
        <img 
          src={coverUrl} 
          alt={title}
          class="h-full w-full object-cover"
        />
        <div class="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 transition-opacity group-hover:opacity-100">
          <CirclePlay size={32} className="text-white" />
        </div>
      </a>

      <div class="min-w-0 flex-1">
        <h4 class="truncate text-lg font-semibold text-slate-900 group-hover:text-indigo-600 dark:text-slate-100 dark:group-hover:text-indigo-400">
          {title}
        </h4>
        <p class="truncate text-sm text-slate-500 dark:text-slate-400">
          {subtitle}
        </p>
        
        <div class="mt-2 flex items-center gap-1">
          <Disc size={12} className="text-slate-400" />
          <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">Deezer</span>
        </div>
      </div>

      <a 
        href={url} 
        target="_blank" 
        rel="noopener noreferrer"
        class="grid h-10 w-10 place-items-center rounded-full bg-slate-50 text-slate-400 transition-all hover:bg-slate-100 hover:text-indigo-600 active:scale-90 dark:bg-white/5 dark:hover:bg-white/10 dark:hover:text-indigo-400"
        onclick={(e) => e.stopPropagation()}
        aria-label="Open on Deezer"
      >
        <ExternalLink size={20} />
      </a>
    </div>
  </div>
{/if}

<style>
  /* Optional: any specific styles for the card */
</style>
