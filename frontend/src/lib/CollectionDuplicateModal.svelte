<script lang="ts">
  import { currentUser } from './session';

  interface Props {
    defaultTitle: string;
    onConfirm: (title: string) => void;
    onCancel: () => void;
  }

  let { defaultTitle, onConfirm, onCancel }: Props = $props();

  let title = $state(defaultTitle);
  let inputRef: HTMLInputElement | null = $state(null);

  $effect(() => {
    if (inputRef) {
      inputRef.focus();
      inputRef.select();
    }
  });

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      onCancel();
    } else if (e.key === 'Enter') {
      handleConfirm();
    }
  }

  function handleConfirm() {
    const trimmedTitle = title.trim();
    if (trimmedTitle) {
      onConfirm(trimmedTitle);
    }
  }

  const DEFAULT_ACCENT = '#4f46e5';

  function getAccent(): string {
    const raw = ($currentUser?.default_collection_header_color || '').trim() || DEFAULT_ACCENT;
    return /^#[0-9a-fA-F]{6}$/.test(raw) ? raw : DEFAULT_ACCENT;
  }
</script>

<div
  class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
  onclick={onCancel}
  onkeydown={handleKeydown}
  role="dialog"
  aria-modal="true"
  tabindex="-1"
>
  <div
    class="w-full max-w-sm overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-white/10 dark:bg-slate-900"
    onclick={(e) => e.stopPropagation()}
    role="document"
  >
    <div class="p-6">
      <h3 class="mb-1 text-lg font-semibold text-slate-900 dark:text-slate-100">
        Duplicate Collection
      </h3>
      <p class="mb-4 text-sm text-slate-500 dark:text-slate-400">
        Enter a name for the copied collection.
      </p>

      <label class="mb-4 block">
        <span class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">
          Collection name
        </span>
        <input
          bind:this={inputRef}
          type="text"
          class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-slate-100 dark:ring-white/10"
          bind:value={title}
          onkeydown={handleKeydown}
          placeholder="Collection name..."
        />
      </label>

      <div class="flex gap-3">
        <button
          class="flex-1 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition-colors hover:bg-slate-50 dark:border-white/10 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
          type="button"
          onclick={onCancel}
        >
          Cancel
        </button>
        <button
          class="flex-1 rounded-xl px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:opacity-90 disabled:opacity-50"
          type="button"
          style="background-color: {getAccent()}"
          onclick={handleConfirm}
          disabled={!title.trim()}
        >
          Duplicate
        </button>
      </div>
    </div>
  </div>
</div>
