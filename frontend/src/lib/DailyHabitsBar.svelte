<script lang="ts">
  import { fly, fade, scale } from 'svelte/transition';
  import Flame from '@animated-color-icons/lucide-svelte/Flame.svelte';
  import ChevronLeft from '@animated-color-icons/lucide-svelte/ChevronLeft.svelte';
  import ChevronRight from '@animated-color-icons/lucide-svelte/ChevronRight.svelte';
  import { api, type Habit } from './api';
  import { isLightColor } from './colors';
  import { currentView } from './stores';

  interface Props {
    habits: Habit[];
    habitsLoaded: boolean;
    headerColor: string;
    day?: string | null;
    onToggleHabit?: (habit: Habit) => Promise<void>;
  }

  let {
    habits = $bindable([]),
    habitsLoaded,
    headerColor,
    day,
    onToggleHabit,
  }: Props = $props();

  let habitsScrollRef: HTMLDivElement | null = $state(null);
  let habitsCanScrollLeft = $state(false);
  let habitsCanScrollRight = $state(false);

  let openDailyHabits = $derived(habits.filter((h) => !h.today_completed));
  let completedDailyHabits = $derived(habits.filter((h) => h.today_completed));

  async function handleToggle(habit: Habit) {
    if (onToggleHabit) {
      await onToggleHabit(habit);
      return;
    }

    const original = habits.map((h) => ({ ...h }));
    habits = habits.map((h) =>
      h.id === habit.id ? { ...h, today_completed: !h.today_completed } : h
    );

    try {
      if (habit.today_completed) {
        await api.habits.uncomplete(habit.id, day ?? undefined);
      } else {
        await api.habits.complete(habit.id, day ?? undefined);
      }
    } catch (err) {
      console.error('Failed to toggle habit:', err);
      habits = original;
    }
  }

  function checkScroll() {
    const el = habitsScrollRef;
    if (!el) return;
    habitsCanScrollLeft = el.scrollLeft > 0;
    habitsCanScrollRight = el.scrollLeft < el.scrollWidth - el.clientWidth - 1;
  }
</script>

{#if !habitsLoaded}
  <div class="mt-2 animate-pulse" in:fade={{ duration: 150 }}>
    <div class="mb-1.5 flex items-center gap-2 text-slate-400 opacity-60">
      <Flame label="" size={14} strokeWidth={2.5} />
      <span class="text-[10px] font-bold uppercase tracking-wider">Habits</span>
    </div>
    <div class="flex items-center gap-2 overflow-hidden py-0.5">
      <div class="h-8 w-24 rounded-full bg-slate-200/60 dark:bg-slate-800/60"></div>
      <div class="h-8 w-28 rounded-full bg-slate-200/60 dark:bg-slate-800/60"></div>
      <div class="h-8 w-20 rounded-full bg-slate-200/60 dark:bg-slate-800/60"></div>
    </div>
  </div>
{:else if habits.length > 0}
  <div class="mt-2">
    <div class="mb-1.5 flex items-center gap-2 text-slate-500 dark:text-slate-400">
      <Flame label="" size={14} strokeWidth={2.5} className="opacity-80" />
      <span class="text-[10px] font-bold uppercase tracking-wider opacity-60">Habits</span>
    </div>
    <div class="flex items-center gap-1">
      {#if habitsCanScrollLeft}
        <button
          type="button"
          class="grid h-7 w-7 shrink-0 place-items-center rounded-full border border-slate-200/80 bg-white/80 text-slate-500 shadow-sm backdrop-blur-md hover:bg-white dark:border-white/10 dark:bg-slate-900/80 dark:text-slate-400"
          aria-label="Scroll habits left"
          onclick={() => habitsScrollRef?.scrollBy({ left: -200, behavior: 'smooth' })}
        >
          <ChevronLeft label="" size={16} strokeWidth={2.5} />
        </button>
      {/if}
      <div
        bind:this={habitsScrollRef}
        class="flex flex-1 gap-2 overflow-x-auto scrollbar-hidden"
        style="touch-action: pan-x; overscroll-behavior-x: contain; -webkit-overflow-scrolling: touch;"
        onscroll={checkScroll}
        ontouchstart={(e) => e.stopPropagation()}
        ontouchmove={(e) => e.stopPropagation()}
        ontouchend={(e) => e.stopPropagation()}
        role="region"
        aria-label="Daily habits list"
      >
        {#each openDailyHabits as habit (habit.id)}
          <button
            class="group flex shrink-0 items-center gap-2 rounded-full border border-slate-200/80 bg-white/80 px-3 py-2 shadow-sm ring-1 ring-black/5 backdrop-blur-md transition-all duration-200 hover:scale-[1.03] hover:shadow-md active:scale-[0.97] dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/5"
            type="button"
            onclick={(e) => {
              e.stopPropagation();
              handleToggle(habit);
            }}
            in:fly={{ y: -10, duration: 200 }}
            out:fade={{ duration: 150 }}
          >
            <span class="text-2xl leading-none">{habit.icon}</span>
            <span class="max-w-[8rem] truncate text-sm font-medium text-slate-800 dark:text-slate-200">{habit.name}</span>
            {#if habit.current_streak > 0}
              <span
                class="flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-[10px] font-bold leading-none"
                style={`background-color: ${headerColor}20; color: ${headerColor}`}
              >
                {habit.current_streak}d
              </span>
            {/if}
            <span
              class="ml-0.5 opacity-0 transition-opacity group-hover:opacity-100"
              onclick={(e) => {
                e.stopPropagation();
                currentView.set({ type: 'habit_detail', id: habit.id });
              }}
              role="button"
              tabindex="0"
              onkeydown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.stopPropagation();
                  currentView.set({ type: 'habit_detail', id: habit.id });
                }
              }}
              title="View details"
              aria-label={`View details for ${habit.name}`}
            >
              <ChevronRight label="" size={12} strokeWidth={2.5} className="text-slate-400 dark:text-slate-500" />
            </span>
          </button>
        {/each}

        {#each completedDailyHabits as habit (habit.id)}
          <button
            class="group relative flex shrink-0 items-center rounded-full border border-slate-200/60 bg-white/50 px-2.5 py-1.5 shadow-sm ring-1 ring-black/5 backdrop-blur-md transition-all duration-200 hover:opacity-80 hover:shadow-md active:scale-[0.97] dark:border-white/5 dark:bg-slate-900/50 dark:ring-white/5"
            type="button"
            onclick={(e) => {
              e.stopPropagation();
              handleToggle(habit);
            }}
            in:fly={{ y: 10, duration: 200 }}
            out:fade={{ duration: 150 }}
          >
            <span class="text-xl leading-none opacity-50">{habit.icon}</span>
            <span
              class="absolute right-0 top-0 flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-bold shadow-sm"
              style={`background-color: ${headerColor}; color: ${isLightColor(headerColor) ? '#1e293b' : 'white'}`}
              in:scale={{ start: 0.5, duration: 150 }}
            >
              ✓
            </span>
            <span
              class="ml-0.5 opacity-0 transition-opacity group-hover:opacity-100"
              onclick={(e) => {
                e.stopPropagation();
                currentView.set({ type: 'habit_detail', id: habit.id });
              }}
              role="button"
              tabindex="0"
              onkeydown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.stopPropagation();
                  currentView.set({ type: 'habit_detail', id: habit.id });
                }
              }}
              title="View details"
              aria-label={`View details for ${habit.name}`}
            >
              <ChevronRight label="" size={12} strokeWidth={2.5} className="text-slate-400 dark:text-slate-500" />
            </span>
          </button>
        {/each}
      </div>
      {#if habitsCanScrollRight}
        <button
          type="button"
          class="grid h-7 w-7 shrink-0 place-items-center rounded-full border border-slate-200/80 bg-white/80 text-slate-500 shadow-sm backdrop-blur-md hover:bg-white dark:border-white/10 dark:bg-slate-900/80 dark:text-slate-400"
          aria-label="Scroll habits right"
          onclick={() => habitsScrollRef?.scrollBy({ left: 200, behavior: 'smooth' })}
        >
          <ChevronRight label="" size={16} strokeWidth={2.5} />
        </button>
      {/if}
    </div>
  </div>
{/if}
