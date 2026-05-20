<script lang="ts">
  import { untrack } from 'svelte';
  import Flame from '@animated-color-icons/lucide-svelte/Flame.svelte';
  import PlusIcon from '@animated-color-icons/lucide-svelte/Plus.svelte';
  import ArrowLeft from '@animated-color-icons/lucide-svelte/ArrowLeft.svelte';
  import Trash from '@animated-color-icons/lucide-svelte/Trash.svelte';
  import Archive from '@animated-color-icons/lucide-svelte/Archive.svelte';
  import { api, type Habit } from '../lib/api';
  import { currentView, habitsStore, isLoading } from '../lib/stores';

  let habits = $state<Habit[]>([]);
  let showArchived = $state(false);
  let showAddForm = $state(false);
  let newName = $state('');
  let newIcon = $state('✅');
  let newReminderTime = $state('');
  let isSubmitting = $state(false);

  $effect(() => {
    habits = $habitsStore;
  });

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
    } catch (e) {
      console.error('Failed to toggle habit:', e);
      habits = originalHabits;
      habitsStore.set(originalHabits);
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

  fetchHabits();
</script>

<div class="mx-auto max-w-2xl">
  <div class="mb-6 flex items-center justify-between">
    <h1 class="text-2xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
      <Flame label="" size={28} />
      Habits
    </h1>
    <button
      class="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-600 text-white shadow-md transition-transform hover:scale-105 active:scale-95 dark:bg-indigo-500"
      onclick={() => showAddForm = !showAddForm}
      aria-label="Add habit"
    >
      <PlusIcon label="" size={20} />
    </button>
  </div>

  {#if showAddForm}
    <div class="mb-6 rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-slate-900">
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

  <div class="space-y-2">
    {#each habits.filter(h => !h.is_archived) as habit (habit.id)}
      <div
        class="group flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm transition-all hover:shadow-md dark:border-white/10 dark:bg-slate-900"
      >
        <button
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 transition-all"
          class:border-indigo-500={habit.today_completed}
          class:bg-indigo-500={habit.today_completed}
          class:text-white={habit.today_completed}
          class:border-slate-300={!habit.today_completed}
          class:dark:border-slate-600={!habit.today_completed}
          onclick={() => toggleComplete(habit)}
          aria-label={habit.today_completed ? 'Mark incomplete' : 'Mark complete'}
        >
          {#if habit.today_completed}
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          {:else}
            <span class="text-lg">{habit.icon}</span>
          {/if}
        </button>

        <button
          class="flex-1 text-left"
          onclick={() => openHabitDetail(habit.id)}
        >
          <div class="font-medium text-slate-800 dark:text-slate-100">{habit.name}</div>
          {#if habit.current_streak > 0}
            <div class="flex items-center gap-1 text-xs text-orange-500">
              <Flame label="" size={12} />
              {habit.current_streak} day{habit.current_streak === 1 ? '' : 's'}
            </div>
          {/if}
        </button>

        <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-slate-200"
            onclick={() => archiveHabit(habit.id)}
            title="Archive"
          >
            <Archive label="" size={16} />
          </button>
          <button
            class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 transition-colors hover:bg-red-50 hover:text-red-600 dark:text-slate-400 dark:hover:bg-red-950/30 dark:hover:text-red-400"
            onclick={() => deleteHabit(habit.id)}
            title="Delete"
          >
            <Trash label="" size={16} />
          </button>
        </div>
      </div>
    {:else}
      <div class="py-12 text-center text-slate-500 dark:text-slate-400">
        <div class="mb-2 text-4xl">🎯</div>
        <p>No habits yet.</p>
        <p class="text-sm">Create your first habit to start tracking!</p>
      </div>
    {/each}
  </div>

  {#if !showArchived && habits.some(h => h.is_archived)}
    <button
      class="mt-4 text-sm text-slate-500 underline transition-colors hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
      onclick={() => { showArchived = true; fetchHabits(); }}
    >
      Show archived habits
    </button>
  {:else if showArchived}
    <button
      class="mt-4 text-sm text-slate-500 underline transition-colors hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
      onclick={() => { showArchived = false; fetchHabits(); }}
    >
      Hide archived habits
    </button>
  {/if}
</div>
