<script lang="ts">
  import { fly, fade } from 'svelte/transition';
  import type { Component } from 'svelte';
  
  interface Props {
    title: string;
    message: string;
    confirmLabel?: string;
    onConfirm: () => void;
    onCancel: () => void;
    icon: Component<any>;
    iconClass?: string;
    confirmClass?: string;
  }

  let { title, message, confirmLabel = 'Confirm', onConfirm, onCancel, icon: Icon, iconClass = "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400", confirmClass = "bg-primary text-white hover:bg-black/80" }: Props = $props();

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      e.preventDefault();
      onCancel();
    } else if (e.key === 'Enter') {
      e.preventDefault();
      onConfirm();
    }
  }
</script>

<svelte:window onkeydown={handleKeydown} />

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<div
  class="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm"
  role="dialog"
  aria-modal="true"
  aria-labelledby="confirm-modal-title"
  tabindex="-1"
  onclick={(e) => e.target === e.currentTarget && onCancel()}
>
  <div class="w-full max-w-sm overflow-hidden rounded-2xl bg-white/95 shadow-2xl ring-1 ring-black/5 backdrop-blur-md dark:bg-slate-900/95 dark:ring-white/10 p-6" in:fly={{ y: 20, duration: 200 }} out:fade={{ duration: 150 }}>
    <div class="flex flex-col items-center text-center">
      <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-full {iconClass}">
        <Icon label="" size={24} />
      </div>
      
      <h2 id="confirm-modal-title" class="text-xl font-bold text-slate-900 dark:text-slate-100">
        {title}
      </h2>
      
      <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
        {message}
      </p>

      <div class="mt-8 flex w-full flex-col gap-3 sm:flex-row-reverse">
        <button
          type="button"
          class="flex h-11 flex-1 items-center justify-center rounded-xl px-4 font-semibold transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 sm:flex-initial sm:min-w-[100px] {confirmClass}"
          onclick={onConfirm}
        >
          {confirmLabel}
        </button>
        <button
          type="button"
          class="flex h-11 flex-1 items-center justify-center rounded-xl bg-slate-100 px-4 font-medium text-slate-600 transition-colors hover:bg-slate-200 focus:outline-none dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 sm:flex-initial sm:min-w-[100px]"
          onclick={onCancel}
        >
          Cancel
        </button>
      </div>
    </div>
  </div>
</div>
