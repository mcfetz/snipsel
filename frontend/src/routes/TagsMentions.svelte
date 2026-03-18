<script lang="ts">
  import Hash from '@animated-color-icons/lucide-svelte/Hash.svelte';
  import { api, type TagCount } from '../lib/api';
  import { collectionAnchor, currentView, isLoading, searchError, searchQuery, searchResults, searchScope } from '../lib/stores';
  import { currentUser } from '../lib/session';

  const DEFAULT_ACCENT = '#4f46e5';
  type Rgb = { r: number; g: number; b: number };

  function clampByte(n: number): number {
    return Math.max(0, Math.min(255, Math.round(n)));
  }

  function hexToRgb(hex: string): Rgb | null {
    const h = (hex || '').trim();
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

  function getAccentTint(): string {
    const isDark = document.documentElement.classList.contains('dark');
    const baseColor = isDark ? '#1e293b' : '#ffffff';
    const base = hexToRgb(baseColor) ?? { r: 255, g: 255, b: 255 };
    const accent = hexToRgb(getAccent());
    const mixed = accent ? mixRgb(base, accent, 0.14) : base;
    return rgba(mixed, 0.96);
  }

  type Mode = 'tags' | 'mentions';
  type Scope = 'my' | 'shared';

  let mode = $state<Mode>('tags');
  let scope = $state<Scope>('my');
  let items = $state<TagCount[]>([]);
  let loadingList = $state(false);

  async function loadList() {
    loadingList = true;
    try {
      if (mode === 'tags') {
        const res = await api.tags.list(scope);
        items = res.tags;
      } else {
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
    // runSearch will be triggered automatically by App.svelte $effect
  }

  $effect(() => {
    loadList();
  });
</script>

<div class="space-y-4">
  <h2 class="flex items-center gap-2 text-2xl font-semibold dark:text-slate-100">
    <Hash size={24} className="text-slate-700 dark:text-slate-300" />
    <span>Tags / Mentions</span>
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
          loadList();
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
          loadList();
        }}
      >
        Shared
      </button>
    </div>
  </div>

  {#if loadingList}
    <div class="py-8 text-center text-sm text-slate-500">Loading...</div>
  {:else if items.length === 0}
    <div class="py-8 text-center text-sm text-slate-500">No {mode} yet</div>
  {:else}
    <div class="space-y-1">
      {#each items as it (it.name)}
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
    </div>
  {/if}
</div>
