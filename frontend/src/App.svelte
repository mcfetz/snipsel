<script lang="ts">
  import { fly, fade } from 'svelte/transition';
  import Sparkles from '@animated-color-icons/lucide-svelte/Sparkles.svelte';
  import { registerSW } from 'virtual:pwa-register';
  import { untrack } from 'svelte';
  import { api } from './lib/api';
  import { currentUser } from './lib/session';
  import { initLiveUpdates, destroyLiveUpdates } from './lib/liveUpdates';
  import { longPress } from './lib/gestures';
  import { setupKeyboardShortcuts } from './lib/keyboardShortcuts';
  import NavigationHeader from './lib/NavigationHeader.svelte';
  import BottomNavBar from './lib/BottomNavBar.svelte';
  import { collections, collectionAnchor, collectionItems, currentView, currentCollection, editingSnipselId, isLoading, pendingReference, searchError, searchQuery, searchResults, notificationsStore, searchType, searchScope, recentCollectionsStore, createSnipselOnLoad, getTodayDate, snipselsSelected, clearSelectionRequest, deleteSelectionRequest, moveSelectionRequest, indentSelectionRequest, aiAssistantRequest, toggleTypeRequest, toggleCardViewRequest, copySnipselsRequest, moveSnipselsRequest, infoSnipselsRequest, uploadAttachmentRequest, newSnipselInCurrentCollectionRequest } from './lib/stores';
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
import UserManagement from './routes/UserManagement.svelte';
import Habits from './routes/Habits.svelte';
import HabitDetail from './routes/HabitDetail.svelte';

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

  let plusPressState = $state<'idle' | 'holding' | 'long'>('idle');
  let showIOSPasteHint = $state(false);

  let needPwaRefresh = $state(false);
  let updateServiceWorker: ((reloadPage?: boolean) => Promise<void>) | undefined;

  async function reloadPwa() {
    needPwaRefresh = false;

    // Send skipWaiting directly to any waiting ServiceWorker
    if (typeof navigator !== 'undefined' && 'serviceWorker' in navigator) {
      try {
        const reg = await navigator.serviceWorker.getRegistration();
        if (reg?.waiting) {
          reg.waiting.postMessage({ type: 'SKIP_WAITING' });
        }
      } catch {}
    }

    // Also trigger update through vite-plugin-pwa
    try {
      if (updateServiceWorker) {
        await updateServiceWorker(true);
      }
    } catch (err) {
      console.warn('updateServiceWorker failed:', err);
    }

    // Listen for controllerchange to reload cleanly once the new SW activates
    let reloaded = false;
    if (typeof navigator !== 'undefined' && 'serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener(
        'controllerchange',
        () => {
          if (!reloaded) {
            reloaded = true;
            window.location.reload();
          }
        },
        { once: true }
      );
    }

    // Safety timeout in case controllerchange doesn't fire
    setTimeout(() => {
      if (!reloaded) {
        reloaded = true;
        window.location.reload();
      }
    }, 1500);
  }

  if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
    updateServiceWorker = registerSW({
      immediate: true,
      onNeedRefresh() {
        needPwaRefresh = true;
      },
      onOfflineReady() {
        console.log('[PWA] Ready to work offline');
      },
      onRegistered(r) {
        if (r) {
          // Periodically check for updates (every 15 minutes) and when user returns to tab
          setInterval(() => {
            r.update().catch(() => {});
          }, 15 * 60 * 1000);
          document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
              r.update().catch(() => {});
            }
          });
        }
      },
      onRegisterError(error) {
        console.error('[PWA] ServiceWorker registration error:', error);
      },
    });
  }

  function isAppleDevice(): boolean {
    if (typeof navigator === 'undefined') return false;
    const ua = navigator.userAgent || '';
    const platform = navigator.platform || '';
    return /iPad|iPhone|iPod/.test(ua) || (platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  }

  function maybeShowIOSPasteHint() {
    if (!isAppleDevice()) return;
    try {
      if (localStorage.getItem('snipsel_ios_paste_hint_shown') === '1') return;
      localStorage.setItem('snipsel_ios_paste_hint_shown', '1');
    } catch {}
    showIOSPasteHint = true;
    setTimeout(() => { showIOSPasteHint = false; }, 7000);
  }

  async function readClipboard(): Promise<{ text?: string; image?: File }> {
    if (typeof navigator === 'undefined' || !navigator.clipboard) return {};

    if (isAppleDevice()) {
      try {
        if (typeof navigator.clipboard.readText === 'function') {
          const text = await navigator.clipboard.readText();
          if (text && text.trim()) return { text };
        }
      } catch (err: any) {
        return {};
      }

      try {
        if (typeof navigator.clipboard.read === 'function') {
          const items = await navigator.clipboard.read();
          for (const item of items) {
            const imageType = item.types.find((t) => t.startsWith('image/'));
            if (imageType) {
              const blob = await item.getType(imageType);
              const ext = imageType.split('/')[1]?.replace('+xml', '') || 'png';
              return { image: new File([blob], `pasted-image-${Date.now()}.${ext}`, { type: imageType }) };
            }
          }
        }
      } catch (err: any) {}
      return {};
    }

    // Non-Apple (Chrome, Firefox, Android): read() first (supports images & rich content)
    try {
      if (typeof navigator.clipboard.read === 'function') {
        const items = await navigator.clipboard.read();
        for (const item of items) {
          const imageType = item.types.find((t) => t.startsWith('image/'));
          if (imageType) {
            const blob = await item.getType(imageType);
            const ext = imageType.split('/')[1]?.replace('+xml', '') || 'png';
            return { image: new File([blob], `pasted-image-${Date.now()}.${ext}`, { type: imageType }) };
          }
          if (item.types.includes('text/plain')) {
            const blob = await item.getType('text/plain');
            const text = await blob.text();
            if (text) return { text };
          }
        }
      }
    } catch (err) {}

    try {
      if (typeof navigator.clipboard.readText === 'function') {
        const text = await navigator.clipboard.readText();
        if (text) return { text };
      }
    } catch (err) {}

    return {};
  }

  async function onNewSnipselFromClipboard() {
    isLoading.set(true);
    try {
      const { text, image } = await readClipboard();
      const clipText = text?.trim() || '';
      const clipImageFile = image || null;

      // If clipboard was empty (or blocked by platform like iOS Safari/PWA), fallback to normal new snipsel
      if (!clipText && !clipImageFile) {
        maybeShowIOSPasteHint();
        await onNewSnipsel();
        return;
      }

      const today = getTodayDate();
      const res = await api.collections.today(today);
      const col = res.collection;

      const createRes = await api.snipsels.create(col.id, {
        content_markdown: clipText || null,
        type: clipImageFile ? 'image' : (col.default_snipsel_type || 'text'),
      });

      if (createRes?.item) {
        const snipselId = createRes.item.snipsel_id;

        if (clipImageFile) {
          try {
            const uploadRes = await api.attachments.upload(snipselId, clipImageFile);
            if (uploadRes?.attachment) {
              createRes.item.snipsel.attachments = [uploadRes.attachment];
              createRes.item.snipsel.type = 'image';
            }
          } catch (uploadErr) {
            console.error('Failed to upload image from clipboard:', uploadErr);
          }
        }

        collectionItems.update((items) => {
          if ($currentCollection?.id === col.id) {
            return items.some((i) => i.snipsel_id === snipselId)
              ? items.map((i) => (i.snipsel_id === snipselId ? createRes.item : i))
              : [...items, createRes.item];
          }
          return items;
        });

        collectionAnchor.set({
          collectionId: col.id,
          snipselId: snipselId,
          pos: createRes.item.position,
        });
      }

      currentCollection.set(col);
      currentView.set({ type: 'collection', id: col.id });
    } catch (err) {
      console.error('Failed to create snipsel from clipboard:', err);
    } finally {
      isLoading.set(false);
    }
  }

  const lpNewSnipsel = longPress(
    () => void onNewSnipselFromClipboard(),
    () => void onNewSnipsel(),
    400,
    (state) => { plusPressState = state; }
  );

  async function openToday() {
    isLoading.set(true);
    isSwitchingCollection = true;
    collectionItems.set([]);
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
      const res = await api.collections.list(true);
      collections.set(res.collections);
      currentView.set({ type: 'collections' });
    } finally {
      isLoading.set(false);
    }
  }

  async function logout() {
    destroyLiveUpdates();
    await api.logout();
    currentUser.set(null);
    currentView.set({ type: 'loading' });
  }

  async function openCollectionById(id: string) {
    isLoading.set(true);
    isSwitchingCollection = true;
    collectionItems.set([]);
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
      isSearching = false;
      return;
    }

    // Minimum 3 characters for full-text search unless filters are used
    if (qRaw.length > 0 && qRaw.length < 3 && !type && !qRaw.startsWith('#') && !qRaw.startsWith('@')) {
      searchResults.set(null);
      isSearching = false;
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

  function isLightColor(color: string): boolean {
    const hex = color.replace('#', '');
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
    return brightness > 128;
  }

  function getNavPlusIconColor(): string {
    const bgColor = getNavPlusColor();
    return isLightColor(bgColor) ? '#1e293b' : 'white';
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
      // Start real-time updates for newly logged-in user
      initLiveUpdates();
      return;
    }

    if (!uid && lastUserId) {
      didInitRoute = false;
      hasSyncedUrl = false;
      lastUserId = null;
      destroyLiveUpdates();
    }
  });

  $effect(() => {
    if (initialized && $currentUser && untrack(() => $currentView.type) === 'loading') {
      applyInitialRoute();
    }
  });

  // Notifications Effect – initial fetch on login/view-change.
  // Badge updates in real-time via SSE (notification_created event in liveUpdates.ts).
  $effect(() => {
    if (!initialized || !$currentUser) return;

    // Re-fetch when switching views (covers first load and tab revisits)
    const viewType = $currentView.type;
    void viewType;

    untrack(() => fetchNotifications());
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

  // Background Color Effect
  $effect(() => {
    const theme = $currentUser?.theme || 'system';
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const isDark = theme === 'dark' || (theme === 'system' && mediaQuery.matches);

    const lightColor = $currentUser?.light_background_color;
    const darkColor = $currentUser?.dark_background_color;

    const bgColor = isDark ? darkColor : lightColor;

    const appContainer = document.querySelector('.app-container') as HTMLElement;
    if (appContainer) {
      if (bgColor && /^#[0-9a-fA-F]{6}$/.test(bgColor)) {
        appContainer.style.backgroundColor = bgColor;
      } else {
        appContainer.style.backgroundColor = '';
      }
    }
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

  // Keyboard shortcuts
  $effect(() => {
    if (!$currentUser) return;

    return setupKeyboardShortcuts({
      onOpenCalendar: () => currentView.set({ type: 'calendar' }),
      onOpenTodos: () => currentView.set({ type: 'todos' }),
      onOpenCollections: openCollections,
      onOpenHabits: () => currentView.set({ type: 'habits' }),
      onNewSnipsel: onNewSnipsel,
      onNewSnipselInCurrentCollection: () => newSnipselInCurrentCollectionRequest.update((n) => n + 1),
      onClearSelection: () => clearSelectionRequest.update((n) => n + 1),
      onDeleteSelection: () => deleteSelectionRequest.update((n) => n + 1),
      hasSelectedSnipsels: () => $snipselsSelected > 0,
      onMoveSelection: (direction) => moveSelectionRequest.set({ direction }),
      onIndentSelection: (direction) => indentSelectionRequest.set({ direction }),
      onAiAssistant: () => aiAssistantRequest.update((n) => n + 1),
      onToggleType: () => toggleTypeRequest.update((n) => n + 1),
      onToggleCardView: () => toggleCardViewRequest.update((n) => n + 1),
      onCopySnipsels: () => copySnipselsRequest.update((n) => n + 1),
      onMoveSnipsels: () => moveSnipselsRequest.update((n) => n + 1),
      onInfoSnipsels: () => infoSnipselsRequest.update((n) => n + 1),
      onUploadAttachment: () => uploadAttachmentRequest.update((n) => n + 1),
    });
  });
</script>

<div class="app-container min-h-screen bg-slate-50 text-slate-900 transition-colors duration-300 dark:bg-slate-950 dark:text-slate-100" class:is-editing={$editingSnipselId !== null}>
  {#if $currentUser}
    <NavigationHeader
      accent={getAccent()}
      navPlusColor={getNavPlusColor()}
      navPlusIconColor={getNavPlusIconColor()}
      isEditing={$editingSnipselId !== null}
      onOpenToday={openToday}
      onRunSearch={runSearch}
      onClearRecent={clearRecent}
    />
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
      {#key $currentView.id}
        <CollectionOutliner collectionId={$currentView.id} />
      {/key}
    {:else if $currentView.type === 'search'}
      <Search />
    {:else if $currentView.type === 'tags_mentions'}
      <TagsMentions />
    {:else if $currentView.type === 'habits'}
      <Habits />
    {:else if $currentView.type === 'habit_detail'}
      <HabitDetail habitId={$currentView.id} />
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
    {:else if $currentView.type === 'user_management'}
      <UserManagement />
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
      <BottomNavBar
        navPlusColor={getNavPlusColor()}
        navPlusIconColor={getNavPlusIconColor()}
        {plusPressState}
        {lpNewSnipsel}
        isEditing={$editingSnipselId !== null}
        onOpenCollections={openCollections}
      />
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

  {#if showIOSPasteHint}
    <div
      class="fixed inset-x-4 z-[997] rounded-xl bg-slate-900/95 px-4 py-3 text-sm text-white shadow-2xl backdrop-blur-md"
      style="bottom: calc(env(safe-area-inset-bottom) + 6.5rem);"
      in:fly={{ y: 20, duration: 200 }}
      out:fade={{ duration: 150 }}
    >
      📋 iOS blocks automatic paste. Long-press the text field and tap "Paste" to insert your clipboard content.
    </div>
  {/if}

  {#if needPwaRefresh}
    <div
      class="fixed bottom-24 left-4 right-4 z-[999] mx-auto max-w-md overflow-hidden rounded-2xl border border-indigo-200/80 bg-white/95 p-4 text-slate-900 shadow-2xl ring-1 ring-black/5 backdrop-blur-xl dark:border-indigo-500/30 dark:bg-slate-900/95 dark:text-slate-100"
      in:fly={{ y: 50, duration: 250 }}
      out:fade={{ duration: 150 }}
    >
      <div class="flex items-start gap-3">
        <div class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950/50 dark:text-indigo-400">
          <Sparkles label="" size={22} strokeWidth={2.5} />
        </div>
        <div class="min-w-0 flex-1">
          <h4 class="text-sm font-bold text-slate-900 dark:text-slate-100">
            Update available
          </h4>
          <p class="mt-0.5 text-xs text-slate-600 dark:text-slate-400">
            A new version of snipsel is ready. Reload to get the latest features and improvements.
          </p>
          <div class="mt-3 flex items-center gap-2">
            <button
              type="button"
              class="flex-1 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-500 active:scale-95 transition-all"
              onclick={reloadPwa}
            >
              Reload now
            </button>
            <button
              type="button"
              class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50 dark:border-white/10 dark:bg-slate-800 dark:text-slate-300"
              onclick={() => (needPwaRefresh = false)}
            >
              Later
            </button>
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>
