<script lang="ts">
  import Youtube from '@animated-color-icons/lucide-svelte/Youtube.svelte';
  import ExternalLink from '@animated-color-icons/lucide-svelte/ExternalLink.svelte';
  import { onMount } from 'svelte';

  interface Props {
    url: string;
  }

  let { url }: Props = $props();

  let data = $state<any>(null);
  let loading = $state(true);
  let error = $state(false);

  async function fetchData() {
    loading = true;
    error = false;
    try {
      const res = await fetch(`/api/proxy/youtube?url=${encodeURIComponent(url)}`, {
        credentials: 'include'
      });
      if (!res.ok) throw new Error('Failed to fetch');
      data = await res.json();
    } catch (e) {
      console.error('YouTube fetch error:', e);
      error = true;
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    fetchData();
  });

  const title = $derived(data?.title || 'YouTube Video');
  const author = $derived(data?.author_name || '');
  const thumbnail = $derived(data?.thumbnail_url || '');
</script>

{#if loading}
  <div class="mt-4 flex animate-pulse items-center gap-4 rounded-2xl border border-slate-200 bg-white/50 p-4 dark:border-white/10 dark:bg-slate-900/50">
    <div class="aspect-video w-32 flex-shrink-0 rounded-xl bg-slate-200 dark:bg-white/10"></div>
    <div class="flex-1 space-y-2">
      <div class="h-4 w-3/4 rounded bg-slate-200 dark:bg-white/10"></div>
      <div class="h-3 w-1/2 rounded bg-slate-200 dark:bg-white/10"></div>
    </div>
  </div>
{:else if error || !data}
  <!-- Silently fail -->
{:else}
  <div class="group relative mt-4 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all hover:shadow-md dark:border-white/10 dark:bg-slate-900">
    <div class="absolute inset-0 z-0 bg-gradient-to-br from-red-500/5 to-orange-500/5 opacity-0 transition-opacity group-hover:opacity-100"></div>
    
    <div class="relative flex flex-col sm:flex-row items-center gap-4 p-4">
      <a 
        href={url} 
        target="_blank" 
        rel="noopener noreferrer"
        class="relative aspect-video w-full sm:w-40 flex-shrink-0 overflow-hidden rounded-xl bg-slate-100 shadow-sm transition-transform hover:scale-[1.02] active:scale-98 dark:bg-white/5"
        onclick={(e) => e.stopPropagation()}
      >
        <img 
          src={thumbnail} 
          alt={title}
          class="h-full w-full object-cover"
        />
        <div class="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 transition-opacity group-hover:opacity-100">
          <Youtube label="" size={40} className="text-white" />
        </div>
      </a>

      <div class="min-w-0 flex-1">
        <h4 class="line-clamp-2 text-lg font-semibold text-slate-900 group-hover:text-red-600 dark:text-slate-100 dark:group-hover:text-red-400">
          {title}
        </h4>
        <p class="truncate text-sm text-slate-500 dark:text-slate-400">
          {author}
        </p>
        
        <div class="mt-2 flex items-center gap-1.5">
          <Youtube label="" size={12} className="text-red-600" />
          <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">YouTube</span>
        </div>
      </div>

      <a 
        href={url} 
        target="_blank" 
        rel="noopener noreferrer"
        class="hidden sm:grid h-10 w-10 place-items-center rounded-full bg-slate-50 text-slate-400 transition-all hover:bg-slate-100 hover:text-red-600 active:scale-90 dark:bg-white/5 dark:hover:bg-white/10 dark:hover:text-red-400"
        onclick={(e) => e.stopPropagation()}
        aria-label="Open on YouTube"
      >
        <ExternalLink label="" size={20} strokeWidth={2} />
      </a>
    </div>
  </div>
{/if}
