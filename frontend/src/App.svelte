<script lang="ts">
  import { fly, fade } from 'svelte/transition';
  import Clock from '@animated-color-icons/lucide-svelte/Clock.svelte';
  import Bell from '@animated-color-icons/lucide-svelte/Bell.svelte';
  import SettingsIcon from '@animated-color-icons/lucide-svelte/Settings.svelte';
  import CalendarIcon from '@animated-color-icons/lucide-svelte/Calendar.svelte';
  import SquareCheck from '@animated-color-icons/lucide-svelte/SquareCheck.svelte';
  import PlusIcon from '@animated-color-icons/lucide-svelte/Plus.svelte';
  import List from '@animated-color-icons/lucide-svelte/List.svelte';
  import Hash from '@animated-color-icons/lucide-svelte/Hash.svelte';
  import { untrack } from 'svelte';
  import { api } from './lib/api';
  import { currentUser } from './lib/session';
import { collections, collectionAnchor, currentView, currentCollection, isLoading, pendingReference, searchError, searchQuery, searchResults, notificationsStore, searchType, searchScope, recentCollectionsStore, createSnipselOnLoad, getTodayDate, snipselsSelected } from './lib/stores';
  import {
    getCurrentUrl,
    parseRouteFromLocation,
    pushUrl,
    replaceUrl,
    routeToUrl,
    routeToView,
    viewToRoute,
  } from './lib/router';
  import Login from './routes/Login.svelte';
  import CollectionsList from './routes/CollectionsList.svelte';
  import CollectionOutliner from './routes/CollectionOutliner.svelte';
  import Search from './routes/Search.svelte';
  import Todos from './routes/Todos.svelte';
  import Calendar from './routes/Calendar.svelte';
  import Settings from './routes/Settings.svelte';
  import SnipselDetail from './routes/SnipselDetail.svelte';
  import CollectionSettings from './routes/CollectionSettings.svelte';
  import TagsMentions from './routes/TagsMentions.svelte';
  import Notifications from './routes/Notifications.svelte';
  import Importer from './routes/Importer.svelte';
  import RecycleBin from './routes/RecycleBin.svelte';
  import PasscodeModal from './lib/PasscodeModal.svelte';
  import PublicView from './routes/PublicView.svelte';

  let initialized = $state(false);

  let isApplyingRoute = $state(false);
  let didInitRoute = $state(false);

  let hasSyncedUrl = $state(false);

  let lastUserId: string | null = $state(null);

  let isSwitchingCollection = $state(false);
  let pendingPasscodeCollectionId = $state<string | null>(null);

  let lastCollectionId: string | null = $state(null);

  let recentContainerRef: HTMLDivElement | undefined = $state();
  let showRecentPopup = $state(false);
  let focusProxyNavRef: HTMLInputElement | undefined = $state();
  async function toggleRecentPopup() {
    if (!showRecentPopup) {
      try {
        const res = await api.collections.listRecent();
        recentCollectionsStore.set(res.collections);
      } catch { /* ignore */ }
    }
    showRecentPopup = !showRecentPopup;
  }
  async function clearRecent() {
    if (!confirm('Clear recently visited history?')) return;
    try {
      await api.collections.clearRecent();
      recentCollectionsStore.set([]);
    } catch { /* ignore */ }
  }

  $effect(() => {
    if (!showRecentPopup) return;
    const onClick = (e: MouseEvent) => {
      if (recentContainerRef && !recentContainerRef.contains(e.target as Node)) {
        showRecentPopup = false;
      }
    };
    window.addEventListener('mousedown', onClick);
    return () => window.removeEventListener('mousedown', onClick);
  });

  async function pruneEmptySnipsels(collectionId: string) {
    try {
      const res = await api.snipsels.list(collectionId);
      const emptyIds = res.items
        .filter((i) => (i.snipsel.content_markdown ?? '').trim().length === 0 && i.snipsel.attachments.length === 0)
        .map((i) => i.snipsel_id);

      if (emptyIds.length === 0) return { items: res.items, deletedCount: 0 };
      for (const id of emptyIds) {
        await api.snipsels.delete(collectionId, id);
      }
      return { items: res.items, deletedCount: emptyIds.length };
    } catch {
      // best-effort
      return { items: [], deletedCount: 0 };
    }
  }

  async function maybeDeleteEmptyDayCollection(collectionId: string) {
    const c = untrack(() => $currentCollection);
    if (!c || c.id !== collectionId) return;
    if (!c.list_for_day) return;

    try {
      const pruneRes = await pruneEmptySnipsels(collectionId);
      if (!pruneRes) return;
      if (pruneRes.items.length > pruneRes.deletedCount) return;

      await api.collections.delete(collectionId);
      if (untrack(() => $currentCollection?.id) === collectionId) currentCollection.set(null);
      collections.update((xs) => xs.filter((x) => x.id !== collectionId));
    } catch {
      // best-effort
    }
  }

  async function initSession() {
    try {
      const res = await api.me();
      currentUser.set(res.user);
    } catch {
      currentUser.set(null);
    } finally {
      applyInitialRoute();
      initialized = true;
    }
  }

  function applyInitialRoute() {
    if (didInitRoute) return;
    didInitRoute = true;

    const route = parseRouteFromLocation(window.location);
    if (!route) {
      openToday().then(() => {
        const id = untrack(() => $currentCollection?.id);
        replaceUrl(id ? routeToUrl({ v: 'collection', id }) : routeToUrl({ v: 'collections' }));
      });
      return;
    }

    isApplyingRoute = true;
    try {
      currentView.set(routeToView(route));
      if (route.v === 'collection') {
        if (route.sn || route.pos) {
          collectionAnchor.set({ collectionId: route.id, snipselId: route.sn, pos: route.pos });
        } else {
          collectionAnchor.set(null);
        }
      } else {
        collectionAnchor.set(null);
      }
      if (route.v === 'search') {
        searchQuery.set(route.q ?? '');
      }
      if (route.v === 'public') {
        // Public route doesn't require authentication, but initSession handles it
      }
    } finally {
      isApplyingRoute = false;
    }
  }

  async function onNewSnipsel() {
    // Focus proxy before any async operations (opens mobile keyboard)
    focusProxyNavRef?.focus();
    // Set flag to create snipsel after collection loads
    createSnipselOnLoad.set(true);
    try {
      await openToday();
      // CollectionOutliner will see the flag and create snipsel
    } finally {
      focusProxyNavRef?.blur();
    }
  }

  async function openToday() {
    isLoading.set(true);
    isSwitchingCollection = true;
    try {
      const today = getTodayDate();
      const res = await api.collections.today(today);
      currentCollection.set(res.collection);
      currentView.set({ type: 'collection', id: res.collection.id });
    } finally {
      isLoading.set(false);
      isSwitchingCollection = false;
    }
  }

  async function openCollections() {
    isLoading.set(true);
    try {
      const res = await api.collections.list();
      collections.set(res.collections);
      currentView.set({ type: 'collections' });
    } finally {
      isLoading.set(false);
    }
  }

  async function logout() {
    await api.logout();
    currentUser.set(null);
    currentView.set({ type: 'loading' });
  }

  async function openCollectionById(id: string) {
    isLoading.set(true);
    isSwitchingCollection = true;
    try {
      const res = await api.collections.get(id);
      currentCollection.set(res.collection);
    } catch (err: any) {
      if (err?.error?.code === 'passcode_required') {
        pendingPasscodeCollectionId = id;
      } else {
        currentCollection.set(null);
        collectionAnchor.set(null);
        currentView.set({ type: 'collections' });
        replaceUrl(routeToUrl({ v: 'collections' }));
      }
    } finally {
      isLoading.set(false);
      isSwitchingCollection = false;
    }
  }

  let isSearching = false;
  async function runSearch() {
    if (isSearching) return;
    const qRaw = untrack(() => $searchQuery).trim();
    const type = untrack(() => $searchType);
    const scope = untrack(() => $searchScope);

    if (!qRaw && !type) {
      searchResults.set(null);
      searchError.set(null);
      return;
    }
    
    isSearching = true;
    
    // Auto-detect tag/mention prefix
    let q = qRaw;
    let tag: string | undefined = undefined;
    let mention: string | undefined = undefined;
    
    if (q.startsWith('#')) {
      tag = q.slice(1);
      q = '';
    } else if (q.startsWith('@')) {
      mention = q.slice(1);
      q = '';
    }

    // Set view to search if not already, but guard it with strict check
    const curView = untrack(() => $currentView);
    if (curView.type !== 'search') {
      currentView.set({ type: 'search' });
    }

    searchError.set(null);
    isLoading.set(true);
    try {
      const res = await api.search({ 
        q: q || undefined, 
        type, 
        tag, 
        mention, 
        scope: scope !== 'all' ? scope : undefined 
      });
      searchResults.set(res);
    } catch (e) {
      console.error('Search failed:', e);
      searchResults.set(null);
      searchError.set('Search failed');
    } finally {
      isLoading.set(false);
      isSearching = false;
    }
  }

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
    const u = $currentUser;
    const raw = (u?.default_collection_header_color || '').trim() || DEFAULT_ACCENT;
    return /^#[0-9a-fA-F]{6}$/.test(raw) ? raw : DEFAULT_ACCENT;
  }

  function getAccentTint(): string {
    const base = { r: 255, g: 255, b: 255 };
    const accent = hexToRgb(getAccent());
    const mixed = accent ? mixRgb(base, accent, 0.14) : base;
    return rgba(mixed, 0.96);
  }

  function getNavPlusColor(): string {
    if ($currentView.type === 'collection' && $currentCollection?.header_color) {
      const color = $currentCollection.header_color.trim();
      if (/^#[0-9a-fA-F]{6}$/.test(color)) {
        return color;
      }
    }
    return getAccent();
  }

  let isFetchingNotifications = false;
  async function fetchNotifications() {
    if (isFetchingNotifications) return;
    isFetchingNotifications = true;
    try {
      const res = await api.notifications.list();
      notificationsStore.set(res.notifications);
    } catch {
      // ignore
    } finally {
      isFetchingNotifications = false;
    }
  }

  $effect(() => {
    if (!initialized) {
      initSession();
    }
  });

  $effect(() => {
    const uid = $currentUser?.id ?? null;

    if (uid && uid !== lastUserId) {
      didInitRoute = false;
      hasSyncedUrl = false;
      lastUserId = uid;
      return;
    }

    if (!uid && lastUserId) {
      didInitRoute = false;
      hasSyncedUrl = false;
      lastUserId = null;
    }
  });

  $effect(() => {
    if (initialized && $currentUser && untrack(() => $currentView.type) === 'loading') {
      applyInitialRoute();
    }
  });

  // Notifications Effect
  $effect(() => {
    if (!initialized || !$currentUser) return;
    
    // Only track view type changes
    const viewType = $currentView.type;
    void viewType;

    untrack(() => fetchNotifications());

    const intervalId = setInterval(() => {
      untrack(() => fetchNotifications());
    }, 60000);
    return () => clearInterval(intervalId);
  });

  // Theme Effect
  $effect(() => {
    const theme = $currentUser?.theme || 'system';
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    function updateTheme() {
      const isDark = theme === 'dark' || (theme === 'system' && mediaQuery.matches);
      document.documentElement.classList.toggle('dark', isDark);
    }

    updateTheme();
    mediaQuery.addEventListener('change', updateTheme);
    return () => mediaQuery.removeEventListener('change', updateTheme);
  });

  // Search Effect
  let searchDebounce: ReturnType<typeof setTimeout> | null = null;
  $effect(() => {
    if (!initialized || !$currentUser) return;
    
    // Track query, type and scope
    const q = $searchQuery;
    const t = $searchType;
    const s = $searchScope;
    void q; void t; void s;

    // Run search if currently in search view
    const viewType = $currentView.type;
    if (viewType === 'search') {
      if (searchDebounce) clearTimeout(searchDebounce);
      searchDebounce = setTimeout(() => {
        untrack(() => runSearch());
      }, 300);
    }
  });

  $effect(() => {
    if (!initialized) return;
    if (!$currentUser) return;
    if (isApplyingRoute) return;

    // Read currentView and searchQuery
    const view = $currentView;
    const query = $searchQuery;

    if (view.type === 'collection') {
      const a = untrack(() => $collectionAnchor);
      if (!a || a.collectionId !== view.id) collectionAnchor.set(null);
    } else {
      if (untrack(() => $collectionAnchor)) collectionAnchor.set(null);
    }

    let route = viewToRoute(view);
    if (route.v === 'collection') {
      const a = untrack(() => $collectionAnchor);
      if (a && a.collectionId === route.id) {
        route = { ...route, sn: a.snipselId, pos: a.pos };
      }
    } else if (route.v === 'search') {
      route = { v: 'search', q: query.trim() || undefined };
    }

    const nextUrl = routeToUrl(route);
    const cur = getCurrentUrl();

    if (!hasSyncedUrl) {
      replaceUrl(nextUrl);
      hasSyncedUrl = true;
      return;
    }

    const shouldReplace = view.type === 'loading' || view.type === 'search';
    if (shouldReplace) replaceUrl(nextUrl);
    else if (cur !== nextUrl) pushUrl(nextUrl);
  });

  $effect(() => {
    if (!initialized) return;

    const onPopState = () => {
      if (!$currentUser) return;
      const route = parseRouteFromLocation(window.location);
      if (!route) return;

      isApplyingRoute = true;
      try {
        currentView.set(routeToView(route));
        if (route.v === 'collection') {
          if (route.sn || route.pos) {
            collectionAnchor.set({ collectionId: route.id, snipselId: route.sn, pos: route.pos });
          } else {
            collectionAnchor.set(null);
          }
        } else {
          collectionAnchor.set(null);
        }
        if (route.v === 'search') {
          searchQuery.set(route.q ?? '');
        }
        if (route.v === 'public') {
          // Handled by view update
        }
      } finally {
        isApplyingRoute = false;
      }
    };

    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  });

  $effect(() => {
    const view = $currentView;
    if (view.type === 'collection') {
      if (isSwitchingCollection) return;
      if (untrack(() => $currentCollection?.id) !== view.id) {
        untrack(() => openCollectionById(view.id));
      }
    }
  });

  $effect(() => {
    const view = $currentView;
    const nextId = view.type === 'collection' ? view.id : null;
    if (lastCollectionId && lastCollectionId !== nextId) {
      untrack(() => {
        pruneEmptySnipsels(lastCollectionId!);
        maybeDeleteEmptyDayCollection(lastCollectionId!);
      });
    }
    lastCollectionId = nextId;
  });
</script>

<div class="min-h-screen bg-slate-50 text-slate-900 transition-colors duration-300 dark:bg-slate-950 dark:text-slate-100">
  {#if $currentUser}
    <!-- Progressive blur layer behind header -->
    <div class="fixed top-0 left-0 right-0 z-[15] pointer-events-none" style="height: 120px;">
      <div class="absolute inset-0 backdrop-blur-lg" style="mask-image: linear-gradient(to bottom, black 0%, black 40%, transparent 100%); -webkit-mask-image: linear-gradient(to bottom, black 0%, black 40%, transparent 100%);"></div>
    </div>
    <header class="sticky top-4 z-20 mx-auto max-w-3xl px-4 pointer-events-none">
      <div class="pointer-events-auto flex items-center gap-3 rounded-full border border-slate-200 bg-white/80 px-3 py-2 shadow-lg ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/5">
        <button
          class="flex items-center gap-2 pl-2 pr-1 font-bold text-lg text-slate-800 transition-colors dark:text-slate-200 group"
          style="--logo-hover: {getAccent()}"
          type="button"
          onclick={openToday}
          onmouseenter={(e) => (e.currentTarget as HTMLButtonElement).style.color = getAccent()}
          onmouseleave={(e) => (e.currentTarget as HTMLButtonElement).style.color = ''}
        >
          <img src="/logo.svg" alt="snipsel logo" class="h-6 w-6 dark:brightness-110 dark:invert transition-transform duration-200 group-hover:scale-110" />
          <span class="hidden sm:inline transition-transform duration-200 origin-left group-hover:scale-105">snipsel</span>
        </button>
        <input
          class="min-w-0 flex-1 rounded-full border border-slate-200 bg-slate-100/50 px-4 py-2 text-base transition-all focus:border-[#4f46e5] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#4f46e5]/20 dark:border-white/5 dark:bg-slate-800/50 dark:text-slate-100 dark:focus:border-indigo-500 dark:focus:bg-slate-800"
          placeholder="Search"
          type="search"
          bind:value={$searchQuery}
          onfocus={() => {
            if ($currentUser && $currentView.type !== 'search') {
              currentView.set({ type: 'search' });
            }
          }}
          onkeydown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              runSearch();
            }
          }}
        />
        <div bind:this={recentContainerRef} class="relative">
          <button
            class="al-icon-wrapper grid h-10 w-10 shrink-0 place-items-center rounded-full transition-colors {showRecentPopup
              ? 'bg-black/10 text-slate-900 dark:bg-white/10 dark:text-white text-white'
              : 'text-slate-600 hover:bg-black/5 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-slate-100'}"
            type="button"
            onclick={toggleRecentPopup}
          aria-label="Recent collections"
          title="Recent"
        >
            <Clock label="" size={20} />
          </button>
          
          {#if showRecentPopup}
            <div class="absolute right-0 top-full z-50 mt-2 w-64 overflow-hidden rounded-xl border border-slate-200 bg-white/95 shadow-xl ring-1 ring-black/5 backdrop-blur-md pointer-events-auto dark:border-white/10 dark:bg-slate-900/95 dark:ring-white/10" in:fly={{ y: -10, duration: 150 }} out:fade={{ duration: 100 }}>
              <div class="px-3 py-2 text-xs font-bold uppercase tracking-wider text-slate-500 bg-slate-50/50 border-b border-slate-100 text-left dark:bg-slate-950/50 dark:border-white/5 dark:text-slate-400">Recently visited</div>
              <div class="max-h-80 overflow-y-auto py-1">
                {#if $recentCollectionsStore.length === 0}
                  <div class="px-4 py-3 text-sm text-slate-500 italic text-left dark:text-slate-400">No recent history</div>
                {:else}
                  {#each $recentCollectionsStore as rc (rc.id)}
                    <button
                      class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-slate-50 transition-colors dark:hover:bg-white/5"
                      type="button"
                      onclick={(e) => {
                        e.stopPropagation();
                        showRecentPopup = false;
                        currentView.set({ type: 'collection', id: rc.id });
                      }}
                    >
                      <span class="text-xl shrink-0">{rc.icon}</span>
                      <span class="truncate font-medium text-slate-800 dark:text-slate-200">{rc.title}</span>
                    </button>
                  {/each}
                {/if}
                {#if $recentCollectionsStore.length > 0}
                  <div class="border-t border-slate-100 mt-1 p-1 dark:border-white/5">
                    <button
                      class="w-full rounded-lg px-3 py-2 text-left text-xs font-medium text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/30 transition-colors"
                      type="button"
                      onclick={(e) => { e.stopPropagation(); clearRecent(); }}
                    >
                      Clear history
                    </button>
                  </div>
                {/if}
              </div>
            </div>
          {/if}
        </div>

        <button
          class="al-icon-wrapper relative grid h-10 w-10 shrink-0 place-items-center rounded-full transition-colors {$currentView.type === 'notifications'
            ? 'bg-black/10 text-slate-900 dark:bg-white/10 dark:text-slate-100'
            : 'text-slate-600 hover:bg-black/5 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-slate-100'}"
          type="button"
          onclick={() => currentView.set({ type: 'notifications' })}
          aria-label="Notifications"
          title="Notifications"
        >
          {#if $notificationsStore.filter(n => !n.is_read).length > 0}
            <span class="al-icon-wrapper absolute -right-1 -top-1 flex h-5 min-w-[1.25rem] items-center justify-center rounded-full px-1 text-xs font-bold text-white shadow-sm ring-2 ring-white dark:ring-slate-900"
                  style="background-color: {getAccent()}"
            >
              {$notificationsStore.filter(n => !n.is_read).length}
            </span>
          {/if}
          <Bell label="" size={20} />
        </button>
        <button
          class="al-icon-wrapper grid h-10 w-10 shrink-0 place-items-center rounded-full transition-colors {$currentView.type === 'settings'
            ? 'bg-black/10 text-slate-900 dark:bg-white/10 dark:text-slate-100'
            : 'text-slate-600 hover:bg-black/5 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-slate-100'}"
          onclick={() => currentView.set({ type: 'settings' })}
          aria-label="Settings"
          title="Settings"
        >
          <SettingsIcon label="" size={20} />
        </button>
      </div>
    </header>
  {/if}

  <main class="mx-auto max-w-3xl px-4 pt-12 pb-24">
    {#if !initialized}
      <div class="py-8 text-center text-sm text-slate-500">Loading...</div>
    {:else if !$currentUser && $currentView.type !== 'public'}
      <Login />
    {:else if $currentView.type === 'loading'}
      <div class="py-8 text-center text-sm text-slate-500">Loading...</div>
    {:else if $currentView.type === 'collections'}
      <CollectionsList />
    {:else if $currentView.type === 'collection'}
      <CollectionOutliner />
    {:else if $currentView.type === 'search'}
      <Search />
    {:else if $currentView.type === 'tags_mentions'}
      <TagsMentions />
    {:else if $currentView.type === 'todos'}
      <Todos />
    {:else if $currentView.type === 'calendar'}
      <Calendar />
    {:else if $currentView.type === 'settings'}
      <Settings />
    {:else if $currentView.type === 'importer'}
      <Importer />
    {:else if $currentView.type === 'notifications'}
      <Notifications />
    {:else if $currentView.type === 'recycle-bin'}
      <RecycleBin />
    {:else if $currentView.type === 'snipsel'}
      <SnipselDetail snipselId={$currentView.id} />
    {:else if $currentView.type === 'collection_settings'}
      <CollectionSettings collectionId={$currentView.id} />
    {:else if $currentView.type === 'public'}
      <PublicView token={$currentView.token} />
    {/if}
  </main>

  {#if pendingPasscodeCollectionId !== null}
    <PasscodeModal
      collectionId={pendingPasscodeCollectionId}
      onSuccess={() => {
        const id = pendingPasscodeCollectionId!;
        pendingPasscodeCollectionId = null;
        openCollectionById(id);
      }}
      onCancel={() => {
        pendingPasscodeCollectionId = null;
        currentView.set({ type: 'collections' });
      }}
    />
  {/if}

  {#if $currentUser}
    {#if $snipselsSelected === 0}
      <!-- Progressive blur layer behind navbar -->
      <div class="fixed bottom-0 left-0 right-0 z-[5] pointer-events-none" style="height: 120px;" in:fly={{ y: 100, duration: 250 }} out:fly={{ y: 100, duration: 200 }}>
        <div class="absolute inset-0 backdrop-blur-lg" style="mask-image: linear-gradient(to top, black 0%, black 40%, transparent 100%); -webkit-mask-image: linear-gradient(to top, black 0%, black 40%, transparent 100%);"></div>
      </div>
      <!-- Navbar -->
      <nav class="pointer-events-none fixed bottom-0 left-0 right-0 z-10" in:fly={{ y: 100, duration: 250 }} out:fly={{ y: 100, duration: 200 }}>
        <div class="mx-auto max-w-3xl px-4 pt-2" style="padding-bottom: calc(env(safe-area-inset-bottom) + 2rem);">
          <div class="pointer-events-auto mx-auto flex w-fit items-center gap-2 rounded-full border border-slate-200 bg-white/85 px-3 py-2 text-slate-700 shadow-lg ring-1 ring-black/5 backdrop-blur-xl dark:border-white/10 dark:bg-slate-900/85 dark:text-slate-200 dark:ring-white/10">
            <button
              class="al-icon-wrapper grid h-12 w-12 place-items-center rounded-full transition-colors {$currentView.type === 'calendar'
                ? 'bg-black/10 text-slate-900 dark:bg-white/10 dark:text-slate-100'
                : 'hover:bg-black/5 hover:text-slate-900 dark:hover:bg-white/5 dark:hover:text-slate-100'}"
              type="button"
              onclick={() => currentView.set({ type: 'calendar' })}
              aria-label="Calendar"
              title="Calendar"
            >
              <CalendarIcon label="" size={24} />
            </button>

            <button
              class="al-icon-wrapper grid h-12 w-12 place-items-center rounded-full transition-colors {$currentView.type === 'todos'
                ? 'bg-black/10 text-slate-900 dark:bg-white/10 dark:text-slate-100'
                : 'hover:bg-black/5 hover:text-slate-900 dark:hover:bg-white/5 dark:hover:text-slate-100'}"
              type="button"
              onclick={() => currentView.set({ type: 'todos' })}
              aria-label="Todos"
              title="Todos"
            >
              <SquareCheck label="" size={24} />
            </button>

            <button
              class="al-icon-wrapper grid h-12 w-12 place-items-center rounded-full transition-all hover:-translate-y-0.5 hover:shadow-lg"
              style={`background-color: ${getNavPlusColor()}; color: white`}
              type="button"
              onclick={onNewSnipsel}
              aria-label="New snipsel (today)"
              title="New snipsel (today)"
            >
              <PlusIcon label="" size={24} strokeWidth={2.5} />
            </button>

            <button
              class="al-icon-wrapper grid h-12 w-12 place-items-center rounded-full transition-colors {$currentView.type === 'collections'
                ? 'bg-black/10 text-slate-900 dark:bg-white/10 dark:text-slate-100'
                : 'hover:bg-black/5 hover:text-slate-900 dark:hover:bg-white/5 dark:hover:text-slate-100'}"
              type="button"
              onclick={openCollections}
              aria-label="Collections"
              title="Collections"
            >
              <List label="" size={24} />
            </button>

            <button
              class="al-icon-wrapper grid h-12 w-12 place-items-center rounded-full transition-colors {$currentView.type === 'tags_mentions'
                ? 'bg-black/10 text-slate-900 dark:bg-white/10 dark:text-slate-100'
                : 'hover:bg-black/5 hover:text-slate-900 dark:hover:bg-white/5 dark:hover:text-slate-100'}"
              type="button"
              onclick={() => currentView.set({ type: 'tags_mentions' })}
              aria-label="Tags and mentions"
              title="Tags / Mentions"
            >
              <Hash label="" size={24} />
            </button>
            
          </div>
        </div>
      </nav>
    {/if}
    <!-- Hidden input for mobile keyboard focus -->
    <input
      bind:this={focusProxyNavRef}
      class="pointer-events-none absolute left-0 top-0 h-0 w-0 opacity-0"
      tabindex="-1"
      aria-hidden="true"
    />
    <div class="h-24"></div>
  {/if}
</div>
