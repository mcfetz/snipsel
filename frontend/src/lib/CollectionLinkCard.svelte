<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, scale } from 'svelte/transition';
  import ExternalLink from '@animated-color-icons/lucide-svelte/ExternalLink.svelte';
  import { api, type Collection } from './api';
  import { currentView } from './stores';

  interface Props {
    collectionId: string;
    accentColor?: string;
  }

  let { collectionId, accentColor = '#6366f1' }: Props = $props();

  let collection = $state<Collection | null>(null);
  let loading = $state(true);
  let error = $state(false);

  async function fetchCollection() {
    loading = true;
    error = false;
    try {
      // The API handles caching/background refresh via IDB
      const res = await api.collections.get(collectionId);
      collection = res.collection;
    } catch (e) {
      console.error('Failed to fetch collection for card:', e);
      error = true;
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    fetchCollection();
  });

  function navigate(e: MouseEvent) {
    e.stopPropagation();
    if (collection) {
      currentView.set({ type: 'collection', id: collection.id });
    }
  }
  
  const headerImage = $derived(collection?.header_image_url);
  const headerColor = $derived(collection?.header_color || accentColor);
</script>

{#if loading}
  <div class="mt-4 flex animate-pulse items-center gap-4 rounded-2xl border border-slate-200 bg-white/50 p-4 dark:border-white/10 dark:bg-slate-900/50" in:fade={{ duration: 150 }}>
    <div class="h-20 w-20 flex-shrink-0 rounded-xl bg-slate-200 dark:bg-white/10"></div>
    <div class="flex-1 space-y-2">
      <div class="h-4 w-3/4 rounded bg-slate-200 dark:bg-white/10"></div>
      <div class="h-3 w-1/2 rounded bg-slate-200 dark:bg-white/10"></div>
    </div>
  </div>
{:else if error || !collection}
  <!-- Silent fallback -->
{:else}
  <button
    type="button"
    class="group relative mt-4 block w-full overflow-hidden rounded-2xl border border-slate-200 bg-white text-left shadow-sm transition-all duration-200 hover:scale-[1.01] hover:shadow-md dark:border-white/10 dark:bg-slate-900"
    style={`--accent: ${headerColor}`}
    onclick={navigate}
    in:scale={{ start: 0.95, duration: 150 }}
  >
    <!-- Background Decorative Header Area -->
    <div class="absolute inset-x-0 top-0 h-20 opacity-15 transition-opacity group-hover:opacity-25 dark:opacity-30" 
         style={headerImage ? `background-image: url('${headerImage}${headerImage.startsWith('/api/attachments/') ? '/thumbnail' : ''}'); background-size: cover; background-position: center` : `background: linear-gradient(to bottom, ${headerColor}, transparent)`}>
    </div>
    
    <!-- Accent subtle highlight on hover -->
    <div class="absolute inset-0 z-0 opacity-0 transition-opacity group-hover:opacity-100" style={`background-color: ${headerColor}0a`}></div>

    <div class="relative flex items-center gap-4 p-4">
      <div 
        class="relative flex h-20 w-20 flex-shrink-0 items-center justify-center rounded-xl bg-white text-3xl shadow-sm ring-1 ring-black/5 dark:bg-slate-800 dark:ring-white/5"
      >
        {collection.icon || '📝'}
      </div>

      <div class="min-w-0 flex-1">
        <h4 class="truncate text-lg font-bold text-slate-900 group-hover:text-[var(--accent)] dark:text-slate-100">
          {collection.title}
        </h4>
        <div class="mt-1 flex items-center gap-1.5 opacity-60">
           <span class="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Collection Link</span>
        </div>
      </div>

      <div class="grid h-10 w-10 place-items-center rounded-full bg-slate-50 text-slate-400 transition-all duration-150 hover:scale-110 hover:bg-slate-100 group-hover:text-[var(--accent)] active:scale-90 dark:bg-white/5 dark:hover:bg-white/10">
        <ExternalLink label="" size={20} />
      </div>
    </div>
  </button>
{/if}
