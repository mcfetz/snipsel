<script lang="ts">
  import { fly, fade, scale } from 'svelte/transition';
  import SquareCheck from '@animated-color-icons/lucide-svelte/SquareCheck.svelte';
  import Bell from '@animated-color-icons/lucide-svelte/Bell.svelte';
  import RotateCw from '@animated-color-icons/lucide-svelte/RotateCw.svelte';
  import { api, type SearchSnipselHit } from '../lib/api';
  import { collectionAnchor, currentView, isLoading } from '../lib/stores';
  import { currentUser } from '../lib/session';
  import { getCurrentUrl } from '../lib/router';

	let items = $state<SearchSnipselHit[]>([]);
	let showDone = $state(false);
	let scope = $state<'my' | 'shared'>('my');
  let titleFilter = $state('');
  
  type SortKey = 'modified' | 'name' | 'reminder';
  type SortDir = 'asc' | 'desc';
  let sortKey = $state<SortKey>('reminder');
  let sortDir = $state<SortDir>('asc');

	let saveStatuses = $state<Record<string, 'success' | 'error' | null>>({});

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

  function isExpired(dateStr: string): boolean {
    return new Date(dateStr).getTime() < Date.now();
  }

  function daysFromNow(dateStr: string): string {
    const d = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.round((new Date(dateStr).setHours(0,0,0,0) - new Date().setHours(0,0,0,0)) / 86400000);
    
    if (diffDays === 0) {
      const diffMs = d.getTime() - now.getTime();
      if (diffMs > 0) {
        const hours = Math.floor(diffMs / 3600000);
        const minutes = Math.floor((diffMs % 3600000) / 60000);
        if (hours > 0) {
          return `fällig in ${hours}h ${minutes}m`;
        }
        return `fällig in ${minutes}m`;
      }
      return 'heute fällig';
    }
    if (diffDays > 0) return `in ${diffDays}d`;
    return `${-diffDays}d ago`;
  }

	async function load() {
		isLoading.set(true);
		try {
			const mentionName = ($currentUser?.username || '').trim();
			const res = await api.search({
				type: 'task',
				mentions_me: Boolean(mentionName),
				task_done: showDone,
				scope: scope,
			});
			items = res.snipsels;
		} finally {
			isLoading.set(false);
		}
	}

  const sorted = $derived.by(() => {
    let list = [...items];
    if (titleFilter.trim()) {
      const q = titleFilter.toLowerCase();
      list = list.filter(t => (t.content_markdown ?? '').toLowerCase().includes(q));
    }
    
    list.sort((a, b) => {
      const dir = sortDir === 'asc' ? 1 : -1;
      if (sortKey === 'name') {
        const ta = (a.content_markdown ?? '').toLowerCase();
        const tb = (b.content_markdown ?? '').toLowerCase();
        return ta.localeCompare(tb) * dir;
      }
      if (sortKey === 'modified') {
        const da = new Date(a.modified_at).getTime();
        const db = new Date(b.modified_at).getTime();
        return (da - db) * dir;
      }
      // reminder (default)
      if (a.reminder_at && b.reminder_at) {
        return (new Date(a.reminder_at).getTime() - new Date(b.reminder_at).getTime()) * dir;
      }
      if (a.reminder_at) return -1 * dir;
      if (b.reminder_at) return 1 * dir;
      return 0;
    });
    return list;
  });

  const visible = $derived(sorted.slice(0, 100));

	$effect(() => {
		const uname = ($currentUser?.username || '').trim();
		void uname;
		void showDone;
		void scope;
		load();
	});

	async function toggleDone(id: string, current: boolean) {
		collectionAnchor.set(null);
		try {
			await api.snipsels.update(id, { task_done: !current });
			saveStatuses[id] = 'success';
			setTimeout(() => { if (saveStatuses[id] === 'success') saveStatuses[id] = null; }, 5000);
			await load();
		} catch (err) {
			console.error('Failed to toggle task:', err);
			saveStatuses[id] = 'error';
			setTimeout(() => { if (saveStatuses[id] === 'error') saveStatuses[id] = null; }, 5000);
		}
	}

  function openInfo(id: string) {
    collectionAnchor.set(null);
    currentView.set({ type: 'snipsel', id, returnTo: getCurrentUrl() });
  }

	function openInCollection(t: SearchSnipselHit) {
		const hasAccess = t.has_collection_access !== false;
		if (!hasAccess) {
			openInfo(t.id);
			return;
		}
		const collectionId = (t.collection_id ?? '').trim();
		if (!collectionId) {
			openInfo(t.id);
			return;
		}
    currentView.set({ type: 'collection', id: collectionId });
    const pos = typeof t.position === 'number' ? t.position : undefined;
    if (pos) {
      collectionAnchor.set({ collectionId, pos });
    } else {
      collectionAnchor.set({ collectionId, snipselId: t.id });
    }
  }

	// loaded via $effect
</script>

<div class="space-y-4">
  <div class="flex items-center justify-between">
    <h2 class="flex items-center gap-2 text-2xl font-semibold dark:text-slate-100">
      <SquareCheck label="" size={24} className="text-slate-700 dark:text-slate-300" />
      <span>Todos</span>
    </h2>
  </div>

	<div class="flex items-center gap-2">
		<div class="flex flex-1 overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-900 dark:ring-white/10" role="tablist">
			<button
				type="button"
				role="tab"
				aria-selected={!showDone}
				class="flex-1 px-4 py-3 text-base font-medium transition-colors {!showDone
					? 'text-slate-900 dark:text-white'
					: 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
				onclick={() => { showDone = false; }}
				style={!showDone ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
			>
				Open
			</button>
			<button
				type="button"
				role="tab"
				aria-selected={showDone}
				class="flex-1 border-l border-black/5 px-4 py-3 text-base font-medium transition-colors dark:border-white/5 {showDone
					? 'text-slate-900 dark:text-white'
					: 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
				onclick={() => { showDone = true; }}
				style={showDone ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
			>
				Done
			</button>
		</div>

		<div class="flex overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-900 dark:ring-white/10" role="tablist" aria-label="Scope">
			<button
				type="button"
				role="tab"
				aria-selected={scope === 'my'}
				class="px-6 py-3 text-base font-medium transition-colors {scope === 'my'
					? 'text-slate-900 dark:text-white'
					: 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
				onclick={() => (scope = 'my')}
				style={scope === 'my' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
			>
				My
			</button>
			<button
				type="button"
				role="tab"
				aria-selected={scope === 'shared'}
				class="border-l border-black/5 px-6 py-3 text-base font-medium transition-colors dark:border-white/5 {scope === 'shared'
					? 'text-slate-900 dark:text-white'
					: 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
				onclick={() => (scope = 'shared')}
				style={scope === 'shared' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
			>
				Shared
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
      placeholder="Filter tasks"
      bind:value={titleFilter}
    />

    <div class="ml-auto flex items-center gap-2">
      <div class="overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-900">
        <div class="flex">
          <button
            class="px-4 py-2 text-sm font-medium {sortKey === 'reminder'
              ? 'text-slate-900 dark:text-white'
              : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
            type="button"
            onclick={() => (sortKey = 'reminder')}
            style={sortKey === 'reminder' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          >
            Reminder
          </button>
          <button
            class="border-l border-black/5 px-4 py-2 text-sm font-medium {sortKey === 'modified'
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

	{#if items.length === 0}
		<div class="py-8 text-center text-sm text-slate-500" in:fade={{ duration: 200 }}>
      No {showDone ? 'done' : 'open'} tasks found.
    </div>
  {:else if visible.length === 0}
		<div class="py-8 text-center text-sm text-slate-500" in:fade={{ duration: 200 }}>
      No tasks match your filter.
    </div>
	{:else}
    <div class="space-y-2">
		{#each visible as t (t.id)}
			{@const hasAccess = t.has_collection_access !== false}
			{@const canToggle = t.can_toggle_task_done === true}
			<div class="flex w-full items-center gap-3 px-1 py-2" in:fly={{ y: 10, duration: 200 }} out:fade={{ duration: 150 }}>
				<button
					class="grid h-8 w-8 place-items-center rounded-full border border-slate-300 bg-white transition-all duration-150 hover:scale-110 active:scale-95 disabled:opacity-40 disabled:hover:scale-100 dark:border-white/20 dark:bg-slate-900"
					type="button"
					aria-label={t.task_done ? 'Mark open' : 'Mark done'}
					title={t.task_done ? 'Open' : 'Done'}
					disabled={!canToggle}
					style={canToggle ? `border-color: ${getAccent()}` : undefined}
					onclick={() => toggleDone(t.id, t.task_done)}
				>
					{#if t.task_done}
						<span in:scale={{ start: 0.5, duration: 150 }} class="text-sm font-semibold" style={`color: ${getAccent()}`}>✓</span>
					{/if}
				</button>

				<button class="al-icon-wrapper min-w-0 flex flex-1 items-start gap-3 text-left" type="button" onclick={() => openInCollection(t)}>
					<div class="min-w-0 flex-1">
						<div class="truncate text-lg font-medium text-slate-900 dark:text-slate-100">{t.content_markdown ?? ''}</div>
						<div class="mt-0.5 flex flex-wrap items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
							<span class="rounded px-1.5 py-0.5" style={`background-color: ${getAccentTint()}; color: ${getAccent()}`}>
								{#if hasAccess}
									{t.collection_icon ? `${t.collection_icon} ` : ''}{t.collection_title ?? 'Collection'}
								{:else}
									Restricted
								{/if}
							</span>
							{#if t.reminder_at}
								{@const expired = isExpired(t.reminder_at)}
								<span 
									class="flex items-center gap-1 rounded px-1.5 py-0.5 {expired ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400' : ''}"
									style={expired 
										? undefined 
										: `background-color: ${getAccentTint()}; color: ${getAccent()}`}
								>
									<Bell label="" size={12} strokeWidth={2.5} />
									{new Date(t.reminder_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
									<span class="opacity-60">· {daysFromNow(t.reminder_at)}</span>
									{#if t.reminder_rrule}
										<RotateCw label="" size={12} strokeWidth={2.5} className="ml-0.5" />
									{/if}
								</span>
							{/if}
						</div>
					</div>
				</button>

				{#if saveStatuses[t.id]}
					<div 
						class="h-2 w-2 rounded-full transition-opacity duration-500"
						style="background-color: {saveStatuses[t.id] === 'success' ? '#22c55e' : '#ef4444'}"
						aria-hidden="true"
					></div>
				{/if}

          <div class="overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-900 dark:ring-white/10">
            <div class="flex">
              <button
                class="grid h-11 w-12 place-items-center text-lg text-slate-700 hover:bg-black/5 dark:text-slate-400 dark:hover:bg-white/5"
                type="button"
                aria-label="Info"
                title="Info"
                onclick={() => openInfo(t.id)}
              >
                ⓘ
              </button>
            </div>
          </div>
        </div>
      {/each}
      
      {#if sorted.length > visible.length}
        <div class="py-6 text-center text-sm text-slate-500 font-medium bg-slate-50/50 rounded-xl border border-slate-200/50 dark:bg-slate-900/30 dark:border-white/5">
          Showing <span class="font-bold text-slate-700 dark:text-slate-300">100</span> of <span class="font-bold text-slate-700 dark:text-slate-300">{sorted.length}</span> tasks.<br/>
          Use the filter above to find more.
        </div>
      {/if}
    </div>
  {/if}
</div>
