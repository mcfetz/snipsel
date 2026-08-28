<script lang="ts">
  import { fade } from 'svelte/transition';
  import Dices from '@animated-color-icons/lucide-svelte/Dices.svelte';
  import Paperclip from '@animated-color-icons/lucide-svelte/Paperclip.svelte';
  import RotateCcw from '@animated-color-icons/lucide-svelte/RotateCcw.svelte';
  import Ban from '@animated-color-icons/lucide-svelte/Ban.svelte';
  import ConfirmModal from './ConfirmModal.svelte';
  import { api, type Snipsel } from './api';
  import { collectionAnchor, currentView } from './stores';

  interface Props {
    dicedLoading: boolean;
    dicedSnipsel: Snipsel | null;
    currentCollectionId?: string;
    onAnchorHighlight?: (snipselId: string) => void;
  }

  let {
    dicedLoading,
    dicedSnipsel = $bindable(null),
    currentCollectionId,
    onAnchorHighlight,
  }: Props = $props();

  let showDicedBanModal = $state(false);
  let isRolling = $state(false);

  async function rollAgain() {
    if (isRolling) return;
    isRolling = true;
    try {
      const res = await api.collections.dicedMoment();
      dicedSnipsel = res.snipsel;
    } catch (err) {
      console.error('Failed to roll diced moment:', err);
    } finally {
      isRolling = false;
    }
  }

  async function banDicedMoment() {
    if (!dicedSnipsel) return;
    try {
      await api.snipsels.banDicedMoment(dicedSnipsel.id);
      await rollAgain();
    } catch (err) {
      console.error('Failed to ban diced moment:', err);
    } finally {
      showDicedBanModal = false;
    }
  }

  function handleCardClick() {
    if (!dicedSnipsel) return;
    if (dicedSnipsel.collection_refs && dicedSnipsel.collection_refs.length > 0) {
      const colId = dicedSnipsel.collection_refs[0].collection_id;
      collectionAnchor.set({ collectionId: colId, snipselId: dicedSnipsel.id });
      if (currentCollectionId === colId) {
        const el = document.getElementById(`snipsel-${dicedSnipsel.id}`);
        el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        if (onAnchorHighlight) {
          onAnchorHighlight(dicedSnipsel.id);
        }
      } else {
        currentView.set({ type: 'collection', id: colId });
      }
    } else {
      currentView.set({ type: 'snipsel', id: dicedSnipsel.id });
    }
  }
</script>

{#if dicedLoading}
  <div
    class="mt-2 animate-pulse rounded-xl border border-slate-200/50 bg-white/30 px-4 py-3 dark:border-white/5 dark:bg-white/5"
    in:fade={{ duration: 150 }}
  >
    <div class="mb-2 flex items-center gap-2 text-slate-400 opacity-60">
      <Dices label="" size={14} strokeWidth={2.5} />
      <span class="text-[10px] font-bold uppercase tracking-wider">Diced Moment</span>
    </div>
    <div class="space-y-1.5 py-1">
      <div class="h-3 w-3/4 rounded bg-slate-200/60 dark:bg-slate-800/60"></div>
      <div class="h-3 w-1/2 rounded bg-slate-200/60 dark:bg-slate-800/60"></div>
    </div>
  </div>
{:else if dicedSnipsel}
  <div
    class="group relative mt-2 overflow-hidden rounded-xl border border-slate-200/60 bg-white/40 px-4 py-3 backdrop-blur-sm transition-all hover:bg-white/60 dark:border-white/10 dark:bg-white/5 dark:hover:bg-white/10"
    in:fade={{ duration: 400 }}
  >
    <div class="relative z-20 mb-2 flex items-center justify-between gap-2">
      <div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
        <Dices label="" size={14} strokeWidth={2.5} className="opacity-80" />
        <span class="text-[10px] font-bold uppercase tracking-wider opacity-60">Diced Moment</span>
        {#if dicedSnipsel.attachments && dicedSnipsel.attachments.length > 0}
          <Paperclip label="" size={12} strokeWidth={2.5} className="ml-0.5 text-slate-400" />
        {/if}
      </div>
      <div class="flex items-center gap-2">
        <button
          type="button"
          class="group/roll flex items-center justify-center rounded-full bg-slate-100 p-2 transition-all duration-300 hover:scale-110 hover:bg-slate-200 active:scale-95 dark:bg-white/10 dark:hover:bg-white/20"
          onclick={(e) => {
            e.stopPropagation();
            rollAgain();
          }}
          title="Roll again"
          aria-label="Roll again"
        >
          <RotateCcw
            label=""
            size={14}
            strokeWidth={2.5}
            className="text-slate-500 transition-transform duration-500 group-hover/roll:rotate-[-180deg] dark:text-slate-400"
          />
        </button>
        <button
          type="button"
          class="group/ban flex items-center justify-center rounded-full bg-red-50 p-2 transition-all duration-300 hover:scale-110 hover:bg-red-100 active:scale-95 dark:bg-red-950/20 dark:hover:bg-red-900/40"
          onclick={(e) => {
            e.stopPropagation();
            showDicedBanModal = true;
          }}
          title="Never show again"
          aria-label="Never show again"
        >
          <Ban
            label=""
            size={14}
            strokeWidth={2.5}
            className="text-red-500 transition-transform duration-300 group-hover/ban:scale-125 dark:text-red-400"
          />
        </button>
      </div>
    </div>
    <div class="relative z-10 pointer-events-none line-clamp-3 text-sm italic text-slate-800 dark:text-slate-200">
      {dicedSnipsel.content_markdown}
    </div>
    <button
      type="button"
      class="absolute inset-0 z-0"
      onclick={handleCardClick}
      aria-label="View diced snipsel"
    ></button>
  </div>
{/if}

{#if showDicedBanModal && dicedSnipsel}
  <ConfirmModal
    title="Ban Diced Moment"
    message={`"${dicedSnipsel.content_markdown.substring(0, 100)}..."\n\nAre you sure you want to exclude this snipsel from Diced Moments forever?`}
    confirmLabel="Ban Forever"
    confirmVariant="danger"
    onConfirm={banDicedMoment}
    onCancel={() => (showDicedBanModal = false)}
  />
{/if}
