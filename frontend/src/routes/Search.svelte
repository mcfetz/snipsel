<script lang="ts">
  import SearchIcon from '@animated-color-icons/lucide-svelte/Search.svelte';
  import { collectionAnchor, currentView, isLoading, searchError, searchQuery, searchResults, searchType, searchScope } from '../lib/stores';
  import type { SearchSnipselHit } from '../lib/api';
  import { getCurrentUrl } from '../lib/router';
  import { currentUser } from '../lib/session';
  import DeezerCard from '../lib/DeezerCard.svelte';
  import SpotifyCard from '../lib/SpotifyCard.svelte';
  import YouTubeCard from '../lib/YouTubeCard.svelte';
  import { computeHeaderColor, computeCardTileBg } from '../lib/colors';
  import { getDeezerLink, getSpotifyLink, getYouTubeLink, stripMediaLinks } from '../lib/embeds';

  let accent = $derived(computeHeaderColor($currentUser?.default_collection_header_color));

  function getAccent(): string {
    return accent;
  }

  function getAccentTint(): string {
    const isDark = typeof document !== 'undefined' && document.documentElement.classList.contains('dark');
    return computeCardTileBg(accent, isDark);
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
    <SearchIcon label="" size={24} className="text-slate-700 dark:text-slate-300" />
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
              <div class="flex w-full items-center gap-3 px-1 py-2 {s.type === 'task' && s.task_done > 0 ? 'task-faded' : ''} {s.type === 'task' && s.task_done === 2 ? 'task-cancelled' : ''}">
                <button class="min-w-0 flex flex-1 items-start gap-3 text-left" type="button" onclick={() => openSnipsel(s)}>
                  <div class="min-w-0 flex-1">
                    {#if getDeezerLink(s.content_markdown)}
                      {@const dz = getDeezerLink(s.content_markdown)!}
                      <DeezerCard url={dz.url} type={null} id={null} accentColor={getHeaderColor()} />
                    {/if}
                    {#if getSpotifyLink(s.content_markdown)}
                      {@const sp = getSpotifyLink(s.content_markdown)!}
                      <SpotifyCard url={sp.url} accentColor={getHeaderColor()} />
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
    {#if $searchQuery.trim().length > 0 && $searchQuery.trim().length < 3 && !$searchType}
      <div class="py-12 text-center text-slate-500">
        Please enter at least 3 characters for a search.
      </div>
    {:else}
      <div class="py-12 text-center text-slate-500">
        Type a query in the header to search across all your snipsels.
      </div>
    {/if}
  {/if}
</div>
