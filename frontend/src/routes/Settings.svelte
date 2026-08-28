<script lang="ts">
  import SettingsIcon from '@animated-color-icons/lucide-svelte/Settings.svelte';
  import ChevronRight from '@animated-color-icons/lucide-svelte/ChevronRight.svelte';
  import Users from '@animated-color-icons/lucide-svelte/Users.svelte';
  import { api, type Collection, type UserStats } from '../lib/api';
  import { currentUser } from '../lib/session';
  import { currentView } from '../lib/stores';
  import { computeHeaderColor, computeCardTileBg } from '../lib/colors';
  import SettingsProfile from '../lib/settings/SettingsProfile.svelte';
  import SettingsAppearance from '../lib/settings/SettingsAppearance.svelte';
  import SettingsGeneral from '../lib/settings/SettingsGeneral.svelte';
  import SettingsAi from '../lib/settings/SettingsAi.svelte';
  import SettingsSecurity from '../lib/settings/SettingsSecurity.svelte';
  import SettingsDataSync from '../lib/settings/SettingsDataSync.svelte';

  let userStats = $state<UserStats | null>(null);
  let templateCollections = $state<Collection[]>([]);
  let isBusy = $state(false);

  let accent = $derived(computeHeaderColor($currentUser?.default_collection_header_color));

  function getAccentTint(): string {
    const isDark = typeof document !== 'undefined' && document.documentElement.classList.contains('dark');
    return computeCardTileBg(accent, isDark);
  }

  async function logout() {
    isBusy = true;
    try {
      await api.logout();
      currentUser.set(null);
      currentView.set({ type: 'collections' });
    } finally {
      isBusy = false;
    }
  }

  async function loadTemplates() {
    try {
      const res = await api.collections.list(true);
      templateCollections = (res.collections || []).filter((c) => c.is_template);
    } catch {
      // best-effort
    }
  }

  $effect(() => {
    if ($currentUser) {
      api.meStats().then((res) => (userStats = res.stats)).catch(() => {});
      loadTemplates();
    }
  });
</script>

<div class="space-y-4">
  <h2 class="flex items-center gap-2 text-2xl font-semibold">
    <SettingsIcon label="" size={24} className="text-slate-700 dark:text-slate-300" />
    <span>Settings</span>
  </h2>

  <div class="space-y-3">
    <!-- Account & Content Stats -->
    <SettingsProfile
      {accent}
      {userStats}
      {isBusy}
      onLogout={logout}
    />

    <!-- Tags & Mentions Navigation -->
    <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
      <div class="text-xs uppercase text-slate-500">Navigation</div>
      <button
        class="mt-3 flex w-full items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3 text-left shadow-sm transition-colors hover:bg-slate-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
        onclick={() => currentView.set({ type: 'tags_mentions' })}
        type="button"
      >
        <div class="flex items-center gap-3">
          <span class="text-xl">#</span>
          <div>
            <div class="text-sm font-medium text-slate-900 dark:text-slate-100">Tags & Mentions</div>
            <div class="text-xs text-slate-500 dark:text-slate-400">Manage your tags and mentions</div>
          </div>
        </div>
        <ChevronRight label="" size={18} className="text-slate-400" />
      </button>
    </div>

    <!-- Appearance (Theme, Default Header Color, Background Colors) -->
    <SettingsAppearance
      {accent}
      {isBusy}
    />

    <!-- General Settings (Day Template, Carry Over Tasks, Push Notifications) -->
    <SettingsGeneral
      {accent}
      {templateCollections}
      {isBusy}
    />

    <!-- AI Integration & Diced Moments -->
    <SettingsAi
      {accent}
      {isBusy}
    />

    <!-- Security (Passcode, 2FA OTP, Passkeys, API Keys) -->
    <SettingsSecurity
      {accent}
      {isBusy}
    />

    {#if $currentUser?.is_admin}
      <!-- Administration -->
      <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
        <div class="text-xs uppercase text-slate-500">Administration</div>
        <div class="mt-3 space-y-3">
          <button
            class="al-icon-wrapper flex w-full items-center gap-4 rounded-xl border border-dashed border-slate-200 p-3 text-left transition-all hover:border-slate-300 hover:bg-slate-50/50 dark:border-white/10 dark:hover:bg-white/5"
            onclick={() => currentView.set({ type: 'user_management' })}
            type="button"
          >
            <div 
              class="grid h-10 w-10 shrink-0 place-items-center rounded-full"
              style={`background-color: ${getAccentTint()}; color: ${accent}`}
            >
              <Users label="" size={20} />
            </div>
            <div class="flex-1">
              <div class="font-medium text-slate-900 dark:text-slate-100">User Management</div>
              <div class="text-xs text-slate-500 dark:text-slate-400">Manage users, create accounts, assign admin roles</div>
            </div>
            <ChevronRight label="" size={20} className="text-slate-400" />
          </button>
        </div>
      </div>
    {/if}

    <!-- Data & Migration (TwoS Importer, Recycle Bin, Offline Sync) -->
    <SettingsDataSync
      {accent}
      {isBusy}
    />

    <!-- Footer -->
    <div class="py-4 text-center text-xs text-slate-400">
      snipsel v{__APP_VERSION__}
      {#if __APP_COMMIT_HASH__}
        <span class="ml-1 opacity-75 font-mono">({__APP_COMMIT_HASH__.slice(0, 7)})</span>
      {/if}
    </div>
  </div>
</div>
