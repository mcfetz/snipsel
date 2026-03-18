<script lang="ts">
  import Download from '@animated-color-icons/lucide-svelte/Download.svelte';
  import X from '@animated-color-icons/lucide-svelte/X.svelte';
  import { api } from './api';

  interface Props {
    attachmentId: string | null;
    filename: string;
    onClose: () => void;
  }

  let { attachmentId, filename, onClose }: Props = $props();

  let videoUrl = $state<string | null>(null);
  let loading = $state(false);
  let error = $state<string | null>(null);

  async function loadVideo(id: string) {
    loading = true;
    error = null;
    try {
      const res = await fetch(api.attachments.downloadUrl(id), { credentials: 'include' });
      if (!res.ok) {
        throw new Error('Failed to load video');
      }
      const blob = await res.blob();
      if (videoUrl) {
        URL.revokeObjectURL(videoUrl);
      }
      videoUrl = URL.createObjectURL(blob);
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load video';
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
      loadVideo(attachmentId);
    }
    return () => {
      if (videoUrl) {
        URL.revokeObjectURL(videoUrl);
      }
    };
  });
</script>

<svelte:window onkeydown={handleKeydown} />

{#if attachmentId}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-4 backdrop-blur-sm"
    role="dialog"
    aria-modal="true"
    aria-label="Video preview"
    tabindex="-1"
    onclick={handleBackdropClick}
  >
    <div class="relative w-full max-w-4xl max-h-full flex flex-col items-center">
      {#if loading}
        <div class="flex h-64 w-full items-center justify-center rounded-xl bg-slate-900/50">
          <div class="flex flex-col items-center gap-3">
             <div class="h-8 w-8 animate-spin rounded-full border-4 border-slate-600 border-t-indigo-500"></div>
             <div class="text-sm text-slate-400 font-medium">Loading video...</div>
          </div>
        </div>
      {:else if error}
        <div class="flex h-64 w-full items-center justify-center rounded-xl bg-slate-900/50 border border-red-500/20">
          <div class="text-sm text-red-400 font-medium">{error}</div>
        </div>
      {:else if videoUrl}
        <div class="relative w-full overflow-hidden rounded-xl bg-black shadow-2xl ring-1 ring-white/10">
          <video
            src={videoUrl}
            class="w-full h-auto max-h-[80vh]"
            controls
            autoplay
          >
            <track kind="captions" />
            Your browser does not support the video tag.
          </video>
        </div>
      {/if}

      <div class="mt-4 flex items-center justify-center gap-3 w-full">
        <span class="truncate text-sm font-medium text-slate-300 max-w-[200px]">{filename}</span>
        
        {#if videoUrl}
          <a
            class="flex h-9 items-center gap-2 rounded-full bg-white/10 px-4 text-sm font-medium text-white transition-colors hover:bg-white/20"
            href={videoUrl}
            download={filename}
          >
            <Download size={16} strokeWidth={2} />
            Download
          </a>
        {/if}
      </div>

      <button
        class="absolute -right-2 -top-12 flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-white transition-colors hover:bg-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
        type="button"
        aria-label="Close"
        onclick={onClose}
      >
        <X size={24} strokeWidth={2.5} />
      </button>
    </div>
  </div>
{/if}
