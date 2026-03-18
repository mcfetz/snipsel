<script lang="ts">
  import CloudUpload from '@animated-color-icons/lucide-svelte/CloudUpload.svelte';
  interface Props {
    filename: string;
    percent: number;
  }

  let { filename, percent }: Props = $props();
</script>

<div
  class="fixed inset-0 z-[120] flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm transition-all"
  role="dialog"
  aria-modal="true"
  aria-labelledby="progress-modal-title"
>
  <div class="w-full max-w-sm overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-black/5 dark:bg-slate-900 dark:ring-white/10 p-6">
    <div class="flex flex-col items-center text-center">
      <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
        <CloudUpload size={24} className="animate-pulse" strokeWidth={2} />
      </div>
      
      <h2 id="progress-modal-title" class="text-xl font-bold text-slate-900 dark:text-slate-100">
        Wird hochgeladen...
      </h2>
      
      <p class="mt-1 text-sm text-slate-500 dark:text-slate-400 truncate w-full px-4">
        {filename}
      </p>

      <div class="mt-6 w-full">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-semibold text-blue-600 dark:text-blue-400">Fortschritt</span>
          <span class="text-xs font-semibold text-blue-600 dark:text-blue-400">{Math.round(percent)}%</span>
        </div>
        <div class="h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
          <div 
            class="h-full bg-blue-600 transition-all duration-300 ease-out" 
            style="width: {percent}%"
          ></div>
        </div>
      </div>

      <p class="mt-6 text-xs text-slate-400 dark:text-slate-500">
        Bitte schließe das Fenster nicht.
      </p>
    </div>
  </div>
</div>
