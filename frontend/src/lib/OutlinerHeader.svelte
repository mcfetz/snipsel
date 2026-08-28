<script lang="ts">
  import { fly, fade } from 'svelte/transition';
  import RotateCcw from '@animated-color-icons/lucide-svelte/RotateCcw.svelte';
  import ChevronsUp from '@animated-color-icons/lucide-svelte/ChevronsUp.svelte';
  import ChevronsDown from '@animated-color-icons/lucide-svelte/ChevronsDown.svelte';
  import { formatModifiedAt } from './dates';
  import { computeHeaderGradient } from './colors';
  import { currentView } from './stores';
  import { currentUser } from './session';
  import type { Collection } from './api';

  interface Props {
    collection: Collection | null;
    headerColor: string;
    dayLabel?: string | null;
    navVisible: boolean;
    swipeNavigating: boolean;
    canWrite: boolean;
    taskProgress: { total: number; done: number; ratio: number };
    hideDoneTasks: boolean;
    throwbackLists: Array<{ id: string; year: number; title: string; icon: string }>;
    collapsibleCount: number;
    allExpanded: boolean;
    onNavigateDay: (direction: -1 | 1) => void;
    onUpdateIcon: (emoji: string) => void;
    onToggleHideDoneTasks: () => void;
    onToggleAllExpanded: () => void;
  }

  let {
    collection,
    headerColor,
    dayLabel,
    navVisible,
    swipeNavigating,
    canWrite,
    taskProgress,
    hideDoneTasks,
    throwbackLists,
    collapsibleCount,
    allExpanded,
    onNavigateDay,
    onUpdateIcon,
    onToggleHideDoneTasks,
    onToggleAllExpanded,
  }: Props = $props();

  let showEmojiPicker = $state(false);
  let showThrowbackPopup = $state(false);
  let throwbackPopupRef: HTMLDivElement | null = $state(null);

  const commonEmojis = ['📝', '📋', '✅', '📌', '🎯', '💡', '⭐', '🔥', '🚀', '💻', '📚', '🎨', '🛒', '💰', '🏠', '📅'];

  function headerBg(): string {
    if (collection?.header_image_url) {
      return headerColor;
    }
    return computeHeaderGradient(headerColor);
  }
</script>

<div class="rounded-xl border border-slate-200 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900">
  <div
    class="relative h-28 w-full overflow-hidden rounded-t-[calc(0.75rem-1px)] dark:brightness-75"
    style="background: {headerBg()}"
  >
    {#if collection?.header_image_url}
      <div
        class="absolute inset-0 bg-cover"
        style="background-image: url('{collection.header_image_url}{ collection.header_image_url.startsWith('/api/attachments/') ? '/thumbnail' : '' }'); background-position: {collection.header_image_x_position || '50%'} {collection.header_image_position || '50%'}; transform: scale({collection.header_image_zoom || 1.0}) translate({(50 - (parseFloat(collection.header_image_x_position || '50') || 50)) * (1 - 1 / (collection.header_image_zoom || 1.0))}%, {(50 - (parseFloat(collection.header_image_position || '50') || 50)) * (1 - 1 / (collection.header_image_zoom || 1.0))}%)"
      ></div>
    {/if}

    {#if collection?.list_for_day}
      <button
        type="button"
        class="day-nav day-nav-prev"
        class:nav-active={navVisible}
        title="go to previous day"
        onclick={() => onNavigateDay(-1)}
        disabled={swipeNavigating}
        aria-label="go to previous day"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m15 18-6-6 6-6"/>
        </svg>
      </button>

      <button
        type="button"
        class="day-nav day-nav-next"
        class:nav-active={navVisible}
        title="go to next day"
        onclick={() => onNavigateDay(1)}
        disabled={swipeNavigating}
        aria-label="go to next day"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m9 18 6-6-6-6"/>
        </svg>
      </button>
    {/if}
  </div>

  <div class="relative px-4 py-3">
    <div class="absolute left-4 top-0 z-10 -translate-y-1/2">
      <button
        class="grid h-16 w-16 place-items-center rounded-xl border border-slate-200 bg-white shadow-sm transition-colors hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:hover:bg-white dark:border-white/10 dark:bg-slate-900 dark:hover:bg-white/5 dark:disabled:hover:bg-slate-900"
        type="button"
        onclick={() => canWrite && (showEmojiPicker = !showEmojiPicker)}
        disabled={!canWrite}
        aria-label="Change collection icon"
      >
        <span class="text-4xl leading-none">{collection?.icon}</span>
      </button>

      {#if showEmojiPicker}
        <div 
          class="absolute left-0 top-full z-50 mt-2 w-64 rounded-xl border border-slate-200 bg-white/95 p-2 shadow-xl ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/95 dark:ring-white/10"
          onfocusout={(e) => {
            const related = e.relatedTarget as Node | null;
            if (related instanceof HTMLElement && e.currentTarget.contains(related)) return;
            showEmojiPicker = false;
          }}
        >
          <div class="grid max-h-48 grid-cols-8 gap-1 overflow-y-auto p-1 text-center">
            {#each commonEmojis as emoji}
              <button
                class="grid h-7 w-7 place-items-center rounded text-lg transition-colors hover:bg-slate-100 dark:hover:bg-white/10"
                type="button"
                onclick={() => {
                  onUpdateIcon(emoji);
                  showEmojiPicker = false;
                }}
              >
                {emoji}
              </button>
            {/each}
          </div>
          <div class="mt-2 border-t border-slate-100 px-1 pt-2 dark:border-white/5">
            <input
              type="text"
              placeholder="Custom emoji..."
              maxlength="4"
              class="w-full rounded border border-slate-200 bg-white px-2 py-1 text-sm outline-none focus:ring-2 focus:ring-indigo-500/20 dark:border-white/10 dark:bg-slate-800 dark:text-slate-100"
              onkeydown={(e) => {
                if (e.key === 'Enter') {
                  const val = (e.currentTarget as HTMLInputElement).value.trim();
                  if (val) {
                    onUpdateIcon(val);
                    showEmojiPicker = false;
                  }
                } else if (e.key === 'Escape') {
                  showEmojiPicker = false;
                }
              }}
            />
          </div>
        </div>
      {/if}
    </div>

    {#if taskProgress.total > 0}
      <button
        class="absolute left-[5.5rem] right-4 top-0 -translate-y-1/2 rounded-full border border-slate-200 bg-white/80 p-1 shadow-sm backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80"
        type="button"
        aria-label="Toggle done tasks"
        title={hideDoneTasks ? 'Show done tasks' : 'Hide done tasks'}
        onclick={onToggleHideDoneTasks}
        in:fly={{ y: -10, duration: 200 }}
        out:fly={{ y: -10, duration: 150 }}
      >
        <div class="h-2 w-full overflow-hidden rounded-full bg-black/10 dark:bg-white/10">
          <div
            class="h-full rounded-full transition-all duration-300 ease-out"
            style={`width: ${Math.round(taskProgress.ratio * 100)}%; background-color: ${headerColor}`}
          ></div>
        </div>
      </button>
    {/if}

    <div class="flex items-center gap-2 pl-20">
      <button
        class="text-lg font-semibold hover:underline dark:text-slate-100"
        type="button"
        onclick={() => collection && currentView.set({ type: 'collection_settings', id: collection.id })}
      >
        {collection?.title}{#if dayLabel}{' · '}{dayLabel}{/if}
      </button>

      {#if throwbackLists.length > 0}
        <div bind:this={throwbackPopupRef} class="relative" onmouseleave={() => showThrowbackPopup = false}>
          <button
            class="al-icon-wrapper relative grid h-9 w-9 place-items-center rounded-full transition-colors {showThrowbackPopup
              ? 'bg-black/10 text-slate-900 dark:bg-white/10 dark:text-white'
              : 'text-slate-400 hover:bg-black/5 hover:text-slate-600 dark:text-slate-500 dark:hover:bg-white/5 dark:hover:text-slate-300'}"
            type="button"
            onmouseenter={() => showThrowbackPopup = true}
            aria-label="Throwback"
            title="Throwback"
          >
            <RotateCcw label="" size={20} />

            {#if throwbackLists.length > 0}
              <span class="absolute -right-0.5 -top-0.5 flex h-3.5 min-w-[0.875rem] items-center justify-center rounded-full bg-slate-400 px-[3px] text-[9px] font-bold text-white shadow-sm dark:bg-slate-500">
                {throwbackLists.length}
              </span>
            {/if}
          </button>

          {#if showThrowbackPopup}
            <div class="absolute left-0 top-full z-50 w-56 pt-2" in:fly={{ y: -10, duration: 150 }} out:fade={{ duration: 100 }}>
              <div class="overflow-hidden rounded-xl border border-slate-200 bg-white/95 shadow-xl ring-1 ring-black/5 backdrop-blur-md pointer-events-auto dark:border-white/10 dark:bg-slate-900/95 dark:ring-white/10">
                <div class="border-b border-slate-100 bg-slate-50/50 px-3 py-2 text-left text-xs font-bold uppercase tracking-wider text-slate-500 dark:border-white/5 dark:bg-slate-950/50 dark:text-slate-400">
                  Throwback
                </div>
                <div class="max-h-80 overflow-y-auto py-1">
                  {#each throwbackLists as tb (tb.id)}
                    <button
                      class="flex w-full items-center gap-3 px-3 py-2 text-left text-sm transition-colors hover:bg-slate-50 dark:hover:bg-white/5"
                      type="button"
                      onclick={(e) => {
                        e.stopPropagation();
                        showThrowbackPopup = false;
                        currentView.set({ type: 'collection', id: tb.id });
                      }}
                    >
                      <span class="text-xl shrink-0">{tb.icon}</span>
                      <span class="truncate font-medium text-slate-800 dark:text-slate-200">{tb.year}</span>
                    </button>
                  {/each}
                </div>
              </div>
            </div>
          {/if}
        </div>
      {/if}
    </div>
  </div>
</div>

{#if collection}
  <div class="mt-1 flex items-center justify-between px-1 text-[10px] text-slate-400">
    <div class="flex items-center" style="padding-left: 0.75rem">
      {#if collapsibleCount > 0}
        <button
          type="button"
          class="al-icon-wrapper grid h-6 w-6 place-items-center text-slate-400 transition-all hover:text-slate-600 focus:outline-none"
          onclick={onToggleAllExpanded}
          title={allExpanded ? 'Collapse All' : 'Expand All'}
        >
          {#if allExpanded}
            <ChevronsUp label="" size={14} strokeWidth={2} />
          {:else}
            <ChevronsDown label="" size={14} strokeWidth={2} />
          {/if}
        </button>
      {/if}
    </div>
    <div class="ml-auto flex items-center gap-1.5">
      <span>Last modified: {formatModifiedAt(collection.modified_at)}</span>
      {#if collection.modified_by_username && collection.modified_by_id !== $currentUser?.id}
        <span>by {collection.modified_by_username}</span>
      {/if}
    </div>
  </div>
{/if}

<style>
  .day-nav {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: none;
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.3s ease, background 0.3s ease, box-shadow 0.3s ease;
    z-index: 10;
  }

  .day-nav:hover,
  .day-nav.nav-active {
    opacity: 1;
    background: rgba(255, 255, 255, 0.15);
  }

  .day-nav:active,
  .day-nav.nav-active:active {
    background: rgba(255, 255, 255, 0.25);
  }

  .day-nav-prev {
    left: 0;
    border-radius: 0.75rem 0 0 0;
  }

  .day-nav-next {
    right: 0;
    border-radius: 0 0.75rem 0 0;
  }

  .day-nav svg {
    color: white;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
    transition: transform 0.2s ease, filter 0.3s ease;
  }

  .day-nav:hover svg,
  .day-nav.nav-active svg {
    transform: scale(1.2);
    filter: drop-shadow(0 0 8px rgba(255, 255, 255, 0.8)) drop-shadow(0 0 16px rgba(255, 255, 255, 0.4));
  }

  .day-nav:active svg,
  .day-nav.nav-active:active svg {
    transform: scale(0.95);
  }

  @keyframes glow-pulse {
    0%, 100% {
      box-shadow: 0 0 5px rgba(255, 255, 255, 0.3), 0 0 10px rgba(255, 255, 255, 0.2);
    }
    50% {
      box-shadow: 0 0 15px rgba(255, 255, 255, 0.5), 0 0 30px rgba(255, 255, 255, 0.3);
    }
  }

  .day-nav:hover,
  .day-nav.nav-active {
    animation: glow-pulse 2s ease-in-out infinite;
  }

  .day-nav:disabled {
    cursor: not-allowed;
    opacity: 0.3;
  }

  .day-nav:disabled:hover,
  .day-nav:disabled.nav-active {
    animation: none;
    background: transparent;
    opacity: 0.3;
  }

  @media (hover: none) {
    .day-nav {
      opacity: 0.4;
    }
    .day-nav:hover,
    .day-nav:active,
    .day-nav:focus {
      opacity: 0.4;
      background: transparent;
      animation: none;
    }
    .day-nav.nav-active,
    .day-nav.nav-active:hover,
    .day-nav.nav-active:active,
    .day-nav.nav-active:focus {
      opacity: 1;
      background: rgba(255, 255, 255, 0.15);
      animation: glow-pulse 2s ease-in-out infinite;
    }
    .day-nav.nav-active svg,
    .day-nav.nav-active:hover svg,
    .day-nav.nav-active:active svg,
    .day-nav.nav-active:focus svg {
      transform: scale(1.2);
      filter: drop-shadow(0 0 8px rgba(255, 255, 255, 0.8)) drop-shadow(0 0 16px rgba(255, 255, 255, 0.4));
    }
  }
</style>
