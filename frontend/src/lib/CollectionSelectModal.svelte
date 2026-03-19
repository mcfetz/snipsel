<script lang="ts">
  import X from '@animated-color-icons/lucide-svelte/X.svelte';
  import Search from '@animated-color-icons/lucide-svelte/Search.svelte';
  import Loader2 from '@animated-color-icons/lucide-svelte/Loader2.svelte';
  import CalendarIcon from '@animated-color-icons/lucide-svelte/Calendar.svelte';
  import { api, type SearchCollectionHit } from './api';
  import { onMount } from 'svelte';
  import { fly } from 'svelte/transition';
  import { toLocalIsoDay } from './stores';
  import { currentUser } from './session';

  interface Props {
    title: string;
    onSelect: (collectionId: string) => void;
    onClose: () => void;
  }

  let { title, onSelect, onClose }: Props = $props();

  let mode = $state<'collections' | 'days'>('collections');

  let query = $state('');
  let recentCollections = $state<SearchCollectionHit[]>([]);
  let searchResults = $state<SearchCollectionHit[]>([]);
  let loading = $state(false);
  let debounceTimer: ReturnType<typeof setTimeout> | null = null;
  let inputRef: HTMLInputElement | undefined = $state();

  let displayItems = $derived(query.trim() ? searchResults : recentCollections);

  // Calendar State
  let cursor = $state(new Date());
  let dayCollections = $state<Map<string, { icon: string | null }>>(new Map());
  let direction = $state(1);
  let isCreatingDay = $state(false);
  let pressedCell = $state<number | null>(null);

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

  function startOfMonth(d: Date) {
    return new Date(d.getFullYear(), d.getMonth(), 1);
  }

  function addMonths(d: Date, delta: number) {
    return new Date(d.getFullYear(), d.getMonth() + delta, 1);
  }

  function monthLabel(d: Date) {
    return d.toLocaleString(undefined, { month: 'long', year: 'numeric' });
  }

  function getGridDays(d: Date): Array<{ day: Date; inMonth: boolean }> {
    const first = startOfMonth(d);
    const start = new Date(first);
    const weekday = (start.getDay() + 6) % 7;
    start.setDate(start.getDate() - weekday);

    const out: Array<{ day: Date; inMonth: boolean }> = [];
    for (let i = 0; i < 42; i += 1) {
      const day = new Date(start);
      day.setDate(start.getDate() + i);
      out.push({ day, inMonth: day.getMonth() === d.getMonth() });
    }
    return out;
  }

  const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  function prevMonth() { direction = -1; cursor = addMonths(cursor, -1); }
  function nextMonth() { direction =  1; cursor = addMonths(cursor,  1); }
  function goToday()  { direction = new Date() > cursor ? 1 : -1; cursor = new Date(); }

  function handleMonthChange(e: Event) {
    const val = (e.currentTarget as HTMLInputElement).value; // YYYY-MM
    if (!val) return;
    const [y, m] = val.split('-').map(Number);
    const next = new Date(y, m - 1, 1);
    direction = next > cursor ? 1 : -1;
    cursor = next;
  }

  function toMonthValue(d: Date) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    return `${y}-${m}`;
  }

  function isSameLocalDay(a: Date, b: Date) {
    return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
  }

  async function loadHighlights() {
    try {
      const res = await api.collections.list(true);
      const map = new Map<string, { icon: string | null }>();
      for (const c of res.collections) {
        if (c.list_for_day) map.set(c.list_for_day, { icon: c.icon });
      }
      dayCollections = map;
    } catch (err) {
      console.error('Failed to load highlights', err);
    }
  }

  async function openDay(day: Date, cellIndex: number) {
    if (isCreatingDay) return;
    pressedCell = cellIndex;
    await new Promise(resolve => setTimeout(resolve, 120));
    isCreatingDay = true;
    const iso = toLocalIsoDay(day);
    try {
      const res = await api.collections.today(iso);
      onSelect(res.collection.id);
      onClose();
    } catch (err) {
      console.error('Failed to open/create day collection', err);
    } finally {
      isCreatingDay = false;
      pressedCell = null;
    }
  }

  // Swipe handling
  let touchStartX = 0;
  let touchStartY = 0;

  function onTouchStart(e: TouchEvent) {
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
  }

  function onTouchEnd(e: TouchEvent) {
    const dx = e.changedTouches[0].clientX - touchStartX;
    const dy = e.changedTouches[0].clientY - touchStartY;
    if (Math.abs(dx) < 50 || Math.abs(dx) < Math.abs(dy)) return;
    dx < 0 ? nextMonth() : prevMonth();
  }

  $effect(() => {
    void cursor;
    if (mode === 'days') {
      loadHighlights();
    }
  });

  onMount(async () => {
    loading = true;
    try {
      const res = await api.collections.listRecent();
      recentCollections = res.collections.map(c => ({
        id: c.id,
        title: c.title,
        icon: c.icon,
        list_for_day: null
      }));
    } catch (err) {
      console.error('Failed to load recent collections', err);
    } finally {
      loading = false;
    }
  });

  function handleSearchInput() {
    if (debounceTimer) clearTimeout(debounceTimer);
    
    if (!query.trim()) {
      searchResults = [];
      return;
    }

    debounceTimer = setTimeout(async () => {
      loading = true;
      try {
        const res = await api.collections.autocomplete(query);
        searchResults = res.collections.map(c => ({
          id: c.id,
          title: c.title,
          icon: c.icon,
          list_for_day: null
        }));
      } catch (err) {
        console.error('Failed to search collections', err);
      } finally {
        loading = false;
      }
    }, 300);
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
    }
  }
</script>

<svelte:window onkeydown={handleKeydown} />

<div
  class="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm transition-all"
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
  tabindex="-1"
  onclick={(e) => e.target === e.currentTarget && onClose()}
  onkeydown={handleKeydown}
>
  <div class="w-full max-w-md overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-black/5 dark:bg-slate-900 dark:ring-white/10 flex flex-col max-h-[85vh]">
    <div class="border-b border-slate-100 bg-slate-50/50 px-6 py-4 dark:border-white/5 dark:bg-slate-800/50 flex items-center justify-between">
      <h2 id="modal-title" class="text-xl font-semibold text-slate-900 dark:text-slate-100">
        {title}
      </h2>
      <button
        class="al-icon-wrapper rounded-full p-2 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-white/5 dark:hover:text-slate-300"
        type="button"
        onclick={onClose}
        aria-label="Close"
      >
        <X label="" size={20} />
      </button>
    </div>

    <div class="px-6 pt-4 pb-2">
      <div class="flex rounded-full bg-slate-100 p-1 dark:bg-slate-800">
        <button
          class="flex-1 rounded-full px-4 py-1.5 text-sm font-medium transition-colors {mode === 'collections' ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-700 dark:text-white' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}"
          onclick={() => mode = 'collections'}
        >
          Collections
        </button>
        <button
          class="flex-1 rounded-full px-4 py-1.5 text-sm font-medium transition-colors {mode === 'days' ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-700 dark:text-white' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}"
          onclick={() => mode = 'days'}
        >
          Days
        </button>
      </div>
    </div>

    {#if mode === 'collections'}
      <div class="p-6 pt-2">
        <div class="relative">
          <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
            <Search label="" size={20} className="text-slate-400" />
          </div>
          <input
            bind:this={inputRef}
            type="text"
            class="block w-full rounded-xl border border-slate-200 bg-white py-3 pl-10 pr-3 text-sm placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-white/10 dark:bg-slate-800 dark:text-slate-100 dark:focus:border-indigo-400 dark:focus:ring-indigo-400 shadow-sm"
            placeholder="Search collections..."
            bind:value={query}
            oninput={handleSearchInput}
          />
        </div>
        
        {#if loading && !query && recentCollections.length === 0}
           <div class="mt-8 flex justify-center text-slate-400">
             <Loader2 label="" size={24} className="animate-spin" />
           </div>
        {/if}
      </div>

      <div class="flex-1 overflow-y-auto px-6 pb-6">
        
        {#if displayItems.length > 0}
          <div class="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            {query.trim() ? 'Search Results' : 'Recent Collections'}
          </div>
          <div class="space-y-1">
            {#each displayItems as c (c.id)}
              <button
                type="button"
                class="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left transition-colors hover:bg-slate-50 dark:hover:bg-white/5 group"
                onclick={() => onSelect(c.id)}
              >
                <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-white shadow-sm ring-1 ring-slate-200 dark:bg-slate-800 dark:ring-white/10 text-xl group-hover:scale-110 transition-transform">
                  {c.icon || '📁'}
                </span>
                <span class="flex-1 truncate font-medium text-slate-700 dark:text-slate-200">
                  {c.title}
                </span>
              </button>
            {/each}
          </div>
        {:else if query.trim() && !loading}
          <div class="py-8 text-center text-sm text-slate-500 dark:text-slate-400">
            No collections found matching "{query}"
          </div>
        {:else if !query.trim() && !loading && recentCollections.length === 0}
          <div class="py-8 text-center text-sm text-slate-500 dark:text-slate-400">
            No recent collections
          </div>
        {/if}
      </div>
    {:else}
      <div class="flex-1 overflow-y-auto px-6 pb-6 pt-2">
        <div class="space-y-4">
          <div class="flex items-center justify-between gap-3">
            <h2 class="flex items-center gap-2 text-xl font-semibold dark:text-slate-100">
              <CalendarIcon label="" size={20} className="text-slate-700 dark:text-slate-300" />
              <span>{monthLabel(cursor)}</span>
            </h2>
          </div>

          <div class="flex items-center gap-2">
            <div class="flex-1 overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-900 dark:ring-white/10">
              <div class="flex items-stretch divide-x divide-black/5 dark:divide-white/5">
                <button
                  class="flex-1 px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-slate-100"
                  type="button"
                  onclick={prevMonth}
                >
                  Prev
                </button>
                <button
                  class="flex-1 px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-slate-100"
                  type="button"
                  onclick={goToday}
                >
                  Today
                </button>
                <button
                  class="flex-1 px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-slate-100"
                  type="button"
                  onclick={nextMonth}
                >
                  Next
                </button>
              </div>
            </div>

            <div class="relative h-9 w-9 flex-shrink-0 overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 hover:bg-slate-50 transition-colors dark:border-white/10 dark:bg-slate-900 dark:ring-white/10 dark:hover:bg-white/5">
              <div class="flex h-full items-center justify-center text-slate-600 pointer-events-none dark:text-slate-400">
                <CalendarIcon label="" size={18} />
              </div>
              <input 
                type="month" 
                class="absolute inset-0 w-full h-full cursor-pointer opacity-0" 
                value={toMonthValue(cursor)} 
                onchange={handleMonthChange}
                onclick={(e) => {
                  if ('showPicker' in e.currentTarget) {
                    try { (e.currentTarget as any).showPicker(); } catch (err) { console.error(err); }
                  }
                }}
              />
            </div>
          </div>

          <div class="grid grid-cols-7 gap-1.5 text-center text-xs font-medium text-slate-500">
            {#each weekdays as w}
              <div class="py-1">{w}</div>
            {/each}
          </div>

          <div class="cal-stack overflow-hidden" role="none" ontouchstart={onTouchStart} ontouchend={onTouchEnd}>
            {#key cursor}
              <div
                class="grid grid-cols-7 gap-1.5"
                in:fly={{ x: direction * 60, duration: 220, opacity: 0 }}
                out:fly={{ x: direction * -60, duration: 220, opacity: 0 }}
              >
                {#each getGridDays(cursor) as cell, idx}
                  {@const iso = toLocalIsoDay(cell.day)}
                  {@const collectionData = dayCollections.get(iso)}
                  {@const hasCollection = !!collectionData}
                  {@const isToday = isSameLocalDay(cell.day, new Date())}
                  {@const showIcon = collectionData?.icon && collectionData.icon !== '📅'}
                  {@const isPressed = pressedCell === idx}
                  <button
                    class="group relative aspect-square rounded-lg transition-all {isPressed ? 'scale-90 opacity-80' : ''} {cell.inMonth
                      ? 'bg-white hover:bg-slate-100 dark:bg-slate-900/40 dark:hover:bg-slate-800/50'
                      : 'bg-slate-50 text-slate-400 hover:bg-slate-100 dark:bg-slate-950/40 dark:text-slate-600 dark:hover:bg-slate-900/40'} {isCreatingDay ? 'opacity-50 cursor-not-allowed' : ''}"
                    type="button"
                    onclick={() => openDay(cell.day, idx)}
                    disabled={isCreatingDay}
                    style={isToday ? `border: 2px solid ${getAccent()}` : undefined}
                  >
                    <div class="flex h-full flex-col items-center justify-center gap-0.5">
                      <span
                        class="text-base font-medium transition-all {isPressed ? 'scale-90' : ''} group-hover:scale-110 {isToday
                          ? 'text-slate-900 dark:text-white'
                          : cell.inMonth
                            ? 'text-slate-800 dark:text-slate-300'
                            : 'text-slate-400 dark:text-slate-600'}"
                      >
                        {cell.day.getDate()}
                      </span>
                      {#if hasCollection}
                        <span
                          class="h-1 w-4 rounded-full transition-all {isPressed ? 'scale-75' : ''} group-hover:scale-110"
                          style="background-color: {getAccent()}"
                        ></span>
                      {:else if isToday}
                        <span
                          class="h-1 w-4 rounded-full bg-slate-300 transition-all {isPressed ? 'scale-75' : ''} group-hover:scale-110 dark:bg-slate-600"
                        ></span>
                      {/if}
                    </div>
                  </button>
                {/each}
              </div>
            {/key}
          </div>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .cal-stack {
    display: grid;
  }
  .cal-stack > * {
    grid-area: 1 / 1;
  }
</style>
