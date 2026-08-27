<script lang="ts">
  import { fly, fade, scale } from 'svelte/transition';
  import { flip } from 'svelte/animate';
  import List from '@animated-color-icons/lucide-svelte/List.svelte';
  import Plus from '@animated-color-icons/lucide-svelte/Plus.svelte';
  import Heart from '@animated-color-icons/lucide-svelte/Heart.svelte';
  import Calendar from '@animated-color-icons/lucide-svelte/Calendar.svelte';
  import User from '@animated-color-icons/lucide-svelte/User.svelte';
  import Users from '@animated-color-icons/lucide-svelte/Users.svelte';
  import LayoutTemplate from '@animated-color-icons/lucide-svelte/LayoutTemplate.svelte';
  import Archive from '@animated-color-icons/lucide-svelte/Archive.svelte';
  import ArrowUp from '@animated-color-icons/lucide-svelte/ArrowUp.svelte';
  import ArrowDown from '@animated-color-icons/lucide-svelte/ArrowDown.svelte';
  import Info from '@animated-color-icons/lucide-svelte/Info.svelte';
  import LayoutList from '@animated-color-icons/lucide-svelte/LayoutList.svelte';
  import LayoutGrid from '@animated-color-icons/lucide-svelte/LayoutGrid.svelte';
  import { api, type Collection } from '../lib/api';
  import { currentUser } from '../lib/session';
  import { collections, collectionAnchor, currentView, isLoading, pendingReference } from '../lib/stores';

  let showCreate = false;
  let newTitle = '';
  let newIcon = '🗒';
  let busy = false;

  type Filter = 'all' | 'favorites' | 'day' | 'mine' | 'shared' | 'templates' | 'archive';
  let filter: Filter = 'favorites';
  let titleFilter = '';

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

  function getAccentTint(): string {
    const isDark = document.documentElement.classList.contains('dark');
    const baseColor = isDark ? '#1e293b' : '#ffffff';
    const base = hexToRgb(baseColor) ?? { r: 255, g: 255, b: 255 };
    const accent = hexToRgb(getAccent());
    const mixed = accent ? mixRgb(base, accent, 0.14) : base;
    return rgba(mixed, 0.96);
  }

  type SortKey = 'modified' | 'name';
  type SortDir = 'desc' | 'asc';
  let sortKey: SortKey = 'modified';
  let sortDir: SortDir = 'desc';

  type ListView = 'list' | 'cards';
  let listView: ListView = (localStorage.getItem('snipsel_collections_view') as ListView) ?? 'list';

  function setListView(v: ListView) {
    listView = v;
    localStorage.setItem('snipsel_collections_view', v);
  }

  let didInitialLoad = false;

  function cmpString(a: string, b: string): number {
    return a.localeCompare(b, undefined, { sensitivity: 'base' });
  }

  function sortCollections(list: Collection[], key: SortKey, dirRaw: SortDir): Collection[] {
    const dir = dirRaw === 'asc' ? 1 : -1;
    const copy = [...list];
    copy.sort((a, b) => {
      if (key === 'name') {
        return cmpString(a.title, b.title) * dir;
      }
      const ta = Date.parse(a.modified_at);
      const tb = Date.parse(b.modified_at);
      if (ta === tb) return cmpString(a.title, b.title);
      return (ta - tb) * dir;
    });
    return copy;
  }

  function matchesFilter(c: Collection, f: Filter): boolean {
    if (f === 'archive') return Boolean(c.archived);
    if (c.archived && f !== 'all') return false;
    if (f === 'favorites') return Boolean(c.is_favorite);
    if (f === 'day') return Boolean(c.list_for_day);
    if (f === 'mine') return c.access_level === 'owner' && !c.list_for_day && !c.is_template;
    if (f === 'shared') {
      return (
        c.access_level === 'read' ||
        c.access_level === 'write' ||
        (c.access_level === 'owner' && Boolean(c.shared_out))
      );
    }
    if (f === 'templates') return Boolean(c.is_template);
    return true;
  }

  function matchesTitle(c: Collection, qRaw: string): boolean {
    const q = qRaw.trim().toLowerCase();
    if (!q) return true;
    return c.title.toLowerCase().includes(q);
  }

  function cardHeaderStyle(c: Collection): string {
    if (c.header_image_url) {
      const thumb = c.header_image_url.startsWith('/api/attachments/') ? '/thumbnail' : '';
      return `background-image: url('${c.header_image_url}${thumb}'); background-size: cover; background-position: ${c.header_image_x_position ?? '50%'} ${c.header_image_position ?? '50%'};`;
    }
    return `background-color: ${c.header_color || getAccent()};`;
  }

  $: filtered = sortCollections(
    $collections.filter((c) => matchesFilter(c, filter) && matchesTitle(c, titleFilter)),
    sortKey,
    sortDir
  );

  const VISIBLE_LIMIT = 100;
  $: visible = filtered.slice(0, VISIBLE_LIMIT);

  async function loadCollections() {
    isLoading.set(true);
    try {
      const res = await api.collections.list(true);
      collections.set(res.collections);
    } finally {
      isLoading.set(false);
    }
  }

  async function openCollection(c: Collection) {
    const pending = $pendingReference;
    if (pending) {
      for (const id of pending.snipselIds) {
        await api.snipsels.reference(c.id, id);
        if (pending.mode === 'move' && pending.fromCollectionId) {
          await api.snipsels.delete(pending.fromCollectionId, id);
        }
      }
      pendingReference.set(null);
      collectionAnchor.set(null);
      currentView.set({ type: 'collection', id: c.id });
      return;
    }
    collectionAnchor.set(null);
    currentView.set({ type: 'collection', id: c.id });
  }

  async function toggleFavorite(c: Collection) {
    const next = !Boolean(c.is_favorite);
    collections.update((list) => list.map((x) => (x.id === c.id ? { ...x, is_favorite: next } : x)));
    try {
      if (next) {
        await api.collections.favorite(c.id);
      } else {
        await api.collections.unfavorite(c.id);
      }
    } catch {
      collections.update((list) => list.map((x) => (x.id === c.id ? { ...x, is_favorite: !next } : x)));
    }
  }

  function editCollection(c: Collection) {
    currentView.set({ type: 'collection_settings', id: c.id });
  }

  async function createCollection() {
    if (!newTitle.trim()) return;
    busy = true;
    try {
      const res = await api.collections.create({ title: newTitle.trim(), icon: newIcon || '🗒' });
      collections.update((list) => [res.collection, ...list]);
      showCreate = false;
      newTitle = '';
      newIcon = '🗒';
      await openCollection(res.collection);
    } finally {
      busy = false;
    }
  }

  $: if (!didInitialLoad) {
    didInitialLoad = true;
    loadCollections();
  }
</script>

<div class="space-y-4">
  <div class="flex items-center justify-between">
    <h2 class="flex items-center gap-2 text-2xl font-semibold text-slate-800 dark:text-slate-100">
      <List label="" size={24} className="text-slate-700 dark:text-slate-300" />
      <span>Collections</span>
    </h2>
    <button
      class="al-icon-wrapper grid h-10 w-10 place-items-center rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 hover:bg-slate-50 transition-all dark:border-white/10 dark:bg-slate-900 dark:ring-white/5 dark:hover:bg-white/5"
      type="button"
      onclick={() => (showCreate = true)}
      aria-label="New collection"
      title="New collection"
    >
      <Plus label="" size={24} color={getAccent()} />
    </button>
  </div>

  <div class="overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-900 dark:ring-white/5">
    <div class="grid grid-cols-7">
      <button
        class="grid place-items-center py-3 text-sm transition-colors {filter === 'all'
          ? 'text-slate-900 dark:text-white'
          : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
        type="button"
        onclick={() => (filter = 'all')}
        style={filter === 'all' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        title="All"
      >
        <span class="text-xl font-bold leading-none mt-1">*</span>
      </button>
      <button
        class="grid place-items-center border-l border-black/5 py-3 text-sm transition-colors {filter === 'favorites'
          ? 'text-slate-900 dark:text-white'
          : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
        type="button"
        onclick={() => (filter = 'favorites')}
        style={filter === 'favorites' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        title="Favs"
      >
        <Heart label="" size={20} />
      </button>
      <button
        class="grid place-items-center border-l border-black/5 py-3 text-sm transition-colors {filter === 'day'
          ? 'text-slate-900 dark:text-white'
          : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
        type="button"
        onclick={() => (filter = 'day')}
        style={filter === 'day' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        title="Days"
      >
        <Calendar label="" size={20} />
      </button>
      <button
        class="grid place-items-center border-l border-black/5 py-3 text-sm transition-colors {filter === 'mine'
          ? 'text-slate-900 dark:text-white'
          : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
        type="button"
        onclick={() => (filter = 'mine')}
        style={filter === 'mine' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        title="My"
      >
        <User label="" size={20} />
      </button>
      <button
        class="grid place-items-center border-l border-black/5 py-3 text-sm transition-colors {filter === 'shared'
          ? 'text-slate-900 dark:text-white'
          : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
        type="button"
        onclick={() => (filter = 'shared')}
        style={filter === 'shared' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        title="Shared"
      >
        <Users label="" size={20} />
      </button>
      <button
        class="grid place-items-center border-l border-black/5 py-3 text-sm transition-colors {filter === 'templates'
          ? 'text-slate-900 dark:text-white'
          : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
        type="button"
        onclick={() => (filter = 'templates')}
        style={filter === 'templates' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        title="Templates"
      >
        <LayoutTemplate label="" size={20} />
      </button>
      <button
        class="grid place-items-center border-l border-black/5 py-3 text-sm transition-colors {filter === 'archive'
          ? 'text-slate-900 dark:text-white'
          : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
        type="button"
        onclick={() => (filter = 'archive')}
        style={filter === 'archive' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        title="Archive"
      >
        <Archive label="" size={20} />
      </button>
    </div>
  </div>

  <div class="flex items-center gap-3">
    <input
      class="min-w-0 flex-1 rounded-full border border-slate-200 bg-white px-4 py-2 text-base shadow-sm outline-none ring-1 ring-black/5 transition-all focus:ring-2 dark:border-white/10 dark:bg-slate-900 dark:text-slate-100"
      style={`--tw-ring-color: ${getAccent()}33; --accent: ${getAccent()}`}
      onfocus={(e) => (e.currentTarget.style.borderColor = getAccent())}
      onblur={(e) => (e.currentTarget.style.borderColor = '')}
      type="search"
      placeholder="Filter by title"
      bind:value={titleFilter}
    />

    {#if listView === 'list'}
      <button
        class="grid h-10 w-10 place-items-center rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 hover:bg-slate-50 transition-all dark:border-white/10 dark:bg-slate-900 dark:ring-white/5 dark:hover:bg-white/5"
        type="button"
        onclick={() => setListView('cards')}
        aria-label="Switch to card view"
        title="Card view"
      >
        <LayoutGrid label="" size={20} color={getAccent()} />
      </button>
    {:else}
      <button
        class="grid h-10 w-10 place-items-center rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 hover:bg-slate-50 transition-all dark:border-white/10 dark:bg-slate-900 dark:ring-white/5 dark:hover:bg-white/5"
        type="button"
        onclick={() => setListView('list')}
        aria-label="Switch to list view"
        title="List view"
      >
        <LayoutList label="" size={20} color={getAccent()} />
      </button>
    {/if}

    <div class="ml-auto flex items-center gap-2">
      <div class="overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-900">
        <div class="flex">
          <button
            class="px-4 py-2 text-sm font-medium {sortKey === 'modified'
              ? 'text-slate-900 dark:text-white'
              : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
            type="button"
            onclick={() => (sortKey = 'modified')}
            style={sortKey === 'modified' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          >
            Modified
          </button>
          <button
            class="border-l border-black/5 px-4 py-2 text-sm font-medium {sortKey === 'name'
              ? 'text-slate-900 dark:text-white'
              : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
            type="button"
            onclick={() => (sortKey = 'name')}
            style={sortKey === 'name' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          >
            Name
          </button>
        </div>
      </div>

      <button
        class="grid h-10 w-10 place-items-center rounded-full border border-slate-200 bg-white text-lg text-slate-700 shadow-sm ring-1 ring-black/5 hover:bg-slate-50 transition-all dark:border-white/10 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-white/5"
        type="button"
        aria-label={sortDir === 'asc' ? 'Sort ascending' : 'Sort descending'}
        title={sortDir === 'asc' ? 'Ascending' : 'Descending'}
        onclick={() => (sortDir = sortDir === 'asc' ? 'desc' : 'asc')}
      >
        {sortDir === 'asc' ? '↑' : '↓'}
      </button>
    </div>
  </div>

  {#if showCreate}
    <form
      class="space-y-4 rounded-3xl border border-slate-200 bg-white/80 p-6 shadow-xl ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10"
      in:fly={{ y: -20, duration: 200 }}
      out:fade={{ duration: 150 }}
      onsubmit={(e) => {
        e.preventDefault();
        createCollection();
      }}
    >
      <div class="flex gap-3">
        <input
          class="w-20 rounded-2xl border border-slate-200 bg-white px-3 py-2 text-center text-2xl shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:ring-white/10"
          bind:value={newIcon}
          maxlength={2}
          placeholder="📋"
        />
        <input
          class="flex-1 rounded-2xl border border-slate-200 bg-white px-4 py-2 text-lg shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:ring-white/10"
          bind:value={newTitle}
          placeholder="Collection title"
        />
      </div>
      <div class="flex gap-2">
        <button
          class="flex-1 rounded-full border border-slate-200 bg-white px-4 py-3 text-base font-bold shadow-sm ring-1 ring-black/5 transition-all hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-slate-700"
          style={`color: ${getAccent()}`}
          type="submit"
          disabled={busy || !newTitle.trim()}
        >
          {busy ? 'Creating...' : 'Create Collection'}
        </button>
        <button
          class="rounded-full border border-slate-200 bg-white px-6 py-3 text-base font-medium text-slate-600 shadow-sm ring-1 ring-black/5 hover:bg-slate-50 transition-all dark:border-white/10 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700"
          type="button"
          onclick={() => (showCreate = false)}
        >
          Cancel
        </button>
      </div>
    </form>
  {/if}

  {#if $isLoading}
    <div class="py-8 text-center text-sm text-slate-500 font-medium" in:fade={{ duration: 200 }}>Loading collections...</div>
  {:else if filtered.length === 0}
    <div class="py-8 text-center text-sm text-slate-500 font-medium" in:fade={{ duration: 200 }}>No collections found</div>
  {:else if listView === 'cards'}
    <div class="grid grid-cols-2 gap-3">
      {#each visible as c (c.id)}
        <div
          class="group relative overflow-hidden rounded-2xl border border-slate-200 bg-white text-left shadow-sm transition-all hover:shadow-md dark:border-white/10 dark:bg-slate-900 cursor-pointer flex h-36 flex-col"
          role="button"
          tabindex="0"
          onclick={() => openCollection(c)}
          onkeydown={(e) => {
            if (e.target === e.currentTarget && (e.key === 'Enter' || e.key === ' ')) {
              e.preventDefault();
              openCollection(c);
            }
          }}
          in:fly={{ y: 10, duration: 200 }}
          out:fade={{ duration: 150 }}
        >
          <div
            class="relative flex flex-1 items-center justify-center overflow-hidden dark:brightness-75"
            style={cardHeaderStyle(c)}
          >
            <button
              class="al-icon-wrapper absolute right-2 top-2 z-10 grid h-8 w-8 place-items-center rounded-full border border-black/5 bg-white/80 shadow-sm backdrop-blur-md transition-all hover:scale-110 hover:bg-white active:scale-95 dark:border-white/10 dark:bg-slate-900/80 dark:hover:bg-slate-900 {c.is_favorite ? '' : 'text-slate-400 hover:text-slate-600 dark:text-slate-400 dark:hover:text-slate-200'}"
              type="button"
              aria-label={c.is_favorite ? 'Unfavorite' : 'Favorite'}
              title={c.is_favorite ? 'Unfavorite' : 'Favorite'}
              onclick={(e) => {
                e.stopPropagation();
                toggleFavorite(c);
              }}
              style={c.is_favorite ? `color: ${getAccent()}` : undefined}
            >
              {#if c.is_favorite}
                <Heart label="" size={16} className="fill-current" />
              {:else}
                <Heart label="" size={16} />
              {/if}
            </button>
          </div>
          <div class="flex items-center gap-2 px-2.5 py-2">
            <span class="text-lg leading-none shrink-0">{c.icon}</span>
            <span class="min-w-0 flex-1 truncate text-sm font-medium text-slate-800 dark:text-slate-200">{c.title}</span>
            {#if c.access_level === 'read' || c.access_level === 'write'}
              <span class="shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-bold" style={`background-color: ${getAccentTint()}; color: ${getAccent()}`}>shared</span>
            {/if}
            <button
              class="al-icon-wrapper grid h-7 w-7 shrink-0 place-items-center rounded-full text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors dark:hover:bg-white/10 dark:hover:text-slate-200"
              type="button"
              aria-label="Edit collection"
              title="Edit"
              onclick={(e) => {
                e.stopPropagation();
                editCollection(c);
              }}
            >
              <Info label="" size={16} />
            </button>
          </div>
        </div>
      {/each}
    </div>
    {#if filtered.length > VISIBLE_LIMIT}
      <div class="mt-4 py-6 text-center text-sm text-slate-500 font-medium bg-slate-50/50 rounded-xl border border-slate-200/50 dark:bg-slate-900/30 dark:border-white/5">
        Showing <span class="font-bold text-slate-700 dark:text-slate-300">{VISIBLE_LIMIT}</span> of <span class="font-bold text-slate-700 dark:text-slate-300">{filtered.length}</span> collections.<br/>
        Use the filter above to find more.
      </div>
    {/if}
  {:else}
    <div class="space-y-2">
      {#each visible as c (c.id)}
        <div class="flex w-full items-center gap-3 px-1 py-2 group" animate:flip={{ duration: 200 }} in:fly={{ y: 10, duration: 200 }} out:fade={{ duration: 150 }}>
          <button class="flex flex-1 items-center gap-3 text-left transition-all hover:translate-x-0.5" type="button" onclick={() => openCollection(c)}>
            <span class="text-3xl transition-transform duration-200 group-hover:scale-110">{c.icon}</span>
            <div class="min-w-0 flex-1">
              <div class="truncate text-lg font-medium text-slate-800 dark:text-slate-200">{c.title.length > 50 ? c.title.slice(0, 47) + '...' : c.title}</div>
              <div class="mt-0.5 flex flex-wrap items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
                {#if c.access_level === 'read' || c.access_level === 'write'}
                  <span class="rounded-full px-2 py-0.5 font-medium border border-black/5 dark:border-white/10" style={`background-color: ${getAccentTint()}; color: ${getAccent()}`}
                    >shared</span
                  >
                {/if}
                {#if c.archived}
                  <span class="rounded-full px-2 py-0.5 font-medium border border-black/5 dark:border-white/10" style={`background-color: ${getAccentTint()}; color: ${getAccent()}`}
                    >archived</span
                  >
                {/if}
              </div>
            </div>
          </button>

          <div class="overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 flex h-11 items-center px-1 dark:border-white/10 dark:bg-slate-900 dark:ring-white/5">
            {#if filter === 'shared'}
              <div
                class="grid h-10 w-10 place-items-center text-lg text-slate-400"
                aria-label={c.access_level === 'owner' && c.shared_out ? 'Shared by you' : 'Shared with you'}
                title={c.access_level === 'owner' && c.shared_out ? 'Shared by you' : 'Shared with you'}
                style={c.access_level === 'owner' && c.shared_out ? `color: ${getAccent()}` : undefined}
              >
                {#if c.access_level === 'owner' && c.shared_out}
                  <ArrowUp label="" size={20} />
                {:else}
                  <ArrowDown label="" size={20} />
                {/if}
              </div>
              <div class="h-6 w-px bg-slate-100 mx-0.5 dark:bg-white/10"></div>
            {/if}

            {#if c.is_template}
              <div class="grid h-9 w-9 place-items-center text-slate-400" title="Template">
                <LayoutTemplate label="" size={16} />
              </div>
              <div class="h-6 w-px bg-slate-100 mx-0.5 dark:bg-white/10"></div>
            {/if}

            <button
              class="al-icon-wrapper grid h-9 w-9 place-items-center rounded-full text-slate-400 hover:bg-slate-50 transition-colors"
              type="button"
              aria-label={c.is_favorite ? 'Unfavorite' : 'Favorite'}
              title={c.is_favorite ? 'Unfavorite' : 'Favorite'}
              onclick={() => toggleFavorite(c)}
              style={c.is_favorite ? `color: ${getAccent()}` : undefined}
            >
              {#if c.is_favorite}
                <Heart label="" size={20} className="fill-current" />
              {:else}
                <Heart label="" size={20} />
              {/if}
            </button>
            <div class="h-6 w-px bg-slate-100 mx-0.5 dark:bg-white/10"></div>
            <button
              class="al-icon-wrapper grid h-9 w-9 place-items-center rounded-full text-slate-400 hover:bg-slate-50 transition-colors dark:hover:bg-white/5"
              type="button"
              aria-label="Edit collection"
              title="Edit"
              onclick={() => editCollection(c)}
            >
              <Info label="" size={20} />
            </button>
          </div>
        </div>
      {/each}
      {#if filtered.length > VISIBLE_LIMIT}
        <div class="py-6 text-center text-sm text-slate-500 font-medium bg-slate-50/50 rounded-xl border border-slate-200/50 dark:bg-slate-900/30 dark:border-white/5">
          Showing <span class="font-bold text-slate-700 dark:text-slate-300">{VISIBLE_LIMIT}</span> of <span class="font-bold text-slate-700 dark:text-slate-300">{filtered.length}</span> collections.<br/>
          Use the filter above to find more.
        </div>
      {/if}
    </div>
  {/if}
</div>
