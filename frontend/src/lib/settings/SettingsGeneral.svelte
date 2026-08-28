<script lang="ts">
  import Check from '@animated-color-icons/lucide-svelte/Check.svelte';
  import BellRing from '@animated-color-icons/lucide-svelte/BellRing.svelte';
  import { api, type Collection } from '../api';
  import { currentUser } from '../session';
  import { getContrastColor } from '../colors';
  import {
    checkPushSubscription,
    subscribeToPushNotifications,
    unsubscribeFromPushNotifications,
  } from '../pushManager';

  interface Props {
    accent: string;
    templateCollections: Collection[];
    isBusy: boolean;
  }

  let { accent, templateCollections, isBusy }: Props = $props();

  let dayTemplateId = $state($currentUser?.day_collection_template_id ?? '');
  let showDayTemplateSaved = $state(false);
  let savingDayTemplate = $state(false);
  let hasPushEnabled = $state(false);
  let pushBusy = $state(false);

  $effect(() => {
    checkPushSubscription().then((enabled) => {
      hasPushEnabled = enabled;
    });
  });

  async function saveDayTemplate() {
    savingDayTemplate = true;
    try {
      const res = await api.updateMe({
        day_collection_template_id: dayTemplateId || null,
      });
      currentUser.set(res.user);
      showDayTemplateSaved = true;
      setTimeout(() => {
        showDayTemplateSaved = false;
      }, 2000);
    } catch (err) {
      console.error('Failed to save day template:', err);
    } finally {
      savingDayTemplate = false;
    }
  }

  async function toggleCarryOver() {
    const next = !Boolean($currentUser?.carry_over_open_tasks ?? true);
    try {
      const res = await api.updateMe({ carry_over_open_tasks: next });
      currentUser.set(res.user);
    } catch (err) {
      console.error('Failed to update carry over tasks:', err);
    }
  }

  async function togglePush() {
    pushBusy = true;
    try {
      if (hasPushEnabled) {
        await unsubscribeFromPushNotifications();
        hasPushEnabled = false;
      } else {
        const success = await subscribeToPushNotifications();
        hasPushEnabled = success;
      }
    } catch (err) {
      console.error('Failed to toggle push notifications:', err);
    } finally {
      pushBusy = false;
    }
  }

  async function sendTestPush() {
    try {
      await api.push.test();
    } catch (err) {
      console.error('Failed to send test push notification:', err);
    }
  }
</script>

<div class="space-y-3">
  <!-- Day Template -->
  <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
    <div class="text-xs uppercase text-slate-500">Day template</div>
    <div class="mt-3">
      <label for="day-template-select" class="block text-sm font-medium text-slate-700 dark:text-slate-300">
        Template for new daily collections
      </label>
      <div class="mt-2 flex items-center gap-2">
        <select
          id="day-template-select"
          class="flex-1 rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:ring-white/10"
          bind:value={dayTemplateId}
        >
          <option value="">No template</option>
          {#each templateCollections as c (c.id)}
            <option value={c.id}>
              {c.icon} {c.title}
            </option>
          {/each}
        </select>
        <button
          class="relative flex items-center justify-center gap-2 rounded-full px-6 py-2.5 text-sm font-bold shadow-xl transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-70"
          style={`background-color: ${accent}; color: ${getContrastColor(accent)}`}
          type="button"
          onclick={saveDayTemplate}
          disabled={isBusy || savingDayTemplate || showDayTemplateSaved}
        >
          {#if savingDayTemplate}
            <div class="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></div>
            <span>Saving...</span>
          {:else if showDayTemplateSaved}
            <div class="flex items-center gap-2">
              <Check label="" size={18} strokeWidth={3} />
              <span>Saved!</span>
            </div>
          {:else}
            <span>Save</span>
          {/if}
        </button>
      </div>
    </div>
  </div>

  <!-- Tasks -->
  <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
    <div class="text-xs uppercase text-slate-500">Tasks</div>
    <div class="mt-3 flex items-center justify-between gap-4">
      <div>
        <div class="text-sm font-medium text-slate-900 dark:text-slate-100">Carry over open tasks</div>
        <div class="text-xs text-slate-500 dark:text-slate-400">Move unfinished tasks from the last 30 days into today.</div>
      </div>
      <button
        type="button"
        class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none disabled:opacity-50"
        style={Boolean($currentUser?.carry_over_open_tasks ?? true) ? `background-color: ${accent}; color: ${getContrastColor(accent)}` : 'background-color: #cbd5e1'}
        role="switch"
        aria-checked={Boolean($currentUser?.carry_over_open_tasks ?? true)}
        aria-label="Toggle carry over tasks"
        onclick={toggleCarryOver}
        disabled={isBusy}
      >
        <span
          class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out {Boolean($currentUser?.carry_over_open_tasks ?? true) ? 'translate-x-5' : 'translate-x-0'}"
        ></span>
      </button>
    </div>
  </div>

  <!-- Notifications -->
  <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
    <div class="text-xs uppercase text-slate-500">Notifications</div>
    <div class="mt-3 flex items-center justify-between gap-4">
      <div>
        <div class="text-sm font-medium text-slate-900 dark:text-slate-100">Push Notifications</div>
        <div class="text-xs text-slate-500 dark:text-slate-400">Receive alerts on this device for reminders.</div>
      </div>
      <button
        type="button"
        class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none disabled:opacity-50"
        style={hasPushEnabled ? `background-color: ${accent}; color: ${getContrastColor(accent)}` : 'background-color: #cbd5e1'}
        role="switch"
        aria-checked={hasPushEnabled}
        aria-label="Toggle push notifications"
        onclick={togglePush}
        disabled={isBusy || pushBusy}
      >
        <span
          class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out {hasPushEnabled ? 'translate-x-5' : 'translate-x-0'}"
        ></span>
      </button>
    </div>

    {#if hasPushEnabled}
      <div class="mt-3 flex items-center justify-end">
        <button
          class="al-icon-wrapper flex items-center gap-1.5 text-xs font-medium text-slate-500 transition-colors hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
          type="button"
          onclick={sendTestPush}
          disabled={isBusy || pushBusy}
        >
          <BellRing label="" size={14} />
          Send Test Notification
        </button>
      </div>
    {/if}
  </div>
</div>
