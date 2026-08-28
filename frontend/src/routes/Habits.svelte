<script lang="ts">
  import { untrack } from 'svelte';
  import { fly, fade, scale } from 'svelte/transition';
  import Flame from '@animated-color-icons/lucide-svelte/Flame.svelte';
  import Bell from '@animated-color-icons/lucide-svelte/Bell.svelte';
  import PlusIcon from '@animated-color-icons/lucide-svelte/Plus.svelte';
  import Archive from '@animated-color-icons/lucide-svelte/Archive.svelte';
  import Trash from '@animated-color-icons/lucide-svelte/Trash.svelte';
  import { api, type Habit } from '../lib/api';
  import { currentView, habitsStore, isLoading } from '../lib/stores';
  import { currentUser } from '../lib/session';
  import { computeHeaderColor, computeCardTileBg } from '../lib/colors';

  let habits = $state<Habit[]>([]);
  let showArchived = $state(false);
  let titleFilter = $state('');
  let saveStatuses = $state<Record<string, 'success' | 'error' | null>>({});

  let showAddForm = $state(false);
  let newName = $state('');
  let newIcon = $state('✅');
  let newReminderTime = $state('');
  let isSubmitting = $state(false);

  type SortKey = 'name' | 'streak' | 'reminder';
  type SortDir = 'asc' | 'desc';
  let sortKey = $state<SortKey>('name');
  let sortDir = $state<SortDir>('asc');

  function getAccent(): string {
    return computeHeaderColor($currentUser?.default_collection_header_color);
  }

  function getAccentTint(): string {
    const isDark = typeof document !== 'undefined' && document.documentElement.classList.contains('dark');
    return computeCardTileBg(getAccent(), isDark);
  }

  async function fetchHabits() {
    isLoading.set(true);
    try {
      const res = await api.habits.list(showArchived);
      habitsStore.set(res.habits);
      habits = res.habits;
    } catch (e) {
      console.error('Failed to fetch habits:', e);
    } finally {
      isLoading.set(false);
    }
  }

  const sorted = $derived.by(() => {
    let list = [...habits];
    if (titleFilter.trim()) {
      const q = titleFilter.toLowerCase();
      list = list.filter(h => h.name.toLowerCase().includes(q));
    }
    list.sort((a, b) => {
      const dir = sortDir === 'asc' ? 1 : -1;
      if (sortKey === 'name') {
        return a.name.localeCompare(b.name) * dir;
      }
      if (sortKey === 'streak') {
        return (a.current_streak - b.current_streak) * dir;
      }
      // reminder
      if (a.reminder_time && b.reminder_time) {
        return a.reminder_time.localeCompare(b.reminder_time) * dir;
      }
      if (a.reminder_time) return -1 * dir;
      if (b.reminder_time) return 1 * dir;
      return 0;
    });
    return list;
  });

  const visible = $derived(sorted.slice(0, 100));

  $effect(() => {
    void showArchived;
    fetchHabits();
  });

  async function toggleComplete(habit: Habit) {
    const originalHabits = untrack(() => habits);
    const updated = habits.map(h =>
      h.id === habit.id ? { ...h, today_completed: !h.today_completed } : h
    );
    habits = updated;
    habitsStore.set(updated);

    try {
      if (habit.today_completed) {
        await api.habits.uncomplete(habit.id);
      } else {
        await api.habits.complete(habit.id);
      }
      saveStatuses[habit.id] = 'success';
      setTimeout(() => { if (saveStatuses[habit.id] === 'success') saveStatuses[habit.id] = null; }, 5000);
    } catch (e) {
      console.error('Failed to toggle habit:', e);
      habits = originalHabits;
      habitsStore.set(originalHabits);
      saveStatuses[habit.id] = 'error';
      setTimeout(() => { if (saveStatuses[habit.id] === 'error') saveStatuses[habit.id] = null; }, 5000);
    }
  }

  async function createHabit() {
    const name = newName.trim();
    if (!name) return;
    isSubmitting = true;
    try {
      const res = await api.habits.create({
        name,
        icon: newIcon,
        reminder_time: newReminderTime || null,
      });
      habits = [...habits, res.habit];
      habitsStore.set(habits);
      newName = '';
      newReminderTime = '';
      showAddForm = false;
    } catch (e) {
      console.error('Failed to create habit:', e);
    } finally {
      isSubmitting = false;
    }
  }

  async function archiveHabit(id: string) {
    const originalHabits = untrack(() => habits);
    habits = habits.filter(h => h.id !== id);
    habitsStore.set(habits);

    try {
      await api.habits.update(id, { is_archived: true });
    } catch (e) {
      console.error('Failed to archive habit:', e);
      habits = originalHabits;
      habitsStore.set(originalHabits);
    }
  }

  async function unarchiveHabit(id: string) {
    const originalHabits = untrack(() => habits);
    habits = habits.filter(h => h.id !== id);
    habitsStore.set(habits);

    try {
      await api.habits.update(id, { is_archived: false });
    } catch (e) {
      console.error('Failed to unarchive habit:', e);
      habits = originalHabits;
      habitsStore.set(originalHabits);
    }
  }

  async function deleteHabit(id: string) {
    if (!confirm('Delete this habit permanently?')) return;
    const originalHabits = untrack(() => habits);
    habits = habits.filter(h => h.id !== id);
    habitsStore.set(habits);

    try {
      await api.habits.delete(id);
    } catch (e) {
      console.error('Failed to delete habit:', e);
      habits = originalHabits;
      habitsStore.set(originalHabits);
    }
  }

  function openHabitDetail(id: string) {
    currentView.set({ type: 'habit_detail', id });
  }
</script>

<div class="space-y-4">
  <div class="flex items-center justify-between">
    <h2 class="flex items-center gap-2 text-2xl font-semibold dark:text-slate-100">
      <Flame label="" size={24} className="text-slate-700 dark:text-slate-300" />
      <span>Habits</span>
    </h2>
    <button
      class="grid h-10 w-10 place-items-center rounded-full border border-slate-200 bg-white text-slate-700 shadow-sm ring-1 ring-black/5 hover:bg-slate-50 transition-all dark:border-white/10 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-white/5"
      type="button"
      aria-label="Add habit"
      title="Add habit"
      onclick={() => showAddForm = !showAddForm}
    >
      <PlusIcon label="" size={20} />
    </button>
  </div>

  {#if showAddForm}
    <div class="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-slate-900" in:fly={{ y: -10, duration: 150 }} out:fade={{ duration: 100 }}>
      <div class="flex gap-2 mb-3">
        <input
          class="w-16 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-center text-xl dark:border-white/10 dark:bg-slate-800"
          placeholder="✅"
          maxlength="2"
          bind:value={newIcon}
        />
        <input
          class="flex-1 rounded-lg border border-slate-200 bg-slate-50 px-4 py-2 text-base dark:border-white/10 dark:bg-slate-800 dark:text-slate-100"
          placeholder="Habit name..."
          bind:value={newName}
          onkeydown={(e) => { if (e.key === 'Enter') createHabit(); }}
        />
      </div>
      <div class="flex items-center gap-3 mb-3">
        <label class="text-sm text-slate-600 dark:text-slate-400">Reminder time:</label>
        <input
          type="time"
          class="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1 text-sm dark:border-white/10 dark:bg-slate-800 dark:text-slate-100"
          bind:value={newReminderTime}
        />
      </div>
      <div class="flex gap-2">
        <button
          class="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600"
          onclick={createHabit}
          disabled={isSubmitting || !newName.trim()}
        >
          {isSubmitting ? 'Creating...' : 'Create'}
        </button>
        <button
          class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-white/10 dark:text-slate-300 dark:hover:bg-white/5"
          onclick={() => { showAddForm = false; newName = ''; }}
        >
          Cancel
        </button>
      </div>
    </div>
  {/if}

  <div class="flex items-center gap-2">
    <div class="flex flex-1 overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-900 dark:ring-white/10" role="tablist">
      <button
        type="button"
        role="tab"
        aria-selected={!showArchived}
        class="flex-1 px-4 py-3 text-base font-medium transition-colors {!showArchived
          ? 'text-slate-900 dark:text-white'
          : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
        onclick={() => { showArchived = false; }}
        style={!showArchived ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
      >
        Active
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={showArchived}
        class="flex-1 border-l border-black/5 px-4 py-3 text-base font-medium transition-colors dark:border-white/5 {showArchived
          ? 'text-slate-900 dark:text-white'
          : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
        onclick={() => { showArchived = true; }}
        style={showArchived ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
      >
        Inactive
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
      placeholder="Filter habits"
      bind:value={titleFilter}
    />

    <div class="ml-auto flex items-center gap-2">
      <div class="overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-900">
        <div class="flex">
          <button
            class="px-4 py-2 text-sm font-medium {sortKey === 'name'
              ? 'text-slate-900 dark:text-white'
              : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
            type="button"
            onclick={() => (sortKey = 'name')}
            style={sortKey === 'name' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          >
            Name
          </button>
          <button
            class="border-l border-black/5 px-4 py-2 text-sm font-medium {sortKey === 'streak'
              ? 'text-slate-900 dark:text-white'
              : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
            type="button"
            onclick={() => (sortKey = 'streak')}
            style={sortKey === 'streak' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          >
            Streak
          </button>
          <button
            class="border-l border-black/5 px-4 py-2 text-sm font-medium {sortKey === 'reminder'
              ? 'text-slate-900 dark:text-white'
              : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
            type="button"
            onclick={() => (sortKey = 'reminder')}
            style={sortKey === 'reminder' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          >
            Reminder
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

  {#if habits.length === 0}
    <div class="py-8 text-center text-sm text-slate-500" in:fade={{ duration: 200 }}>
      No {showArchived ? 'inactive' : 'active'} habits found.
    </div>
  {:else if visible.length === 0}
    <div class="py-8 text-center text-sm text-slate-500" in:fade={{ duration: 200 }}>
      No habits match your filter.
    </div>
  {:else}
    <div class="space-y-2">
      {#each visible as h (h.id)}
        <div class="flex w-full items-center gap-3 px-1 py-2 {h.today_completed ? 'task-faded' : ''}" in:fly={{ y: 10, duration: 200 }} out:fade={{ duration: 150 }}>
          <button
            class="grid h-8 w-8 place-items-center rounded-full border border-slate-300 bg-white transition-all duration-150 hover:scale-110 active:scale-95 dark:border-white/20 dark:bg-slate-900"
            type="button"
            aria-label={h.today_completed ? 'Mark incomplete' : 'Mark complete'}
            title={h.today_completed ? 'Completed today' : 'Mark complete'}
            style={`border-color: ${getAccent()}`}
            onclick={() => toggleComplete(h)}
          >
            {#if h.today_completed}
              <span in:scale={{ start: 0.5, duration: 150 }} class="text-sm font-semibold" style={`color: ${getAccent()}`}>✓</span>
            {/if}
          </button>

          <button class="al-icon-wrapper min-w-0 flex flex-1 items-start gap-3 text-left" type="button" onclick={() => openHabitDetail(h.id)}>
            <div class="min-w-0 flex-1">
              <div class="truncate text-lg font-medium text-slate-900 dark:text-slate-100">{h.name}</div>
              <div class="mt-0.5 flex flex-wrap items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
                {#if h.current_streak > 0}
                  <span class="flex items-center gap-1 rounded px-1.5 py-0.5" style={`background-color: ${getAccentTint()}; color: ${getAccent()}`}>
                    <Flame label="" size={12} strokeWidth={2.5} />
                    {h.current_streak} day{h.current_streak === 1 ? '' : 's'}
                  </span>
                {/if}
                {#if h.reminder_time}
                  <span class="flex items-center gap-1 rounded px-1.5 py-0.5" style={`background-color: ${getAccentTint()}; color: ${getAccent()}`}>
                    <Bell label="" size={12} strokeWidth={2.5} />
                    {h.reminder_time}
                  </span>
                {/if}
                {#if h.is_archived}
                  <span class="rounded px-1.5 py-0.5 bg-slate-200 text-slate-600 dark:bg-slate-800 dark:text-slate-400">
                    Archived
                  </span>
                {/if}
              </div>
            </div>
          </button>

          {#if saveStatuses[h.id]}
            <div
              class="h-2 w-2 rounded-full transition-opacity duration-500"
              style="background-color: {saveStatuses[h.id] === 'success' ? '#22c55e' : '#ef4444'}"
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
                onclick={() => openHabitDetail(h.id)}
              >
                ⓘ
              </button>
              {#if showArchived}
                <button
                  class="grid h-11 w-12 place-items-center border-l border-black/5 text-slate-700 hover:bg-black/5 dark:border-white/5 dark:text-slate-400 dark:hover:bg-white/5"
                  type="button"
                  aria-label="Unarchive"
                  title="Unarchive"
                  onclick={() => unarchiveHabit(h.id)}
                >
                  <Archive label="" size={18} />
                </button>
                <button
                  class="grid h-11 w-12 place-items-center border-l border-black/5 text-red-600 hover:bg-red-50 dark:border-white/5 dark:text-red-400 dark:hover:bg-red-950/30"
                  type="button"
                  aria-label="Delete"
                  title="Delete"
                  onclick={() => deleteHabit(h.id)}
                >
                  <Trash label="" size={18} />
                </button>
              {:else}
                <button
                  class="grid h-11 w-12 place-items-center border-l border-black/5 text-slate-700 hover:bg-black/5 dark:border-white/5 dark:text-slate-400 dark:hover:bg-white/5"
                  type="button"
                  aria-label="Archive"
                  title="Archive"
                  onclick={() => archiveHabit(h.id)}
                >
                  <Archive label="" size={18} />
                </button>
              {/if}
            </div>
          </div>
        </div>
      {/each}

      {#if sorted.length > visible.length}
        <div class="py-6 text-center text-sm text-slate-500 font-medium bg-slate-50/50 rounded-xl border border-slate-200/50 dark:bg-slate-900/30 dark:border-white/5">
          Showing <span class="font-bold text-slate-700 dark:text-slate-300">100</span> of <span class="font-bold text-slate-700 dark:text-slate-300">{sorted.length}</span> habits.<br/>
          Use the filter above to find more.
        </div>
      {/if}
    </div>
  {/if}
</div>
