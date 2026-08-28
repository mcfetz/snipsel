<script lang="ts">
  import { fly, scale } from 'svelte/transition';
  import ChevronUp from '@animated-color-icons/lucide-svelte/ChevronUp.svelte';
  import ChevronDown from '@animated-color-icons/lucide-svelte/ChevronDown.svelte';
  import Outdent from '@animated-color-icons/lucide-svelte/Outdent.svelte';
  import Indent from '@animated-color-icons/lucide-svelte/Indent.svelte';
  import Type from '@animated-color-icons/lucide-svelte/Type.svelte';
  import FileText from '@animated-color-icons/lucide-svelte/FileText.svelte';
  import SquareCheck from '@animated-color-icons/lucide-svelte/SquareCheck.svelte';
  import Sparkles from '@animated-color-icons/lucide-svelte/Sparkles.svelte';
  import LayoutTemplate from '@animated-color-icons/lucide-svelte/LayoutTemplate.svelte';
  import Paperclip from '@animated-color-icons/lucide-svelte/Paperclip.svelte';
  import Check from '@animated-color-icons/lucide-svelte/Check.svelte';
  import Share from '@animated-color-icons/lucide-svelte/Share.svelte';
  import Copy from '@animated-color-icons/lucide-svelte/Copy.svelte';
  import ArrowRightLeft from '@animated-color-icons/lucide-svelte/ArrowRightLeft.svelte';
  import CornerDownRight from '@animated-color-icons/lucide-svelte/CornerDownRight.svelte';
  import ListPlus from '@animated-color-icons/lucide-svelte/ListPlus.svelte';
  import Plus from '@animated-color-icons/lucide-svelte/Plus.svelte';
  import Info from '@animated-color-icons/lucide-svelte/Info.svelte';
  import Trash2 from '@animated-color-icons/lucide-svelte/Trash2.svelte';
  import X from '@animated-color-icons/lucide-svelte/X.svelte';
  import type { Collection } from './api';

  interface LongPressHandlers {
    onclick: (e: MouseEvent) => void;
    onpointerdown: (e: PointerEvent) => void;
    onpointerup: (e: PointerEvent) => void;
    onpointercancel: (e: PointerEvent) => void;
    onpointerleave: (e: PointerEvent) => void;
    oncontextmenu: (e: MouseEvent) => void;
  }

  interface Props {
    selectedCount: number;
    selectionPulse: boolean;
    headerColor: string;
    toolboxBg: string;
    canWrite: boolean;
    uploadingAttachments: boolean;
    aiEnabled: boolean;
    templates: Collection[];
    isCardViewActive: boolean;
    shareSuccess: boolean;
    lpMoveTop: LongPressHandlers;
    lpMoveBottom: LongPressHandlers;
    lpOutdentToZero: LongPressHandlers;
    lpInsert: LongPressHandlers;
    onAdjustIndent: (delta: number) => void;
    onSetType: (type: 'text' | 'task') => void;
    onToggleCardView: () => void;
    onOpenAiModal: () => void;
    onInsertTemplate: (templateId: string) => void;
    onUploadAttachments: (e: Event) => void;
    onShareSelected: () => void;
    onOpenCollectionModal: (mode: 'copy' | 'move' | 'link') => void;
    onCreateCollectionFromSnipsel: () => void;
    onOpenDetailSelected: () => void;
    onDeleteSelected: () => void;
    onClearSelection: () => void;
  }

  let {
    selectedCount,
    selectionPulse,
    headerColor,
    toolboxBg,
    canWrite,
    uploadingAttachments,
    aiEnabled,
    templates,
    isCardViewActive,
    shareSuccess,
    lpMoveTop,
    lpMoveBottom,
    lpOutdentToZero,
    lpInsert,
    onAdjustIndent,
    onSetType,
    onToggleCardView,
    onOpenAiModal,
    onInsertTemplate,
    onUploadAttachments,
    onShareSelected,
    onOpenCollectionModal,
    onCreateCollectionFromSnipsel,
    onOpenDetailSelected,
    onDeleteSelected,
    onClearSelection,
  }: Props = $props();

  let attachmentsInputRef: HTMLInputElement | null = $state(null);
  let showTypeMenu = $state(false);
  let showTemplateMenu = $state(false);

  function closeTypeMenu() {
    showTypeMenu = false;
  }

  function closeTemplateMenu() {
    showTemplateMenu = false;
  }
</script>

{#if selectedCount > 0}
  <!-- Progressive blur layer behind toolbox -->
  <div
    class="pointer-events-none fixed bottom-0 left-0 right-0 z-10"
    style="height: 120px;"
    in:fly={{ y: 100, duration: 250 }}
    out:fly={{ y: 100, duration: 200 }}
  >
    <div
      class="absolute inset-0 backdrop-blur-lg"
      style="mask-image: linear-gradient(to top, black 0%, black 40%, transparent 100%); -webkit-mask-image: linear-gradient(to top, black 0%, black 40%, transparent 100%);"
    ></div>
  </div>

  <!-- Toolbox -->
  <div
    class="fixed bottom-0 left-0 right-0 z-20 px-4 pb-4"
    style="padding-bottom: calc(env(safe-area-inset-bottom) + 2rem);"
    in:fly={{ y: 100, duration: 250 }}
    out:fly={{ y: 100, duration: 200 }}
  >
    <div
      class="mx-auto flex max-w-3xl flex-wrap items-center justify-center gap-2 rounded-xl px-3 py-3 text-slate-900 shadow-lg ring-1 ring-black/5 backdrop-blur-xl dark:text-slate-100 dark:ring-white/10"
      style={`background-color: ${toolboxBg}`}
    >
      <div class="flex min-w-[2rem] items-center justify-center rounded-full bg-black/10 px-2 py-1 dark:bg-white/10">
        <span
          class="text-sm font-bold transition-transform duration-150 {selectionPulse ? 'scale-125' : ''}"
          style="color: {headerColor}"
        >
          {selectedCount}
        </span>
      </div>

      <input
        bind:this={attachmentsInputRef}
        class="hidden"
        type="file"
        multiple
        onchange={onUploadAttachments}
        disabled={uploadingAttachments}
      />

      <button
        class="al-icon-wrapper grid h-11 w-11 select-none place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Move up"
        title="Move up"
        onclick={lpMoveTop.onclick}
        onpointerdown={lpMoveTop.onpointerdown}
        onpointerup={lpMoveTop.onpointerup}
        onpointercancel={lpMoveTop.onpointercancel}
        onpointerleave={lpMoveTop.onpointerleave}
        oncontextmenu={lpMoveTop.oncontextmenu}
        disabled={!canWrite}
      >
        <ChevronUp label="" size={20} strokeWidth={2} />
      </button>

      <button
        class="al-icon-wrapper grid h-11 w-11 select-none place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Move down"
        title="Move down"
        onclick={lpMoveBottom.onclick}
        onpointerdown={lpMoveBottom.onpointerdown}
        onpointerup={lpMoveBottom.onpointerup}
        onpointercancel={lpMoveBottom.onpointercancel}
        onpointerleave={lpMoveBottom.onpointerleave}
        oncontextmenu={lpMoveBottom.oncontextmenu}
        disabled={!canWrite}
      >
        <ChevronDown label="" size={20} strokeWidth={2} />
      </button>

      <button
        class="al-icon-wrapper grid h-11 w-11 select-none place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Outdent"
        title="Outdent"
        onclick={lpOutdentToZero.onclick}
        onpointerdown={lpOutdentToZero.onpointerdown}
        onpointerup={lpOutdentToZero.onpointerup}
        onpointercancel={lpOutdentToZero.onpointercancel}
        onpointerleave={lpOutdentToZero.onpointerleave}
        oncontextmenu={lpOutdentToZero.oncontextmenu}
        disabled={!canWrite}
      >
        <Outdent label="" size={20} strokeWidth={2} />
      </button>

      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Indent"
        title="Indent"
        onclick={() => onAdjustIndent(1)}
        disabled={!canWrite}
      >
        <Indent label="" size={20} strokeWidth={2} />
      </button>

      <div class="relative">
        <button
          class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
          type="button"
          aria-label="Change type"
          title="Change type"
          onclick={() => (showTypeMenu = !showTypeMenu)}
          disabled={!canWrite}
        >
          <Type label="" size={20} strokeWidth={2} />
        </button>
        {#if showTypeMenu}
          <div class="absolute bottom-12 right-0 z-50 w-48 overflow-hidden rounded-xl border border-slate-200 bg-white/95 shadow-xl ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/95 dark:ring-white/10">
            <div class="border-b border-slate-100 bg-slate-50/50 px-3 py-2 text-left text-xs font-bold uppercase tracking-wider text-slate-500 dark:border-white/5 dark:bg-slate-950/50 dark:text-slate-400">
              Change type
            </div>
            <div class="py-1">
              <button
                class="al-icon-wrapper flex w-full items-center gap-2.5 px-3 py-2 text-left text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-white/5"
                type="button"
                onclick={() => {
                  onSetType('text');
                  closeTypeMenu();
                }}
              >
                <FileText label="" size={16} strokeWidth={2} />
                Note
              </button>
              <button
                class="al-icon-wrapper flex w-full items-center gap-2.5 px-3 py-2 text-left text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-white/5"
                type="button"
                onclick={() => {
                  onSetType('task');
                  closeTypeMenu();
                }}
              >
                <SquareCheck label="" size={16} strokeWidth={2} />
                Task
              </button>
            </div>
            <div class="border-t border-slate-100 px-3 py-2 dark:border-white/5">
              <label class="flex cursor-pointer items-center justify-between">
                <span class="text-sm text-slate-600 dark:text-slate-400">Card view</span>
                <button
                  type="button"
                  class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none {isCardViewActive ? '' : 'bg-slate-200 dark:bg-slate-700'}"
                  style={isCardViewActive ? `background-color: ${headerColor}` : ''}
                  onclick={onToggleCardView}
                  role="switch"
                  aria-checked={isCardViewActive}
                  aria-label="Toggle card view"
                >
                  <span
                    class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out {isCardViewActive ? 'translate-x-5' : 'translate-x-0'}"
                  ></span>
                </button>
              </label>
            </div>
            <div class="border-t border-slate-100 p-1 dark:border-white/5">
              <button
                class="w-full rounded-lg px-3 py-2 text-left text-xs font-medium text-slate-500 transition-colors hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-white/5"
                type="button"
                onclick={closeTypeMenu}
              >
                Cancel
              </button>
            </div>
          </div>
        {/if}
      </div>

      {#if aiEnabled}
        <button
          class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
          type="button"
          aria-label="AI Assistant"
          title="AI Assistant"
          onclick={onOpenAiModal}
          disabled={!canWrite}
        >
          <Sparkles label="" size={20} />
        </button>
      {/if}

      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Insert template"
        title="Insert template"
        onclick={() => (showTemplateMenu = !showTemplateMenu)}
        disabled={!canWrite}
      >
        <LayoutTemplate label="" size={20} strokeWidth={2} />
      </button>

      {#if showTemplateMenu}
        <div class="absolute bottom-12 right-0 max-h-80 w-64 overflow-y-auto rounded-lg border border-slate-200 bg-white text-slate-900 shadow-xl dark:border-white/10 dark:bg-slate-900 dark:text-slate-100">
          <div class="border-b border-slate-100 bg-slate-50 px-3 py-2 text-xs font-bold uppercase tracking-wider text-slate-500 dark:border-white/5 dark:bg-slate-950">
            Templates
          </div>
          {#if templates.length === 0}
            <div class="px-3 py-4 text-sm italic text-slate-500 dark:text-slate-400">No templates found</div>
          {:else}
            {#each templates as t (t.id)}
              <button
                class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-slate-50 dark:hover:bg-white/5"
                type="button"
                onclick={() => {
                  onInsertTemplate(t.id);
                  closeTemplateMenu();
                }}
              >
                <span class="text-xl">{t.icon}</span>
                <span class="truncate font-medium">{t.title}</span>
              </button>
            {/each}
          {/if}
          <button
            class="w-full border-t px-3 py-2 text-left text-sm text-slate-500 hover:bg-slate-50 dark:border-white/5 dark:hover:bg-white/5"
            type="button"
            onclick={closeTemplateMenu}
          >
            Cancel
          </button>
        </div>
      {/if}

      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Upload files"
        title="Upload files"
        onclick={() => attachmentsInputRef?.click()}
        disabled={uploadingAttachments || !canWrite}
      >
        <Paperclip label="" size={20} strokeWidth={2} />
      </button>

      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Share"
        title="Copy content to clipboard"
        onclick={onShareSelected}
      >
        {#if shareSuccess}
          <div in:scale={{ duration: 150 }}>
            <Check label="" size={20} strokeWidth={3} className="text-green-600 dark:text-green-400" />
          </div>
        {:else}
          <Share label="" size={20} strokeWidth={2} />
        {/if}
      </button>

      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Copy"
        title="Copy"
        onclick={() => onOpenCollectionModal('copy')}
        disabled={!canWrite}
      >
        <Copy label="" size={20} strokeWidth={2} />
      </button>

      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Move"
        title="Move"
        onclick={() => onOpenCollectionModal('move')}
        disabled={!canWrite}
      >
        <ArrowRightLeft label="" size={20} strokeWidth={2} />
      </button>

      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg transition-all duration-300 ease-out hover:bg-black/10 disabled:scale-95 disabled:opacity-40 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Create collection"
        title="Create collection from snipsel"
        onclick={onCreateCollectionFromSnipsel}
        disabled={selectedCount !== 1 || !canWrite}
      >
        <CornerDownRight label="" size={20} strokeWidth={2} />
      </button>

      <button
        class="al-icon-wrapper grid h-11 w-11 select-none place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Insert snipsel"
        title="Click: Below last, Long: Above first"
        onclick={lpInsert.onclick}
        onpointerdown={lpInsert.onpointerdown}
        onpointerup={lpInsert.onpointerup}
        onpointercancel={lpInsert.onpointercancel}
        onpointerleave={lpInsert.onpointerleave}
        oncontextmenu={lpInsert.oncontextmenu}
        disabled={!canWrite}
      >
        <ListPlus label="" size={20} strokeWidth={2} />
      </button>

      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Add to collection"
        title="Add to collection"
        onclick={() => onOpenCollectionModal('link')}
        disabled={!canWrite}
      >
        <Plus label="" size={20} strokeWidth={2} />
      </button>

      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg transition-all duration-300 ease-out hover:bg-black/10 disabled:scale-95 disabled:opacity-40 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Info"
        title="Info"
        onclick={onOpenDetailSelected}
        disabled={selectedCount !== 1}
      >
        <Info label="" size={20} strokeWidth={2} />
      </button>

      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-red-600/90 text-lg text-white hover:bg-red-600 dark:bg-red-700 dark:hover:bg-red-600"
        type="button"
        aria-label="Delete"
        title="Delete"
        onclick={onDeleteSelected}
        disabled={!canWrite}
      >
        <Trash2 label="" size={20} strokeWidth={2} />
      </button>

      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md text-lg text-slate-600 hover:bg-black/5 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-slate-100"
        type="button"
        aria-label="Clear selection"
        title="Clear selection"
        onclick={() => {
          onClearSelection();
          closeTypeMenu();
          closeTemplateMenu();
        }}
      >
        <X label="" size={20} strokeWidth={2} />
      </button>
    </div>
  </div>
{/if}
