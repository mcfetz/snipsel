<script lang="ts">
  import { scale, fade } from 'svelte/transition';
  import MapPin from '@animated-color-icons/lucide-svelte/MapPin.svelte';
  import ExternalLink from '@animated-color-icons/lucide-svelte/ExternalLink.svelte';
  import { onMount } from 'svelte';

  interface Props {
    url: string;
    lat?: number;
    lng?: number;
    accentColor?: string;
  }

  let { url, lat: initialLat, lng: initialLng, accentColor = '#22c55e' }: Props = $props();

  let lat = $state<number | null>(null);
  let lng = $state<number | null>(null);
  let resolved = $state(false);
  let error = $state(false);

  async function resolveCoordinates() {
    try {
      const res = await fetch(`/api/proxy/link-metadata?url=${encodeURIComponent(url)}`, {
        credentials: 'include'
      });
      if (!res.ok) throw new Error('Failed to fetch');
      const data = await res.json();
      if (typeof data.lat === 'number' && typeof data.lng === 'number') {
        lat = data.lat;
        lng = data.lng;
        resolved = true;
      } else {
        error = true;
      }
    } catch (e) {
      console.error('Map coordinate resolution error:', e);
      error = true;
    }
  }

  onMount(() => {
    if (initialLat !== undefined && initialLng !== undefined) {
      lat = initialLat;
      lng = initialLng;
      resolved = true;
    } else {
      resolveCoordinates();
    }
  });

  function getMapEmbedUrl(lat: number, lng: number): string {
    const bboxDelta = 0.005;
    return `https://www.openstreetmap.org/export/embed.html?bbox=${lng - bboxDelta},${lat - bboxDelta},${lng + bboxDelta},${lat + bboxDelta}&layer=mapnik&marker=${lat},${lng}`;
  }
</script>

{#if !resolved && !error}
  <div class="mt-4 flex animate-pulse items-center gap-4 rounded-2xl border border-slate-200 bg-white/50 p-4 dark:border-white/10 dark:bg-slate-900/50" in:fade={{ duration: 150 }}>
    <div class="h-14 w-14 flex-shrink-0 rounded-xl bg-slate-200 dark:bg-white/10"></div>
    <div class="flex-1 space-y-2">
      <div class="h-4 w-3/4 rounded bg-slate-200 dark:bg-white/10"></div>
      <div class="h-3 w-1/2 rounded bg-slate-200 dark:bg-white/10"></div>
    </div>
  </div>
{:else if error}
  <div class="group relative mt-4 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all duration-200 hover:scale-[1.01] hover:shadow-md dark:border-white/10 dark:bg-slate-900" style={`--accent: ${accentColor}`} in:scale={{ start: 0.95, duration: 150 }}>
    <div class="absolute inset-0 z-0 bg-gradient-to-br from-green-500/5 to-emerald-500/5 opacity-0 transition-opacity group-hover:opacity-100"></div>

    <div class="relative flex items-center gap-4 p-4">
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        class="relative h-14 w-14 flex-shrink-0 overflow-hidden rounded-xl bg-slate-100 shadow-sm transition-transform hover:scale-105 active:scale-95 dark:bg-white/5"
        onclick={(e) => e.stopPropagation()}
      >
        <div class="flex h-full w-full items-center justify-center">
          <MapPin label="" size={24} className="text-green-600 dark:text-green-400" />
        </div>
      </a>

      <div class="min-w-0 flex-1">
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          class="hover:underline"
          onclick={(e) => e.stopPropagation()}
        >
          <h4 class="truncate text-base font-semibold text-slate-900 group-hover:text-[var(--accent)] dark:text-slate-100">
            Open in Maps
          </h4>
        </a>
        <p class="truncate text-sm text-slate-500 dark:text-slate-400">
          {url.replace(/^https?:\/\//, '').split('/')[0]}
        </p>
      </div>

      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        class="grid h-10 w-10 place-items-center rounded-full bg-slate-50 text-slate-400 transition-all duration-150 hover:scale-110 hover:bg-slate-100 group-hover:text-[var(--accent)] active:scale-90 dark:bg-white/5 dark:hover:bg-white/10"
        onclick={(e) => e.stopPropagation()}
        aria-label="Open in original maps"
      >
        <ExternalLink label="" size={20} />
      </a>
    </div>
  </div>
{:else}
  <div class="group relative mt-4 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all duration-200 hover:scale-[1.01] hover:shadow-md dark:border-white/10 dark:bg-slate-900" style={`--accent: ${accentColor}`} in:scale={{ start: 0.95, duration: 150 }}>
    <div class="absolute inset-0 z-0 bg-gradient-to-br from-green-500/5 to-emerald-500/5 opacity-0 transition-opacity group-hover:opacity-100"></div>

    <div class="relative">
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        class="block"
        onclick={(e) => e.stopPropagation()}
        aria-label="View map location"
      >
        <iframe
          src={getMapEmbedUrl(lat!, lng!)}
          width="100%"
          height="180"
          frameborder="0"
          class="w-full rounded-t-2xl"
          loading="lazy"
          title="Map location"
        ></iframe>
      </a>

      <div class="flex items-center gap-3 p-3">
        <div class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-green-50 dark:bg-green-900/20">
          <MapPin label="" size={20} className="text-green-600 dark:text-green-400" />
        </div>

        <div class="min-w-0 flex-1">
          <p class="truncate text-sm font-semibold text-slate-900 group-hover:text-[var(--accent)] dark:text-slate-100">
            {lat!.toFixed(4)}, {lng!.toFixed(4)}
          </p>
          <p class="truncate text-xs text-slate-500 dark:text-slate-400">
            OpenStreetMap
          </p>
        </div>

        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          class="grid h-10 w-10 place-items-center rounded-full bg-slate-50 text-slate-400 transition-all duration-150 hover:scale-110 hover:bg-slate-100 group-hover:text-[var(--accent)] active:scale-90 dark:bg-white/5 dark:hover:bg-white/10"
          onclick={(e) => e.stopPropagation()}
          aria-label="Open in original maps"
        >
          <ExternalLink label="" size={20} />
        </a>
      </div>
    </div>
  </div>
{/if}