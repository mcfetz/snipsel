<script lang="ts">
  import Info from '@animated-color-icons/lucide-svelte/Info.svelte';
  interface Props {
    title: string;
    message: string;
    onClose: () => void;
  }

  let { title, message, onClose }: Props = $props();

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape' || e.key === 'Enter') {
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
    <div class="flex flex-col items-center text-center">
      <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
        <Info size={24} strokeWidth={2} />
      </div>
      
      <h2 id="info-modal-title" class="text-xl font-bold text-slate-900 dark:text-slate-100">
        {title}
      </h2>
      
      <p class="mt-2 text-sm text-slate-500 dark:text-slate-400 whitespace-pre-wrap">
        {message}
      </p>

      <div class="mt-8 flex w-full">
        <button
          type="button"
          class="flex h-11 w-full items-center justify-center rounded-xl bg-slate-900 px-4 font-semibold text-white transition-all hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white"
          onclick={onClose}
        >
          OK
        </button>
      </div>
    </div>
  </div>
</div>
