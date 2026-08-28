<script lang="ts">
  import Hash from '@animated-color-icons/lucide-svelte/Hash.svelte';
  import MapPin from '@animated-color-icons/lucide-svelte/MapPin.svelte';
  import { api, type TagCount } from '../lib/api';
  import { collectionAnchor, currentView, isLoading, searchError, searchQuery, searchResults, searchScope } from '../lib/stores';
  import { currentUser } from '../lib/session';
  import { onMount, onDestroy } from 'svelte';
  import { slide, fade } from 'svelte/transition';
  import L from 'leaflet';
  import 'leaflet/dist/leaflet.css';
  import { computeHeaderColor, computeCardTileBg } from '../lib/colors';

  function getAccent(): string {
    return computeHeaderColor($currentUser?.default_collection_header_color);
  }

  function getAccentTint(): string {
    const isDark = typeof document !== 'undefined' && document.documentElement.classList.contains('dark');
    return computeCardTileBg(getAccent(), isDark);
  }

  type Mode = 'tags' | 'mentions' | 'locations';
  type Scope = 'my' | 'shared';

  let mode = $state<Mode>('tags');
  let scope = $state<Scope>('my');
  let items = $state<TagCount[]>([]);
  let loadingList = $state(false);

  const VISIBLE_LIMIT = 100;
  let visibleItems = $derived(items.slice(0, VISIBLE_LIMIT));

  // Map related state
  let mapContainer = $state<HTMLDivElement>()
  let map: L.Map | null = null;
  let markers: L.Marker[] = [];
  let geoSnipsels = $state<Array<{
    id: string;
    lat: number;
    lng: number;
    excerpt: string;
    type: string;
    task_done: boolean;
    collection: {
      id: string;
      title: string;
      icon: string;
      header_color: string | null;
    };
    created_at: string;
  }>>([]);
  let loadingMap = $state(false);
  let mapError = $state<string | null>(null);

  async function loadList() {
    loadingList = true;
    try {
      if (mode === 'tags') {
        const res = await api.tags.list(scope);
        items = res.tags;
      } else if (mode === 'mentions') {
        const res = await api.mentions.list(scope);
        items = res.mentions;
      }
    } finally {
      loadingList = false;
    }
  }

  async function selectToken(name: string) {
    collectionAnchor.set(null);
    searchQuery.set((mode === 'tags' ? '#' : '@') + name);
    searchScope.set(scope);
    searchError.set(null);
    searchResults.set(null);
    currentView.set({ type: 'search' });
  }

  function initMap() {
    if (!mapContainer || map) return;

    map = L.map(mapContainer).setView([51.1657, 10.4515], 6); // Default to Germany

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map);

    // Try to get current location
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          // Set view to current location with ~50km radius (zoom level 10)
          map?.setView([latitude, longitude], 10);
          loadSnipselsInBounds();
        },
        () => {
          // If geolocation fails, just load with default view
          loadSnipselsInBounds();
        }
      );
    } else {
      loadSnipselsInBounds();
    }

    // Load snipsels when map moves
    map.on('moveend', () => {
      loadSnipselsInBounds();
    });
  }

  async function loadSnipselsInBounds() {
    if (!map) return;

    loadingMap = true;
    mapError = null;

    try {
      const bounds = map.getBounds();
      const ne = bounds.getNorthEast();
      const sw = bounds.getSouthWest();

      const res = await api.geo.getSnipselsByBounds({
        ne_lat: ne.lat,
        ne_lng: ne.lng,
        sw_lat: sw.lat,
        sw_lng: sw.lng,
        scope,
      });

      geoSnipsels = res.snipsels;
      updateMarkers();
    } catch (e) {
      mapError = e instanceof Error ? e.message : 'Failed to load locations';
    } finally {
      loadingMap = false;
    }
  }

  function updateMarkers() {
    if (!map) return;

    // Clear existing markers
    markers.forEach((marker) => marker.remove());
    markers = [];

    // Create custom SVG icon
    const customIcon = L.divIcon({
      className: 'custom-map-marker',
      html: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="${getAccent()}" width="32" height="32" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));">
        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
      </svg>`,
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -32],
    });

    // Add new markers
    geoSnipsels.forEach((snipsel) => {
      const marker = L.marker([snipsel.lat, snipsel.lng], { icon: customIcon })
        .addTo(map!)
        .bindPopup(createPopupContent(snipsel));

      marker.on('click', () => {
        openSnipsel(snipsel);
      });

      markers.push(marker);
    });
  }

  function createPopupContent(snipsel: typeof geoSnipsels[0]): string {
    const accent = getAccent();
    return `
      <div style="max-width: 200px;">
        <div style="font-weight: 600; margin-bottom: 4px; color: ${accent};">
          ${snipsel.collection.icon} ${escapeHtml(snipsel.collection.title)}
        </div>
        <div style="font-size: 13px; color: #666; margin-bottom: 8px;">
          ${escapeHtml(snipsel.excerpt)}
        </div>
        <button 
          onclick="window.openSnipsel('${snipsel.id}', '${snipsel.collection.id}')"
          style="background: ${accent}; color: white; border: none; padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 12px;"
        >
          Open
        </button>
      </div>
    `;
  }

  function escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function openSnipsel(snipsel: typeof geoSnipsels[0]) {
    collectionAnchor.set({
      collectionId: snipsel.collection.id,
      snipselId: snipsel.id,
      pos: null,
    });
    currentView.set({ type: 'collection', id: snipsel.collection.id });
  }

  // Expose function for popup buttons
  $effect(() => {
    (window as any).openSnipsel = (snipselId: string, collectionId: string) => {
      collectionAnchor.set({
        collectionId,
        snipselId,
        pos: null,
      });
      currentView.set({ type: 'collection', id: collectionId });
    };
  });

  $effect(() => {
    if (mode === 'locations' && mapContainer) {
      setTimeout(() => initMap(), 0);
    }
  });

  onDestroy(() => {
    if (map) {
      map.remove();
      map = null;
    }
  });

  $effect(() => {
    if (mode !== 'locations') {
      loadList();
    }
  });
</script>

<div class="space-y-4">
  <h2 class="flex items-center gap-2 text-2xl font-semibold dark:text-slate-100">
    <Hash label="" size={24} className="text-slate-700 dark:text-slate-300" />
    <span>Tags, Mentions and Locations</span>
  </h2>

  <div class="flex items-center gap-2">
    <div class="flex flex-1 overflow-hidden rounded-full border border-slate-200 bg-white dark:border-white/10 dark:bg-slate-900" role="tablist">
      <button
        type="button"
        role="tab"
        aria-selected={mode === 'tags'}
        class="flex-1 px-4 py-3 text-base font-medium transition-colors {mode === 'tags'
          ? 'text-slate-900'
          : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
        style={mode === 'tags' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        onclick={() => {
          mode = 'tags';
          loadList();
        }}
      >
        <span class="flex items-center justify-center gap-2">
          <span aria-hidden="true">#</span>
          <span>Tags</span>
        </span>
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={mode === 'mentions'}
        class="flex-1 border-l border-black/5 px-4 py-3 text-base font-medium transition-colors dark:border-white/5 {mode === 'mentions'
          ? 'text-slate-900'
          : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
        style={mode === 'mentions' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        onclick={() => {
          mode = 'mentions';
          loadList();
        }}
      >
        <span class="flex items-center justify-center gap-2">
          <span aria-hidden="true">@</span>
          <span>Mentions</span>
        </span>
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={mode === 'locations'}
        class="flex-1 border-l border-black/5 px-4 py-3 text-base font-medium transition-colors dark:border-white/5 {mode === 'locations'
          ? 'text-slate-900'
          : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
        style={mode === 'locations' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        onclick={() => {
          mode = 'locations';
        }}
      >
        <span class="flex items-center justify-center gap-2">
          <MapPin label="" size={18} />
          <span>Geo</span>
        </span>
      </button>
    </div>

    <div class="flex overflow-hidden rounded-full border border-slate-200 bg-white dark:border-white/10 dark:bg-slate-900" role="tablist" aria-label="Scope">
      <button
        type="button"
        role="tab"
        aria-selected={scope === 'my'}
        class="px-4 py-3 text-base font-medium transition-colors {scope === 'my'
          ? 'text-slate-900'
          : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
        style={scope === 'my' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        onclick={() => {
          scope = 'my';
          if (mode === 'locations') {
            loadSnipselsInBounds();
          } else {
            loadList();
          }
        }}
      >
        My
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={scope === 'shared'}
        class="border-l border-black/5 px-4 py-3 text-base font-medium transition-colors dark:border-white/5 {scope === 'shared'
          ? 'text-slate-900'
          : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
        style={scope === 'shared' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        onclick={() => {
          scope = 'shared';
          if (mode === 'locations') {
            loadSnipselsInBounds();
          } else {
            loadList();
          }
        }}
      >
        Shared
      </button>
    </div>
  </div>

  {#if mode === 'locations'}
    <div class="space-y-3">
      {#if mapError}
        <div class="rounded-lg bg-red-50 p-3 text-sm text-red-600 dark:bg-red-950/30 dark:text-red-400">
          {mapError}
        </div>
      {/if}

      <div
        bind:this={mapContainer}
        class="h-[400px] w-full rounded-xl border border-slate-200 dark:border-white/10"
        style="z-index: 1;"
      ></div>

      {#if loadingMap}
        <div class="flex items-center justify-center gap-2 py-4 text-sm text-slate-500">
          <div class="h-4 w-4 animate-spin rounded-full border-2 border-slate-200 border-t-slate-800"></div>
          <span>Loading locations...</span>
        </div>
      {:else if geoSnipsels.length === 0}
        <div class="py-8 text-center text-sm text-slate-500">
          No locations found in this area. Try zooming out or panning the map.
        </div>
      {:else}
        <div class="space-y-3" in:slide={{ duration: 300 }} out:fade={{ duration: 200 }}>
          <div class="flex items-center justify-between px-1">
            <div class="text-xs font-medium uppercase tracking-wider text-slate-500">
              Locations on map
            </div>
            <div class="text-xs text-slate-400">
              {geoSnipsels.length} found
            </div>
          </div>

          <div class="space-y-2">
            {#each geoSnipsels as snipsel (snipsel.id)}
              <button
                type="button"
                class="w-full rounded-xl border border-slate-200 bg-white/80 p-3 text-left shadow-sm ring-1 ring-black/5 backdrop-blur-md transition-all hover:-translate-y-0.5 hover:shadow-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10"
                onclick={() => openSnipsel(snipsel)}
                in:slide={{ duration: 200, delay: 50 }}
              >
                <div class="flex items-start gap-3">
                  <span class="text-2xl">{snipsel.collection.icon}</span>
                  <div class="min-w-0 flex-1">
                    <div class="font-medium text-slate-900 truncate dark:text-slate-100">
                      {snipsel.excerpt || '(No content)'}
                    </div>
                    <div class="mt-1 flex items-center gap-2 text-xs text-slate-500">
                      <span>{snipsel.collection.title}</span>
                      <span>•</span>
                      <span>{new Date(snipsel.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                    </div>
                  </div>
                </div>
              </button>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  {:else if loadingList}
    <div class="py-8 text-center text-sm text-slate-500">Loading...</div>
  {:else if items.length === 0}
    <div class="py-8 text-center text-sm text-slate-500">No {mode} yet</div>
  {:else}
    <div class="space-y-1">
      {#each visibleItems as it (it.name)}
        <button
          type="button"
          class="w-full px-2 py-3 text-left transition-colors hover:bg-slate-50 active:bg-slate-100 dark:hover:bg-white/5 dark:active:bg-white/10"
          onclick={() => selectToken(it.name)}
        >
          <div class="flex items-center justify-between gap-3">
            <span class="text-lg font-medium text-slate-900 dark:text-slate-100">
              <span class="text-slate-400 dark:text-slate-500" aria-hidden="true">{mode === 'tags' ? '#' : '@'}</span>{it.name}
            </span>
            <span class="rounded-full border border-slate-200 bg-white px-3 py-1 text-sm font-medium text-slate-600 shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-slate-300 dark:ring-white/10">
              {it.count}
            </span>
          </div>
        </button>
      {/each}
      {#if items.length > VISIBLE_LIMIT}
        <div class="py-6 mt-4 text-center text-sm text-slate-500 font-medium bg-slate-50/50 rounded-xl border border-slate-200/50 dark:bg-slate-900/30 dark:border-white/5">
          Showing <span class="font-bold text-slate-700 dark:text-slate-300">{VISIBLE_LIMIT}</span> of <span class="font-bold text-slate-700 dark:text-slate-300">{items.length}</span> {mode}.<br/>
          Use the global search at the top to find more.
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  :global(.custom-map-marker) {
    background: transparent !important;
    border: none !important;
  }
</style>
