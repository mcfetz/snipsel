<script lang="ts">
  import Heart from '@animated-color-icons/lucide-svelte/Heart.svelte';
  import LayoutTemplate from '@animated-color-icons/lucide-svelte/LayoutTemplate.svelte';
  import Lock from '@animated-color-icons/lucide-svelte/Lock.svelte';
  import Unlock from '@animated-color-icons/lucide-svelte/Unlock.svelte';
  import Link from '@animated-color-icons/lucide-svelte/Link.svelte';
  import X from '@animated-color-icons/lucide-svelte/X.svelte';
  import Copy from '@animated-color-icons/lucide-svelte/Copy.svelte';
  import UnsplashSearchModal from '../lib/UnsplashSearchModal.svelte';
  import Check from '@animated-color-icons/lucide-svelte/Check.svelte';
  import Archive from '@animated-color-icons/lucide-svelte/Archive.svelte';
  import { api, type Collection, type CollectionShare, type UserLite, type CollectionBacklink } from '../lib/api';
  import { collectionAnchor, collections, currentCollection, currentView, isLoading } from '../lib/stores';
  import { currentUser } from '../lib/session';
  import DeleteConfirmModal from '../lib/DeleteConfirmModal.svelte';
  import InfoModal from '../lib/InfoModal.svelte';
  import ProgressModal from '../lib/ProgressModal.svelte';

  interface Props {
    collectionId: string;
  }

  let { collectionId }: Props = $props();

  let collection = $state<Collection | null>(null);
  let title = $state('');
  let icon = $state('');
  let headerImageUrl = $state('');
  let headerColor = $state('');
  let headerImagePosition = $state('50%');
  let headerImageXPosition = $state('50%');
  let headerImageZoom = $state(1.0);
  let isFavorite = $state(false);
  let defaultSnipselType = $state('');
  let showCompletedTasks = $state(true);
  let muteNotifications = $state(false);
  let excludeFromTodoList = $state(false);
  let saving = $state(false);
  let showDeleteModal = $state(false);
  let showBulkDeleteModal = $state(false);
  let showBulkResetModal = $state(false);
  let showUnsplashModal = $state(false);
  let errorModal = $state<{ title: string; message: string } | null>(null);
  let uploadProgress = $state<{ filename: string; percent: number } | null>(null);
  let showSavedFeedback = $state(false);

  let users = $state<UserLite[]>([]);
  let shares = $state<CollectionShare[]>([]);
  let shareUserId = $state('');
  let sharePermission = $state<'read' | 'write'>('read');
  let sharingBusy = $state(false);
  let backlinks = $state<CollectionBacklink[]>([]);

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
    if (headerColor && /^#[0-9a-fA-F]{6}$/.test(headerColor)) return headerColor;
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

  function isLightColor(color: string): boolean {
    const hex = color.replace('#', '');
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
    return brightness > 128;
  }

  function getContrastColor(bgColor: string): string {
    return isLightColor(bgColor) ? '#1e293b' : 'white';
  }

  async function load() {
    isLoading.set(true);
    try {
      const res = await api.collections.get(collectionId);
      collection = res.collection;
      title = collection.title;
      icon = collection.icon;
      headerImageUrl = collection.header_image_url ?? '';
      headerColor = collection.header_color ?? '';
      headerImagePosition = collection.header_image_position ?? '50%';
      headerImageXPosition = collection.header_image_x_position ?? '50%';
      headerImageZoom = collection.header_image_zoom ?? 1.0;
      isFavorite = Boolean(collection.is_favorite);
      defaultSnipselType = collection.default_snipsel_type ?? '';
      showCompletedTasks = collection.show_completed_tasks ?? true;
      muteNotifications = collection.mute_notifications ?? false;
      excludeFromTodoList = collection.exclude_from_todo_list ?? false;

      const [uRes, sRes, blRes] = await Promise.all([
        api.users.list(),
        api.collections.listShares(collectionId),
        api.collections.listBacklinks(collectionId),
      ]);
      users = uRes.users;
      shares = sRes.shares;
      backlinks = blRes.backlinks;
    } finally {
      isLoading.set(false);
    }
  }

  async function addShare() {
    if (!collection) return;
    if (!shareUserId) return;
    sharingBusy = true;
    try {
      await api.collections.createShare(collection.id, {
        shared_with_user_id: shareUserId,
        permission: sharePermission,
      });
      const sRes = await api.collections.listShares(collection.id);
      shares = sRes.shares;
      shareUserId = '';
      sharePermission = 'read';
    } finally {
      sharingBusy = false;
    }
  }

  async function revokeShare(shareId: string) {
    if (!collection) return;
    if (!confirm('Remove access?')) return;
    sharingBusy = true;
    try {
      await api.collections.deleteShare(collection.id, shareId);
      shares = shares.filter((s) => s.id !== shareId);
    } finally {
      sharingBusy = false;
    }
  }

  async function save() {
    if (!collection) return;
    saving = true;
    try {
      const res = await api.collections.update(collection.id, {
        title: title.trim(),
        icon: icon.trim(),
        header_image_url: headerImageUrl.trim() || null,
        header_color: headerColor.trim() || null,
        header_image_position: headerImagePosition,
        header_image_x_position: headerImageXPosition,
        header_image_zoom: headerImageZoom,
        is_template: Boolean(collection.is_template),
        is_passcode_protected: Boolean(collection.is_passcode_protected),
        default_snipsel_type: defaultSnipselType.trim() || null,
        show_completed_tasks: showCompletedTasks,
        mute_notifications: muteNotifications,
        exclude_from_todo_list: excludeFromTodoList,
      });
      collection = res.collection;
      collections.update((list) => list.map((c) => (c.id === res.collection.id ? res.collection : c)));
      currentCollection.update((c) => (c?.id === res.collection.id ? res.collection : c));
      
      showSavedFeedback = true;
      setTimeout(() => {
        showSavedFeedback = false;
      }, 2000);
    } finally {
      saving = false;
    }
  }

  async function onFileSelected(e: Event) {
    const target = e.target as HTMLInputElement;
    if (!target.files?.length || !collection) return;
    const file = target.files[0];

    const maxBytes = $currentUser?.max_upload_bytes ?? (10 * 1024 * 1024);
    if (file.size > maxBytes) {
      const formatSize = (b: number) => b < 1024 * 1024 ? Math.round(b / 1024) + ' KB' : Math.round(b / (1024 * 1024)) + ' MB';
      errorModal = {
        title: 'File too large',
        message: `The header image is too large (limit: ${formatSize(maxBytes)}).`
      };
      target.value = '';
      return;
    }

    saving = true;
    try {
      uploadProgress = { filename: file.name, percent: 0 };
      const res = await api.collections.uploadHeaderImage(collection.id, file, (p) => {
        if (uploadProgress) uploadProgress.percent = p;
      });
      collection = res.collection;
      headerImageUrl = collection.header_image_url ?? '';
      headerImagePosition = collection.header_image_position ?? '50%';
      // Update stores
      collections.update((list) => list.map((c) => (c.id === res.collection.id ? { ...c, ...res.collection } : c)));
      currentCollection.update((c) => (c?.id === res.collection.id ? { ...c, ...res.collection } : c));
    } catch (err: any) {
      console.error('Upload failed:', err);
      if (err.error?.code === 'payload_too_large') {
        errorModal = {
          title: 'File too large',
          message: err.error.message || 'The file exceeds the upload limit of 10 MB.'
        };
      } else {
        errorModal = {
          title: 'Upload failed',
          message: err.error?.message || 'An unexpected error occurred.'
        };
      }
    } finally {
      uploadProgress = null;
      saving = false;
    }
  }

  async function toggleArchive() {
    if (!collection) return;
    const res = await api.collections.update(collection.id, { archived: !collection.archived });
    collection = res.collection;
    collections.update((list) => list.map((c) => (c.id === res.collection.id ? res.collection : c)));
  }

  async function toggleFavorite() {
    if (!collection) return;
    const next = !isFavorite;
    isFavorite = next;
    if (next) {
      await api.collections.favorite(collection.id);
    } else {
      await api.collections.unfavorite(collection.id);
    }
    const refreshed = await api.collections.get(collection.id);
    collection = refreshed.collection;
    collections.update((list) => list.map((c) => (c.id === collection?.id ? collection : c)));
    currentCollection.update((c) => (c?.id === collection?.id ? collection : c));
  }

  async function toggleTemplate() {
    if (!collection) return;
    const next = !Boolean(collection.is_template);
    const res = await api.collections.update(collection.id, { is_template: next });
    collection = res.collection;
    collections.update((list) => list.map((c) => (c.id === res.collection.id ? res.collection : c)));
    currentCollection.update((c) => (c?.id === res.collection.id ? res.collection : c));
  }

  async function togglePasscodeProtection() {
    if (!collection) return;
    if (!$currentUser?.passcode_set) return;
    const next = !Boolean(collection.is_passcode_protected);
    const res = await api.collections.update(collection.id, { is_passcode_protected: next });
    collection = res.collection;
    collections.update((list) => list.map((c) => (c.id === res.collection.id ? res.collection : c)));
    currentCollection.update((c) => (c?.id === res.collection.id ? res.collection : c));
  }

  function deleteCollection() {
    if (!collection) return;
    showDeleteModal = true;
  }

  function cancelDeleteCollection() {
    showDeleteModal = false;
  }

  async function confirmDeleteCollection() {
    if (!collection) return;
    showDeleteModal = false;
    const id = collection.id;
    try {
      await api.collections.delete(id);
      collections.update((list) => list.filter((c) => c.id !== id));
      currentCollection.set(null);
      collectionAnchor.set(null);
      currentView.set({ type: 'collections' });
    } catch (e: any) {
      if (e.error?.code === 'has_backlinks') {
        alert('Cannot delete collection because it is referenced in other snipsels. Remove the links first.');
      } else {
        alert('Failed to delete collection: ' + (e.error?.message || 'Unknown error'));
      }
    }
  }

  async function deleteCompletedTasks() {
    if (!collection) return;
    showBulkDeleteModal = true;
  }

  async function confirmBulkDelete() {
    if (!collection) return;
    showBulkDeleteModal = false;
    saving = true;
    try {
      await api.collections.deleteCompletedTasks(collection.id);
    } catch (err: any) {
      alert('Failed to delete completed tasks: ' + (err.error?.message || 'Unknown error'));
    } finally {
      saving = false;
    }
  }

  async function resetCompletedTasks() {
    if (!collection) return;
    showBulkResetModal = true;
  }

  async function confirmBulkReset() {
    if (!collection) return;
    showBulkResetModal = false;
    saving = true;
    try {
      await api.collections.resetCompletedTasks(collection.id);
    } catch (err: any) {
      alert('Failed to reset completed tasks: ' + (err.error?.message || 'Unknown error'));
    } finally {
      saving = false;
    }
  }

  function goBack() {
    currentView.set({ type: 'collection', id: collectionId });
  }
  function openBacklink(bl: CollectionBacklink) {
    collectionAnchor.set({ collectionId: bl.collection_id, snipselId: bl.snipsel_id, pos: bl.position });
    currentView.set({ type: 'collection', id: bl.collection_id });
  }

  load();
</script>

<div class="space-y-4">
  <div class="flex items-center justify-between gap-3">
    <button
      class="rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-sm font-medium text-slate-700 shadow-sm ring-1 ring-black/5 backdrop-blur-md hover:bg-white dark:border-white/10 dark:bg-slate-900/80 dark:text-slate-300 dark:ring-white/10 dark:hover:bg-slate-900"
      type="button"
      onclick={goBack}
      aria-label="Back"
      title="Back"
    >
      Back
    </button>

    <div
      class="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-sm font-medium shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10"
      style={`background-color: ${getAccentTint()}; color: ${getAccent()}`}
    >
      <span class="text-xs uppercase tracking-wide">Collection</span>
      <span class="opacity-70">·</span>
      <span class="font-semibold text-slate-800 dark:text-slate-200">Settings</span>
    </div>
  </div>

  {#if !collection}
    <div class="text-sm text-slate-500">Loading...</div>
  {:else}
    <div class="space-y-3">
      <!-- General Info -->
      <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
        <div class="flex items-center justify-between gap-2">
          <div class="text-xs font-medium uppercase text-slate-500">General</div>
          <div class="flex items-center gap-1 rounded-full border border-slate-200 bg-white/80 p-1 shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-800/80">
            <button
              class="al-icon-wrapper grid h-9 w-9 place-items-center rounded-full text-slate-700 hover:bg-black/5 dark:text-slate-300 dark:hover:bg-white/5"
              type="button"
              aria-label={isFavorite ? 'Unfavorite' : 'Favorite'}
              title={isFavorite ? 'Unfavorite' : 'Favorite'}
              onclick={toggleFavorite}
              style={isFavorite ? `color: ${getAccent()}` : undefined}
            >
              <Heart label="" size={16} className={isFavorite ? "fill-current" : ""} strokeWidth={isFavorite ? 0 : 1.6} />
            </button>
            <button
              class="al-icon-wrapper grid h-9 w-9 place-items-center rounded-full text-slate-700 hover:bg-black/5 dark:text-slate-300 dark:hover:bg-white/5"
              type="button"
              aria-label={collection?.archived ? 'Unarchive' : 'Archive'}
              title={collection?.archived ? 'Archived' : 'Archive'}
              onclick={toggleArchive}
              style={collection?.archived ? `color: ${getAccent()}` : undefined}
            >
              <Archive label="" size={16} />
            </button>
            <button
              class="al-icon-wrapper grid h-9 w-9 place-items-center rounded-full text-slate-700 hover:bg-black/5 dark:text-slate-300 dark:hover:bg-white/5"
              type="button"
              aria-label={collection?.is_template ? 'Unset template' : 'Mark as template'}
              title={collection?.is_template ? 'Template' : 'Not a template'}
              onclick={toggleTemplate}
              style={collection?.is_template ? `color: ${getAccent()}` : undefined}
            >
              <LayoutTemplate label="" size={16} />
            </button>
            <button
              class="al-icon-wrapper grid h-9 w-9 place-items-center rounded-full text-slate-700 hover:bg-black/5 disabled:opacity-30 disabled:cursor-not-allowed transition-colors dark:text-slate-300 dark:hover:bg-white/5"
              type="button"
              aria-label={collection?.is_passcode_protected ? 'Remove passcode protection' : 'Enable passcode protection'}
              title={$currentUser?.passcode_set ? (collection?.is_passcode_protected ? 'Protected — click to remove' : 'Protect with passcode') : 'Set a passcode in Settings first'}
              onclick={togglePasscodeProtection}
              disabled={!$currentUser?.passcode_set}
              style={collection?.is_passcode_protected ? `color: ${getAccent()}` : ''}
            >
              {#if collection?.is_passcode_protected}
                <Lock label="" size={16} />
              {:else}
                <Unlock label="" size={16} />
              {/if}
            </button>
          </div>
        </div>

        <div class="mt-4 space-y-4">
          <div class="flex gap-3">
            <label class="block">
              <span class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">Icon</span>
              <input class="w-20 rounded-lg border border-slate-200 bg-white px-3 py-2 text-center text-xl shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-slate-100 dark:ring-white/10" bind:value={icon} />
            </label>

            <label class="block flex-1">
              <span class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">Title</span>
              <input class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-slate-100 dark:ring-white/10" bind:value={title} />
            </label>
          </div>

          <div class="block">
            <span class="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300">Default snipsel type</span>
            <div class="overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-900 dark:ring-white/10">
              <div class="grid grid-cols-4">
                <button
                  class="px-2 py-2.5 text-xs font-medium transition-colors {defaultSnipselType === '' || defaultSnipselType === 'text' ? '' : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
                  type="button"
                  onclick={() => (defaultSnipselType = '')}
                  style={defaultSnipselType === '' || defaultSnipselType === 'text' ? `background-color: ${getAccent()}; color: ${getContrastColor(getAccent())}` : undefined}
                >
                  Note
                </button>
                <button
                  class="border-l border-black/5 dark:border-white/5 px-2 py-2.5 text-xs font-medium transition-colors {defaultSnipselType === 'image' ? '' : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
                  type="button"
                  onclick={() => (defaultSnipselType = 'image')}
                  style={defaultSnipselType === 'image' ? `background-color: ${getAccent()}; color: ${getContrastColor(getAccent())}` : undefined}
                >
                  Image
                </button>
                <button
                  class="border-l border-black/5 dark:border-white/5 px-2 py-2.5 text-xs font-medium transition-colors {defaultSnipselType === 'attachment' ? '' : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
                  type="button"
                  onclick={() => (defaultSnipselType = 'attachment')}
                  style={defaultSnipselType === 'attachment' ? `background-color: ${getAccent()}; color: ${getContrastColor(getAccent())}` : undefined}
                >
                  File
                </button>
                <button
                  class="border-l border-black/5 dark:border-white/5 px-2 py-2.5 text-xs font-medium transition-colors {defaultSnipselType === 'task' ? '' : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
                  type="button"
                  onclick={() => (defaultSnipselType = 'task')}
                  style={defaultSnipselType === 'task' ? `background-color: ${getAccent()}; color: ${getContrastColor(getAccent())}` : undefined}
                >
                  Task
                </button>
              </div>
            </div>
          </div>
          
          <label class="flex items-center gap-3 cursor-pointer group">
            <div class="relative inline-flex h-6 w-11 items-center">
              <input type="checkbox" class="peer sr-only" bind:checked={muteNotifications} />
              <div 
                class="h-6 w-11 rounded-full bg-slate-200 transition-colors dark:bg-slate-700"
                style={muteNotifications ? `background-color: ${getAccent()}` : undefined}
              ></div>
              <div class="absolute left-1 h-4 w-4 rounded-full bg-white transition-transform peer-checked:translate-x-5"></div>
            </div>
            <div class="flex flex-col">
              <span class="text-sm font-medium text-slate-700 dark:text-slate-300 group-hover:text-slate-900 dark:group-hover:text-slate-100">Mute Notifications</span>
              <span class="text-xs text-slate-500 dark:text-slate-400">Disable notifications for mentions, assignments and finished tasks in this collection</span>
            </div>
          </label>
        </div>
      </div>

      <!-- Appearance -->
      <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
        <div class="text-xs font-medium uppercase text-slate-500">Appearance</div>
        <div class="mt-4 space-y-4">
          <label class="block">
            <span class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">Header image</span>
            <div class="space-y-3">
              <div class="flex items-center gap-3">
                <input
                  class="flex-1 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-slate-100 dark:ring-white/10"
                  bind:value={headerImageUrl}
                  placeholder="https://..."
                />
                <label
                  class="cursor-pointer rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50 dark:border-white/10 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
                >
                  Upload
                  <input type="file" accept="image/*" class="hidden" onchange={onFileSelected} disabled={saving} />
                </label>
                <button
                  class="rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50 dark:border-white/10 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
                  type="button"
                  onclick={() => (showUnsplashModal = true)}
                  disabled={saving}
                >
                  Unsplash
                </button>
              </div>

              {#if headerImageUrl}
                <div class="space-y-2">
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-medium text-slate-500">Vertical position</span>
                    <span class="text-xs font-mono text-slate-400">{headerImagePosition}</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="1"
                    class="h-1.5 w-full cursor-pointer appearance-none rounded-lg bg-slate-200 dark:bg-slate-700"
                    value={parseInt(headerImagePosition) || 50}
                    oninput={(e) => (headerImagePosition = `${e.currentTarget.value}%`)}
                    style={`--accent: ${getAccent()}`}
                  />
                  
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-medium text-slate-500">Horizontal position</span>
                    <span class="text-xs font-mono text-slate-400">{headerImageXPosition}</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="1"
                    class="h-1.5 w-full cursor-pointer appearance-none rounded-lg bg-slate-200 dark:bg-slate-700"
                    value={parseInt(headerImageXPosition) || 50}
                    oninput={(e) => (headerImageXPosition = `${e.currentTarget.value}%`)}
                    style={`--accent: ${getAccent()}`}
                  />
                  
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-medium text-slate-500">Zoom</span>
                    <span class="text-xs font-mono text-slate-400">{headerImageZoom.toFixed(2)}x</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="3"
                    step="0.05"
                    class="h-1.5 w-full cursor-pointer appearance-none rounded-lg bg-slate-200 dark:bg-slate-700"
                    value={headerImageZoom}
                    oninput={(e) => (headerImageZoom = parseFloat(e.currentTarget.value))}
                    style={`--accent: ${getAccent()}`}
                  />
                  
                  <!-- Preview -->
                  <div class="h-28 w-full overflow-hidden rounded-lg border border-slate-200 bg-slate-100 dark:border-white/10 dark:bg-slate-800 relative">
                    <div 
                      class="absolute inset-0 bg-cover"
                      style="background-image: url('{headerImageUrl}{ headerImageUrl.startsWith('/api/attachments/') ? '/thumbnail' : '' }'); background-position: {headerImageXPosition} {headerImagePosition}; transform: scale({headerImageZoom}) translate({(50 - (parseFloat(headerImageXPosition) || 50)) * (1 - 1 / headerImageZoom)}%, {(50 - (parseFloat(headerImagePosition) || 50)) * (1 - 1 / headerImageZoom)}%)"
                    ></div>
                  </div>
                </div>
              {/if}
            </div>
          </label>

          <label class="block">
            <span class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">Header color</span>
            <div class="flex items-center gap-3">
              <div class="flex flex-1 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:ring-white/10">
                <input class="h-8 w-8 cursor-pointer overflow-hidden rounded border-none bg-transparent" type="color" bind:value={headerColor} />
                <input class="min-w-0 flex-1 border-none bg-transparent text-sm font-mono text-slate-700 dark:text-slate-100 focus:outline-none focus:ring-0" bind:value={headerColor} placeholder="#4f46e5" />
              </div>
              {#if headerColor}
                <button
                  class="rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50 dark:border-white/10 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
                  type="button"
                  onclick={() => (headerColor = '')}
                >
                  Clear
                </button>
              {/if}
            </div>
          </label>
        </div>
      </div>

      <!-- Tasks -->
      <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
        <div class="text-xs font-medium uppercase text-slate-500">Tasks</div>
        <div class="mt-4 space-y-4">
          <label class="flex items-center gap-3 cursor-pointer group">
            <div class="relative inline-flex h-6 w-11 items-center">
              <input type="checkbox" class="peer sr-only" bind:checked={showCompletedTasks} />
              <div 
                class="h-6 w-11 rounded-full bg-slate-200 transition-colors dark:bg-slate-700"
                style={showCompletedTasks ? `background-color: ${getAccent()}` : undefined}
              ></div>
              <div class="absolute left-1 h-4 w-4 rounded-full bg-white transition-transform peer-checked:translate-x-5"></div>
            </div>
            <span class="text-sm font-medium text-slate-600 dark:text-slate-400 group-hover:text-slate-900 dark:group-hover:text-slate-200">Show completed tasks by default</span>
          </label>
          
          <label class="flex items-center gap-3 cursor-pointer group">
            <div class="relative inline-flex h-6 w-11 items-center">
              <input type="checkbox" class="peer sr-only" bind:checked={excludeFromTodoList} />
              <div 
                class="h-6 w-11 rounded-full bg-slate-200 transition-colors dark:bg-slate-700"
                style={excludeFromTodoList ? `background-color: ${getAccent()}` : undefined}
              ></div>
              <div class="absolute left-1 h-4 w-4 rounded-full bg-white transition-transform peer-checked:translate-x-5"></div>
            </div>
            <div class="flex flex-col">
              <span class="text-sm font-medium text-slate-700 dark:text-slate-300 group-hover:text-slate-900 dark:group-hover:text-slate-100">Exclude from Todo list</span>
              <span class="text-xs text-slate-500 dark:text-slate-400">Hide open tasks from this collection in the global Todo view</span>
            </div>
          </label>

          <div class="flex flex-wrap gap-2">
            <button
              class="rounded-lg bg-red-600/90 px-3 py-1.5 text-xs font-medium text-white shadow-sm transition-colors hover:bg-red-600 dark:bg-red-700 dark:hover:bg-red-600"
              type="button"
              onclick={deleteCompletedTasks}
              disabled={saving}
            >
              Delete completed tasks
            </button>
            <button
              class="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 shadow-sm hover:bg-slate-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
              type="button"
              onclick={resetCompletedTasks}
              disabled={saving}
            >
              Reset completed tasks
            </button>
          </div>
        </div>
      </div>

      <!-- Sharing -->
      <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
        <div class="text-xs font-medium uppercase text-slate-500">Sharing</div>
        
        <div class="mt-4 space-y-3">
          <div class="flex flex-col gap-2">
            <select class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-slate-100 dark:ring-white/10" bind:value={shareUserId} disabled={sharingBusy}>
              <option value="">Select user…</option>
              {#each users as u (u.id)}
                <option value={u.id}>{u.username}</option>
              {/each}
            </select>
            <div class="flex gap-2">
              <div class="flex flex-1 overflow-hidden rounded-full border border-slate-200 bg-white p-1 shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-900 dark:ring-white/10">
                <button
                  class="flex-1 rounded-full py-1.5 text-xs font-medium transition-all {sharePermission === 'read' ? '' : 'text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-white/5'}"
                  type="button"
                  onclick={() => (sharePermission = 'read')}
                  disabled={sharingBusy}
                  style={sharePermission === 'read' ? `background-color: ${getAccent()}; color: ${getContrastColor(getAccent())}` : undefined}
                >
                  Read
                </button>
                <button
                  class="flex-1 rounded-full py-1.5 text-xs font-medium transition-all {sharePermission === 'write' ? '' : 'text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-white/5'}"
                  type="button"
                  onclick={() => (sharePermission = 'write')}
                  disabled={sharingBusy}
                  style={sharePermission === 'write' ? `background-color: ${getAccent()}; color: ${getContrastColor(getAccent())}` : undefined}
                >
                  Write
                </button>
              </div>
              <button
                class="rounded-full border border-slate-200 bg-white px-6 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
                style={`color: ${getAccent()}`}
                type="button"
                onclick={addShare}
                disabled={sharingBusy || !shareUserId}
              >
                Add
              </button>
            </div>
          </div>

          {#if shares.length > 0}
            <div class="space-y-2 pt-2">
              {#each shares as s (s.id)}
                <div class="flex items-center justify-between gap-3 rounded-lg border border-slate-100 bg-white/50 px-3 py-2 dark:border-white/10 dark:bg-white/5">
                  <div class="min-w-0">
                    <div class="truncate text-sm font-medium text-slate-900 dark:text-slate-100">
                      {#if s.shared_with_user_id === 'public'}
                        <span class="inline-flex items-center gap-1.5 text-indigo-600 dark:text-indigo-400">
                          <Link label="" size={16} />
                          Public Link
                        </span>
                      {:else}
                        {s.shared_with_username ?? s.shared_with_user_id}
                      {/if}
                    </div>
                    <div class="text-xs text-slate-500 uppercase tracking-wider font-semibold dark:text-slate-400">{s.permission}</div>
                  </div>
                  <button
                    class="al-icon-wrapper grid h-8 w-8 place-items-center rounded-full text-slate-400 hover:bg-red-50 hover:text-red-600 transition-colors dark:hover:bg-red-900/20"
                    type="button"
                    aria-label="Remove share"
                    title="Remove"
                    onclick={() => revokeShare(s.id)}
                    disabled={sharingBusy}
                  >
                    <X label="" size={16} />
                  </button>
                </div>
                {#if s.shared_with_user_id === 'public' && collection.public_token}
                  <div class="mt-2 rounded-lg bg-indigo-50 p-3 dark:bg-indigo-950/30">
                    <div class="text-xs font-semibold text-indigo-700 dark:text-indigo-300 uppercase tracking-wider mb-1">Secret Link</div>
                    <div class="flex items-center gap-2">
                      <input 
                        readonly 
                        class="flex-1 bg-transparent text-xs font-mono text-indigo-900 dark:text-indigo-100 border-none p-0 focus:ring-0" 
                        value={`${window.location.origin}/?v=public&token=${collection.public_token}`}
                      />
                      <button 
                        class="al-icon-wrapper text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-300"
                        onclick={() => {
                          navigator.clipboard.writeText(`${window.location.origin}/?v=public&token=${collection!.public_token}`);
                        }}
                        title="Copy link"
                      >
                        <Copy label="" size={16} />
                      </button>
                    </div>
                  </div>
                {/if}
              {/each}
            </div>
          {/if}
        </div>
      </div>

      <!-- Backlinks -->
      {#if backlinks.length > 0}
        <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
          <div class="text-xs font-medium uppercase text-slate-500">Linked in</div>
          <div class="mt-4 space-y-2">
            {#each backlinks as bl (bl.snipsel_id + bl.collection_id)}
              <button
                class="flex w-full items-start gap-3 rounded-lg border border-slate-100 bg-white/50 p-3 text-left transition-all hover:bg-white hover:shadow-sm dark:border-white/10 dark:bg-white/5 dark:hover:bg-white/10"
                type="button"
                onclick={() => openBacklink(bl)}
              >
                <span class="text-xl shrink-0 leading-none">{bl.collection_icon}</span>
                <div class="min-w-0 flex-1">
                  <div class="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">{bl.collection_title}</div>
                  <div class="truncate text-xs text-slate-500 dark:text-slate-400 mt-0.5">{bl.snipsel_content}</div>
                </div>
              </button>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Actions -->
      <div class="flex flex-col gap-2 pt-4">
        <button 
          class="w-full relative overflow-hidden rounded-full border border-slate-200 bg-white px-4 py-3 text-base font-semibold shadow-sm ring-1 ring-black/5 transition-all hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-900 dark:ring-white/10 dark:hover:bg-slate-800 flex items-center justify-center gap-2" 
          style={`color: ${getAccent()}`}
          type="button" 
          onclick={save} 
          disabled={saving || showSavedFeedback}
        >
          {#if saving}
            <span class="animate-pulse">Saving...</span>
          {:else if showSavedFeedback}
            <div class="flex items-center gap-2 animate-in fade-in zoom-in duration-300">
              <Check size={20} strokeWidth={2.5} />
              <span>Saved!</span>
            </div>
          {:else}
            <span class="animate-in fade-in duration-200">Save changes</span>
          {/if}
        </button>
        
        <button 
          class="w-full rounded-xl bg-red-600/90 px-4 py-3 text-base font-semibold text-white shadow-sm transition-all hover:bg-red-600 dark:bg-red-700 dark:hover:bg-red-600" 
          type="button" 
          onclick={deleteCollection}
        >
          Delete collection
        </button>
      </div>
    </div>
  {/if}
</div>

{#if showDeleteModal}
  <DeleteConfirmModal
    title="Delete collection?"
    message={`Are you sure you want to permanently delete the collection "${title}"? This cannot be undone.`}
    onConfirm={confirmDeleteCollection}
    onCancel={cancelDeleteCollection}
  />
{/if}

{#if showBulkDeleteModal}
  <DeleteConfirmModal
    title="Delete completed tasks?"
    message="Are you sure you want to delete all completed tasks from this collection? This cannot be undone."
    onConfirm={confirmBulkDelete}
    onCancel={() => (showBulkDeleteModal = false)}
  />
{/if}

{#if showBulkResetModal}
  <DeleteConfirmModal
    title="Reset completed tasks?"
    message="Are you sure you want to reset all completed tasks in this collection to incomplete?"
    confirmLabel="Reset"
    onConfirm={confirmBulkReset}
    onCancel={() => (showBulkResetModal = false)}
  />
{/if}

{#if uploadProgress}
  <ProgressModal
    filename={uploadProgress.filename}
    percent={uploadProgress.percent}
  />
{/if}

{#if errorModal}
  <InfoModal
    title={errorModal.title}
    message={errorModal.message}
    onClose={() => (errorModal = null)}
  />
{/if}

{#if showUnsplashModal}
  <UnsplashSearchModal
    initialQuery={title}
    accentColor={getAccent()}
    onSelect={(url) => { headerImageUrl = url; save(); }}
    onClose={() => (showUnsplashModal = false)}
  />
{/if}

