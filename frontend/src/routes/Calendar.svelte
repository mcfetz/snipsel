<script lang="ts">
  import CalendarIcon from '@animated-color-icons/lucide-svelte/Calendar.svelte';
  import { api } from '../lib/api';
  import { fly } from 'svelte/transition';
  import { collectionAnchor, currentCollection, currentView, isLoading, toLocalIsoDay } from '../lib/stores';
  import { currentUser } from '../lib/session';

  let cursor = $state(new Date());
  let dayCollections = $state<Map<string, { icon: string | null }>>(new Map());

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

  async function loadHighlights() {
    isLoading.set(true);
    try {
      const res = await api.collections.list(true);
      const map = new Map<string, { icon: string | null }>();
      for (const c of res.collections) {
        if (c.list_for_day) map.set(c.list_for_day, { icon: c.icon });
      }
      dayCollections = map;
    } finally {
      isLoading.set(false);
    }
  }

  $effect(() => {
    void cursor;
    loadHighlights();
  });

  async function openDay(day: Date) {
    const iso = toLocalIsoDay(day);
    isLoading.set(true);
    try {
      const res = await api.collections.today(iso);
      currentCollection.set(res.collection);
      collectionAnchor.set(null);
      currentView.set({ type: 'collection', id: res.collection.id });
    } finally {
      isLoading.set(false);
    }
  }

  function isSameLocalDay(a: Date, b: Date) {
    return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
  }

  const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
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

  // Direction for slide animation: 1 = forward (next), -1 = backward (prev)
  let direction = $state(1);

  function prevMonth() { direction = -1; cursor = addMonths(cursor, -1); }
  function nextMonth() { direction =  1; cursor = addMonths(cursor,  1); }
  function goToday()  { direction = new Date() > cursor ? 1 : -1; cursor = new Date(); }

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
</script>

<div class="space-y-4">
  <div class="flex items-center justify-between gap-3">
    <h2 class="flex items-center gap-2 text-2xl font-semibold dark:text-slate-100">
      <CalendarIcon label="" size={24} className="text-slate-700 dark:text-slate-300" />
      <span>{monthLabel(cursor)}</span>
    </h2>
  </div>

  <div class="flex items-center gap-2">
    <div class="flex-1 overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-900 dark:ring-white/10">
      <div class="flex items-stretch divide-x divide-black/5 dark:divide-white/5">
        <button
          class="flex-1 px-4 py-3 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-slate-100"
          type="button"
          onclick={prevMonth}
        >
          Prev
        </button>
        <button
          class="flex-1 px-4 py-3 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-slate-100"
          type="button"
          onclick={goToday}
        >
          Today
        </button>
        <button
          class="flex-1 px-4 py-3 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-slate-100"
          type="button"
          onclick={nextMonth}
        >
          Next
        </button>
      </div>
    </div>

    <div class="relative h-[46px] w-[46px] flex-shrink-0 overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 hover:bg-slate-50 transition-colors dark:border-white/10 dark:bg-slate-900 dark:ring-white/10 dark:hover:bg-white/5">
      <div class="flex h-full items-center justify-center text-slate-600 pointer-events-none dark:text-slate-400">
        <CalendarIcon label="" size={20} />
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

  <div class="grid grid-cols-7 gap-1 text-center text-sm font-medium text-slate-500">
    {#each weekdays as w}
      <div class="py-1">{w}</div>
    {/each}
  </div>

  <div class="cal-stack overflow-hidden" role="none" ontouchstart={onTouchStart} ontouchend={onTouchEnd}>
    {#key cursor}
      <div
        class="grid grid-cols-7 gap-1"
        in:fly={{ x: direction * 60, duration: 220, opacity: 0 }}
        out:fly={{ x: direction * -60, duration: 220, opacity: 0 }}
      >
        {#each getGridDays(cursor) as cell}
          {@const iso = toLocalIsoDay(cell.day)}
          {@const collectionData = dayCollections.get(iso)}
          {@const hasCollection = !!collectionData}
          {@const isToday = isSameLocalDay(cell.day, new Date())}
          {@const showIcon = collectionData?.icon && collectionData.icon !== '📅'}
          <button
            class="relative aspect-square rounded-lg text-lg transition-colors {cell.inMonth
              ? 'bg-white hover:bg-slate-50 dark:bg-slate-900/40 dark:hover:bg-slate-800/60'
              : 'bg-slate-50 text-slate-400 hover:bg-slate-100 dark:bg-slate-950/40 dark:text-slate-600 dark:hover:bg-slate-900/40'}"
            type="button"
            onclick={() => openDay(cell.day)}
            style={isToday ? `box-shadow: inset 0 0 0 2px ${getAccent()}` : undefined}
          >
            {#if showIcon}
              <span class="absolute -right-1 -top-1 flex h-[22px] w-[22px] items-center justify-center rounded-full bg-white text-[12px] shadow-sm ring-1 ring-black/5 dark:bg-slate-800 dark:ring-white/10">
                {collectionData.icon}
              </span>
            {/if}
            <span
              class="mx-auto grid h-10 w-10 place-items-center rounded-full text-base {hasCollection
                ? 'font-semibold'
                : isToday
                  ? 'bg-slate-100 font-semibold text-slate-900 dark:bg-slate-800 dark:text-white'
                  : cell.inMonth
                    ? 'text-slate-800 dark:text-slate-300'
                    : 'text-slate-400 dark:text-slate-600'}"
              style={hasCollection ? `background-color: ${getAccent()}; color: white` : undefined}
            >
              {cell.day.getDate()}
            </span>
          </button>
        {/each}
      </div>
    {/key}
  </div>
</div>

<style>
  /* Stack old and new grid in the same layout cell during transitions
     so they don't push each other down and cause a height jump */
  .cal-stack {
    display: grid;
  }
  .cal-stack > * {
    grid-area: 1 / 1;
  }
</style>
