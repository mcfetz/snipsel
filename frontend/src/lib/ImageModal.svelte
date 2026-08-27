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

  let blobUrlCache = $state<Record<string, string>>({});
  let currentBlobUrl = $state<string | null>(null);
  let loading = $state(false);
  let error = $state<string | null>(null);
  let direction = $state<'left' | 'right'>('right');

  let lastRequestedId: string | null = null;

  const currentAttachment = $derived(attachments[currentIndex]);

  function preloadAdjacentImages() {
    const prevIndex = currentIndex - 1;
    const nextIndex = currentIndex + 1;
    if (prevIndex >= 0 && !blobUrlCache[attachments[prevIndex].id]) {
      loadImage(attachments[prevIndex].id, false);
    }
    if (nextIndex < attachments.length && !blobUrlCache[attachments[nextIndex].id]) {
      loadImage(attachments[nextIndex].id, false);
    }
  }

  async function loadImage(id: string, setAsCurrent: boolean = true) {
    if (blobUrlCache[id]) {
      if (setAsCurrent) currentBlobUrl = blobUrlCache[id];
      return;
    }
    if (setAsCurrent) {
      loading = true;
      error = null;
      lastRequestedId = id;
    }
    try {
      const res = await fetch(`/api/attachments/${id}`, { credentials: 'include' });
      if (!res.ok) {
        throw new Error('Failed to load image');
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      blobUrlCache[id] = url;
      if (setAsCurrent && lastRequestedId === id) {
        currentBlobUrl = url;
      }
    } catch (e) {
      if (setAsCurrent && lastRequestedId === id) {
        error = e instanceof Error ? e.message : 'Failed to load image';
      }
    } finally {
      if (setAsCurrent && lastRequestedId === id) {
        loading = false;
      }
    }
  }

  function navigate(delta: number) {
    const newIndex = currentIndex + delta;
    if (newIndex >= 0 && newIndex < attachments.length) {
      direction = delta > 0 ? 'right' : 'left';
      onNavigate(newIndex);
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
    if (currentAttachment) {
      currentBlobUrl = blobUrlCache[currentAttachment.id] ?? null;
      loading = !currentBlobUrl;
      error = null;
      loadImage(currentAttachment.id).then(() => {
        preloadAdjacentImages();
      });
    }
  });
</script>

<svelte:window onkeydown={handleKeydown} />

{#if attachments.length > 0 && currentIndex >= 0}
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-2 sm:p-4 backdrop-blur-sm"
    role="dialog"
    aria-modal="true"
    aria-label="Image preview"
    tabindex="-1"
    onclick={handleBackdropClick}
    onkeydown={handleKeydown}
  >
    <div class="relative max-h-full max-w-full flex items-center justify-center" in:scale={{ start: 0.9, duration: 150 }} out:fade={{ duration: 100 }}>
      {#if currentBlobUrl}
        {#key currentIndex}
          <img
            class="max-h-[92vh] max-w-[96vw] rounded-xl object-contain shadow-2xl select-none block"
            src={currentBlobUrl}
            alt={currentAttachment?.filename ?? ''}
            in:fly={{ x: direction === 'right' ? 40 : -40, duration: 350, opacity: 0, easing: (t) => 1 - Math.pow(1 - t, 3) }}
          />
        {/key}
      {:else if error}
        <div class="flex h-48 w-48 items-center justify-center rounded-xl bg-white/10">
          <div class="text-sm text-red-400">{error}</div>
        </div>
      {:else}
        <div class="flex h-48 w-48 items-center justify-center rounded-xl bg-white/10">
          <div class="text-sm text-white/70">Loading...</div>
        </div>
      {/if}

      {#if attachments.length > 1}
        {#if currentIndex > 0}
          <button
            class="nav-arrow nav-arrow-left"
            type="button"
            onclick={(e) => { e.stopPropagation(); navigate(-1); }}
            aria-label="Previous image"
          >
            <div class="nav-arrow-pill">
              <ChevronLeft label="" size={28} strokeWidth={2.5} />
            </div>
          </button>
        {/if}
        
        {#if currentIndex < attachments.length - 1}
          <button
            class="nav-arrow nav-arrow-right"
            type="button"
            onclick={(e) => { e.stopPropagation(); navigate(1); }}
            aria-label="Next image"
          >
            <div class="nav-arrow-pill">
              <ChevronRight label="" size={28} strokeWidth={2.5} />
            </div>
          </button>
        {/if}

        <div class="absolute bottom-3 left-1/2 -translate-x-1/2 rounded-full bg-black/60 px-3.5 py-1 text-xs font-medium text-white shadow-lg backdrop-blur-md pointer-events-none">
          {currentIndex + 1} / {attachments.length}
        </div>
      {/if}

      {#if currentBlobUrl}
        <div class="modal-controls absolute right-3 top-3 z-30 flex items-center overflow-hidden rounded-full bg-black/50 shadow-xl backdrop-blur-md transition-all duration-300 hover:bg-black/75">
          <a
            class="flex h-9 w-9 items-center justify-center text-white/90 transition-colors hover:text-white"
            href={currentBlobUrl}
            download={currentAttachment?.filename ?? ''}
            aria-label="Download image"
            onclick={(e) => e.stopPropagation()}
          >
            <Download label="" size={18} strokeWidth={2} />
          </a>
          <div class="h-4 w-px bg-white/20"></div>
          <button
            class="al-icon-wrapper flex h-9 w-9 items-center justify-center text-white/90 transition-colors hover:text-white"
            type="button"
            aria-label="Close"
            onclick={(e) => { e.stopPropagation(); onClose(); }}
          >
            <X label="" size={18} strokeWidth={2} />
          </button>
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .nav-arrow {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 15%;
    min-width: 60px;
    max-width: 120px;
    display: flex;
    align-items: center;
    background: transparent;
    border: none;
    cursor: pointer;
    z-index: 20;
    padding: 0 12px;
  }

  .nav-arrow-left {
    left: 0;
    justify-content: flex-start;
  }

  .nav-arrow-right {
    right: 0;
    justify-content: flex-end;
  }

  .nav-arrow-pill {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    border-radius: 9999px;
    background: rgba(0, 0, 0, 0.45);
    color: white;
    backdrop-filter: blur(8px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    transition: all 0.2s ease;
    opacity: 0.7;
  }

  .nav-arrow:hover .nav-arrow-pill {
    opacity: 1;
    background: rgba(0, 0, 0, 0.75);
    transform: scale(1.08);
  }

  .nav-arrow:active .nav-arrow-pill {
    transform: scale(0.95);
  }

  .modal-controls {
    opacity: 0.85;
  }

  .modal-controls:hover {
    opacity: 1;
  }

  @media (max-width: 768px) {
    .nav-arrow {
      width: 20%;
      min-width: 48px;
      padding: 0 8px;
    }

    .nav-arrow-pill {
      width: 38px;
      height: 38px;
      opacity: 0.85;
    }
  }
</style>
