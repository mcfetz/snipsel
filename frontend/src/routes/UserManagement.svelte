<script lang="ts">
  import { onMount } from 'svelte';
  import ArrowLeft from '@animated-color-icons/lucide-svelte/ArrowLeft.svelte';
  import Users from '@animated-color-icons/lucide-svelte/Users.svelte';
  import Plus from '@animated-color-icons/lucide-svelte/Plus.svelte';
  import Trash2 from '@animated-color-icons/lucide-svelte/Trash2.svelte';
  import Shield from '@animated-color-icons/lucide-svelte/Shield.svelte';
  import User from '@animated-color-icons/lucide-svelte/User.svelte';
  import { api } from '../lib/api';
  import { currentView } from '../lib/stores';
  import { currentUser } from '../lib/session';

  type AdminUser = {
    id: string;
    username: string;
    email: string;
    is_admin: boolean;
    is_active: boolean;
    created_at: string;
    last_login: string | null;
  };

  let users = $state<AdminUser[]>([]);
  let isLoading = $state(true);
  let error = $state('');
  let isCreating = $state(false);
  let isSubmitting = $state(false);

  let newUsername = $state('');
  let newEmail = $state('');
  let newPassword = $state('');
  let newIsAdmin = $state(false);
  let createError = $state('');

  let deleteConfirmUser: AdminUser | null = $state(null);

  onMount(async () => {
    if (!$currentUser?.is_admin) {
      currentView.set({ type: 'settings' });
      return;
    }
    await loadUsers();
  });

  async function loadUsers() {
    isLoading = true;
    error = '';
    try {
      const res = await api.admin.listUsers();
      users = res.users;
    } catch (e: any) {
      error = e.error?.message || 'Failed to load users';
    } finally {
      isLoading = false;
    }
  }

  async function createUser() {
    if (!newUsername || !newEmail || !newPassword) {
      createError = 'All fields are required';
      return;
    }
    if (newPassword.length < 8) {
      createError = 'Password must be at least 8 characters';
      return;
    }

    isSubmitting = true;
    createError = '';
    try {
      await api.admin.createUser({
        username: newUsername,
        email: newEmail,
        password: newPassword,
        is_admin: newIsAdmin,
      });
      await loadUsers();
      isCreating = false;
      newUsername = '';
      newEmail = '';
      newPassword = '';
      newIsAdmin = false;
    } catch (e: any) {
      createError = e.error?.message || 'Failed to create user';
    } finally {
      isSubmitting = false;
    }
  }

  async function deleteUser(userId: string) {
    try {
      await api.admin.deleteUser(userId);
      await loadUsers();
      deleteConfirmUser = null;
    } catch (e: any) {
      alert(e.error?.message || 'Failed to delete user');
    }
  }

  async function toggleAdmin(user: AdminUser) {
    try {
      await api.admin.updateUser(user.id, { is_admin: !user.is_admin });
      await loadUsers();
    } catch (e: any) {
      alert(e.error?.message || 'Failed to update user');
    }
  }

  async function toggleActive(user: AdminUser) {
    try {
      await api.admin.updateUser(user.id, { is_active: !user.is_active });
      await loadUsers();
    } catch (e: any) {
      alert(e.error?.message || 'Failed to update user');
    }
  }

  function goBack() {
    currentView.set({ type: 'settings' });
  }
</script>

<div class="mx-auto max-w-3xl px-4">
  <div class="mb-6 flex items-center gap-3">
    <button
      class="al-icon-wrapper grid h-10 w-10 shrink-0 place-items-center rounded-full bg-slate-100 text-slate-600 transition-colors hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700"
      onclick={goBack}
      type="button"
      aria-label="Back to settings"
    >
      <ArrowLeft label="" size={20} />
    </button>
    <div class="flex items-center gap-2">
      <Users label="" size={24} className="text-indigo-600 dark:text-indigo-400" />
      <h1 class="text-2xl font-bold text-slate-900 dark:text-slate-100">User Management</h1>
    </div>
  </div>

  {#if error}
    <div class="mb-4 rounded-lg bg-red-50 p-4 text-red-700 dark:bg-red-950/20 dark:text-red-400">
      {error}
    </div>
  {/if}

  <div class="mb-6 flex items-center justify-between">
    <div class="text-sm text-slate-500 dark:text-slate-400">
      {users.length} user{users.length !== 1 ? 's' : ''}
    </div>
    <button
      class="flex items-center gap-2 rounded-full bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50"
      onclick={() => { isCreating = true; createError = ''; }}
      disabled={isCreating}
      type="button"
    >
      <Plus label="" size={16} />
      Create User
    </button>
  </div>

  {#if isCreating}
    <div class="mb-6 rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm dark:border-white/10 dark:bg-slate-900/80">
      <h2 class="mb-4 text-lg font-semibold text-slate-900 dark:text-slate-100">Create New User</h2>
      
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300">Username</label>
          <input
            type="text"
            class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none dark:border-white/10 dark:bg-slate-800"
            bind:value={newUsername}
            placeholder="johndoe"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300">Email</label>
          <input
            type="email"
            class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none dark:border-white/10 dark:bg-slate-800"
            bind:value={newEmail}
            placeholder="john@example.com"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300">Password</label>
          <input
            type="password"
            class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none dark:border-white/10 dark:bg-slate-800"
            bind:value={newPassword}
            placeholder="At least 8 characters"
          />
        </div>

        <label class="flex items-center gap-2">
          <input
            type="checkbox"
            class="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
            bind:checked={newIsAdmin}
          />
          <span class="text-sm text-slate-700 dark:text-slate-300">Admin user</span>
        </label>

        {#if createError}
          <div class="text-sm text-red-600 dark:text-red-400">{createError}</div>
        {/if}

        <div class="flex gap-2">
          <button
            class="flex-1 rounded-full bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
            onclick={createUser}
            disabled={isSubmitting}
            type="button"
          >
            Create
          </button>
          <button
            class="flex-1 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-white/10 dark:bg-slate-800 dark:text-slate-300"
            onclick={() => { isCreating = false; createError = ''; }}
            type="button"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  {/if}

  {#if isLoading}
    <div class="py-8 text-center text-slate-500 dark:text-slate-400">Loading users...</div>
  {:else if users.length === 0}
    <div class="py-8 text-center text-slate-500 dark:text-slate-400">No users found</div>
  {:else}
    <div class="space-y-3">
      {#each users as user (user.id)}
        <div class="flex items-center gap-3 rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm dark:border-white/10 dark:bg-slate-900/80">
          <div class="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-slate-100 dark:bg-slate-800">
            {#if user.is_admin}
              <Shield label="" size={20} className="text-indigo-600 dark:text-indigo-400" />
            {:else}
              <User label="" size={20} className="text-slate-400" />
            {/if}
          </div>

          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <span class="font-medium text-slate-900 dark:text-slate-100">{user.username}</span>
              {#if user.is_admin}
                <span class="rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300">Admin</span>
              {/if}
              {#if !user.is_active}
                <span class="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700 dark:bg-red-900/30 dark:text-red-300">Inactive</span>
              {/if}
            </div>
            <div class="text-sm text-slate-500 dark:text-slate-400">{user.email}</div>
          </div>

          <div class="flex items-center gap-2">
            {#if user.id !== $currentUser?.id}
              <button
                class="rounded-lg px-3 py-1.5 text-xs font-medium transition-colors {user.is_admin ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'}"
                onclick={() => toggleAdmin(user)}
                type="button"
                title={user.is_admin ? 'Remove admin' : 'Make admin'}
              >
                {user.is_admin ? 'Admin' : 'User'}
              </button>

              <button
                class="rounded-lg px-3 py-1.5 text-xs font-medium transition-colors {user.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'}"
                onclick={() => toggleActive(user)}
                type="button"
              >
                {user.is_active ? 'Active' : 'Inactive'}
              </button>

              <button
                class="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/20"
                onclick={() => deleteConfirmUser = user}
                type="button"
                title="Delete user"
              >
                <Trash2 label="" size={16} />
              </button>
            {:else}
              <span class="text-xs text-slate-400 dark:text-slate-500">You</span>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

{#if deleteConfirmUser}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
    <div class="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl dark:bg-slate-900">
      <h3 class="mb-2 text-lg font-semibold text-slate-900 dark:text-slate-100">Delete User?</h3>
      <p class="mb-4 text-sm text-slate-600 dark:text-slate-400">
        Are you sure you want to delete <strong>{deleteConfirmUser.username}</strong>? This action cannot be undone.
      </p>
      <div class="flex gap-2">
        <button
          class="flex-1 rounded-full bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700"
          onclick={() => deleteUser(deleteConfirmUser!.id)}
          type="button"
        >
          Delete
        </button>
        <button
          class="flex-1 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-white/10 dark:bg-slate-800 dark:text-slate-300"
          onclick={() => deleteConfirmUser = null}
          type="button"
        >
          Cancel
        </button>
      </div>
    </div>
  </div>
{/if}
