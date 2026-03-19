<script lang="ts">
  import { fly, fade, scale } from 'svelte/transition';
  import Download from '@animated-color-icons/lucide-svelte/Download.svelte';
  import X from '@animated-color-icons/lucide-svelte/X.svelte';
  interface Props {
    attachmentId: string | null;
    filename: string;
    onClose: () => void;
  }

  let { attachmentId, filename, onClose }: Props = $props();

  let blobUrl = $state<string | null>(null);
  let loading = $state(false);
  let error = $state<string | null>(null);

  async function loadImage(id: string) {
    loading = true;
    error = null;
    try {
      const res = await fetch(`/api/attachments/${id}`, { credentials: 'include' });
      if (!res.ok) {
        throw new Error('Failed to load image');
      }
      const blob = await res.blob();
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
      }
      blobUrl = URL.createObjectURL(blob);
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load image';
    } finally {
      loading = false;
    }
  }

  function handleBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) {
      onClose();
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      onClose();
    }
  }

  $effect(() => {
    if (attachmentId) {
      loadImage(attachmentId);
    }
    return () => {
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
      }
    };
  });
</script>

<svelte:window onkeydown={handleKeydown} />

{#if attachmentId}
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm"
    role="dialog"
    aria-modal="true"
    aria-label="Image preview"
    tabindex="-1"
    onclick={handleBackdropClick}
    onkeydown={handleKeydown}
  >
    <div class="relative max-h-full max-w-full" in:scale={{ start: 0.9, duration: 150 }} out:fade={{ duration: 100 }}>
      {#if loading}
        <div class="flex h-48 w-48 items-center justify-center rounded-lg bg-white/10">
          <div class="text-sm text-white/70">Loading...</div>
        </div>
      {:else if error}
        <div class="flex h-48 w-48 items-center justify-center rounded-lg bg-white/10">
          <div class="text-sm text-red-400">{error}</div>
        </div>
      {:else if blobUrl}
        <img
          class="max-h-[85vh] max-w-[85vw] rounded-lg object-contain shadow-2xl"
          src={blobUrl}
          alt={filename}
        />
      {/if}

      {#if blobUrl}
        <a
          class="absolute right-2 top-2 flex h-10 w-10 items-center justify-center rounded-full bg-white/90 text-slate-700 shadow-lg transition-colors hover:bg-white"
          href={blobUrl}
          download={filename}
          aria-label="Download image"
        >
          <Download label="" size={20} strokeWidth={2} />
        </a>
      {/if}

      <button
        class="al-icon-wrapper absolute -right-3 -top-3 flex h-8 w-8 items-center justify-center rounded-full bg-white/90 text-slate-700 shadow-lg transition-colors hover:bg-white"
        type="button"
        aria-label="Close"
        onclick={onClose}
      >
        <X label="" size={20} strokeWidth={2} />
      </button>
    </div>
  </div>
{/if}
