<script lang="ts">
  import { untrack } from 'svelte';
  import { fade } from 'svelte/transition';
  import ArrowLeft from '@animated-color-icons/lucide-svelte/ArrowLeft.svelte';
  import Flame from '@animated-color-icons/lucide-svelte/Flame.svelte';
  import Trash from '@animated-color-icons/lucide-svelte/Trash.svelte';
  import { api, type Habit, type HabitStats } from '../lib/api';
  import { currentView, isLoading } from '../lib/stores';

  let { habitId }: { habitId: string } = $props();

  let habit = $state<Habit | null>(null);
  let stats = $state<HabitStats | null>(null);
  let isEditing = $state(false);
  let editName = $state('');
  let editIcon = $state('');
  let editReminderTime = $state('');

  async function fetchData() {
    isLoading.set(true);
    try {
      const [habitRes, statsRes] = await Promise.all([
        api.habits.get(habitId),
        api.habits.stats(),
      ]);
      habit = habitRes.habit;
      const found = statsRes.habits.find(h => h.id === habitId);
      if (found) stats = found;
      editName = habit?.name || '';
      editIcon = habit?.icon || '✅';
      editReminderTime = habit?.reminder_time || '';
    } catch (e) {
      console.error('Failed to fetch habit:', e);
    } finally {
      isLoading.set(false);
    }
  }

  async function toggleComplete() {
    if (!habit) return;
    const original = untrack(() => habit!);
    habit = { ...habit, today_completed: !habit.today_completed };

    try {
      if (original.today_completed) {
        await api.habits.uncomplete(habitId);
      } else {
        await api.habits.complete(habitId);
      }
      fetchData();
    } catch (e) {
      console.error('Failed to toggle habit:', e);
      habit = original;
    }
  }

  async function saveEdit() {
    if (!habit) return;
    const name = editName.trim();
    if (!name) return;

    try {
      const res = await api.habits.update(habitId, {
        name,
        icon: editIcon,
        reminder_time: editReminderTime || null,
      });
      habit = res.habit;
      isEditing = false;
    } catch (e) {
      console.error('Failed to update habit:', e);
    }
  }

  async function deleteHabit() {
    if (!confirm('Delete this habit permanently?')) return;
    try {
      await api.habits.delete(habitId);
      currentView.set({ type: 'habits' });
    } catch (e) {
      console.error('Failed to delete habit:', e);
    }
  }

  function goBack() {
    currentView.set({ type: 'habits' });
  }

  function getDaysInRange(from: string, to: string): string[] {
    const days: string[] = [];
    const start = new Date(from + 'T00:00:00');
    const end = new Date(to + 'T00:00:00');
    for (let d = new Date(end); d >= start; d.setDate(d.getDate() - 1)) {
      days.push(d.toISOString().slice(0, 10));
    }
    return days;
  }

  function getHeatmapDays(): Array<{ date: string; completed: boolean }> {
    if (!stats) return [];
    const to = new Date().toISOString().slice(0, 10);
    const from = new Date(Date.now() - 90 * 86400000).toISOString().slice(0, 10);
    const days = getDaysInRange(from, to);
    const completionSet = new Set(stats.completions);
    return days.map(date => ({
      date,
      completed: completionSet.has(date),
    }));
  }

  fetchData();
</script>

<div class="mx-auto max-w-2xl">
  <div class="mb-6 flex items-center gap-3">
    <button
      class="flex h-10 w-10 items-center justify-center rounded-full text-slate-600 transition-colors hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-white/5"
      onclick={goBack}
      aria-label="Back"
    >
      <ArrowLeft label="" size={20} />
    </button>
    <h1 class="text-xl font-bold text-slate-800 dark:text-slate-100">Habit Details</h1>
  </div>

  {#if habit}
    <div class="mb-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-white/10 dark:bg-slate-900">
      {#if isEditing}
        <div class="space-y-3">
          <div class="flex gap-2">
            <input
              class="w-16 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-center text-xl dark:border-white/10 dark:bg-slate-800"
              maxlength="2"
              bind:value={editIcon}
            />
            <input
              class="flex-1 rounded-lg border border-slate-200 bg-slate-50 px-4 py-2 text-base dark:border-white/10 dark:bg-slate-800 dark:text-slate-100"
              bind:value={editName}
            />
          </div>
          <div class="flex items-center gap-3">
            <label class="text-sm text-slate-600 dark:text-slate-400">Reminder:</label>
            <input
              type="time"
              class="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1 text-sm dark:border-white/10 dark:bg-slate-800 dark:text-slate-100"
              bind:value={editReminderTime}
            />
          </div>
          <div class="flex gap-2">
            <button
              class="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600"
              onclick={saveEdit}
            >
              Save
            </button>
            <button
              class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-white/10 dark:text-slate-300 dark:hover:bg-white/5"
              onclick={() => { isEditing = false; editName = habit?.name || ''; editIcon = habit?.icon || '✅'; editReminderTime = habit?.reminder_time || ''; }}
            >
              Cancel
            </button>
          </div>
        </div>
      {:else}
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <span class="text-3xl">{habit.icon}</span>
            <div>
              <h2 class="text-lg font-semibold text-slate-800 dark:text-slate-100">{habit.name}</h2>
              {#if habit.reminder_time}
                <p class="text-sm text-slate-500 dark:text-slate-400">Reminder at {habit.reminder_time}</p>
              {/if}
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button
              class="rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-600 transition-colors hover:bg-slate-50 dark:border-white/10 dark:text-slate-300 dark:hover:bg-white/5"
              onclick={() => isEditing = true}
            >
              Edit
            </button>
            <button
              class="rounded-lg p-2 text-slate-500 transition-colors hover:bg-red-50 hover:text-red-600 dark:text-slate-400 dark:hover:bg-red-950/30 dark:hover:text-red-400"
              onclick={deleteHabit}
              title="Delete"
            >
              <Trash label="" size={18} />
            </button>
          </div>
        </div>

        <div class="mt-4 flex items-center justify-between">
          <button
            class="flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors"
            class:bg-indigo-600={habit.today_completed}
            class:text-white={habit.today_completed}
            class:bg-slate-100={!habit.today_completed}
            class:text-slate-700={!habit.today_completed}
            class:dark:bg-indigo-500={habit.today_completed}
            class:dark:bg-slate-800={!habit.today_completed}
            class:dark:text-slate-200={!habit.today_completed}
            onclick={toggleComplete}
          >
            {#if habit.today_completed}
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              Completed today
            {:else}
              Mark as done
            {/if}
          </button>
        </div>
      {/if}
    </div>

    {#if stats}
      <div class="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div class="rounded-xl border border-slate-200 bg-white p-4 text-center shadow-sm dark:border-white/10 dark:bg-slate-900">
          <div class="text-2xl font-bold text-indigo-600 dark:text-indigo-400">{stats.current_streak}</div>
          <div class="text-xs text-slate-500 dark:text-slate-400">Current Streak</div>
        </div>
        <div class="rounded-xl border border-slate-200 bg-white p-4 text-center shadow-sm dark:border-white/10 dark:bg-slate-900">
          <div class="text-2xl font-bold text-indigo-600 dark:text-indigo-400">{stats.longest_streak}</div>
          <div class="text-xs text-slate-500 dark:text-slate-400">Best Streak</div>
        </div>
        <div class="rounded-xl border border-slate-200 bg-white p-4 text-center shadow-sm dark:border-white/10 dark:bg-slate-900">
          <div class="text-2xl font-bold text-indigo-600 dark:text-indigo-400">{Math.round(stats.completion_rate * 100)}%</div>
          <div class="text-xs text-slate-500 dark:text-slate-400">Completion Rate</div>
        </div>
        <div class="rounded-xl border border-slate-200 bg-white p-4 text-center shadow-sm dark:border-white/10 dark:bg-slate-900">
          <div class="text-2xl font-bold text-indigo-600 dark:text-indigo-400">{stats.completed_days}</div>
          <div class="text-xs text-slate-500 dark:text-slate-400">Total Done</div>
        </div>
      </div>

      <div class="mb-6 rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-slate-900">
        <h3 class="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-300">Last 90 Days</h3>
        <div class="grid grid-cols-7 gap-1">
          {#each getHeatmapDays() as day}
            <div
              class="aspect-square rounded-sm"
              class:bg-green-500={day.completed}
              class:bg-slate-200={!day.completed}
              class:dark:bg-green-600={day.completed}
              class:dark:bg-slate-700={!day.completed}
              title="{day.date}: {day.completed ? 'Completed' : 'Not completed'}"
            ></div>
          {/each}
        </div>
      </div>
    {/if}
  {:else}
    <div class="py-12 text-center text-slate-500 dark:text-slate-400">
      Loading habit...
    </div>
  {/if}
</div>
