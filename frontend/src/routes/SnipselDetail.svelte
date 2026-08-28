<script lang="ts">
  import Download from '@animated-color-icons/lucide-svelte/Download.svelte';
  import Trash2 from '@animated-color-icons/lucide-svelte/Trash2.svelte';
  import Heart from '@animated-color-icons/lucide-svelte/Heart.svelte';
  import Info from '@animated-color-icons/lucide-svelte/Info.svelte';
  import Dices from '@animated-color-icons/lucide-svelte/Dices.svelte';
  import Ban from '@animated-color-icons/lucide-svelte/Ban.svelte';
  import CirclePlay from '@animated-color-icons/lucide-svelte/CirclePlay.svelte';
  import { api, type Attachment, type Snipsel, type SnipselDetailResponse } from '../lib/api';
  import ImageModal from '../lib/ImageModal.svelte';
  import { collectionAnchor, currentView, isLoading, searchError, searchQuery, searchResults, currentCollection } from '../lib/stores';
  import { currentUser } from '../lib/session';
  import { getCurrentUrl } from '../lib/router';
  import DeezerCard from '../lib/DeezerCard.svelte';
  import SpotifyCard from '../lib/SpotifyCard.svelte';
  import YouTubeCard from '../lib/YouTubeCard.svelte';
  import VideoModal from '../lib/VideoModal.svelte';
  import RRuleBuilder from '../lib/RRuleBuilder.svelte';
  import {
    computeHeaderColor,
    computeCardTileBg,
    computeToolboxBg,
    isLightColor,
    getContrastColor,
  } from '../lib/colors';
  import {
    getDeezerLink,
    getSpotifyLink,
    getYouTubeLink,
    stripMediaLinks,
  } from '../lib/embeds';

  interface Props {
    snipselId: string;
  }

  let { snipselId }: Props = $props();

  let snipsel = $state<Snipsel | null>(null);
  let placements = $state<Array<{
    collection_id: string;
    collection_title?: string;
    collection_icon?: string;
    position: number;
    indent: number;
  }>>([]);
	let loading = $state(true);
  let changingType = $state(false);
  let changingCardView = $state(false);
  let saveStatus = $state<'success' | 'error' | null>(null);
  let showSavedFeedback = $state(false);

  let copied = $state(false);
  let reminderAt = $state<string | null>(null);
  let reminderRRule = $state<string | null>(null);
  let updatingReminders = $state(false);

  function toLocalDatetimeString(iso: string | null): string | null {
    if (!iso) return null;
    const d = new Date(iso);
    if (isNaN(d.getTime())) return null;
    const offset = d.getTimezoneOffset() * 60000;
    const local = new Date(d.getTime() - offset);
    return local.toISOString().slice(0, 16);
  }

  function getAccent(): string {
    return computeHeaderColor($currentUser?.default_collection_header_color);
  }

  function getHeaderColor(): string {
    return computeHeaderColor($currentCollection?.header_color, $currentUser?.default_collection_header_color);
  }

  function getAccentTint(): string {
    const isDark = typeof document !== 'undefined' && document.documentElement.classList.contains('dark');
    return computeCardTileBg(getAccent(), isDark);
  }

  let modalImages = $state<Array<{ id: string; filename: string }>>([]);
  let modalImageIndex = $state<number>(-1);
  let modalVideo = $state<{ id: string; filename: string } | null>(null);

  function openImageModal(images: Array<{ id: string; filename: string }>, index: number) {
    modalImages = images;
    modalImageIndex = index;
  }

  function closeImageModal() {
    modalImages = [];
    modalImageIndex = -1;
  }

  function openVideoModal(id: string, filename: string) {
    modalVideo = { id, filename };
  }

  function closeVideoModal() {
    modalVideo = null;
  }

	let hasWriteAccess = $state(true);

	async function load() {
		loading = true;
		try {
			const res = (await fetch(`/api/snipsels/${snipselId}`, { credentials: 'include' }).then((r) => r.json())) as SnipselDetailResponse;
			snipsel = res.snipsel;
			snipsel = { ...res.snipsel, tags: res.tags ?? [], mentions: res.mentions ?? [] };
			hasWriteAccess = res.has_write_access !== false;
			reminderAt = toLocalDatetimeString(res.snipsel.reminder_at || null);
			reminderRRule = res.snipsel.reminder_rrule ?? null;
			const nextPlacements = res.placements ?? [];
			placements = nextPlacements;
			void loadPlacementFavorites(nextPlacements);
		// backlinks currently unused in UI
	} finally {
		loading = false;
	}
	}

	async function setType(nextType: 'text' | 'image' | 'attachment' | 'task') {
		if (!hasWriteAccess) return;
		if (!snipsel) return;
		if (snipsel.type === nextType) return;
		changingType = true;
		try {
			await api.snipsels.update(snipselId, { type: nextType });
			saveStatus = 'success';
			setTimeout(() => { if (saveStatus === 'success') saveStatus = null; }, 5000);
			await load();
		} catch (err) {
			console.error('Failed to update type:', err);
			saveStatus = 'error';
			setTimeout(() => { if (saveStatus === 'error') saveStatus = null; }, 5000);
		} finally {
			changingType = false;
		}
	}

  async function toggleCardView() {
    if (!hasWriteAccess) return;
    if (!snipsel) return;
    changingCardView = true;
    try {
      await api.snipsels.update(snipselId, { card_view: !snipsel.card_view });
      saveStatus = 'success';
      setTimeout(() => { if (saveStatus === 'success') saveStatus = null; }, 5000);
      await load();
    } catch (err) {
      console.error('Failed to update card_view:', err);
      saveStatus = 'error';
      setTimeout(() => { if (saveStatus === 'error') saveStatus = null; }, 5000);
    } finally {
      changingCardView = false;
    }
  }
  
	async function updateReminders() {
		if (!hasWriteAccess) return;
		updatingReminders = true;
		try {
			const nextAt = reminderAt ? new Date(reminderAt).toISOString() : null;
			await api.snipsels.update(snipselId, {
				reminder_at: nextAt,
				reminder_rrule: reminderRRule
			});
			showSavedFeedback = true;
			setTimeout(() => { showSavedFeedback = false; }, 2000);
			await load();
		} catch (err) {
			console.error('Failed to update reminders:', err);
		} finally {
			updatingReminders = false;
		}
	}

  function isImageAttachment(a: Attachment): boolean {
    return Boolean(a.mime_type?.startsWith('image/') || (a.has_thumbnail && !a.mime_type?.startsWith('video/')));
  }

  function isVideoAttachment(a: Attachment): boolean {
    return Boolean(a.mime_type?.startsWith('video/') || (a.has_thumbnail && a.filename.toLowerCase().match(/\.(mp4|mov|webm|avi|mkv)$/)));
  }

  function isMediaAttachment(a: Attachment): boolean {
    return isImageAttachment(a) || isVideoAttachment(a);
  }

  function formatWhen(iso: string | null): string {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleString();
  }

  function hasGeo(s: Snipsel): boolean {
    return typeof s.geo_lat === 'number' && typeof s.geo_lng === 'number';
  }

  function osmEmbedUrl(lat: number, lng: number): string {
    const delta = 0.005;
    const bbox = `${lng - delta},${lat - delta},${lng + delta},${lat + delta}`;
    const marker = `${lat},${lng}`;
    return `https://www.openstreetmap.org/export/embed.html?bbox=${encodeURIComponent(bbox)}&layer=mapnik&marker=${encodeURIComponent(marker)}`;
  }

  function highlightTokens(text: string | null): string {
    if (!text) return '';
    const escaped = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    const raw = ($currentUser?.default_collection_header_color || '').trim() || '#4f46e5';
    const accent = /^#[0-9a-fA-F]{6}$/.test(raw) ? raw : '#4f46e5';
    
    const isDark = typeof document !== 'undefined' && document.documentElement.classList.contains('dark');
    // tinted background like the toolbox for readability
    const tokenBg = isDark ? `rgba(30, 41, 59, 0.8)` : `rgba(255, 255, 255, 0.96)`;

    return escaped.replace(
      /(^|[^\p{L}\p{N}_])(#[A-Za-z\p{L}][\p{L}\p{N}_-]*|@[A-Za-z\p{L}][\p{L}\p{N}_-]*)/gu,
      (m, p1, token) => {
        const isTag = token.startsWith('#');
        const value = token.slice(1);
        const attr = isTag ? `data-tag="${value}"` : `data-mention="${value}"`;
        return `${p1}<mark class="snip-token cursor-pointer" ${attr} style="background-color:${tokenBg}; color:${accent}">${token}</mark>`;
      }
    );
  }

	let favoriteByCollectionId = $state<Record<string, boolean>>({});

	async function loadPlacementFavorites(nextPlacements: Array<{ collection_id: string }>) {
		const ids = Array.from(new Set(nextPlacements.map((p) => p.collection_id)));
		if (ids.length === 0) return;

		const missing = ids.filter((id) => !(id in favoriteByCollectionId));
		if (missing.length === 0) return;

		try {
			const res = await api.collections.list(true);
			const wanted = new Set(missing);
			const next: Record<string, boolean> = {};
			for (const c of res.collections) {
				if (wanted.has(c.id)) next[c.id] = Boolean(c.is_favorite);
			}
			favoriteByCollectionId = { ...favoriteByCollectionId, ...next };
		} catch {
			// best-effort
		}
	}

	async function toggleCollectionFavorite(collectionId: string) {
		const current = Boolean(favoriteByCollectionId[collectionId]);
		const next = !current;
		favoriteByCollectionId = { ...favoriteByCollectionId, [collectionId]: next };
		try {
			if (next) {
				await api.collections.favorite(collectionId);
			} else {
				await api.collections.unfavorite(collectionId);
			}
		} catch {
			favoriteByCollectionId = { ...favoriteByCollectionId, [collectionId]: current };
		}
	}

	function openCollectionInfo(collectionId: string) {
		currentView.set({ type: 'collection_settings', id: collectionId });
	}

	async function deleteAttachment(attachmentId: string) {
		if (!hasWriteAccess) return;
		if (!confirm('Delete attachment?')) return;
		await api.attachments.delete(attachmentId);
		await load();
	}

  async function toggleDicedBan() {
    if (!snipsel || !hasWriteAccess) return;
    try {
      const newCount = snipsel.diced_count === -1 ? 0 : -1;
      await api.snipsels.update(snipselId, { diced_count: newCount });
      await load();
    } catch (err) {
      console.error('Failed to toggle diced ban:', err);
    }
  }

  load();

	function directLinkUrl(): string {
		const u = new URL(window.location.href);
		u.searchParams.set('v', 'snipsel');
		u.searchParams.set('id', snipselId);
		// drop unrelated params
		u.searchParams.delete('sn');
		u.searchParams.delete('pos');
		u.searchParams.delete('q');
		u.searchParams.delete('returnTo');
		return u.toString();
	}

  async function copyDirectLink() {
    const text = directLinkUrl();
    try {
      await navigator.clipboard.writeText(text);
      copied = true;
      setTimeout(() => {
        copied = false;
      }, 1200);
    } catch {
      // fallback
      const el = document.getElementById('snipsel-direct-link') as HTMLInputElement | null;
      if (el) {
        el.focus();
        el.select();
      }
    }
  }

	function goBack() {
		const returnTo = ($currentView.type === 'snipsel' ? ($currentView as { returnTo?: string }).returnTo : undefined) ?? '';
		if (returnTo) {
			history.replaceState(null, '', returnTo);
			window.dispatchEvent(new PopStateEvent('popstate'));
			return;
		}

    // If we have browser history (e.g. came from search/collection), go back.
    // Otherwise fallback to collections.
    if (history.length > 1) {
      history.back();
      return;
    }

    // Ensure URL is in a sensible state even if history is not usable
    // (e.g. opened in a new tab).
    if (getCurrentUrl().includes('v=snipsel')) {
      currentView.set({ type: 'collections' });
      return;
    }

    currentView.set({ type: 'collections' });
  }
</script>

<div class="space-y-4">
  <div class="flex items-center justify-between gap-3">
    <button
      class="rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-sm font-medium text-slate-700 shadow-sm ring-1 ring-black/5 backdrop-blur-md hover:bg-white dark:border-white/10 dark:bg-slate-900/80 dark:text-slate-300 dark:hover:bg-slate-900"
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
      <span class="text-xs uppercase tracking-wide">Snipsel</span>
      <span class="opacity-70">·</span>
      <span class="font-semibold text-slate-800 dark:text-slate-200">Settings</span>
    </div>
  </div>

  {#if loading}
    <div class="text-sm text-slate-500">Loading...</div>
  {:else if !snipsel}
    <div class="text-sm text-slate-500">Not found</div>
  {:else}
    <div class="space-y-3">

			
			<div class="rounded-xl border border-slate-200 bg-white/80 p-3 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80">
				<div class="flex items-center justify-between gap-2">
					<div class="text-xs uppercase text-slate-500 dark:text-slate-400">Type</div>
          {#if changingType}
            <div class="text-xs text-slate-500">Updating...</div>
          {/if}
        </div>
        <div class="mt-2 overflow-hidden rounded-full border border-slate-200 bg-white dark:border-white/10 dark:bg-slate-900">
          <div class="grid grid-cols-2">
          <button
            class="px-4 py-3 text-sm font-medium transition-colors {snipsel.type === 'text' ? '' : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
            type="button"
            onclick={() => setType('text')}
            disabled={changingType}
            style={snipsel.type === 'text' ? `background-color: ${getAccent()}; color: ${getContrastColor(getAccent())}` : undefined}
          >
            Note
          </button>
          <button
            class="border-l border-black/5 px-4 py-3 text-sm font-medium transition-colors dark:border-white/5 {snipsel.type === 'task'
              ? ''
              : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
            type="button"
            onclick={() => setType('task')}
            disabled={changingType}
            style={snipsel.type === 'task' ? `background-color: ${getAccent()}; color: ${getContrastColor(getAccent())}` : undefined}
          >
            Task
          </button>
				</div>
</div>
          <div class="mt-3 flex items-center justify-between">
            <span class="text-sm text-slate-600 dark:text-slate-400">Use card view</span>
            <button
              type="button"
              class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 {snipsel?.card_view !== false ? '' : 'bg-slate-200 dark:bg-slate-700'}"
              style={snipsel?.card_view !== false ? `background-color: ${getHeaderColor()}; --tw-ring-color: ${getHeaderColor()}40` : ''}
              onclick={toggleCardView}
              disabled={changingCardView || !hasWriteAccess}
              role="switch"
              aria-checked={snipsel?.card_view !== false}
              aria-label="Toggle card view"
            >
              <span 
                class="pointer-events-none inline-block h-5 w-5 transform rounded-full shadow ring-0 transition duration-200 ease-in-out {snipsel?.card_view !== false ? 'translate-x-5' : 'translate-x-0'}"
                style={snipsel?.card_view !== false ? `background-color: ${getContrastColor(getHeaderColor())}` : 'background-color: white'}
              ></span>
            </button>
          </div>
			</div>

			<div class="rounded-xl border border-slate-200 bg-white/80 p-3 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80">
				<div class="text-xs uppercase text-slate-500 dark:text-slate-400">Timestamps</div>
				<div class="mt-2 space-y-1 text-sm text-slate-600 dark:text-slate-400">
					<div>
						<span class="font-medium">Created:</span>
						<span class="ml-1">{formatWhen(snipsel.created_at)}</span>
						{#if snipsel.created_by_username}
						<span class="ml-1 text-slate-500 dark:text-slate-500">by {snipsel.created_by_username}</span>
						{/if}
					</div>
					<div>
						<span class="font-medium">Modified:</span>
						<span class="ml-1">{formatWhen(snipsel.modified_at)}</span>
						<span class="ml-1 text-slate-500 dark:text-slate-500">by {snipsel.modified_by_username}</span>
					</div>
					{#if snipsel.type === 'task' && snipsel.done_at}
						<div>
							<span class="font-medium">{snipsel.task_done === 2 ? 'Cancelled:' : 'Done:'}</span>
							<span class="ml-1">{formatWhen(snipsel.done_at)}</span>
							{#if snipsel.done_by_username}
								<span class="ml-1 text-slate-500 dark:text-slate-500">by {snipsel.done_by_username}</span>
							{/if}
						</div>
					{/if}
				</div>
			</div>

      <!-- Diced Moments Info -->
      <div class="rounded-xl border border-slate-200 bg-white/80 p-3 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80">
        <div class="flex items-center justify-between gap-2">
          <div class="text-xs uppercase text-slate-500 dark:text-slate-400">Diced Moments</div>
          <div class="flex items-center gap-2">
            <Dices label="" size={14} className="text-slate-400" />
            <span class="text-sm font-bold text-slate-700 dark:text-slate-200">
               {snipsel.diced_count === -1 ? 'Banned' : `${snipsel.diced_count ?? 0} rolls`}
            </span>
          </div>
        </div>
        <div class="mt-3 flex items-center justify-between border-t border-slate-100 pt-3 dark:border-white/5">
          <div class="flex items-center gap-2">
            <Ban label="" size={16} className={snipsel.diced_count === -1 ? 'text-red-500' : 'text-slate-400'} />
            <span class="text-sm text-slate-600 dark:text-slate-400">Ban from Diced Moments</span>
          </div>
          <button
            type="button"
            class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 {snipsel.diced_count === -1 ? 'bg-red-500' : 'bg-slate-200 dark:bg-slate-700'}"
            onclick={toggleDicedBan}
            disabled={!hasWriteAccess}
            role="switch"
            aria-checked={snipsel.diced_count === -1}
          >
            <span 
              class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out {snipsel.diced_count === -1 ? 'translate-x-5' : 'translate-x-0'}"
            ></span>
          </button>
        </div>
      </div>




    </div>

    {#if snipsel.content_markdown}
      <div class="rounded-xl border border-slate-200 bg-white/80 p-6 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80">
        {#if getDeezerLink(snipsel.content_markdown)}
          {@const dz = getDeezerLink(snipsel.content_markdown)!}
          <div class="mb-4">
            <DeezerCard url={dz.url} type={dz.type} id={dz.id} />
          </div>
        {/if}

        {#if getSpotifyLink(snipsel.content_markdown)}
          {@const sp = getSpotifyLink(snipsel.content_markdown)!}
          <div class="mb-4">
            <SpotifyCard url={sp.url} accentColor={getHeaderColor()} />
          </div>
        {/if}
        
        {#if getYouTubeLink(snipsel.content_markdown)}
          {@const yt = getYouTubeLink(snipsel.content_markdown)!}
          <div class="mb-4">
            <YouTubeCard url={yt.url} />
          </div>
        {/if}

        <div 
          class="prose prose-sm max-w-none text-lg prose-p:my-0 prose-headings:my-2 prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg whitespace-pre-wrap dark:prose-invert break-words {snipsel.type === 'task' && snipsel.task_done > 0 ? 'task-faded' : ''} {snipsel.type === 'task' && snipsel.task_done === 2 ? 'task-cancelled' : ''}"
          onclick={(e) => {
            const tagTarget = (e.target as HTMLElement).closest('[data-tag]');
            if (tagTarget) {
              const tag = tagTarget.getAttribute('data-tag');
              if (tag) {
                searchQuery.set('#' + tag);
                currentView.set({ type: 'search' });
              }
              return;
            }

            const mentionTarget = (e.target as HTMLElement).closest('[data-mention]');
            if (mentionTarget) {
              const mention = mentionTarget.getAttribute('data-mention');
              if (mention) {
                searchQuery.set('@' + mention);
                currentView.set({ type: 'search' });
              }
              return;
            }
          }}
          role="presentation"
        >
          {@html highlightTokens(stripMediaLinks(snipsel.content_markdown))}
        </div>

        {#if (snipsel.tags?.length ?? 0) > 0 || (snipsel.mentions?.length ?? 0) > 0}
          <div class="mt-4 flex flex-wrap gap-1.5 border-t border-slate-100 pt-4 dark:border-white/5">
            {#each snipsel.tags ?? [] as t (t)}
              <button 
                type="button"
                class="rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider transition-colors hover:opacity-80"
                style={`background-color: ${getAccentTint()}; color: ${getAccent()}; border: 1px solid rgba(0,0,0,0.05)`}
                onclick={() => {
                  searchQuery.set('#' + t);
                  currentView.set({ type: 'search' });
                }}
              >
                #{t}
              </button>
            {/each}
            {#each snipsel.mentions ?? [] as m (m)}
              <button 
                type="button"
                class="rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider transition-colors hover:opacity-80"
                style={`background-color: rgba(255,255,255,0.92); color: ${getAccent()}; border: 1px solid rgba(0,0,0,0.05)`}
                onclick={() => {
                  searchQuery.set('@' + m);
                  currentView.set({ type: 'search' });
                }}
              >
                @{m}
              </button>
            {/each}
          </div>
        {/if}
      </div>
    {/if}

    <div class="rounded-xl border border-slate-200 bg-white/80 p-3 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80">
      <div class="flex items-center justify-between gap-2">
        <div class="text-xs uppercase text-slate-500 dark:text-slate-400">Reminders</div>
        {#if updatingReminders}
          <div class="text-xs text-slate-500">Saving...</div>
        {/if}
      </div>
      <div class="mt-3 space-y-3">
        <div>
          <label for="reminder-at" class="block text-xs font-medium text-slate-500 dark:text-slate-400">Next Reminder</label>
          <div class="mt-1 flex items-center gap-2">
            <input
              id="reminder-at"
              type="datetime-local"
              class="flex-1 rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-slate-100 dark:ring-white/10"
              bind:value={reminderAt}
            />
            {#if reminderAt}
              <button
                type="button"
                class="rounded-full border border-slate-200 bg-white px-6 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
                style={`color: ${getAccent()}`}
                onclick={() => { reminderAt = null; updateReminders(); }}
              >
                Clear
              </button>
            {/if}
            <button
              class="relative flex items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-6 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
              style={`color: ${getAccent()}`}
              type="button"
              onclick={updateReminders}
              disabled={updatingReminders || showSavedFeedback}
            >
              {#if updatingReminders}
                <div class="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent opacity-40"></div>
                <span>Saving...</span>
              {:else if showSavedFeedback}
                <div class="animate-in zoom-in fade-in duration-300 flex items-center gap-2">
                  <Check label="" size={18} strokeWidth={3} />
                  <span>Saved!</span>
                </div>
              {:else}
                <span>Save</span>
              {/if}
            </button>
          </div>
        </div>
        <RRuleBuilder
          bind:rrule={reminderRRule}
          accent={getAccent()}
          disabled={!hasWriteAccess}
          onChange={updateReminders}
        />
        <p class="mt-1 text-[10px] text-slate-400">
          Standard iCalendar RRule format. Leave empty for one-time reminder.
        </p>
      </div>
    </div>


    {#if hasGeo(snipsel)}
      <div class="rounded-xl border border-slate-200 bg-white/80 p-3 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80">
        <div class="text-xs uppercase text-slate-500 dark:text-slate-400">Location</div>
        <div class="mt-2 overflow-hidden rounded-md border border-black/5 dark:border-white/10">
          <iframe
            class="h-64 w-full"
            title="OpenStreetMap"
            src={osmEmbedUrl(snipsel.geo_lat ?? 0, snipsel.geo_lng ?? 0)}
            loading="lazy"
          ></iframe>
        </div>
        <div class="mt-2 text-sm text-slate-500">
          {snipsel.geo_lat?.toFixed(5)}, {snipsel.geo_lng?.toFixed(5)}
          {#if typeof snipsel.geo_accuracy_m === 'number'}
            · ±{Math.round(snipsel.geo_accuracy_m)}m
          {/if}
        </div>
      </div>
    {/if}

		{@const allImages = snipsel.attachments.filter(isImageAttachment).filter(a => a.has_thumbnail)}
		<div class="rounded-xl border border-slate-200 bg-white/80 p-3 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80">
			<div class="text-xs uppercase text-slate-500 dark:text-slate-400">Attachments</div>
			{#if snipsel.attachments.length === 0}
				<div class="mt-2 text-sm text-slate-500">No attachments</div>
			{:else}
				<div class="mt-3 space-y-2">
					{#each snipsel.attachments as a}
						{@const imgIdx = allImages.findIndex(img => img.id === a.id)}
						<div class="flex items-center gap-3 px-1 py-1">
							{#if isVideoAttachment(a) && a.has_thumbnail}
								<button
									type="button"
									class="al-icon-wrapper relative h-10 w-10 overflow-hidden rounded group"
									aria-label={`Play ${a.filename}`}
									onclick={() => openVideoModal(a.id, a.filename)}
								>
									<img class="h-10 w-10 object-cover" src={api.attachments.thumbnailUrl(a.id)} alt={a.filename} loading="lazy" />
									<div class="absolute inset-0 flex items-center justify-center bg-black/20 group-hover:bg-black/30 transition-colors">
										<CirclePlay label="" size={20} className="text-white" />
									</div>
								</button>
							{:else if isImageAttachment(a) && a.has_thumbnail}
								<button
									type="button"
									class="h-10 w-10 overflow-hidden rounded"
									aria-label={`View ${a.filename}`}
									onclick={() => openImageModal(allImages.map(img => ({ id: img.id, filename: img.filename })), imgIdx)}
								>
									<img class="h-10 w-10 object-cover" src={api.attachments.thumbnailUrl(a.id)} alt={a.filename} loading="lazy" />
								</button>
								{:else if a.has_thumbnail}
									<img class="h-10 w-10 rounded object-cover" src={api.attachments.thumbnailUrl(a.id)} alt={a.filename} loading="lazy" />
								{:else}
									<div class="h-10 w-10 rounded bg-slate-100 flex items-center justify-center text-xs dark:bg-slate-800">
                    {a.filename.split('.').pop()?.toUpperCase() || 'FILE'}
                  </div>
								{/if}
								<div class="min-w-0 flex-1">
									<div class="truncate text-sm font-medium dark:text-slate-200">{a.filename}</div>
									<div class="text-xs text-slate-500 dark:text-slate-400">{a.size_bytes} bytes</div>
								</div>
								<div class="flex items-center gap-1 rounded-full border border-slate-200 bg-white/80 p-1 shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-800/80">
									<a
										class="grid h-9 w-9 place-items-center rounded-full text-slate-700 hover:bg-black/5 dark:text-slate-300 dark:hover:bg-white/5"
										href={api.attachments.downloadUrl(a.id)}
										target="_blank"
										rel="noreferrer"
										aria-label="Download attachment"
										title="Download"
									>
										<Download label="" size={20} />
									</a>
									<button
										class="al-icon-wrapper grid h-9 w-9 place-items-center rounded-full text-slate-700 hover:bg-black/5 dark:text-slate-300 dark:hover:bg-white/5"
										type="button"
										aria-label="Delete attachment"
										onclick={() => deleteAttachment(a.id)}
										title="Delete"
									>
										<Trash2 label="" size={20} />
									</button>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>

    <div class="rounded-xl border border-slate-200 bg-white/80 p-3 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80">
      <div class="text-xs uppercase text-slate-500 dark:text-slate-400">Placements</div>
      {#if placements.length === 0}
        <div class="mt-2 text-sm text-slate-500">Not in any collection</div>
      {:else}
		<div class="mt-2 flex flex-col gap-2">
			{#each placements as p}
				<div class="flex items-center justify-between gap-2">
					<button
						class="min-w-0 flex-1 text-left text-sm font-medium text-slate-700 hover:underline dark:text-slate-300 dark:hover:text-slate-100"
						type="button"
						onclick={() => {
							currentView.set({ type: 'collection', id: p.collection_id });
							collectionAnchor.set({ collectionId: p.collection_id, pos: p.position });
						}}
					>
						<span class="truncate">{p.collection_icon ? `${p.collection_icon} ` : ''}{p.collection_title ?? p.collection_id}</span>
					</button>
					<div class="flex items-center gap-1 rounded-full border border-slate-200 bg-white/80 p-1 shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-800/80">
						<button
							class="al-icon-wrapper grid h-9 w-9 place-items-center rounded-full text-slate-700 hover:bg-black/5 dark:text-slate-300 dark:hover:bg-white/5"
							type="button"
							aria-label={(favoriteByCollectionId[p.collection_id] ?? false) ? 'Unfavorite collection' : 'Favorite collection'}
							title={(favoriteByCollectionId[p.collection_id] ?? false) ? 'Unfavorite' : 'Favorite'}
							onclick={() => toggleCollectionFavorite(p.collection_id)}
							style={(favoriteByCollectionId[p.collection_id] ?? false) ? `color: ${getAccent()}` : undefined}
						>
							<Heart label="" size={16} className={favoriteByCollectionId[p.collection_id] ? "fill-current" : ""} strokeWidth={favoriteByCollectionId[p.collection_id] ? 0 : 1.6} />
						</button>
						<button
							class="al-icon-wrapper grid h-9 w-9 place-items-center rounded-full text-slate-700 hover:bg-black/5 dark:text-slate-300 dark:hover:bg-white/5"
							type="button"
							aria-label="Collection info"
							title="Info"
							onclick={() => openCollectionInfo(p.collection_id)}
						>
							<Info label="" size={16} strokeWidth={1.6} />
						</button>
					</div>
				</div>
			{/each}
        </div>
      {/if}
    </div>

    <div class="rounded-xl border border-slate-200 bg-white/80 p-3 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80">
      <div class="flex items-center justify-between gap-2">
        <div class="text-xs uppercase text-slate-500 dark:text-slate-400">Direct link</div>
        {#if copied}
          <div class="text-xs text-slate-500">Copied</div>
        {/if}
      </div>
      <div class="mt-2 flex items-center gap-2">
        <input
          id="snipsel-direct-link"
          class="min-w-0 flex-1 rounded-md border border-slate-200 bg-white/80 px-3 py-2 text-sm text-slate-700 shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-900/50 dark:text-slate-300"
          readonly
          value={directLinkUrl()}
        />
        <div class="flex items-center gap-1">
          <button
            class="rounded-full border border-slate-200 bg-white px-6 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
            style={`color: ${getAccent()}`}
            type="button"
            onclick={copyDirectLink}
            aria-label="Copy direct link"
            title="Copy"
          >
            {copied ? 'Copied!' : 'Copy link'}
          </button>
        </div>
      </div>
    </div>



			
  {/if}

  {#if saveStatus}
    <div 
      class="fixed bottom-4 right-4 h-3 w-3 rounded-full shadow-lg z-50 transition-opacity duration-500"
      style="background-color: {saveStatus === 'success' ? '#22c55e' : '#ef4444'}"
      aria-hidden="true"
    ></div>
  {/if}
</div>

<ImageModal
  attachments={modalImages}
  currentIndex={modalImageIndex}
  onClose={closeImageModal}
  onNavigate={(idx) => modalImageIndex = idx}
/>

{#if modalVideo}
  <VideoModal
    attachmentId={modalVideo.id}
    filename={modalVideo.filename}
    onClose={closeVideoModal}
  />
{/if}
