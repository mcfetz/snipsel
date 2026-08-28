<script lang="ts">
  import List from '@animated-color-icons/lucide-svelte/List.svelte';
  import FileText from '@animated-color-icons/lucide-svelte/FileText.svelte';
  import SquareCheck from '@animated-color-icons/lucide-svelte/SquareCheck.svelte';
  import Paperclip from '@animated-color-icons/lucide-svelte/Paperclip.svelte';
  import Check from '@animated-color-icons/lucide-svelte/Check.svelte';
  import { api, type UserStats } from '../api';
  import { currentUser } from '../session';
  import { getContrastColor } from '../colors';

  interface Props {
    accent: string;
    userStats: UserStats | null;
    isBusy: boolean;
    onLogout: () => void;
  }

  let { accent, userStats, isBusy, onLogout }: Props = $props();

  let showAccountForm = $state(false);
  let newEmail = $state('');
  let newPassword = $state('');
  let currentPasswordConfirm = $state('');
  let accountUpdateError = $state('');
  let accountUpdateSuccess = $state('');
  let showAccountSaved = $state(false);
  let updatingAccount = $state(false);

  async function handleUpdateAccount() {
    if (!newEmail && !newPassword) {
      accountUpdateError = 'Please provide a new email or password to update.';
      return;
    }
    if (!currentPasswordConfirm) {
      accountUpdateError = 'Please confirm your current password.';
      return;
    }

    updatingAccount = true;
    accountUpdateError = '';
    accountUpdateSuccess = '';

    try {
      const res = await api.updateAccount({
        email: newEmail || undefined,
        password: newPassword || undefined,
        current_password: currentPasswordConfirm,
      });
      currentUser.set(res.user);
      accountUpdateSuccess = 'Account updated successfully.';
      showAccountSaved = true;
      setTimeout(() => {
        showAccountSaved = false;
        showAccountForm = false;
      }, 2000);
      newEmail = '';
      newPassword = '';
      currentPasswordConfirm = '';
    } catch (err: any) {
      accountUpdateError = err?.message || 'Failed to update account.';
    } finally {
      updatingAccount = false;
    }
  }
</script>

<div class="space-y-3">
  <!-- Account -->
  <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
    <div class="text-xs uppercase text-slate-500">Account</div>
    <div class="mt-3 flex items-center justify-between gap-4">
      <div class="min-w-0 flex-1">
        <div class="truncate text-lg font-medium text-slate-900 dark:text-slate-100">{$currentUser?.username}</div>
        <div class="truncate text-sm text-slate-500 dark:text-slate-400">{$currentUser?.email}</div>
      </div>
      <div class="flex gap-2">
        <button
          class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
          style={`color: ${accent}`}
          type="button"
          onclick={() => {
            showAccountForm = !showAccountForm;
            accountUpdateError = '';
            accountUpdateSuccess = '';
          }}
          disabled={isBusy || updatingAccount}
        >
          {showAccountForm ? 'Cancel' : 'Edit'}
        </button>
        <button
          class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-red-600 shadow-sm ring-1 ring-black/5 hover:bg-red-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:text-red-400 dark:hover:bg-red-950/30"
          type="button"
          onclick={onLogout}
          disabled={isBusy || updatingAccount}
        >
          Logout
        </button>
      </div>
    </div>

    {#if showAccountForm}
      <div class="mt-4 space-y-4 border-t border-slate-100 pt-4 dark:border-white/5">
        <div>
          <label for="new-email" class="block text-sm font-medium text-slate-700 dark:text-slate-300">
            New Email Address (optional)
          </label>
          <input
            id="new-email"
            type="email"
            class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:ring-white/10"
            bind:value={newEmail}
            placeholder="new.email@example.com"
          />
        </div>
        <div>
          <label for="new-password" class="block text-sm font-medium text-slate-700 dark:text-slate-300">
            New Password (optional, min 4 chars)
          </label>
          <input
            id="new-password"
            type="password"
            class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:ring-white/10"
            bind:value={newPassword}
            placeholder="••••••••"
          />
        </div>
        <div class="rounded-lg bg-slate-50 p-3 dark:bg-white/5">
          <label for="account-password-confirm" class="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Confirm Current Password to save
          </label>
          <input
            id="account-password-confirm"
            type="password"
            class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:ring-white/10"
            bind:value={currentPasswordConfirm}
            placeholder="Your current password"
          />
        </div>

        {#if accountUpdateError}
          <div class="text-xs font-medium text-red-600 dark:text-red-400">{accountUpdateError}</div>
        {/if}
        {#if accountUpdateSuccess}
          <div class="text-xs font-medium text-green-600 dark:text-green-400">{accountUpdateSuccess}</div>
        {/if}

        <button
          class="relative flex w-full items-center justify-center gap-2 rounded-full px-6 py-2.5 text-sm font-bold shadow-xl transition-all duration-300 hover:scale-[1.01] active:scale-[0.99] disabled:opacity-70"
          style={`background-color: ${accent}; color: ${getContrastColor(accent)}`}
          type="button"
          onclick={handleUpdateAccount}
          disabled={updatingAccount || (!newEmail && !newPassword) || !currentPasswordConfirm || showAccountSaved}
        >
          {#if updatingAccount}
            <div class="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></div>
            <span>Saving...</span>
          {:else if showAccountSaved}
            <div class="flex items-center gap-2">
              <Check label="" size={18} strokeWidth={3} />
              <span>Saved!</span>
            </div>
          {:else}
            <span>Save Account Changes</span>
          {/if}
        </button>
      </div>
    {/if}
  </div>

  <!-- Your Content Stats -->
  <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
    <div class="text-xs uppercase text-slate-500">Your Content</div>
    <div class="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
      {#each [
        { label: 'Collections', type: 'collections', value: userStats?.collections },
        { label: 'Snipsels', type: 'snipsels', value: userStats?.snipsels },
        { label: 'Tasks done', type: 'tasks', value: userStats?.completed_tasks },
        { label: 'Attachments', type: 'attachments', value: userStats?.attachments },
      ] as stat}
        <div class="flex flex-col items-center gap-1 rounded-lg bg-slate-50 px-3 py-3 dark:bg-white/5">
          <div class="mb-1 text-slate-500 dark:text-slate-400">
            {#if stat.type === 'collections'}
              <List label="" size={20} />
            {:else if stat.type === 'snipsels'}
              <FileText label="" size={20} />
            {:else if stat.type === 'tasks'}
              <SquareCheck label="" size={20} />
            {:else if stat.type === 'attachments'}
              <Paperclip label="" size={20} />
            {/if}
          </div>
          <span class="text-2xl font-bold tabular-nums" style={`color: ${accent}`}>
            {stat.value !== undefined ? stat.value.toLocaleString() : '–'}
          </span>
          <span class="text-center text-xs text-slate-500 dark:text-slate-400">{stat.label}</span>
        </div>
      {/each}
    </div>
  </div>
</div>
