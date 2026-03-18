<script lang="ts">
  import SearchIcon from '@animated-color-icons/lucide-svelte/Search.svelte';
  import { collectionAnchor, currentView, isLoading, searchError, searchQuery, searchResults, searchType, searchScope } from '../lib/stores';
  import type { SearchSnipselHit } from '../lib/api';
  import { getCurrentUrl } from '../lib/router';
  import { currentUser } from '../lib/session';
  import DeezerCard from '../lib/DeezerCard.svelte';
  import YouTubeCard from '../lib/YouTubeCard.svelte';

  const DEFAULT_ACCENT = '#4f46e5';
  type Rgb = { r: number; g: number; b: number };

  function clampByte(n: number): number {
    return Math.max(0, Math.min(255, Math.round(n)));
  }

  function hexToRgb(hex: string): Rgb | null {
    const h = hex.trim();
    const m = /^#([0-9a-fA-F]{6})$/.exec(h);
    if (!m) return null;
    const v = m[1];
    return {
      r: parseInt(v.slice(0, 2), 16),
      g: parseInt(v.slice(2, 4), 16),
      b: parseInt(v.slice(4, 6), 16),
    };
  }

  function mixRgb(a: Rgb, b: Rgb, t: number): Rgb {
    const tt = Math.max(0, Math.min(1, t));
    return {
      r: clampByte(a.r + (b.r - a.r) * tt),
      g: clampByte(a.g + (b.g - a.g) * tt),
      b: clampByte(a.b + (b.b - a.b) * tt),
    };
  }

  function rgba(c: Rgb, alpha: number): string {
    const a = Math.max(0, Math.min(1, alpha));
    return `rgba(${c.r}, ${c.g}, ${c.b}, ${a})`;
  }

  function getAccent(): string {
    const raw = ($currentUser?.default_collection_header_color || '').trim() || DEFAULT_ACCENT;
    return /^#[0-9a-fA-F]{6}$/.test(raw) ? raw : DEFAULT_ACCENT;
  }

  const DEFAULT_HEADER_COLOR = '#4f46e5';
  const TOOLBOX_BASE_COLOR = '#ffffff';

  function getHeaderColor(): string {
    const raw = ($currentUser?.default_collection_header_color || '').trim() || DEFAULT_HEADER_COLOR;
    return /^#[0-9a-fA-F]{6}$/.test(raw) ? raw : DEFAULT_HEADER_COLOR;
  }

  function getToolboxBg(): string {
    const isDark = document.documentElement.classList.contains('dark');
    const baseColor = isDark ? '#1e293b' : TOOLBOX_BASE_COLOR;
    const base = hexToRgb(baseColor) ?? { r: 255, g: 255, b: 255 };
    const header = hexToRgb(getHeaderColor());
    const mixed = header ? mixRgb(base, header, 0.14) : base;
    return rgba(mixed, 0.96);
  }

  function getAccentTint(): string {
    const isDark = document.documentElement.classList.contains('dark');
    const baseColor = isDark ? '#1e293b' : '#ffffff';
    const base = hexToRgb(baseColor) ?? { r: 255, g: 255, b: 255 };
    const accent = hexToRgb(getAccent());
    const mixed = accent ? mixRgb(base, accent, 0.14) : base;
    return rgba(mixed, 0.96);
  }

  function openSnipsel(s: SearchSnipselHit) {
    if (s.collection_id) {
      collectionAnchor.set({ collectionId: s.collection_id, snipselId: s.id, pos: s.position ?? undefined });
      currentView.set({ type: 'collection', id: s.collection_id });
    } else {
      collectionAnchor.set(null);
      currentView.set({ type: 'snipsel', id: s.id, returnTo: getCurrentUrl() });
    }
  }

  function formatDate(iso: string) {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  function getDeezerLink(text: string | null) {
    if (!text) return null;
    const stdMatch = text.match(/https?:\/\/(?:www\.)?deezer\.com\/(track|album|artist)\/(\d+)/);
    if (stdMatch) return { url: stdMatch[0] };
    const shortMatch = text.match(/https?:\/\/link\.deezer\.com\/s\/[A-Za-z0-9]+/);
    if (shortMatch) return { url: shortMatch[0] };
    return null;
  }

  function getYouTubeLink(text: string | null) {
    if (!text) return null;
    const match = text.match(/https?:\/\/(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|v\/|shorts\/)|youtu\.be\/)([A-Za-z0-9_-]{11})(?:[^\s\)]*)/);
    if (match) {
      return { id: match[1], url: match[0] };
    }
    return null;
  }

  function stripMediaLinks(text: string | null): string {
    if (!text) return '';
    let result = text;
    const dz = getDeezerLink(text);
    if (dz) result = result.replace(dz.url, '');
    const yt = getYouTubeLink(text);
    if (yt) result = result.replace(yt.url, '');
    return result.trim();
  }

  const filters = [
    { label: 'All', value: undefined },
    { label: 'Notes', value: 'text' },
    { label: 'Images', value: 'image' },
    { label: 'Files', value: 'attachment' },
    { label: 'Tasks', value: 'task' },
  ];
</script>

<div class="space-y-4">
  <h2 class="flex items-center gap-2 text-2xl font-semibold dark:text-slate-100">
    <SearchIcon size={24} className="text-slate-700 dark:text-slate-300" />
    <span>Search</span>
  </h2>

  <div class="flex flex-wrap items-center gap-2">
    <div class="flex-1 min-w-[200px] overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-900 dark:ring-white/10">
      <div class="grid grid-cols-5">
        {#each filters as f}
          <button
            class="whitespace-nowrap px-1 py-3 text-[10px] sm:text-xs font-medium transition-colors border-l first:border-l-0 border-black/5 dark:border-white/5 {$searchType === f.value ? 'text-slate-900 dark:text-white' : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
            type="button"
            onclick={() => searchType.set(f.value)}
            style={$searchType === f.value ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          >
            {f.label}
          </button>
        {/each}
      </div>
    </div>

    <div class="overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-900 dark:ring-white/10">
      <div class="flex">
        {#each [{label: 'All', value: 'all'}, {label: 'My', value: 'my'}, {label: 'Shared', value: 'shared'}] as s}
          <button
            class="px-3 sm:px-4 py-3 text-[10px] sm:text-xs font-medium transition-colors border-l first:border-l-0 border-black/5 dark:border-white/5 {$searchScope === s.value ? 'text-slate-900 dark:text-white' : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
            type="button"
            onclick={() => searchScope.set(s.value as any)}
            style={$searchScope === s.value ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          >
            {s.label}
          </button>
        {/each}
      </div>
    </div>
  </div>

  {#if $searchError}
    <div class="rounded-xl border border-red-200 bg-red-50/50 p-4 text-base text-red-700 backdrop-blur-md dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-400">
      {$searchError}
    </div>
  {/if}

  {#if $isLoading && !$searchResults}
    <div class="py-12 text-center text-slate-500">Searching...</div>
  {:else if $searchResults}
    <div class="space-y-6">
      {#if $searchResults.collections.length > 0}
        <div class="space-y-3">
          <div class="text-xs font-medium uppercase tracking-wider text-slate-500 px-1">Collections</div>
          <div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {#each $searchResults.collections as c (c.id)}
              <button 
                class="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white/80 p-3 shadow-sm ring-1 ring-black/5 backdrop-blur-md transition-all hover:-translate-y-0.5 hover:shadow-md text-left dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10"
                type="button"
                onclick={() => currentView.set({ type: 'collection', id: c.id })}
              >
                <span class="text-2xl">{c.icon}</span>
                <span class="font-medium text-slate-900 truncate dark:text-slate-100">{c.title}</span>
              </button>
            {/each}
          </div>
        </div>
      {/if}

      <div class="space-y-3">
        <div class="flex items-center justify-between px-1">
          <div class="text-xs font-medium uppercase tracking-wider text-slate-500">
            Snipsels for "{$searchQuery.trim() || '—'}"
          </div>
          <div class="text-xs text-slate-400">
            {$searchResults.snipsels.length} found
          </div>
        </div>

        {#if $searchResults.snipsels.length === 0}
          <div class="rounded-xl border border-slate-200 bg-white/80 p-8 text-center text-slate-500 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:text-slate-400">
            No matches found
          </div>
        {:else}
          <div class="space-y-2">
            {#each $searchResults.snipsels as s (s.id)}
              <div class="flex w-full items-center gap-3 px-1 py-2">
                <button class="min-w-0 flex flex-1 items-start gap-3 text-left" type="button" onclick={() => openSnipsel(s)}>
                  <div class="min-w-0 flex-1">
                    {#if getDeezerLink(s.content_markdown)}
                      {@const dz = getDeezerLink(s.content_markdown)!}
                      <DeezerCard url={dz.url} type={null} id={null} />
                    {/if}
                    {#if getYouTubeLink(s.content_markdown)}
                      {@const yt = getYouTubeLink(s.content_markdown)!}
                      <YouTubeCard url={yt.url} />
                    {/if}

                    <div class="line-clamp-2 text-lg font-medium text-slate-900 dark:text-slate-100">{stripMediaLinks(s.content_markdown) || '(No content)'}</div>

                    {#if (s.tags?.length ?? 0) > 0 || (s.mentions?.length ?? 0) > 0}
                      <div class="mt-2 flex flex-wrap gap-1.5">
                        {#each s.tags ?? [] as t (t)}
                          <span 
                            class="rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider"
                            style="background-color: {getToolboxBg()}; color: {getHeaderColor()}; border: 1px solid rgba(0,0,0,0.05)"
                          >
                            #{t}
                          </span>
                        {/each}
                        {#each s.mentions ?? [] as m (m)}
                          <span 
                            class="rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider"
                            style="background-color: {getToolboxBg()}; color: {getHeaderColor()}; border: 1px solid rgba(0,0,0,0.05)"
                          >
                            @{m}
                          </span>
                        {/each}
                      </div>
                    {/if}
                    <div class="mt-0.5 flex items-center gap-2 text-xs text-slate-500">
                      <span class="font-semibold uppercase tracking-tight" style={`color: ${getAccent()}`}>{s.type}</span>
                      {#if s.collection_title}
                        <span class="opacity-30">|</span>
                        <span class="flex items-center gap-1">
                          <span class="opacity-70">{s.collection_icon}</span>
                          <span>{s.collection_title}</span>
                        </span>
                      {/if}
                      <span class="opacity-30">|</span>
                      <span>{formatDate(s.modified_at)}</span>
                    </div>
                  </div>
                </button>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>
  {:else}
    <div class="py-12 text-center text-slate-500">
      Type a query in the header and press Enter to start searching.
    </div>
  {/if}
</div>
