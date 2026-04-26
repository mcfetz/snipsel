<script lang="ts">
  import { fly, fade } from 'svelte/transition';
  import Info from '@animated-color-icons/lucide-svelte/Info.svelte';
  import Dices from '@animated-color-icons/lucide-svelte/Dices.svelte';
  import Ban from '@animated-color-icons/lucide-svelte/Ban.svelte';
  import { api, type Snipsel } from '../lib/api';

  interface Props {
    snipsel: Snipsel;
    onClose: () => void;
    onUpdate: (updated: Snipsel) => void;
  }

  let { snipsel, onClose, onUpdate }: Props = $props();
  let isBusy = $state(false);

  async function toggleBan() {
    isBusy = true;
    try {
      const newCount = snipsel.diced_count === -1 ? 0 : -1;
      const res = await api.snipsels.update(snipsel.id, { diced_count: newCount } as any);
      onUpdate(res.snipsel);
    } catch (err) {
      console.error("Failed to toggle ban", err);
    } finally {
      isBusy = false;
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
    }
  }
</script>

<svelte:window onkeydown={handleKeydown} />

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<div
  class="fixed inset-0 z-[110] flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm transition-all"
  role="dialog"
  aria-modal="true"
  aria-labelledby="info-modal-title"
  tabindex="-1"
  onclick={(e) => e.target === e.currentTarget && onClose()}
>
  <div class="w-full max-w-sm overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-black/5 dark:bg-slate-900 dark:ring-white/10 p-6">
    <div class="flex flex-col items-start text-left">
      <div class="mb-4 flex h-12 w-12 self-center items-center justify-center rounded-full bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
        <Info label="" size={24} strokeWidth={2} />
      </div>
      
      <h2 id="info-modal-title" class="w-full self-center text-center text-xl font-bold text-slate-900 dark:text-slate-100 mb-6">
        Snipsel Info
      </h2>
      
      <div class="w-full space-y-4 text-sm">
        <div class="flex justify-between border-b border-slate-100 dark:border-white/5 pb-2">
          <span class="text-slate-500">ID</span>
          <span class="font-mono text-[10px] text-slate-400">{snipsel.id}</span>
        </div>
        <div class="flex justify-between border-b border-slate-100 dark:border-white/5 pb-2">
          <span class="text-slate-500">Type</span>
          <span class="font-medium dark:text-slate-200">{snipsel.type}</span>
        </div>
        <div class="flex justify-between border-b border-slate-100 dark:border-white/5 pb-2">
          <span class="text-slate-500">Created</span>
          <span class="dark:text-slate-300">{new Date(snipsel.created_at).toLocaleString()}</span>
        </div>
        
        <div class="pt-2">
          <div class="flex items-center justify-between rounded-xl bg-slate-50 p-3 dark:bg-white/5">
            <div class="flex items-center gap-2">
              <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-white shadow-sm dark:bg-slate-800">
                <Dices label="" size={16} className="text-slate-600 dark:text-slate-400" />
              </div>
              <div>
                <div class="text-xs font-semibold text-slate-700 dark:text-slate-200">Diced Count</div>
                <div class="text-[10px] text-slate-500">{snipsel.diced_count === -1 ? 'Banned' : `${snipsel.diced_count} times shown`}</div>
              </div>
            </div>
            <div class="text-lg font-bold text-slate-700 dark:text-slate-200">
              {snipsel.diced_count === -1 ? '-' : snipsel.diced_count}
            </div>
          </div>
        </div>

        <div class="flex items-center justify-between p-1">
          <div class="flex items-center gap-2">
            <Ban label="" size={16} className={snipsel.diced_count === -1 ? 'text-red-500' : 'text-slate-400'} />
            <span class="font-medium text-slate-700 dark:text-slate-200">Ban from Diced Moments</span>
          </div>
          <button
            class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 {snipsel.diced_count === -1 ? 'bg-red-500' : 'bg-slate-200 dark:bg-slate-700'}"
            role="switch"
            aria-checked={snipsel.diced_count === -1}
            onclick={toggleBan}
            disabled={isBusy}
          >
            <span
              class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out {snipsel.diced_count === -1 ? 'translate-x-5' : 'translate-x-0'}"
            ></span>
          </button>
        </div>
      </div>

      <div class="mt-8 flex w-full">
        <button
          type="button"
          class="flex h-11 w-full items-center justify-center rounded-xl bg-slate-900 px-4 font-semibold text-white transition-all hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white"
          onclick={onClose}
        >
          Close
        </button>
      </div>
    </div>
  </div>
</div>
