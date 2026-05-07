<script lang="ts">
  import SettingsIcon from '@animated-color-icons/lucide-svelte/Settings.svelte';
  import List from '@animated-color-icons/lucide-svelte/List.svelte';
  import FileText from '@animated-color-icons/lucide-svelte/FileText.svelte';
  import SquareCheck from '@animated-color-icons/lucide-svelte/SquareCheck.svelte';
  import Paperclip from '@animated-color-icons/lucide-svelte/Paperclip.svelte';
  import BellRing from '@animated-color-icons/lucide-svelte/BellRing.svelte';
  import Lock from '@animated-color-icons/lucide-svelte/Lock.svelte';
  import Key from '@animated-color-icons/lucide-svelte/Key.svelte';
  import Upload from '@animated-color-icons/lucide-svelte/Upload.svelte';
  import Trash2 from '@animated-color-icons/lucide-svelte/Trash2.svelte';
  import Check from '@animated-color-icons/lucide-svelte/Check.svelte';
  import ChevronRight from '@animated-color-icons/lucide-svelte/ChevronRight.svelte';
  import Users from '@animated-color-icons/lucide-svelte/Users.svelte';
  import Dices from '@animated-color-icons/lucide-svelte/Dices.svelte';
  import { api, type Collection, type UserStats, type ApiKey } from '../lib/api';
  import { currentUser } from '../lib/session';
  import { collectionAnchor, currentView } from '../lib/stores';
  import { idbSaveBulkSync, idbClearAllCollections, idbClearAllCollectionItems, idbAddCollectionItemsBulk, idbSaveCollections } from '../lib/db';
  import {
    checkPushSubscription,
    subscribeToPushNotifications,
    unsubscribeFromPushNotifications,
  } from '../lib/pushManager';
  import { startRegistration } from '@simplewebauthn/browser';

  let defaultHeaderColor = $state('');
  let templateCollections = $state<Collection[]>([]);
  let dayTemplateId = $state<string>('');
  let isBusy = $state(false);
  let initialized = $state(false);
  let showPasscodeForm = $state(false);
  let passcode = $state('');
  let passcodeError = $state('');
  let hasPushEnabled = $state(false);
  let userStats = $state<UserStats | null>(null);

  let isOtpSetupActive = $state(false);
  let isOtpDisableActive = $state(false);
  let passcodeConfirmPassword = $state('');
  let otpSetupConfirmPassword = $state('');
  let otpDisableConfirmPassword = $state('');
  let otpSecret = $state('');
  let otpProvisioningUrl = $state('');
  let otpCodeInput = $state('');
  let otpSetupError = $state('');
  let securityError = $state('');

  let passkeys = $state<import('../lib/api').UserPasskey[]>([]);
  let isPasskeyAddActive = $state(false);
  let newPasskeyName = $state('');
  let passkeyError = $state('');
  
  let newEmail = $state('');
  let newPassword = $state('');
  let currentPasswordConfirm = $state('');
  let accountUpdateError = $state('');
  let accountUpdateSuccess = $state('');
  let showAccountForm = $state(false);
  
  let aiLlmUrl = $state('');
  let aiModelName = $state('');
  let aiApiKey = $state('');
  let lightBackgroundColor = $state('');
  let darkBackgroundColor = $state('');
  let availableModels = $state<Array<{ id: string; name: string }>>([]);
  let isLoadingModels = $state(false);
  let modelsError = $state('');
  
  let dicedMomentsTags = $state('');
  let showDicedMomentsSaved = $state(false);
  let allUserTags = $state<string[]>([]);
  let showTagSuggestions = $state(false);
  let tagSearchQuery = $state('');
  
  const tagSuggestions = $derived(
    tagSearchQuery 
      ? allUserTags
          .map(t => '#' + t)
          .filter(t => t.toLowerCase().includes(tagSearchQuery.toLowerCase()) && !dicedMomentsTags.toLowerCase().includes(t.toLowerCase()))
      : []
  );

  // API Keys
  let apiKeys = $state<ApiKey[]>([]);
  let isApiKeyAddActive = $state(false);
  let newApiKeyName = $state('');
  let newApiKeyValue = $state('');
  let apiKeyError = $state('');
  let showCopiedKey = $state(false);

  // Offline Sync
  let syncStatus = $state<'idle' | 'syncing' | 'success' | 'error'>('idle');
  let syncError = $state('');
  let syncProgress = $state(0);
  let syncStage = $state('');
  let lastFullSync = $state<number | null>(null);

  // Success Feedback states
  let showAccountSaved = $state(false);
  let showAppearanceSaved = $state(false);
  let showDayTemplateSaved = $state(false);
  let showAiSaved = $state(false);
  let showPasscodeSaved = $state(false);
  let showApiKeySaved = $state(false);

  const DEFAULT_ACCENT = '#4f46e5';
  type Rgb = { r: number; g: number; b: number };

  function clampByte(n: number): number {
    return Math.max(0, Math.min(255, Math.round(n)));
  }

  function hexToRgb(hex: string): Rgb | null {
    const h = (hex || '').trim();
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

  function isLightColor(color: string): boolean {
    const hex = color.replace('#', '');
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
    return brightness > 128;
  }

  function getContrastColor(bgColor: string): string {
    return isLightColor(bgColor) ? '#1e293b' : 'white';
  }

  async function startOtpSetup() {
    isBusy = true;
    otpSetupError = '';
    try {
      const res = await api.twoFactor.generate();
      otpSecret = res.secret;
      otpProvisioningUrl = res.provisioning_url;
      isOtpSetupActive = true;
    } catch (e: any) {
      otpSetupError = e.error?.message || 'Failed to initiate 2FA';
    } finally {
      isBusy = false;
    }
  }

  async function enableOtp() {
    if (!otpCodeInput || !otpSetupConfirmPassword) return;
    isBusy = true;
    otpSetupError = '';
    try {
      console.log('[2FA Setup] Enabling with password length:', otpSetupConfirmPassword.length);
      await api.twoFactor.enable({ code: otpCodeInput, password_confirm: otpSetupConfirmPassword });
      const res = await api.me();
      currentUser.set(res.user);
      isOtpSetupActive = false;
      otpCodeInput = '';
      otpSetupConfirmPassword = '';
    } catch (e: any) {
      otpSetupError = e.error?.message || 'Failed to enable 2FA';
    } finally {
      isBusy = false;
    }
  }

  async function disableOtp(pass: string) {
    console.log('[2FA Disable] Called with password length:', pass.length);
    isBusy = true;
    securityError = '';
    try {
      await api.twoFactor.disable(pass);
      const res = await api.me();
      currentUser.set(res.user);
      isOtpDisableActive = false;
      otpDisableConfirmPassword = '';
    } catch (e: any) {
      console.error('[2FA Disable] Error:', e);
      securityError = e.error?.message || 'Failed to disable 2FA';
    } finally {
      isBusy = false;
    }
  }

  async function loadPasskeys() {
    try {
      const res = await api.passkeys.list();
      passkeys = res.passkeys;
    } catch (err) {
      console.error('Failed to load passkeys', err);
    }
  }

  async function addPasskey() {
    if (!newPasskeyName) return;
    isBusy = true;
    passkeyError = '';
    try {
      const options = await api.passkeys.registerBegin();
      const attResp = await startRegistration(options);
      await api.passkeys.registerComplete(attResp, newPasskeyName);
      
      await loadPasskeys();
      const meRes = await api.me();
      currentUser.set(meRes.user);
      isPasskeyAddActive = false;
      newPasskeyName = '';
    } catch (e: any) {
      console.error(e);
      passkeyError = e.error?.message || e.message || 'Failed to register passkey';
    } finally {
      isBusy = false;
    }
  }

  async function removePasskey(id: string) {
    if (!confirm('Are you sure you want to remove this passkey?')) return;
    isBusy = true;
    try {
      await api.passkeys.delete(id);
      await loadPasskeys();
      const meRes = await api.me();
      currentUser.set(meRes.user);
    } catch (e: any) {
      alert(e.error?.message || 'Failed to delete passkey');
    } finally {
      isBusy = false;
    }
  }

  async function loadAllTags() {
    try {
      const res = await api.tags.list('my');
      allUserTags = res.tags.map(t => t.name);
    } catch (err) {
      console.error("Failed to load tags", err);
    }
  }

  function handleTagKeyDown(e: KeyboardEvent) {
    if (e.key === 'Tab' && tagSuggestions.length > 0 && showTagSuggestions) {
      e.preventDefault();
      selectTag(tagSuggestions[0]);
    }
  }

  function handleTagInput(e: Event) {
    const val = (e.target as HTMLInputElement).value;
    const parts = val.split(',');
    const lastPart = parts[parts.length - 1].trim();
    if (lastPart.length > 0) {
      tagSearchQuery = lastPart;
      showTagSuggestions = true;
    } else {
      showTagSuggestions = false;
    }
  }

  function selectTag(tag: string) {
    let parts = dicedMomentsTags.split(',').map(p => p.trim()).filter(p => !!p);
    if (parts.length > 0 && tagSearchQuery && parts[parts.length - 1].toLowerCase().includes(tagSearchQuery.toLowerCase().replace('#', ''))) {
        parts[parts.length - 1] = tag;
    } else if (parts.length > 0 && tagSearchQuery && tag.toLowerCase().includes(tagSearchQuery.toLowerCase())) {
        parts[parts.length - 1] = tag;
    } else {
        parts.push(tag);
    }
    dicedMomentsTags = parts.join(', ') + ', ';
    showTagSuggestions = false;
    tagSearchQuery = '';
  }

  async function loadApiKeys() {
    try {
      const res = await api.apiKeys.list();
      apiKeys = res.api_keys;
    } catch (err) {
      console.error('Failed to load API keys', err);
    }
  }

  async function createApiKey() {
    if (!newApiKeyName) return;
    isBusy = true;
    apiKeyError = '';
    try {
      const res = await api.apiKeys.create(newApiKeyName);
      newApiKeyValue = res.api_key.key;
      showApiKeySaved = true;
      setTimeout(() => showApiKeySaved = false, 2000);
      await loadApiKeys();
    } catch (e: any) {
      apiKeyError = e.error?.message || 'Failed to create API key';
    } finally {
      isBusy = false;
    }
  }

  async function deleteApiKey(id: string) {
    if (!confirm('Are you sure you want to delete this API key? This action cannot be undone.')) return;
    isBusy = true;
    try {
      await api.apiKeys.delete(id);
      await loadApiKeys();
    } catch (e: any) {
      alert(e.error?.message || 'Failed to delete API key');
    } finally {
      isBusy = false;
    }
  }

  function copyApiKey() {
    navigator.clipboard.writeText(newApiKeyValue);
    showCopiedKey = true;
    setTimeout(() => showCopiedKey = false, 2000);
  }

  async function logout() {
    await api.logout();
    currentUser.set(null);
    collectionAnchor.set(null);
    currentView.set({ type: 'loading' });
  }

  async function saveAppearanceSettings() {
    isBusy = true;
    try {
      const res = await api.updateMe({
        default_collection_header_color: defaultHeaderColor.trim() || null,
        light_background_color: lightBackgroundColor.trim() || null,
        dark_background_color: darkBackgroundColor.trim() || null,
      });
      currentUser.set(res.user);
      showAppearanceSaved = true;
      setTimeout(() => showAppearanceSaved = false, 2000);
    } finally {
      isBusy = false;
    }
  }

  async function toggleCarryOver() {
    isBusy = true;
    try {
      const next = !Boolean($currentUser?.carry_over_open_tasks ?? true);
      const res = await api.updateMe({ carry_over_open_tasks: next });
      currentUser.set(res.user);
    } finally {
      isBusy = false;
    }
  }

  async function loadTemplates() {
    const res = await api.collections.list();
    templateCollections = res.collections.filter((c) => Boolean(c.is_template));
  }

  async function saveDayTemplate() {
    isBusy = true;
    try {
      const id = dayTemplateId.trim() || null;
      const res = await api.updateMe({ day_collection_template_id: id });
      currentUser.set(res.user);
      showDayTemplateSaved = true;
      setTimeout(() => showDayTemplateSaved = false, 2000);
    } finally {
      isBusy = false;
    }
  }

  async function savePasscode() {
    if (passcode.length < 4) {
      passcodeError = 'Passcode must be at least 4 digits';
      return;
    }
    isBusy = true;
    passcodeError = '';
    try {
      await api.passcode.set({ passcode, password_confirm: passcodeConfirmPassword });
      const res = await api.me();
      currentUser.set(res.user);
      showPasscodeSaved = true;
      setTimeout(() => { showPasscodeSaved = false; showPasscodeForm = false; }, 2000);
      passcode = '';
      passcodeConfirmPassword = '';
    } catch (e: any) {
      passcodeError = e.error?.message || 'Failed to set passcode';
    } finally {
      isBusy = false;
    }
  }

  async function togglePush() {
    isBusy = true;
    try {
      if (hasPushEnabled) {
        await unsubscribeFromPushNotifications();
        hasPushEnabled = false;
      } else {
        await subscribeToPushNotifications();
        hasPushEnabled = true;
      }
    } catch (err: any) {
      alert(err.message || 'Failed to toggle push notifications');
    } finally {
      isBusy = false;
    }
  }

  async function updateAccount() {
    if (!newEmail && !newPassword) {
      accountUpdateError = 'Please enter a new email or password';
      return;
    }
    if (!currentPasswordConfirm) {
      accountUpdateError = 'Current password is required to save changes';
      return;
    }
    
    isBusy = true;
    accountUpdateError = '';
    accountUpdateSuccess = '';
    try {
      const res = await api.updateMe({
        email: newEmail || undefined,
        password: newPassword || undefined,
        current_password: currentPasswordConfirm
      });
      currentUser.set(res.user);
      showAccountSaved = true;
      setTimeout(() => { showAccountSaved = false; showAccountForm = false; }, 2000);
      newEmail = '';
      newPassword = '';
      currentPasswordConfirm = '';
    } catch (e: any) {
      accountUpdateError = e.error?.message || 'Failed to update account';
    } finally {
      isBusy = false;
    }
  }

  async function saveAiSettings() {
    isBusy = true;
    try {
      const updateData: any = {
        ai_llm_url: aiLlmUrl.trim() || null,
        ai_model_name: aiModelName.trim() || null,
      };
      
      const trimmedKey = aiApiKey.trim();
      if (trimmedKey) {
        updateData.ai_api_key = trimmedKey;
      }

      const res = await api.updateMe(updateData);
      currentUser.set(res.user);
      showAiSaved = true;
      setTimeout(() => showAiSaved = false, 2000);
      aiApiKey = '';
    } finally {
      isBusy = false;
    }
  }

  async function saveDicedMomentsSettings() {
    isBusy = true;
    try {
      const res = await api.updateMe({
        diced_moments_tags: dicedMomentsTags.trim() || null,
      });
      currentUser.set(res.user);
      showDicedMomentsSaved = true;
      setTimeout(() => showDicedMomentsSaved = false, 2000);
    } finally {
      isBusy = false;
    }
  }

  async function fetchModels() {
    if (!aiLlmUrl.trim()) {
      modelsError = 'Please enter LLM URL first';
      return;
    }
    if (!aiApiKey.trim() && !$currentUser?.ai_api_key_set) {
      modelsError = 'Please enter API key first';
      return;
    }
    isLoadingModels = true;
    modelsError = '';
    try {
      const res = await api.ai.getModels();
      availableModels = res.models;
      if (availableModels.length === 0) {
        modelsError = 'No models found';
      }
    } catch (e: any) {
      modelsError = e.error?.message || 'Failed to fetch models';
      availableModels = [];
    } finally {
      isLoadingModels = false;
    }
  }

  async function sendTestPush() {
    isBusy = true;
    try {
      await api.notifications.testPush();
    } catch (err: any) {
      alert(err.error?.message || 'Failed to send test notification');
    } finally {
      isBusy = false;
    }
  }

  async function performFullSync() {
    if (!navigator.onLine) {
      syncStatus = 'error';
      syncError = 'You must be online to perform a full sync.';
      return;
    }

    syncStatus = 'syncing';
    syncError = '';
    syncProgress = 5;
    syncStage = 'Connecting to server...';
    isBusy = true;

    try {
      const batchSize = 500;
      
      // Stage 1: Collections
      syncProgress = 10;
      syncStage = 'Downloading collections...';
      const colRes = await api.collections.syncAll({ include_items: false });
      
      syncProgress = 15;
      syncStage = 'Saving collections...';
      await idbClearAllCollections();
      await idbSaveCollections(colRes.collections);
      
      // Stage 2: Items in batches
      const totalItems = colRes.total_items || 0;
      let fetchedItems = 0;
      
      await idbClearAllCollectionItems();
      
      while (true) {
        syncStage = `Downloading snipsels (${fetchedItems.toLocaleString()} / ${totalItems.toLocaleString()})...`;
        syncProgress = 15 + Math.floor((fetchedItems / Math.max(1, totalItems)) * 80);
        
        const itemRes = await api.collections.syncAll({ 
          include_collections: false, 
          offset: fetchedItems, 
          limit: batchSize 
        });
        
        const batchItemCount = Object.values(itemRes.items).reduce((acc, items) => acc + items.length, 0);
        if (batchItemCount === 0) break;
        
        await idbAddCollectionItemsBulk(itemRes.items);
        fetchedItems += batchItemCount;
        
        if (batchItemCount < batchSize) break;
      }
      
      const now = Date.now();
      lastFullSync = now;
      localStorage.setItem('snipsel_last_full_sync', String(now));
      
      syncProgress = 100;
      syncStage = 'Sync complete!';
      syncStatus = 'success';
      setTimeout(() => { 
        if (syncStatus === 'success') {
          syncStatus = 'idle';
          syncProgress = 0;
          syncStage = '';
        }
      }, 5000);
    } catch (e: any) {
      console.error('Full sync failed', e);
      syncStatus = 'error';
      syncProgress = 0;
      syncStage = '';
      syncError = e.error?.message || 'Sync failed. Please try again later.';
    } finally {
      isBusy = false;
    }
  }


  $effect(() => {
    if (!$currentUser || initialized) return;
    defaultHeaderColor = $currentUser.default_collection_header_color ?? '#4f46e5';
    dayTemplateId = $currentUser.day_collection_template_id ?? '';
    aiLlmUrl = $currentUser.ai_llm_url ?? '';
    aiModelName = $currentUser.ai_model_name ?? '';
    lightBackgroundColor = $currentUser.light_background_color ?? '';
    darkBackgroundColor = $currentUser.dark_background_color ?? '';
    dicedMomentsTags = $currentUser.diced_moments_tags ?? '';
    initialized = true;
    
    const savedLastSync = localStorage.getItem('snipsel_last_full_sync');
    if (savedLastSync) {
      lastFullSync = parseInt(savedLastSync, 10);
    }
  });

  $effect(() => {
    loadTemplates();
  });

  $effect(() => {
    checkPushSubscription().then(v => hasPushEnabled = v);
  });

  $effect(() => {
    loadPasskeys();
  });

  $effect(() => {
    loadApiKeys();
  });

  $effect(() => {
    api.meStats().then((res) => (userStats = res.stats)).catch(() => {});
  });

  $effect(() => {
    loadAllTags();
  });
</script>

<div class="space-y-4">
  <h2 class="flex items-center gap-2 text-2xl font-semibold">
    <SettingsIcon label="" size={24} className="text-slate-700 dark:text-slate-300" />
    <span>Settings</span>
  </h2>

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
              style={`color: ${getAccent()}`}
              type="button" 
              onclick={() => { showAccountForm = !showAccountForm; accountUpdateError = ''; accountUpdateSuccess = ''; }}
              disabled={isBusy}
            >
              {showAccountForm ? 'Cancel' : 'Edit'}
            </button>
            <button 
              class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-red-600 shadow-sm ring-1 ring-black/5 hover:bg-red-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:text-red-400 dark:hover:bg-red-950/30" 
              type="button" 
              onclick={logout}
              disabled={isBusy}
            >
              Logout
            </button>
        </div>
      </div>

      {#if showAccountForm}
        <div class="mt-4 space-y-4 border-t border-slate-100 pt-4 dark:border-white/5">
          <div>
            <label for="new-email" class="block text-sm font-medium text-slate-700 dark:text-slate-300">New Email Address (optional)</label>
            <input
              id="new-email"
              type="email"
              class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:ring-white/10"
              bind:value={newEmail}
              placeholder="new.email@example.com"
            />
          </div>
          <div>
            <label for="new-password" class="block text-sm font-medium text-slate-700 dark:text-slate-300">New Password (optional, min 4 chars)</label>
            <input
              id="new-password"
              type="password"
              class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:ring-white/10"
              bind:value={newPassword}
              placeholder="••••••••"
            />
          </div>
          <div class="rounded-lg bg-slate-50 p-3 dark:bg-white/5">
            <label for="account-password-confirm" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Confirm Current Password to save</label>
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
            style={`background-color: ${getAccent()}; color: ${getContrastColor(getAccent())}`}
            type="button"
            onclick={updateAccount}
            disabled={isBusy || (!newEmail && !newPassword) || !currentPasswordConfirm || showAccountSaved}
          >
            {#if isBusy}
              <div class="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></div>
              <span>Saving...</span>
            {:else if showAccountSaved}
              <div class="animate-in zoom-in fade-in duration-300 flex items-center gap-2">
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
          { label: 'Snipsels',    type: 'snipsels',    value: userStats?.snipsels },
          { label: 'Tasks done',  type: 'tasks',       value: userStats?.completed_tasks },
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
            <span
              class="text-2xl font-bold tabular-nums"
              style={`color: ${getAccent()}`}
            >
              {stat.value !== undefined ? stat.value.toLocaleString() : '–'}
            </span>
            <span class="text-center text-xs text-slate-500 dark:text-slate-400">{stat.label}</span>
          </div>
        {/each}
      </div>
    </div>

    <!-- Appearance -->
    <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/60">
      <div class="text-xs uppercase text-slate-500">Appearance</div>
      
      <div class="mt-4">
        <label for="theme-select" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Color Theme</label>
        <div class="mt-2 grid grid-cols-3 gap-2">
          {#each ['system', 'light', 'dark'] as t}
            <button
              class="rounded-lg border px-3 py-2 text-sm font-medium transition-all {$currentUser?.theme === t ? 'bg-slate-900 text-white border-slate-900 dark:bg-white dark:text-slate-900 dark:border-white' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700 dark:hover:bg-slate-700'}"
              type="button"
              onclick={async () => {
                isBusy = true;
                try {
                  const res = await api.updateMe({ theme: t as any });
                  currentUser.set(res.user);
                } finally {
                  isBusy = false;
                }
              }}
              disabled={isBusy}
            >
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          {/each}
        </div>
      </div>

      <div class="mt-6">
        <label for="accent-color-picker" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Default collection header color</label>
        <div class="mt-2 flex items-center gap-2">
          <div class="flex flex-1 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-sm ring-1 ring-black/5 dark:border-slate-700 dark:bg-slate-800">
            <label class="relative block h-8 w-8 cursor-pointer">
              <input
                id="accent-color-picker"
                class="h-full w-full cursor-pointer rounded border-0 p-0"
                type="color"
                value={defaultHeaderColor}
                oninput={(e) => defaultHeaderColor = (e.target as HTMLInputElement).value}
              />
            </label>
            <input
              class="min-w-0 flex-1 border-none bg-transparent text-sm font-mono text-slate-700 focus:outline-none focus:ring-0 dark:text-slate-300"
              value={defaultHeaderColor}
              oninput={(e) => {
                let v = (e.target as HTMLInputElement).value;
                if (v && !v.startsWith('#')) v = '#' + v;
                if (/^#[0-9a-fA-F]{6}$/.test(v)) defaultHeaderColor = v;
              }}
            />
          </div>
        </div>
      </div>

      <div class="mt-6">
        <span class="block text-sm font-medium text-slate-700 dark:text-slate-300">Background colors</span>
        <div class="mt-3 grid grid-cols-2 gap-4">
          <div>
            <label for="light-bg-color-picker" class="block text-xs text-slate-500 dark:text-slate-400 mb-1">Light mode</label>
            <div class="flex items-center gap-2">
              <div class="flex max-w-[160px] md:max-w-none flex-1 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-sm ring-1 ring-black/5 dark:border-slate-700 dark:bg-slate-800">
                <label class="relative block h-8 w-8 cursor-pointer">
                  <input
                    id="light-bg-color-picker"
                    class="h-full w-full cursor-pointer rounded border-0 p-0"
                    type="color"
                    value={lightBackgroundColor || '#ffffff'}
                    oninput={(e) => lightBackgroundColor = (e.target as HTMLInputElement).value}
                  />
                </label>
                <input
                  class="min-w-0 flex-1 border-none bg-transparent text-sm font-mono text-slate-700 focus:outline-none focus:ring-0 dark:text-slate-300"
                  value={lightBackgroundColor || ''}
                  property=""
                  placeholder="#ffffff"
                  oninput={(e) => {
                    let v = (e.target as HTMLInputElement).value;
                    if (v && !v.startsWith('#')) v = '#' + v;
                    if (/^#[0-9a-fA-F]{6}$/.test(v)) lightBackgroundColor = v;
                  }}
                />
              </div>
            </div>
          </div>
          <div>
            <label for="dark-bg-color-picker" class="block text-xs text-slate-500 dark:text-slate-400 mb-1">Dark mode</label>
            <div class="flex items-center gap-2">
              <div class="flex max-w-[160px] md:max-w-none flex-1 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-sm ring-1 ring-black/5 dark:border-slate-700 dark:bg-slate-800">
                <label class="relative block h-8 w-8 cursor-pointer">
                  <input
                    id="dark-bg-color-picker"
                    class="h-full w-full cursor-pointer rounded border-0 p-0"
                    type="color"
                    value={darkBackgroundColor || '#0f172a'}
                    oninput={(e) => darkBackgroundColor = (e.target as HTMLInputElement).value}
                  />
                </label>
                <input
                  class="min-w-0 flex-1 border-none bg-transparent text-sm font-mono text-slate-700 focus:outline-none focus:ring-0 dark:text-slate-300"
                  value={darkBackgroundColor || ''}
                  placeholder="#0f172a"
                  oninput={(e) => {
                    let v = (e.target as HTMLInputElement).value;
                    if (v && !v.startsWith('#')) v = '#' + v;
                    if (/^#[0-9a-fA-F]{6}$/.test(v)) darkBackgroundColor = v;
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="mt-6 flex justify-end">
        <button
          class="relative flex items-center justify-center gap-2 rounded-full px-6 py-2.5 text-sm font-bold shadow-xl transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-70"
          style={`background-color: ${getAccent()}; color: ${getContrastColor(getAccent())}`}
          type="button"
          onclick={saveAppearanceSettings}
          disabled={isBusy || showAppearanceSaved}
        >
          {#if isBusy}
            <div class="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></div>
            <span>Saving...</span>
          {:else if showAppearanceSaved}
            <div class="animate-in zoom-in fade-in duration-300 flex items-center gap-2">
              <Check label="" size={18} strokeWidth={3} />
              <span>Saved!</span>
            </div>
          {:else}
            <span>Save Appearance</span>
          {/if}
        </button>
      </div>
    </div>

    <!-- Day Template -->
    <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
      <div class="text-xs uppercase text-slate-500">Day template</div>
      <div class="mt-3">
        <label for="day-template-select" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Template for new daily collections</label>
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
            style={`background-color: ${getAccent()}; color: ${getContrastColor(getAccent())}`}
            type="button"
            onclick={saveDayTemplate}
            disabled={isBusy || showDayTemplateSaved}
          >
            {#if isBusy}
              <div class="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></div>
              <span>Saving...</span>
            {:else if showDayTemplateSaved}
              <div class="animate-in zoom-in fade-in duration-300 flex items-center gap-2">
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
          style={Boolean($currentUser?.carry_over_open_tasks ?? true) ? `background-color: ${getAccent()}; color: ${getContrastColor(getAccent())}` : 'background-color: #cbd5e1'}
          role="switch"
          aria-checked={Boolean($currentUser?.carry_over_open_tasks ?? true)}
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
          style={hasPushEnabled ? `background-color: ${getAccent()}; color: ${getContrastColor(getAccent())}` : 'background-color: #cbd5e1'}
          role="switch"
          aria-checked={hasPushEnabled}
          onclick={togglePush}
          disabled={isBusy}
        >
          <span
            class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out {hasPushEnabled ? 'translate-x-5' : 'translate-x-0'}"
          ></span>
        </button>
      </div>

      {#if hasPushEnabled}
        <div class="mt-3 flex items-center justify-end">
          <button
            class="al-icon-wrapper text-xs font-medium text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 transition-colors flex items-center gap-1.5"
            type="button"
            onclick={sendTestPush}
            disabled={isBusy}
          >
            <BellRing label="" size={14} />
            Send Test Notification
          </button>
        </div>
      {/if}
    </div>

    <!-- Diced Moments -->
    <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
      <div class="flex items-center gap-2 text-xs uppercase text-slate-500">
        <Dices label="" size={12} strokeWidth={2.5} />
        <span>Diced Moments</span>
      </div>
      <div class="mt-3 space-y-4">
        <div>
          <label for="diced-tags" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Tags (comma separated)</label>
          <div class="text-xs text-slate-500 dark:text-slate-400 mb-2">Snipsels with these tags will be randomly picked for your daily collection.</div>
          <div class="relative">
            <input
              id="diced-tags"
              type="text"
              class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:ring-white/10"
              bind:value={dicedMomentsTags}
              oninput={handleTagInput}
              onkeydown={handleTagKeyDown}
              onblur={() => setTimeout(() => showTagSuggestions = false, 200)}
              placeholder="quote, thought, memory"
              autocomplete="off"
            />
            {#if showTagSuggestions && tagSuggestions.length > 0}
              <div class="absolute z-50 mt-1 max-h-40 w-full overflow-auto rounded-lg border border-slate-200 bg-white shadow-xl dark:border-white/10 dark:bg-slate-800">
                {#each tagSuggestions as tag}
                  <button
                    type="button"
                    class="block w-full px-4 py-2 text-left text-sm hover:bg-slate-100 dark:hover:bg-white/5"
                    onclick={() => selectTag(tag)}
                  >
                    {tag}
                  </button>
                {/each}
              </div>
            {/if}
          </div>
        </div>
        <div class="flex justify-end">
          <button
            class="relative flex items-center justify-center gap-2 rounded-full px-6 py-2.5 text-sm font-bold shadow-xl transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-70"
            style={`background-color: ${getAccent()}; color: ${getContrastColor(getAccent())}`}
            type="button"
            onclick={saveDicedMomentsSettings}
            disabled={isBusy || showDicedMomentsSaved}
          >
            {#if isBusy}
              <div class="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></div>
              <span>Saving...</span>
            {:else if showDicedMomentsSaved}
              <div class="animate-in zoom-in fade-in duration-300 flex items-center gap-2">
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

    <!-- AI Integration -->
    <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
      <div class="text-xs uppercase text-slate-500">AI Integration</div>
      <div class="mt-3 space-y-4">
        <div>
          <label for="ai-url" class="block text-sm font-medium text-slate-700 dark:text-slate-300">LLM API URL (OpenAI compatible)</label>
          <input
            id="ai-url"
            type="text"
            class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none dark:border-white/10 dark:bg-slate-800"
            bind:value={aiLlmUrl}
            placeholder="https://api.openai.com/v1/chat/completions"
          />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <div class="flex items-center justify-between">
              <label for="ai-model" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Model Name</label>
              <button
                type="button"
                onclick={fetchModels}
                disabled={isLoadingModels}
                class="text-xs text-slate-500 hover:text-slate-700 disabled:opacity-50 dark:text-slate-400 dark:hover:text-slate-200"
              >
                {isLoadingModels ? 'Loading...' : 'Refresh'}
              </button>
            </div>
            {#if availableModels.length > 0}
              <select
                id="ai-model"
                class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none dark:border-white/10 dark:bg-slate-800"
                bind:value={aiModelName}
              >
                <option value="">Select a model...</option>
                {#each availableModels as model}
                  <option value={model.id}>{model.name}</option>
                {/each}
              </select>
            {:else}
              <input
                id="ai-model"
                type="text"
                class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none dark:border-white/10 dark:bg-slate-800"
                bind:value={aiModelName}
                placeholder="gpt-3.5-turbo"
              />
            {/if}
            {#if modelsError}
              <div class="mt-1 text-xs text-red-500">{modelsError}</div>
            {/if}
          </div>
          <div>
            <label for="ai-key" class="block text-sm font-medium text-slate-700 dark:text-slate-300">API Key {($currentUser?.ai_api_key_set) ? '(Set)' : ''}</label>
            <input
              id="ai-key"
              type="password"
              class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none dark:border-white/10 dark:bg-slate-800"
              bind:value={aiApiKey}
              placeholder="sk-..."
            />
          </div>
        </div>
        <div class="flex justify-end pt-2">
          <button
            class="relative flex items-center justify-center gap-2 rounded-full px-6 py-2.5 text-sm font-bold shadow-xl transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-70"
            style={`background-color: ${getAccent()}; color: ${getContrastColor(getAccent())}`}
            type="button"
            onclick={saveAiSettings}
            disabled={isBusy || showAiSaved}
          >
            {#if isBusy}
              <div class="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></div>
              <span>Saving...</span>
            {:else if showAiSaved}
              <div class="animate-in zoom-in fade-in duration-300 flex items-center gap-2">
                <Check label="" size={18} strokeWidth={3} />
                <span>Saved!</span>
              </div>
            {:else}
              <span>Save AI Settings</span>
            {/if}
          </button>
        </div>
      </div>
    </div>

    <!-- Security -->
    <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
      <div class="flex items-center gap-2 text-xs uppercase text-slate-500">
        <Lock label="" size={12} strokeWidth={2.5} />
        <span>Security</span>
      </div>
      
      <!-- Passcode -->
      <div class="border-b border-slate-100 pb-4 dark:border-white/5">
        {#if !showPasscodeForm}
          <div class="mt-3 flex items-center justify-between gap-4">
            <div>
              <div class="text-sm font-medium text-slate-900 dark:text-slate-100">Personal Passcode</div>
              <div class="text-xs text-slate-500 dark:text-slate-400">
                {$currentUser?.passcode_set ? 'Passcode is active.' : 'Set a passcode to protect sensitive collections.'}
              </div>
            </div>
            <button
              class="rounded-full border border-slate-200 bg-white px-6 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
              style={`color: ${getAccent()}`}
              type="button"
              onclick={() => { showPasscodeForm = true; passcodeError = ''; }}
              disabled={isBusy}
            >
              {$currentUser?.passcode_set ? 'Change' : 'Set Passcode'}
            </button>
          </div>
        {:else}
          <div class="mt-4 space-y-4 transition-all">
            <div>
              <label for="new-passcode" class="block text-sm font-medium text-slate-700 dark:text-slate-300">New 4-digit passcode</label>
              <input
                id="new-passcode"
                type="password"
                inputmode="numeric"
                maxlength="12"
                class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:ring-white/10"
                bind:value={passcode}
                oninput={(e) => passcode = e.currentTarget.value.replace(/\D/g, '')}
                placeholder="••••"
              />
            </div>
            <div>
              <label for="password-confirm" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Confirm account password</label>
              <input
                id="password-confirm"
                type="password"
                class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:ring-white/10"
                bind:value={passcodeConfirmPassword}
                placeholder="Your account password"
              />
            </div>
            
            {#if passcodeError}
              <div class="text-xs font-medium text-red-600 dark:text-red-400">{passcodeError}</div>
            {/if}
            
            <div class="flex items-center gap-2 pt-2">
              <button
                class="relative flex flex-1 items-center justify-center gap-2 rounded-full px-6 py-2.5 text-sm font-bold shadow-xl transition-all duration-300 hover:scale-[1.01] active:scale-[0.99] disabled:opacity-70"
                style={`background-color: ${getAccent()}; color: ${getContrastColor(getAccent())}`}
                type="button"
                onclick={savePasscode}
                disabled={isBusy || passcode.length < 4 || !passcodeConfirmPassword || showPasscodeSaved}
              >
                {#if isBusy}
                  <div class="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></div>
                  <span>Saving...</span>
                {:else if showPasscodeSaved}
                  <div class="animate-in zoom-in fade-in duration-300 flex items-center gap-2">
                    <Check label="" size={18} strokeWidth={3} />
                    <span>Saved!</span>
                  </div>
                {:else}
                  <span>Save Passcode</span>
                {/if}
              </button>
              <button
                class="flex-1 rounded-full border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
                style={`color: ${getAccent()}`}
                type="button"
                onclick={() => { showPasscodeForm = false; passcode = ''; passcodeConfirmPassword = ''; }}
                disabled={isBusy}
              >
                Cancel
              </button>
            </div>
          </div>
        {/if}
      </div>

      <!-- Two-Factor Authentication -->
      <div class="border-b border-slate-100 py-4 dark:border-white/5">
        <div class="flex items-center justify-between gap-4">
          <div>
            <div class="text-sm font-medium text-slate-900 dark:text-slate-100">Two-Factor Authentication (OTP)</div>
            <div class="text-xs text-slate-500 dark:text-slate-400">
              {$currentUser?.otp_enabled ? 'Active. Extra security for your account.' : 'Enhance security by requiring a code from an authenticator app.'}
            </div>
          </div>
          {#if $currentUser?.otp_enabled}
            <button
              class="rounded-full border border-slate-200 bg-white px-6 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5 {isOtpDisableActive ? 'text-red-600 dark:text-red-400' : ''}"
              style={isOtpDisableActive ? '' : `color: ${getAccent()}`}
              type="button"
              onclick={() => {
                isOtpDisableActive = !isOtpDisableActive;
                securityError = '';
                otpDisableConfirmPassword = '';
              }}
              disabled={isBusy}
            >
              {isOtpDisableActive ? 'Cancel' : 'Disable'}
            </button>
          {:else}
            <button
              class="rounded-full border border-slate-200 bg-white px-6 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
              style={`color: ${getAccent()}`}
              type="button"
              onclick={startOtpSetup}
              disabled={isBusy}
            >
              Set up 2FA
            </button>
          {/if}
        </div>

        {#if securityError}
          <div class="mt-2 text-xs font-medium text-red-600 dark:text-red-400">{securityError}</div>
        {/if}

        {#if isOtpDisableActive}
          <div class="mt-4 space-y-4 rounded-xl bg-red-50/50 p-4 dark:bg-red-950/20">
            <div>
              <label for="otp-disable-pass" class="block text-sm font-medium text-red-800 dark:text-red-300">Confirm account password to disable 2FA</label>
              <input
                id="otp-disable-pass"
                type="password"
                class="mt-1 block w-full rounded-lg border border-red-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none dark:border-red-900/30 dark:bg-slate-800"
                bind:value={otpDisableConfirmPassword}
                placeholder="Your account password"
              />
            </div>
            <button
              class="w-full rounded-full bg-red-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-700 disabled:opacity-50"
              type="button"
              onclick={() => disableOtp(otpDisableConfirmPassword)}
              disabled={isBusy || !otpDisableConfirmPassword}
            >
              Confirm Disable 2FA
            </button>
          </div>
        {/if}

        {#if isOtpSetupActive}
          <div class="mt-4 space-y-4 rounded-xl bg-slate-50 p-4 dark:bg-white/5">
            <div class="text-sm font-medium">Scan this QR code in your app</div>
            <div class="flex justify-center rounded-lg bg-white p-2">
              <img src={`/api/auth/2fa/qr?provisioning_url=${encodeURIComponent(otpProvisioningUrl)}`} alt="2FA QR Code" class="h-48 w-48" />
            </div>
            <div class="text-xs text-slate-500 text-center">
              Or enter manually: <code class="bg-slate-200 px-1 dark:bg-white/10">{otpSecret}</code>
            </div>
            
            <div class="space-y-3">
              <div>
                <label for="otp-code" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Enter code from app</label>
                <input
                  id="otp-code"
                  type="text"
                  inputmode="numeric"
                  maxlength="6"
                  class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none dark:border-white/10 dark:bg-slate-800"
                  bind:value={otpCodeInput}
                  placeholder="000000"
                />
              </div>
              <div>
                <label for="otp-password-confirm" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Confirm account password</label>
                <input
                  id="otp-password-confirm"
                  type="password"
                  class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none dark:border-white/10 dark:bg-slate-800"
                  bind:value={otpSetupConfirmPassword}
                  placeholder="Your account password"
                />
              </div>
            </div>

            {#if otpSetupError}
              <div class="text-xs font-medium text-red-600 dark:text-red-400">{otpSetupError}</div>
            {/if}

            <div class="flex gap-2">
              <button
                class="flex-1 rounded-full px-4 py-2 text-sm font-bold shadow-xl transition-all duration-300 hover:scale-[1.01] active:scale-[0.99] disabled:opacity-70"
                style={`background-color: ${getAccent()}; color: ${getContrastColor(getAccent())}`}
                type="button"
                onclick={enableOtp}
                disabled={isBusy || otpCodeInput.length < 6 || !otpSetupConfirmPassword}
              >
                {isBusy ? 'Enabling...' : 'Enable 2FA'}
              </button>
              <button
                class="flex-1 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
                style={`color: ${getAccent()}`}
                type="button"
                onclick={() => { isOtpSetupActive = false; otpCodeInput = ''; otpSetupConfirmPassword = ''; }}
                disabled={isBusy}
              >
                Cancel
              </button>
            </div>
          </div>
        {/if}
      </div>

      <!-- Passkeys -->
      <div class="mt-4">
        <div class="flex items-center justify-between gap-4">
          <div>
            <div class="text-sm font-medium text-slate-900 dark:text-slate-100">Passkeys</div>
            <div class="text-xs text-slate-500 dark:text-slate-400">
              Use biometric or hardware keys to log in without a password.
            </div>
          </div>
          <button
            class="rounded-full border border-slate-200 bg-white px-6 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
            style={`color: ${getAccent()}`}
            type="button"
            onclick={() => { isPasskeyAddActive = true; passkeyError = ''; loadPasskeys(); }}
            disabled={isBusy}
          >
            Add Key
          </button>
        </div>

        {#if isPasskeyAddActive}
          <div class="mt-4 space-y-4 rounded-xl bg-slate-50 p-4 dark:bg-white/5">
            <div>
              <label for="passkey-name" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Key Name</label>
              <input
                id="passkey-name"
                type="text"
                class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none dark:border-white/10 dark:bg-slate-800"
                bind:value={newPasskeyName}
                placeholder="e.g. MacBook Air, YubiKey"
              />
            </div>
            
            {#if passkeyError}
              <div class="text-xs font-medium text-red-600 dark:text-red-400">{passkeyError}</div>
            {/if}

            <div class="flex gap-2">
              <button
                class="flex-1 rounded-full px-4 py-2 text-sm font-bold shadow-xl transition-all duration-300 hover:scale-[1.01] active:scale-[0.99] disabled:opacity-70"
                style={`background-color: ${getAccent()}; color: ${getContrastColor(getAccent())}`}
                type="button"
                onclick={addPasskey}
                disabled={isBusy || !newPasskeyName}
              >
                {isBusy ? 'Registering...' : 'Continue'}
              </button>
              <button
                class="flex-1 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
                style={`color: ${getAccent()}`}
                type="button"
                onclick={() => { isPasskeyAddActive = false; newPasskeyName = ''; }}
                disabled={isBusy}
              >
                Cancel
              </button>
            </div>
          </div>
        {/if}

        {#if passkeys.length > 0}
          <div class="mt-4 space-y-2">
            {#each passkeys as pk (pk.id)}
              <div class="flex items-center justify-between rounded-lg border border-slate-100 bg-white/50 px-3 py-2 dark:border-white/5 dark:bg-slate-900/50">
                <div class="flex items-center gap-2">
                  <Key label="" size={16} className="text-slate-400" />
                  <span class="text-sm font-medium">{pk.name}</span>
                </div>
                <button
                  class="rounded-full bg-red-600/10 px-3 py-1.5 text-xs font-bold text-red-600 transition-all hover:bg-red-600 hover:text-white dark:bg-red-900/30 dark:text-red-400 dark:hover:bg-red-600 dark:hover:text-white"
                  type="button"
                  onclick={() => removePasskey(pk.id)}
                  disabled={isBusy}
                >
                  Delete
                </button>
              </div>
            {/each}
          </div>
        {/if}
      </div>

      <!-- API Keys -->
      <div class="border-t border-slate-100 pt-4 dark:border-white/5">
        <div class="flex items-center justify-between gap-4">
          <div>
            <div class="text-sm font-medium text-slate-900 dark:text-slate-100">API Keys</div>
            <div class="text-xs text-slate-500 dark:text-slate-400">
              Create API keys for integrations like iOS Shortcuts or browser extensions.
            </div>
          </div>
          <button
            class="rounded-full border border-slate-200 bg-white px-6 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
            style={`color: ${getAccent()}`}
            type="button"
            onclick={() => { isApiKeyAddActive = true; apiKeyError = ''; newApiKeyName = ''; newApiKeyValue = ''; }}
            disabled={isBusy}
          >
            Create Key
          </button>
        </div>

        {#if isApiKeyAddActive}
          <div class="mt-4 space-y-4 rounded-xl bg-slate-50 p-4 dark:bg-white/5">
            {#if newApiKeyValue}
              <!-- Show newly created key -->
              <div class="space-y-3">
                <div class="rounded-lg bg-amber-50 border border-amber-200 p-3 dark:bg-amber-950/20 dark:border-amber-900/30">
                  <div class="text-sm font-medium text-amber-800 dark:text-amber-300 mb-2">
                    Copy your API key now!
                  </div>
                  <div class="text-xs text-amber-700 dark:text-amber-400 mb-2">
                    This is the only time you will see this key. Store it securely.
                  </div>
                  <div class="flex items-center gap-2">
                    <code class="flex-1 bg-white dark:bg-slate-900 px-2 py-1.5 rounded text-xs font-mono break-all">
                      {newApiKeyValue}
                    </code>
                    <button
                      class="shrink-0 rounded-lg bg-amber-100 dark:bg-amber-900/30 px-3 py-1.5 text-xs font-medium text-amber-800 dark:text-amber-300"
                      type="button"
                      onclick={copyApiKey}
                    >
                      {showCopiedKey ? 'Copied!' : 'Copy'}
                    </button>
                  </div>
                </div>
                <button
                  class="w-full rounded-full border border-slate-200 bg-white px-6 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
                  style={`color: ${getAccent()}`}
                  type="button"
                  onclick={() => { isApiKeyAddActive = false; newApiKeyValue = ''; }}
                >
                  Done
                </button>
              </div>
            {:else}
              <!-- Create new key form -->
              <div>
                <label for="api-key-name" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Key Name</label>
                <input
                  id="api-key-name"
                  type="text"
                  class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none dark:border-white/10 dark:bg-slate-800"
                  bind:value={newApiKeyName}
                  placeholder="e.g. iOS Shortcuts, Chrome Extension"
                />
              </div>

              {#if apiKeyError}
                <div class="text-xs font-medium text-red-600 dark:text-red-400">{apiKeyError}</div>
              {/if}

              <div class="flex gap-2">
                <button
                  class="relative flex flex-1 items-center justify-center gap-2 rounded-full px-6 py-2.5 text-sm font-bold shadow-xl transition-all duration-300 hover:scale-[1.01] active:scale-[0.99] disabled:opacity-70"
                  style={`background-color: ${getAccent()}; color: ${getContrastColor(getAccent())}`}
                  type="button"
                  onclick={createApiKey}
                  disabled={isBusy || !newApiKeyName || showApiKeySaved}
                >
                  {#if isBusy}
                    <div class="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></div>
                    <span>Creating...</span>
                  {:else if showApiKeySaved}
                    <div class="animate-in zoom-in fade-in duration-300 flex items-center gap-2">
                      <Check label="" size={18} strokeWidth={3} />
                      <span>Saved!</span>
                    </div>
                  {:else}
                    <span>Create</span>
                  {/if}
                </button>
                <button
                  class="flex-1 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
                  style={`color: ${getAccent()}`}
                  type="button"
                  onclick={() => { isApiKeyAddActive = false; newApiKeyName = ''; }}
                  disabled={isBusy}
                >
                  Cancel
                </button>
              </div>
            {/if}
          </div>
        {/if}

        {#if apiKeys.length > 0}
          <div class="mt-4 space-y-2">
            {#each apiKeys as key (key.id)}
              <div class="flex items-center justify-between rounded-lg border border-slate-100 bg-white/50 px-3 py-2 dark:border-white/5 dark:bg-slate-900/50">
                <div class="flex items-center gap-2 min-w-0">
                  <Key label="" size={16} className="text-slate-400 shrink-0" />
                  <div class="min-w-0 flex-1">
                    <span class="text-sm font-medium block truncate">{key.name}</span>
                    <span class="text-xs text-slate-400">
                      Created {new Date(key.created_at).toLocaleDateString()}
                      {#if key.last_used_at}
                        · Last used {new Date(key.last_used_at).toLocaleDateString()}
                      {:else}
                        · Never used
                      {/if}
                    </span>
                  </div>
                </div>
                <button
                  class="shrink-0 ml-2 rounded-full bg-red-600/10 px-3 py-1.5 text-xs font-bold text-red-600 transition-all hover:bg-red-600 hover:text-white dark:bg-red-900/30 dark:text-red-400 dark:hover:bg-red-600 dark:hover:text-white"
                  type="button"
                  onclick={() => deleteApiKey(key.id)}
                  disabled={isBusy}
                >
                  Delete
                </button>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>

    {#if $currentUser?.is_admin}
      <!-- Admin -->
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
              style={`background-color: ${getAccentTint()}; color: ${getAccent()}`}
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

    <!-- Data & Migration -->
    <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
      <div class="text-xs uppercase text-slate-500">Data & Migration</div>
      <div class="mt-3 space-y-3">
        <button
          class="al-icon-wrapper flex w-full items-center gap-4 rounded-xl border border-dashed border-slate-200 p-3 text-left transition-all hover:border-slate-300 hover:bg-slate-50/50 dark:border-white/10 dark:hover:bg-white/5"
          onclick={() => currentView.set({ type: 'importer' })}
          type="button"
        >
          <div class="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400">
            <Upload label="" size={20} />
          </div>
          <div class="flex-1">
            <div class="font-medium text-slate-900 dark:text-slate-100">Import from TwoS</div>
            <div class="text-xs text-slate-500 dark:text-slate-400">Bring your lists and things into snipsel</div>
          </div>
          <ChevronRight label="" size={20} className="text-slate-400" />
        </button>
        
        <button
          class="al-icon-wrapper flex w-full items-center gap-4 rounded-xl border border-slate-200 p-3 text-left transition-all hover:border-slate-300 hover:bg-slate-50/50 dark:border-white/10 dark:hover:bg-white/5"
          onclick={() => currentView.set({ type: 'recycle-bin' })}
          type="button"
        >
          <div class="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-red-50 text-red-600 dark:bg-red-900/20 dark:text-red-400">
            <Trash2 label="" size={20} />
          </div>
          <div class="flex-1">
            <div class="font-medium text-slate-900 dark:text-slate-100">Recycle Bin</div>
            <div class="text-xs text-slate-500 dark:text-slate-400">Restore deleted collections and snipsels</div>
          </div>
          <ChevronRight label="" size={20} className="text-slate-400" />
        </button>

        <div class="mt-6 border-t border-slate-100 pt-6 dark:border-white/5">
          <div class="flex items-center justify-between gap-4">
            <div class="flex-1">
              <div class="flex items-center gap-2 font-medium text-slate-900 dark:text-slate-100">
                <div class="grid h-8 w-8 place-items-center rounded-full bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400">
                  <SquareCheck label="" size={16} />
                </div>
                Full Offline Sync
              </div>
              <div class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                Download all collections and snipsels to your device for offline use.
                {#if lastFullSync}
                  <div class="mt-1 font-medium text-blue-600 dark:text-blue-400">Last sync: {new Date(lastFullSync).toLocaleString()}</div>
                {/if}
              </div>
            </div>
            <button
              class="rounded-full border border-slate-200 bg-white px-6 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
              style={`color: ${getAccent()}`}
              type="button"
              onclick={performFullSync}
              disabled={isBusy || syncStatus === 'syncing'}
            >
              {#if syncStatus === 'syncing'}
                Syncing...
              {:else}
                Sync Now
              {/if}
            </button>
          </div>

          {#if syncStatus === 'syncing'}
            <div class="mt-4 space-y-2">
              <div class="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-slate-400">
                <span>{syncStage}</span>
                <span>{Math.round(syncProgress)}%</span>
              </div>
              <div class="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-white/5">
                <div 
                  class="h-full transition-all duration-500 ease-out"
                  style={`width: ${syncProgress}%; background-color: ${getAccent()}; box-shadow: 0 0 10px ${getAccent()}40`}
                ></div>
              </div>
            </div>
          {/if}

          {#if syncStatus === 'error'}
            <div class="mt-2 text-xs font-medium text-red-600 dark:text-red-400">{syncError}</div>
          {/if}
          {#if syncStatus === 'success'}
            <div class="mt-2 text-xs font-medium text-green-600 dark:text-green-400">Sync completed successfully!</div>
          {/if}
        </div>
      </div>
    </div>

    <div class="py-4 text-center text-xs text-slate-400">
      More settings coming soon.
    </div>
  </div>
</div>
