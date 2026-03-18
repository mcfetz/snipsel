<script lang="ts">
  import Trash2 from '@animated-color-icons/lucide-svelte/Trash2.svelte';
  interface Props {
    title: string;
    message: string;
    confirmLabel?: string;
    onConfirm: () => void;
    onCancel: () => void;
  }

  let { title, message, confirmLabel = 'Löschen', onConfirm, onCancel }: Props = $props();

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
  class="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm transition-all"
  role="dialog"
  aria-modal="true"
  aria-labelledby="delete-modal-title"
  tabindex="-1"
  onclick={(e) => e.target === e.currentTarget && onCancel()}
>
  <div class="w-full max-w-sm overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-black/5 dark:bg-slate-900 dark:ring-white/10 p-6">
    <div class="flex flex-col items-center text-center">
      <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400">
        <Trash2 size={24} />
      </div>
      
      <h2 id="delete-modal-title" class="text-xl font-bold text-slate-900 dark:text-slate-100">
        {title}
      </h2>
      
      <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
        {message}
      </p>

      <div class="mt-8 flex w-full flex-col gap-3 sm:flex-row-reverse">
        <button
          type="button"
          class="flex h-11 flex-1 items-center justify-center rounded-xl bg-red-600 px-4 font-semibold text-white transition-all hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 dark:bg-red-700 dark:hover:bg-red-600 sm:flex-initial sm:min-w-[100px]"
          onclick={onConfirm}
        >
          {confirmLabel}
        </button>
        <button
          type="button"
          class="flex h-11 flex-1 items-center justify-center rounded-xl bg-slate-100 px-4 font-medium text-slate-600 transition-colors hover:bg-slate-200 focus:outline-none dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 sm:flex-initial sm:min-w-[100px]"
          onclick={onCancel}
        >
          Abbrechen
        </button>
      </div>
    </div>
  </div>
</div>
