<script lang="ts">
  import Download from '@animated-color-icons/lucide-svelte/Download.svelte';
  import Trash2 from '@animated-color-icons/lucide-svelte/Trash2.svelte';
  import Heart from '@animated-color-icons/lucide-svelte/Heart.svelte';
  import Info from '@animated-color-icons/lucide-svelte/Info.svelte';
  import CirclePlay from '@animated-color-icons/lucide-svelte/CirclePlay.svelte';
  import { api, type Attachment, type Snipsel, type SnipselDetailResponse } from '../lib/api';
  import ImageModal from '../lib/ImageModal.svelte';
  import { collectionAnchor, currentView, isLoading, searchError, searchQuery, searchResults } from '../lib/stores';
  import { currentUser } from '../lib/session';
  import { getCurrentUrl } from '../lib/router';
  import DeezerCard from '../lib/DeezerCard.svelte';
  import YouTubeCard from '../lib/YouTubeCard.svelte';
  import VideoModal from '../lib/VideoModal.svelte';

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

  let copied = $state(false);
  let reminderAt = $state<string | null>(null);
  let reminderRRule = $state<string | null>(null);
  let updatingReminders = $state(false);
  let showRRuleBuilder = $state(false);

  // RRule builder state
  let rrFreq = $state<'DAILY' | 'WEEKLY' | 'MONTHLY' | 'YEARLY'>('WEEKLY');
  let rrInterval = $state(1);
  let rrByDay = $state<string[]>([]);
	
  function toLocalDatetimeString(iso: string | null): string | null {
    if (!iso) return null;
    const d = new Date(iso);
    if (isNaN(d.getTime())) return null;
    const offset = d.getTimezoneOffset() * 60000;
    const local = new Date(d.getTime() - offset);
    return local.toISOString().slice(0, 16);
  }



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
    const isDark = typeof document !== 'undefined' && document.documentElement.classList.contains('dark');
    const base = isDark ? { r: 30, g: 41, b: 59 } : { r: 255, g: 255, b: 255 }; // slate-800 or white
    const accent = hexToRgb(getAccent());
    const mixed = accent ? mixRgb(base, accent, 0.14) : base;
    return rgba(mixed, 0.96);
  }

  let modalImage = $state<{ id: string; filename: string } | null>(null);
  let modalVideo = $state<{ id: string; filename: string } | null>(null);

  function openImageModal(id: string, filename: string) {
    modalImage = { id, filename };
  }

  function closeImageModal() {
    modalImage = null;
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
			saveStatus = 'success';
			setTimeout(() => { if (saveStatus === 'success') saveStatus = null; }, 5000);
			await load();
		} catch (err) {
			console.error('Failed to update reminders:', err);
			saveStatus = 'error';
			setTimeout(() => { if (saveStatus === 'error') saveStatus = null; }, 5000);
		} finally {
			updatingReminders = false;
		}
	}

  function applyRRuleBuilder() {
    let parts = [`FREQ=${rrFreq}`];
    if (rrInterval > 1) parts.push(`INTERVAL=${rrInterval}`);
    if (rrFreq === 'WEEKLY' && rrByDay.length > 0) {
      parts.push(`BYDAY=${rrByDay.join(',')}`);
    }
    reminderRRule = parts.join(';');
    showRRuleBuilder = false;
    updateReminders();
  }

  function parseCurrentRRule() {
    if (!reminderRRule) return;
    const parts = reminderRRule.split(';');
    rrByDay = [];
    for (const p of parts) {
      const [key, val] = p.split('=');
      if (key === 'FREQ') rrFreq = val as any;
      if (key === 'INTERVAL') rrInterval = parseInt(val) || 1;
      if (key === 'BYDAY') rrByDay = val.split(',');
    }
  }

  function toggleDay(day: string) {
    if (rrByDay.includes(day)) {
      rrByDay = rrByDay.filter(d => d !== day);
    } else {
      rrByDay = [...rrByDay, day];
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
      (m, p1, token) =>
        `${p1}<mark class="snip-token" style="background-color:${tokenBg}; color:${accent}">${token}</mark>`
    );
  }

  function getDeezerLink(text: string | null) {
    if (!text) return null;
    const stdMatch = text.match(/https?:\/\/(?:www\.)?deezer\.com\/(track|album|artist)\/(\d+)/);
    if (stdMatch) {
      return { type: stdMatch[1] as 'track' | 'album' | 'artist', id: stdMatch[2], url: stdMatch[0] };
    }
    const shortMatch = text.match(/https?:\/\/link\.deezer\.com\/s\/[A-Za-z0-9]+/);
    if (shortMatch) {
      return { type: null, id: null, url: shortMatch[0] };
    }
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
      class="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-sm font-medium shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80"
      style={`background-color: ${getAccentTint()}; color: ${getAccent()}`}
    >
      <span class="text-xs uppercase tracking-wide" style={`color: ${getAccent()}`}>Snipsel</span>
      <span class="opacity-70">·</span>
      <span class="font-semibold">{snipselId}</span>
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
            class="px-4 py-3 text-sm font-medium transition-colors {snipsel.type === 'text' ? 'text-slate-900 dark:text-white' : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
            type="button"
            onclick={() => setType('text')}
            disabled={changingType}
            style={snipsel.type === 'text' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          >
            Note
          </button>
          <button
            class="border-l border-black/5 px-4 py-3 text-sm font-medium transition-colors dark:border-white/5 {snipsel.type === 'task'
              ? 'text-slate-900 dark:text-white'
              : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
            type="button"
            onclick={() => setType('task')}
            disabled={changingType}
            style={snipsel.type === 'task' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          >
            Task
          </button>
				</div>
</div>
          <div class="mt-3 flex items-center justify-between">
            <span class="text-sm text-slate-600 dark:text-slate-400">Use card view</span>
            <button
              type="button"
              class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 {snipsel?.card_view !== false ? 'bg-indigo-600' : 'bg-slate-200 dark:bg-slate-700'}"
              onclick={toggleCardView}
              disabled={changingCardView || !hasWriteAccess}
              role="switch"
              aria-checked={snipsel?.card_view !== false}
            >
              <span class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out {snipsel?.card_view !== false ? 'translate-x-5' : 'translate-x-0'}"></span>
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
							<span class="font-medium">Done:</span>
							<span class="ml-1">{formatWhen(snipsel.done_at)}</span>
							{#if snipsel.done_by_username}
								<span class="ml-1 text-slate-500 dark:text-slate-500">by {snipsel.done_by_username}</span>
							{/if}
						</div>
					{/if}
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
        
        {#if getYouTubeLink(snipsel.content_markdown)}
          {@const yt = getYouTubeLink(snipsel.content_markdown)!}
          <div class="mb-4">
            <YouTubeCard url={yt.url} />
          </div>
        {/if}

        <div class="prose prose-sm max-w-none text-lg prose-p:my-0 prose-ul:my-0 prose-ol:my-0 prose-li:my-0 prose-headings:my-2 prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg whitespace-pre-wrap dark:prose-invert">
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
                  currentView.set({ type: 'search' });
                  searchQuery.set('');
                  api.search({ tag: t }).then(searchResults.set).catch(() => searchError.set('Search failed'));
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
                  currentView.set({ type: 'search' });
                  searchQuery.set('');
                  api.search({ mention: m }).then(searchResults.set).catch(() => searchError.set('Search failed'));
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
              class="flex-1 rounded-md border border-slate-200 bg-white/50 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:border-white/10 dark:bg-slate-900/50"
              bind:value={reminderAt}
              onchange={updateReminders}
            />
            {#if reminderAt}
              <button
                type="button"
                class="rounded-md bg-slate-100 px-2 py-2 text-xs font-medium text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700"
                onclick={() => { reminderAt = null; updateReminders(); }}
              >
                Clear
              </button>
            {/if}
          </div>
        </div>
        <div>
          <label for="reminder-rrule" class="block text-xs font-medium text-slate-500 dark:text-slate-400">Recurrence (RRule)</label>
          <div class="mt-1 flex items-center gap-2">
            <input
              id="reminder-rrule"
              type="text"
              placeholder="e.g. FREQ=DAILY"
              class="flex-1 rounded-md border border-slate-200 bg-white/50 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:border-white/10 dark:bg-slate-900/50"
              bind:value={reminderRRule}
              onblur={updateReminders}
            />
            <button
              type="button"
              class="rounded-md bg-slate-100 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700"
              onclick={() => { parseCurrentRRule(); showRRuleBuilder = !showRRuleBuilder; }}
            >
              {showRRuleBuilder ? 'Close' : 'Builder'}
            </button>
          </div>
          
          {#if showRRuleBuilder}
            <div class="mt-3 space-y-3 rounded-lg border border-slate-200 bg-slate-50/50 p-3 dark:border-white/5 dark:bg-white/5">
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label for="rr-freq" class="block text-[10px] uppercase tracking-wider text-slate-400">Frequency</label>
                  <select
                    id="rr-freq"
                    bind:value={rrFreq}
                    class="mt-1 w-full rounded-md border border-slate-200 bg-white px-2 py-1 text-sm dark:border-white/10 dark:bg-slate-800"
                  >
                    <option value="DAILY">Daily</option>
                    <option value="WEEKLY">Weekly</option>
                    <option value="MONTHLY">Monthly</option>
                    <option value="YEARLY">Yearly</option>
                  </select>
                </div>
                <div>
                  <label for="rr-interval" class="block text-[10px] uppercase tracking-wider text-slate-400">Interval</label>
                  <input
                    id="rr-interval"
                    type="number"
                    min="1"
                    bind:value={rrInterval}
                    class="mt-1 w-full rounded-md border border-slate-200 bg-white px-2 py-1 text-sm dark:border-white/10 dark:bg-slate-800"
                  />
                </div>
              </div>

              {#if rrFreq === 'WEEKLY'}
                <div>
                  <div class="block text-[10px] uppercase tracking-wider text-slate-400">Days</div>
                  <div class="mt-1 flex flex-wrap gap-1">
                    {#each ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'] as day}
                      <button
                        type="button"
                        class="h-7 w-8 rounded text-[10px] font-bold transition-colors {rrByDay.includes(day) ? 'text-white' : 'bg-white text-slate-600 hover:bg-slate-100 dark:bg-slate-800 dark:text-slate-400'}"
                        style={rrByDay.includes(day) ? `background-color: ${getAccent()}` : undefined}
                        onclick={() => toggleDay(day)}
                      >
                        {day}
                      </button>
                    {/each}
                  </div>
                </div>
              {/if}

              <div class="flex justify-end pt-1">
                <button
                  type="button"
                  class="rounded-md px-3 py-1.5 text-xs font-semibold text-white shadow-sm transition-opacity hover:opacity-90"
                  style={`background-color: ${getAccent()}`}
                  onclick={applyRRuleBuilder}
                >
                  Apply
                </button>
              </div>
            </div>
          {/if}
          
          <p class="mt-1 text-[10px] text-slate-400">
            Standard iCalendar RRule format. Leave empty for one-time reminder.
          </p>
        </div>
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

			<div class="rounded-xl border border-slate-200 bg-white/80 p-3 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80">
				<div class="text-xs uppercase text-slate-500 dark:text-slate-400">Attachments</div>
				{#if snipsel.attachments.length === 0}
					<div class="mt-2 text-sm text-slate-500">No attachments</div>
				{:else}
					<div class="mt-3 space-y-2">
						{#each snipsel.attachments as a}
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
										onclick={() => openImageModal(a.id, a.filename)}
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
        <div class="flex items-center gap-1 rounded-full border border-slate-200 bg-white/80 p-1 shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-800/80">
          <button
            class="rounded-full px-4 py-2 text-sm font-medium text-slate-700 hover:bg-black/5 dark:text-slate-300 dark:hover:text-slate-100"
            type="button"
            onclick={copyDirectLink}
            aria-label="Copy direct link"
            title="Copy"
          >
            Copy
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
  attachmentId={modalImage?.id ?? null}
  filename={modalImage?.filename ?? ''}
  onClose={closeImageModal}
/>

{#if modalVideo}
  <VideoModal
    attachmentId={modalVideo.id}
    filename={modalVideo.filename}
    onClose={closeVideoModal}
  />
{/if}
