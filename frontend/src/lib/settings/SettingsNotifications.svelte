<script lang="ts">
  import BellRing from '@animated-color-icons/lucide-svelte/BellRing.svelte';
  import Check from '@animated-color-icons/lucide-svelte/Check.svelte';
  import { api } from '../api';
  import { currentUser } from '../session';
  import { getContrastColor } from '../colors';
  import {
    checkPushSubscription,
    subscribeToPushNotifications,
    unsubscribeFromPushNotifications,
  } from '../pushManager';

  interface Props {
    accent: string;
    isBusy: boolean;
  }

  let { accent, isBusy }: Props = $props();

  let hasPushEnabled = $state(false);
  let pushBusy = $state(false);

  let ntfyEnabled = $state(false);
  let ntfyUrl = $state('');
  let ntfyTopic = $state('');
  let ntfyToken = $state('');
  let ntfyReplace = $state(false);
  let ntfyBusy = $state(false);
  let ntfyError = $state('');
  let ntfySaved = $state(false);
  let ntfyTesting = $state(false);
  let ntfyTestResult = $state('');
  let ntfyTestOk = $state(false);

  $effect(() => {
    checkPushSubscription().then((enabled) => {
      hasPushEnabled = enabled;
    });
  });

  $effect(() => {
    ntfyEnabled = Boolean($currentUser?.ntfy_enabled);
    ntfyUrl = $currentUser?.ntfy_url ?? '';
    ntfyTopic = $currentUser?.ntfy_topic ?? '';
    ntfyReplace = Boolean($currentUser?.ntfy_replace_web_push);
    ntfyToken = '';
  });

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
      await api.notifications.testPush();
    } catch (err) {
      console.error('Failed to send test push notification:', err);
    }
  }

  async function saveNtfy() {
    ntfyBusy = true;
    ntfyError = '';
    ntfyTestResult = '';
    try {
      const input: {
        ntfy_enabled: boolean;
        ntfy_url: string | null;
        ntfy_topic: string | null;
        ntfy_replace_web_push: boolean;
        ntfy_token?: string;
      } = {
        ntfy_enabled: ntfyEnabled,
        ntfy_url: ntfyUrl.trim() || null,
        ntfy_topic: ntfyTopic.trim() || null,
        ntfy_replace_web_push: ntfyReplace,
      };
      if (ntfyToken.trim()) input.ntfy_token = ntfyToken.trim();
      const res = await api.updateMe(input);
      currentUser.set(res.user);
      ntfyToken = '';
      ntfySaved = true;
      setTimeout(() => {
        ntfySaved = false;
      }, 2000);
    } catch (err) {
      ntfyError = (err as any)?.error?.message || 'Failed to save ntfy settings.';
    } finally {
      ntfyBusy = false;
    }
  }

  async function clearNtfyToken() {
    ntfyBusy = true;
    ntfyError = '';
    try {
      const res = await api.updateMe({ ntfy_token: null });
      currentUser.set(res.user);
    } catch (err) {
      ntfyError = (err as any)?.error?.message || 'Failed to remove token.';
    } finally {
      ntfyBusy = false;
    }
  }

  async function testNtfy() {
    ntfyTesting = true;
    ntfyTestResult = '';
    ntfyTestOk = false;
    try {
      await api.notifications.testNtfy();
      ntfyTestOk = true;
      ntfyTestResult = 'Test notification sent.';
    } catch (err) {
      ntfyTestOk = false;
      ntfyTestResult = (err as any)?.error?.message || 'Failed to send test notification.';
    } finally {
      ntfyTesting = false;
    }
  }
</script>

<div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
  <div class="flex items-center gap-2 text-xs uppercase text-slate-500">
    <BellRing label="" size={12} strokeWidth={2.5} />
    <span>Notifications</span>
  </div>

  <!-- Web Push -->
  <div class="mt-3 border-b border-slate-100 py-4 dark:border-white/5">
    <div class="flex items-center justify-between gap-4">
      <div>
        <div class="text-sm font-medium text-slate-900 dark:text-slate-100">Web Push</div>
        <div class="text-xs text-slate-500 dark:text-slate-400">
          Receive alerts on this device for reminders.
        </div>
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

  <!-- ntfy -->
  <div class="pt-4">
    <div class="flex items-center justify-between gap-4">
      <div>
        <div class="text-sm font-medium text-slate-900 dark:text-slate-100">ntfy</div>
        <div class="text-xs text-slate-500 dark:text-slate-400">
          Forward notifications to an ntfy server (self-hosted or ntfy.sh).
        </div>
      </div>
      <button
        type="button"
        class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none disabled:opacity-50"
        style={ntfyEnabled ? `background-color: ${accent}; color: ${getContrastColor(accent)}` : 'background-color: #cbd5e1'}
        role="switch"
        aria-checked={ntfyEnabled}
        aria-label="Toggle ntfy notifications"
        onclick={() => (ntfyEnabled = !ntfyEnabled)}
        disabled={isBusy || ntfyBusy}
      >
        <span
          class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out {ntfyEnabled ? 'translate-x-5' : 'translate-x-0'}"
        ></span>
      </button>
    </div>

    <div class="mt-4 space-y-4">
      <div>
        <label for="ntfy-url" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Server URL</label>
        <input
          id="ntfy-url"
          type="url"
          class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:ring-white/10"
          bind:value={ntfyUrl}
          placeholder="https://ntfy.sh"
        />
      </div>

      <div>
        <label for="ntfy-topic" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Topic</label>
        <input
          id="ntfy-topic"
          type="text"
          class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:ring-white/10"
          bind:value={ntfyTopic}
          placeholder="my-snipsel-topic"
        />
      </div>

      <div>
        <label for="ntfy-token" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Access Token (optional)</label>
        <input
          id="ntfy-token"
          type="password"
          class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:ring-white/10"
          bind:value={ntfyToken}
          placeholder={$currentUser?.ntfy_token_set ? '•••••••• (stored)' : 'tk_...'}
          autocomplete="off"
        />
        <div class="mt-1 flex items-center justify-between">
          <span class="text-xs text-slate-400">
            {#if $currentUser?.ntfy_token_set}Token is stored. Leave blank to keep it.{:else}Send as Bearer token.{/if}
          </span>
          {#if $currentUser?.ntfy_token_set}
            <button
              class="text-xs font-medium text-red-600 hover:underline dark:text-red-400"
              type="button"
              onclick={clearNtfyToken}
              disabled={isBusy || ntfyBusy}
            >
              Remove token
            </button>
          {/if}
        </div>
      </div>

      <div class="flex items-center justify-between gap-4">
        <div>
          <div class="text-sm font-medium text-slate-900 dark:text-slate-100">Use ntfy instead of Web Push</div>
          <div class="text-xs text-slate-500 dark:text-slate-400">
            When enabled, Web Push is skipped and only ntfy is sent.
          </div>
        </div>
        <button
          type="button"
          class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none disabled:opacity-50"
          style={ntfyReplace ? `background-color: ${accent}; color: ${getContrastColor(accent)}` : 'background-color: #cbd5e1'}
          role="switch"
          aria-checked={ntfyReplace}
          aria-label="Toggle ntfy instead of web push"
          onclick={() => (ntfyReplace = !ntfyReplace)}
          disabled={isBusy || ntfyBusy}
        >
          <span
            class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out {ntfyReplace ? 'translate-x-5' : 'translate-x-0'}"
          ></span>
        </button>
      </div>

      {#if ntfyError}
        <div class="text-xs font-medium text-red-600 dark:text-red-400">{ntfyError}</div>
      {/if}

      <div class="flex items-center gap-2">
        <button
          class="relative flex flex-1 items-center justify-center gap-2 rounded-full px-6 py-2.5 text-sm font-bold shadow-xl transition-all duration-300 hover:scale-[1.01] active:scale-[0.99] disabled:opacity-70"
          style={`background-color: ${accent}; color: ${getContrastColor(accent)}`}
          type="button"
          onclick={saveNtfy}
          disabled={isBusy || ntfyBusy || ntfySaved}
        >
          {#if ntfyBusy}
            <div class="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></div>
            <span>Saving...</span>
          {:else if ntfySaved}
            <div class="flex items-center gap-2">
              <Check label="" size={18} strokeWidth={3} />
              <span>Saved!</span>
            </div>
          {:else}
            <span>Save</span>
          {/if}
        </button>
        <button
          class="flex-1 rounded-full border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
          style={`color: ${accent}`}
          type="button"
          onclick={testNtfy}
          disabled={isBusy || ntfyTesting || !$currentUser?.ntfy_enabled}
        >
          {ntfyTesting ? 'Sending...' : 'Send Test'}
        </button>
      </div>

      {#if ntfyTestResult}
        <div class="text-xs font-medium {ntfyTestOk ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}">
          {ntfyTestResult}
        </div>
      {/if}
    </div>
  </div>
</div>
