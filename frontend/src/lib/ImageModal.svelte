<script lang="ts">
  import { fly, fade, scale } from 'svelte/transition';
  import Download from '@animated-color-icons/lucide-svelte/Download.svelte';
  import X from '@animated-color-icons/lucide-svelte/X.svelte';
  import ChevronLeft from '@animated-color-icons/lucide-svelte/ChevronLeft.svelte';
  import ChevronRight from '@animated-color-icons/lucide-svelte/ChevronRight.svelte';
  
  interface Attachment {
    id: string;
    filename: string;
  }
  
  interface Props {
    attachments: Attachment[];
    currentIndex: number;
    onClose: () => void;
    onNavigate: (index: number) => void;
  }

  let { attachments, currentIndex, onClose, onNavigate }: Props = $props();

  let blobUrls = $state<Map<string, string>>(new Map());
  let loading = $state(false);
  let error = $state<string | null>(null);
  let direction = $state<'left' | 'right'>('right');

  const currentAttachment = $derived(attachments[currentIndex]);
  const currentBlobUrl = $derived(currentAttachment ? blobUrls.get(currentAttachment.id) : null);

  async function loadImage(id: string) {
    if (blobUrls.has(id)) return;
    
    loading = true;
    error = null;
    try {
      const res = await fetch(`/api/attachments/${id}`, { credentials: 'include' });
      if (!res.ok) {
        throw new Error('Failed to load image');
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      blobUrls.set(id, url);
      blobUrls = blobUrls;
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load image';
    } finally {
      loading = false;
    }
  }

  function navigate(delta: number) {
    const newIndex = currentIndex + delta;
    if (newIndex >= 0 && newIndex < attachments.length) {
      direction = delta > 0 ? 'right' : 'left';
      onNavigate(newIndex);
      loadImage(attachments[newIndex].id);
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
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      navigate(-1);
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      navigate(1);
    }
  }

  $effect(() => {
    if (attachments.length > 0 && currentIndex >= 0) {
      const attachment = attachments[currentIndex];
      if (attachment) {
        loadImage(attachment.id);
      }
    }
  });
</script>

<svelte:window onkeydown={handleKeydown} />

{#if attachments.length > 0 && currentIndex >= 0}
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
      {#if currentBlobUrl}
        {#key currentIndex}
          <img
            class="max-h-[85vh] max-w-[85vw] rounded-lg object-contain shadow-2xl"
            src={currentBlobUrl}
            alt={currentAttachment.filename}
            in:fly={{ x: direction === 'right' ? 100 : -100, duration: 300, opacity: 0.8 }}
            out:fly={{ x: direction === 'right' ? -100 : 100, duration: 300, opacity: 0.8 }}
          />
        {/key}
      {:else if error}
        <div class="flex h-48 w-48 items-center justify-center rounded-lg bg-white/10">
          <div class="text-sm text-red-400">{error}</div>
        </div>
      {:else}
        <div class="flex h-48 w-48 items-center justify-center rounded-lg bg-white/10">
          <div class="text-sm text-white/70">Loading...</div>
        </div>
      {/if}

      {#if attachments.length > 1}
        <button
          class="nav-arrow nav-arrow-left"
          type="button"
          onclick={() => navigate(-1)}
          disabled={currentIndex === 0}
          aria-label="Previous image"
          style="opacity: {currentIndex === 0 ? '0.2' : '0.6'}"
        >
          <ChevronLeft label="" size={32} strokeWidth={2} />
        </button>
        
        <button
          class="nav-arrow nav-arrow-right"
          type="button"
          onclick={() => navigate(1)}
          disabled={currentIndex === attachments.length - 1}
          aria-label="Next image"
          style="opacity: {currentIndex === attachments.length - 1 ? '0.2' : '0.6'}"
        >
          <ChevronRight label="" size={32} strokeWidth={2} />
        </button>

        <div class="absolute -bottom-10 left-1/2 -translate-x-1/2 rounded-full bg-white/20 px-4 py-1.5 text-sm font-medium text-white backdrop-blur-sm">
          {currentIndex + 1} / {attachments.length}
        </div>
      {/if}

      {#if currentBlobUrl}
        <div class="absolute right-2 top-2 flex items-center overflow-hidden rounded-full bg-white/90 shadow-lg backdrop-blur-sm">
          <a
            class="flex h-10 w-10 items-center justify-center text-slate-700 transition-colors hover:bg-white"
            href={currentBlobUrl}
            download={currentAttachment.filename}
            aria-label="Download image"
          >
            <Download label="" size={20} strokeWidth={2} />
          </a>
          <div class="h-5 w-px bg-slate-200"></div>
          <button
            class="al-icon-wrapper flex h-10 w-10 items-center justify-center text-slate-700 transition-colors hover:bg-white"
            type="button"
            aria-label="Close"
            onclick={onClose}
          >
            <X label="" size={20} strokeWidth={2} />
          </button>
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .nav-arrow {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    width: 48px;
    height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.1);
    border: none;
    border-radius: 8px;
    color: white;
    cursor: pointer;
    transition: all 0.2s ease;
    backdrop-filter: blur(4px);
  }

  .nav-arrow:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.25);
    opacity: 1 !important;
  }

  .nav-arrow:disabled {
    cursor: not-allowed;
  }

  .nav-arrow-left {
    left: -64px;
  }

  .nav-arrow-right {
    right: -64px;
  }

  @media (max-width: 768px) {
    .nav-arrow {
      width: 40px;
      height: 60px;
    }
    
    .nav-arrow-left {
      left: -48px;
    }

    .nav-arrow-right {
      right: -48px;
    }
  }
</style>
