<script lang="ts">
  import { scale, fade } from 'svelte/transition';
  import CirclePlay from '@animated-color-icons/lucide-svelte/CirclePlay.svelte';
  import AudioLines from '@animated-color-icons/lucide-svelte/AudioLines.svelte';
  import ExternalLink from '@animated-color-icons/lucide-svelte/ExternalLink.svelte';
  import { onMount } from 'svelte';

  interface Props {
    url: string;
    accentColor?: string;
  }

  let { url, accentColor = '#1db954' }: Props = $props();

  let data = $state<any>(null);
  let loading = $state(true);
  let error = $state(false);

  async function fetchData() {
    loading = true;
    error = false;
    try {
      if (!url) throw new Error('Missing url parameter');

      const res = await fetch(`/api/proxy/spotify?url=${encodeURIComponent(url)}`, {
        credentials: 'include'
      });
      if (!res.ok) throw new Error('Failed to fetch');
      const json = await res.json();
      data = json;
    } catch (e) {
      console.error('Spotify fetch error:', e);
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
    return data.title || 'Spotify Media';
  });

  const subtitle = $derived.by(() => {
    if (!data) return '';
    // Optional: we can extract type from URL
    if (url.includes('/track/')) return 'Song';
    if (url.includes('/album/')) return 'Album';
    if (url.includes('/artist/')) return 'Artist';
    if (url.includes('/playlist/')) return 'Playlist';
    if (url.includes('/episode/')) return 'Episode';
    if (url.includes('/show/')) return 'Podcast';
    return data.provider_name || 'Spotify';
  });

  const coverUrl = $derived.by(() => {
    if (!data) return '';
    return data.thumbnail_url || '';
  });
</script>

{#if loading}
  <div class="mt-4 flex animate-pulse items-center gap-4 rounded-2xl border border-slate-200 bg-white/50 p-4 dark:border-white/10 dark:bg-slate-900/50" in:fade={{ duration: 150 }}>
    <div class="h-20 w-20 flex-shrink-0 rounded-xl bg-slate-200 dark:bg-white/10"></div>
    <div class="flex-1 space-y-2">
      <div class="h-4 w-3/4 rounded bg-slate-200 dark:bg-white/10"></div>
      <div class="h-3 w-1/2 rounded bg-slate-200 dark:bg-white/10"></div>
    </div>
  </div>
{:else if error || !data || data.error}
  <!-- Silently fail or minimal fallback -->
{:else}
  <div class="group relative mt-4 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all duration-200 hover:scale-[1.01] hover:shadow-md dark:border-white/10 dark:bg-slate-900" style={`--accent: ${accentColor}`} in:scale={{ start: 0.95, duration: 150 }}>
    <!-- Glassmorphic background effect -->
    <div class="absolute inset-0 z-0 opacity-0 transition-opacity group-hover:opacity-100" style={`background-color: ${accentColor}0d`}></div>
    
    <div class="relative flex items-center gap-4 p-4">
      <a 
        href={url} 
        target="_blank" 
        rel="noopener noreferrer"
        class="relative h-20 w-20 flex-shrink-0 overflow-hidden rounded-xl bg-slate-100 shadow-sm transition-transform hover:scale-105 active:scale-95 dark:bg-white/5"
        onclick={(e) => e.stopPropagation()}
      >
        {#if coverUrl}
          <img 
            src={coverUrl} 
            alt={title}
            class="h-full w-full object-cover"
          />
        {:else}
          <div class="flex h-full w-full items-center justify-center bg-slate-100 dark:bg-slate-800">
            <AudioLines label="" size={32} className="text-slate-400" />
          </div>
        {/if}
        <div class="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 transition-opacity group-hover:opacity-100">
          <CirclePlay label="" size={32} className="text-white" />
        </div>
      </a>

      <div class="min-w-0 flex-1">
        <h4 class="truncate text-lg font-semibold text-slate-900 group-hover:text-[var(--accent)] dark:text-slate-100">
          {title}
        </h4>
        <p class="truncate text-sm text-slate-500 dark:text-slate-400">
          {subtitle}
        </p>
        
        <div class="mt-2 flex items-center gap-1">
          <AudioLines label="" size={12} className="text-slate-400" />
          <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">Spotify</span>
        </div>
      </div>

      <a 
        href={url} 
        target="_blank" 
        rel="noopener noreferrer"
        class="grid h-10 w-10 place-items-center rounded-full bg-slate-50 text-slate-400 transition-all duration-150 hover:scale-110 hover:bg-slate-100 group-hover:text-[var(--accent)] active:scale-90 dark:bg-white/5 dark:hover:bg-white/10"
        onclick={(e) => e.stopPropagation()}
        aria-label="Open on Spotify"
      >
        <ExternalLink label="" size={20} />
      </a>
    </div>
  </div>
{/if}
