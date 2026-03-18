<script lang="ts">
  import Globe from '@animated-color-icons/lucide-svelte/Globe.svelte';
  import ExternalLink from '@animated-color-icons/lucide-svelte/ExternalLink.svelte';
  import { onMount } from 'svelte';

  interface Props {
    url: string;
  }

  let { url }: Props = $props();

  interface LinkMetadata {
    title: string;
    favicon_url: string | null;
    domain: string;
  }

  let data = $state<LinkMetadata | null>(null);
  let loading = $state(true);
  let error = $state(false);

  async function fetchData() {
    loading = true;
    error = false;
    try {
      const res = await fetch(`/api/proxy/link-metadata?url=${encodeURIComponent(url)}`, {
        credentials: 'include'
      });
      if (!res.ok) throw new Error('Failed to fetch');
      data = await res.json();
    } catch (e) {
      console.error('Link metadata fetch error:', e);
      error = true;
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    fetchData();
  });
</script>

{#if loading}
  <div class="mt-4 flex animate-pulse items-center gap-4 rounded-2xl border border-slate-200 bg-white/50 p-4 dark:border-white/10 dark:bg-slate-900/50">
    <div class="h-14 w-14 flex-shrink-0 rounded-xl bg-slate-200 dark:bg-white/10"></div>
    <div class="flex-1 space-y-2">
      <div class="h-4 w-3/4 rounded bg-slate-200 dark:bg-white/10"></div>
      <div class="h-3 w-1/2 rounded bg-slate-200 dark:bg-white/10"></div>
    </div>
  </div>
{:else if error || !data}
{:else}
  <div class="group relative mt-4 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all hover:shadow-md dark:border-white/10 dark:bg-slate-900">
    <div class="absolute inset-0 z-0 bg-gradient-to-br from-cyan-500/5 to-blue-500/5 opacity-0 transition-opacity group-hover:opacity-100"></div>

    <div class="relative flex items-center gap-4 p-4">
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        class="relative h-14 w-14 flex-shrink-0 overflow-hidden rounded-xl bg-slate-100 shadow-sm transition-transform hover:scale-105 active:scale-95 dark:bg-white/5"
        onclick={(e) => e.stopPropagation()}
      >
        {#if data.favicon_url}
          <img
            src={data.favicon_url}
            alt={data.title}
            class="h-full w-full object-contain p-3"
            onerror={(e) => {
              (e.currentTarget as HTMLImageElement).style.display = 'none';
            }}
          />
        {:else}
          <div class="flex h-full w-full items-center justify-center">
            <Globe label="" size={24} className="text-slate-400 dark:text-slate-500" />
          </div>
        {/if}
      </a>

      <div class="min-w-0 flex-1">
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          class="hover:underline"
          onclick={(e) => e.stopPropagation()}
        >
          <h4 class="truncate text-base font-semibold text-slate-900 group-hover:text-blue-600 dark:text-slate-100 dark:group-hover:text-blue-400">
            {data.title}
          </h4>
        </a>
        <p class="truncate text-sm text-slate-500 dark:text-slate-400">
          {data.domain}
        </p>
      </div>

      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        class="grid h-10 w-10 place-items-center rounded-full bg-slate-50 text-slate-400 transition-all hover:bg-slate-100 hover:text-blue-600 active:scale-90 dark:bg-white/5 dark:hover:bg-white/10 dark:hover:text-blue-400"
        onclick={(e) => e.stopPropagation()}
        aria-label="Open link"
      >
        <ExternalLink label="" size={20} />
      </a>
    </div>
  </div>
{/if}