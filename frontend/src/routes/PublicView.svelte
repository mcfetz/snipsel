<script lang="ts">
  import { onMount } from 'svelte';
  import { api, type CollectionItem } from '../lib/api';
  import PublicCollectionOutliner from '../lib/PublicCollectionOutliner.svelte';

  let { token } = $props<{ token: string }>();

  let collection = $state<any>(null);
  let items = $state<CollectionItem[]>([]);
  let canWrite = $state(false);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let passcode = $state('');
  let verifyingPasscode = $state(false);
  let passcodeError = $state<string | null>(null);

  async function loadData() {
    loading = true;
    error = null;
    try {
      const res = await api.public.getCollection(token);
      collection = res.collection;
      
      if (collection.is_unlocked) {
        await loadItems();
      }
    } catch (err: any) {
      error = err.error?.message || 'Kollektion konnte nicht geladen werden.';
    } finally {
      loading = false;
    }
  }

  async function loadItems() {
    try {
      const res = await api.public.listSnipsels(token);
      items = res.items;
      canWrite = res.can_write;
    } catch (err: any) {
      error = err.error?.message || 'Inhalt konnte nicht geladen werden.';
    }
  }

  async function handleVerifyPasscode() {
    verifyingPasscode = true;
    passcodeError = null;
    try {
      await api.public.verifyPasscode(token, passcode);
      await loadData(); // Reload to get items
    } catch (err: any) {
      passcodeError = err.error?.message || 'Invalid passcode.';
    } finally {
      verifyingPasscode = false;
    }
  }

  onMount(loadData);

  function getHeaderColor(): string {
    return collection?.header_color || '#4f46e5';
  }
</script>

<div class="min-h-screen bg-slate-50 dark:bg-slate-950 transition-colors duration-300">
  {#if loading}
    <div class="flex flex-col items-center justify-center min-h-screen p-8 text-center">
      <div class="w-10 h-10 border-4 border-slate-200 border-t-indigo-500 rounded-full animate-spin mb-4"></div>
      <p class="text-slate-500 dark:text-slate-400 font-medium">Lade öffentliche Kollektion...</p>
    </div>
  {:else if error}
    <div class="flex flex-col items-center justify-center min-h-screen p-8 text-center space-y-4">
      <div class="text-6xl">😕</div>
      <h1 class="text-2xl font-bold text-slate-900 dark:text-white">Oops!</h1>
      <p class="text-slate-600 dark:text-slate-400 max-w-md">{error}</p>
    </div>
  {:else if collection && collection.is_passcode_protected && !collection.is_unlocked}
    <div class="flex flex-col items-center justify-center min-h-screen p-8 text-center">
      <div class="text-7xl mb-6 transform hover:scale-110 transition-transform duration-300">{collection.icon}</div>
      <h1 class="text-3xl font-bold text-slate-900 dark:text-white mb-2">{collection.title}</h1>
      <p class="text-slate-600 dark:text-slate-400 mb-8">Diese Kollektion ist passwortgeschützt.</p>
      
      <div class="flex flex-col sm:flex-row gap-3 w-full max-w-sm">
        <input 
          type="password" 
          placeholder="Passcode eingeben" 
          class="flex-1 px-4 py-3 rounded-xl border border-slate-200 bg-white shadow-sm focus:ring-2 focus:ring-indigo-500/20 outline-none dark:border-white/10 dark:bg-slate-900 dark:text-white"
          bind:value={passcode}
          onkeydown={(e) => e.key === 'Enter' && handleVerifyPasscode()}
        />
        <button 
          class="px-6 py-3 rounded-xl font-bold text-white shadow-lg shadow-indigo-500/20 transition-all hover:brightness-110 active:scale-95 disabled:opacity-50"
          style="background-color: {getHeaderColor()}"
          onclick={handleVerifyPasscode} 
          disabled={verifyingPasscode || !passcode}
        >
          {verifyingPasscode ? 'Verifying...' : 'Unlock'}
        </button>
      </div>
      {#if passcodeError}
        <p class="mt-4 text-sm font-medium text-red-500">{passcodeError}</p>
      {/if}
    </div>
  {:else if collection}
    <PublicCollectionOutliner 
      {token} 
      {collection} 
      {items} 
      {canWrite}
      onReload={loadItems}
    />
  {/if}
</div>
