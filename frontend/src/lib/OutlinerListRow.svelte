<script lang="ts">
  import { scale } from 'svelte/transition';
  import ChevronDown from '@animated-color-icons/lucide-svelte/ChevronDown.svelte';
  import Plus from '@animated-color-icons/lucide-svelte/Plus.svelte';
  import Bell from '@animated-color-icons/lucide-svelte/Bell.svelte';
  import Repeat from '@animated-color-icons/lucide-svelte/Repeat.svelte';
  import CirclePlay from '@animated-color-icons/lucide-svelte/CirclePlay.svelte';
  import DeezerCard from './DeezerCard.svelte';
  import SpotifyCard from './SpotifyCard.svelte';
  import YouTubeCard from './YouTubeCard.svelte';
  import MapCard from './MapCard.svelte';
  import HyperlinkCard from './HyperlinkCard.svelte';
  import CollectionLinkCard from './CollectionLinkCard.svelte';
  import AttachmentCard from './AttachmentCard.svelte';
  import { api, type Attachment, type CollectionItem } from './api';
  import { isExpired, daysFromNow } from './dates';
  import { parseSnipselEmbeds } from './embeds';
  import { renderWithWikiLinks } from './markdown';
  import { currentView, searchQuery } from './stores';
  import { currentUser } from './session';

  const REACTION_EMOJIS = ['👍', '❤️', '🔥', '🎉', '💡', '😂'];

  interface RangeLongPressHandlers {
    onclick: (e: MouseEvent) => void;
    onpointerdown: (e: PointerEvent) => void;
    onpointerup: (e: PointerEvent) => void;
    onpointercancel: (e: PointerEvent) => void;
    onpointerleave: (e: PointerEvent) => void;
    oncontextmenu: (e: MouseEvent) => void;
  }

  interface Props {
    item: CollectionItem;
    headerColor: string;
    toolboxBg: string;
    isSelected: boolean;
    isExpanded: boolean;
    hasChildren: boolean;
    saveStatus?: 'success' | 'error' | null;
    rangeLongPress: RangeLongPressHandlers;
    onStartEdit: (item: CollectionItem) => void;
    onToggleTask: (item: CollectionItem) => void;
    onToggleExpand: (id: string) => void;
    onToggleReaction: (id: string, emoji: string) => void;
    onOpenImageModal: (images: Array<{ id: string; filename: string }>, index: number) => void;
    onOpenVideoModal: (id: string, filename: string) => void;
  }

  let {
    item,
    headerColor,
    toolboxBg,
    isSelected,
    isExpanded,
    hasChildren,
    saveStatus,
    rangeLongPress,
    onStartEdit,
    onToggleTask,
    onToggleExpand,
    onToggleReaction,
    onOpenImageModal,
    onOpenVideoModal,
  }: Props = $props();

  let activeReactionPickerId = $state<string | null>(null);
  let showCustomEmojiInput = $state(false);
  let customEmojiInput = $state('');

  const isImageAttachment = (a: Attachment) =>
    Boolean(a.mime_type?.startsWith('image/') || (a.has_thumbnail && !a.mime_type?.startsWith('video/')));
  const isVideoAttachment = (a: Attachment) =>
    Boolean(a.mime_type?.startsWith('video/') || (a.has_thumbnail && a.filename.toLowerCase().match(/\.(mp4|mov|webm|avi|mkv)$/)));
  const isMediaAttachment = (a: Attachment) => isImageAttachment(a) || isVideoAttachment(a);

  let media = $derived(item.snipsel.attachments ? item.snipsel.attachments.filter(isMediaAttachment) : []);
  let others = $derived(item.snipsel.attachments ? item.snipsel.attachments.filter((a) => !isMediaAttachment(a)) : []);
  let images = $derived(media.filter(isImageAttachment));
</script>

<!-- Tree line guides -->
{#each Array(item.indent) as _, level}
  <div
    class="tree-guide pointer-events-none absolute bottom-0 top-0 w-px bg-slate-200 transition-colors duration-200 group-hover:bg-slate-300 dark:bg-slate-800 dark:group-hover:bg-slate-700"
    style="left: calc(0.75rem + {level * 1.25}rem)"
  ></div>
{/each}

<!-- Task checkbox or note expand/collapse -->
{#if item.snipsel.type === 'task'}
  <button
    class="absolute top-3.5 z-20 grid h-5 w-5 place-items-center rounded-full border border-slate-300 bg-white transition-all duration-150 hover:scale-110 active:scale-95 dark:border-white/20 dark:bg-slate-800"
    style="left: calc(0.25rem + {item.indent * 1.25}rem); {item.snipsel.task_done > 0
      ? `border-color: ${headerColor}; background-color: ${toolboxBg}; color: ${headerColor}; font-size: 10px`
      : ''}"
    type="button"
    aria-label={item.snipsel.task_done ? 'Toggle task status' : 'Mark task done'}
    title={item.snipsel.task_done === 1 ? 'Done' : item.snipsel.task_done === 2 ? 'Cancelled' : 'Open'}
    onclick={(e) => {
      e.stopPropagation();
      onToggleTask(item);
    }}
  >
    {#if item.snipsel.task_done === 1}
      <span in:scale={{ start: 0.5, duration: 150 }}>✓</span>
    {:else if item.snipsel.task_done === 2}
      <span in:scale={{ start: 0.5, duration: 150 }}>✕</span>
    {/if}
  </button>
{/if}

<!-- Selection Strip on the right -->
<button
  type="button"
  aria-label={isSelected ? 'Deselect snipsel' : 'Select snipsel'}
  class="absolute bottom-0 right-0 top-0 z-20 flex w-7 select-none items-center justify-end transition-opacity {isSelected
    ? ''
    : 'opacity-0 group-hover:opacity-100'}"
  onpointerdown={(e) => {
    e.stopPropagation();
    rangeLongPress.onpointerdown(e);
  }}
  onpointerup={(e) => {
    e.stopPropagation();
    rangeLongPress.onpointerup(e);
  }}
  onpointercancel={() => rangeLongPress.onpointercancel(new PointerEvent('pointercancel'))}
  onpointerleave={rangeLongPress.onpointerleave}
  oncontextmenu={(e) => {
    e.stopPropagation();
    rangeLongPress.oncontextmenu(e);
  }}
  onclick={(e) => {
    e.stopPropagation();
    rangeLongPress.onclick(e);
  }}
>
  <div
    class="h-full w-1.5 origin-right transition-all duration-150 ease-out hover:scale-x-150 active:scale-x-75"
    style={isSelected ? `background-color: ${headerColor}` : 'background-color: #94a3b8'}
  ></div>
</button>

{#if item.snipsel.type !== 'task' && hasChildren}
  <button
    type="button"
    class="al-icon-wrapper absolute top-1/2 z-20 grid h-6 w-6 -translate-y-1/2 place-items-center rounded-full transition-transform hover:bg-slate-100 dark:hover:bg-white/10 {isExpanded
      ? ''
      : '-rotate-90'}"
    style="left: calc(0.25rem + {item.indent * 1.25}rem)"
    onclick={(e) => {
      e.stopPropagation();
      onToggleExpand(item.snipsel_id);
    }}
    aria-label={isExpanded ? 'Collapse' : 'Expand'}
  >
    <ChevronDown label="" size={14} className="text-slate-400" strokeWidth={2} />
  </button>
{/if}

<div
  class="rounded py-3 {item.snipsel.type === 'task' ? 'pl-10 pr-2' : 'px-2'} {isSelected
    ? 'bg-slate-100 dark:bg-white/5'
    : 'hover:bg-slate-50 dark:hover:bg-white/[0.02]'} {item.snipsel.task_done > 0 ? 'task-faded' : ''} {item.snipsel.task_done === 2 ? 'task-cancelled' : ''}"
  role="button"
  tabindex="0"
  onclick={(e) => {
    const colTarget = (e.target as HTMLElement).closest('[data-collection-id]');
    if (colTarget) {
      e.preventDefault();
      e.stopPropagation();
      const id = colTarget.getAttribute('data-collection-id');
      if (id) currentView.set({ type: 'collection', id });
      return;
    }

    const tagTarget = (e.target as HTMLElement).closest('[data-tag]');
    if (tagTarget) {
      e.preventDefault();
      e.stopPropagation();
      const tag = tagTarget.getAttribute('data-tag');
      if (tag) {
        searchQuery.set('#' + tag);
        currentView.set({ type: 'search' });
      }
      return;
    }

    const mentionTarget = (e.target as HTMLElement).closest('[data-mention]');
    if (mentionTarget) {
      e.preventDefault();
      e.stopPropagation();
      const mention = mentionTarget.getAttribute('data-mention');
      if (mention) {
        searchQuery.set('@' + mention);
        currentView.set({ type: 'search' });
      }
      return;
    }

    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    if (x < rect.width * 0.25 || x > rect.width * 0.75) {
      return;
    }

    onStartEdit(item);
  }}
  onkeydown={(e) => e.key === 'Enter' && onStartEdit(item)}
>
  {#if item.snipsel.content_markdown}
    {#if item.snipsel.card_view !== false}
      {@const embeds = parseSnipselEmbeds(item.snipsel.content_markdown, item.collection_refs)}
      {#if embeds.deezer}
        <DeezerCard type={embeds.deezer.type} id={embeds.deezer.id} url={embeds.deezer.url} accentColor={headerColor} />
      {/if}
      {#if embeds.spotify}
        <SpotifyCard url={embeds.spotify.url} accentColor={headerColor} />
      {/if}
      {#if embeds.youtube}
        <YouTubeCard url={embeds.youtube.url} accentColor={headerColor} />
      {/if}
      {#if embeds.map}
        <MapCard lat={embeds.map.lat} lng={embeds.map.lng} url={embeds.map.url} accentColor={headerColor} />
      {/if}
      {#if embeds.generic}
        <HyperlinkCard url={embeds.generic.url} accentColor={headerColor} />
      {/if}
      {#if embeds.collectionId}
        <CollectionLinkCard collectionId={embeds.collectionId} accentColor={headerColor} />
      {/if}
    {/if}

    <div class="flex items-start gap-2">
      <div
        class="prose prose-sm max-w-none min-w-0 flex-1 break-words whitespace-pre-wrap text-lg prose-headings:my-2 prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg prose-p:my-0 dark:prose-invert"
        style="--accent-light: {toolboxBg}"
      >
        {@html renderWithWikiLinks(
          item.snipsel.card_view !== false
            ? parseSnipselEmbeds(item.snipsel.content_markdown, item.collection_refs).strippedText
            : item.snipsel.content_markdown,
          item.collection_refs,
          toolboxBg,
          headerColor
        )}
      </div>

      {#if item.snipsel.created_by_id !== $currentUser?.id}
        <div class="relative ml-1 shrink-0 self-center">
          <button
            type="button"
            class="al-icon-wrapper flex h-6 w-6 items-center justify-center rounded-full bg-slate-100 text-slate-400 hover:bg-slate-200 dark:bg-white/5 dark:hover:bg-white/10"
            onclick={(e) => {
              e.stopPropagation();
              activeReactionPickerId = activeReactionPickerId === item.snipsel_id ? null : item.snipsel_id;
            }}
            aria-label="Add reaction"
          >
            <Plus label="" size={14} strokeWidth={2.5} />
          </button>

          {#if activeReactionPickerId === item.snipsel_id}
            <div class="absolute bottom-full right-0 z-50 mb-2 flex items-center gap-1 overflow-hidden rounded-full border border-slate-200 bg-white/95 p-1 shadow-xl ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/95">
              {#if showCustomEmojiInput}
                <input
                  type="text"
                  class="h-8 w-24 bg-transparent px-3 py-1 text-sm focus:outline-none dark:text-white"
                  placeholder="Emoji..."
                  bind:value={customEmojiInput}
                  onkeydown={(e) => {
                    if (e.key === 'Enter' && customEmojiInput.trim()) {
                      onToggleReaction(item.snipsel_id, customEmojiInput.trim());
                      showCustomEmojiInput = false;
                      customEmojiInput = '';
                      activeReactionPickerId = null;
                    } else if (e.key === 'Escape') {
                      showCustomEmojiInput = false;
                      activeReactionPickerId = null;
                    }
                  }}
                  onclick={(e) => e.stopPropagation()}
                />
              {:else}
                {#each REACTION_EMOJIS as emoji}
                  <button
                    type="button"
                    class="flex h-8 w-8 items-center justify-center rounded-full text-base transition-all hover:scale-110 hover:bg-slate-100 dark:hover:bg-white/10"
                    onclick={(e) => {
                      e.stopPropagation();
                      onToggleReaction(item.snipsel_id, emoji);
                      activeReactionPickerId = null;
                    }}
                  >
                    {emoji}
                  </button>
                {/each}
                <button
                  type="button"
                  class="flex h-8 w-8 items-center justify-center rounded-full text-base font-medium text-slate-400 transition-all hover:scale-110 hover:bg-slate-100 dark:hover:bg-white/10"
                  onclick={(e) => {
                    e.stopPropagation();
                    showCustomEmojiInput = true;
                    customEmojiInput = '';
                  }}
                >
                  +
                </button>
              {/if}
            </div>
          {/if}
        </div>
      {/if}
    </div>

    {#if (item.snipsel.tags?.length ?? 0) > 0 || (item.snipsel.mentions?.length ?? 0) > 0}
      <div class="mt-2 flex flex-wrap gap-1.5">
        {#each item.snipsel.tags ?? [] as t (t)}
          <span 
            class="rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider"
            style="background-color: {toolboxBg}; color: {headerColor}; border: 1px solid rgba(0,0,0,0.05)"
          >
            #{t}
          </span>
        {/each}
        {#each item.snipsel.mentions ?? [] as m (m)}
          <span 
            class="rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider"
            style="background-color: {toolboxBg}; color: {headerColor}; border: 1px solid rgba(0,0,0,0.05)"
          >
            @{m}
          </span>
        {/each}
      </div>
    {/if}

  {:else if !item.snipsel.attachments || !item.snipsel.attachments.length}
    <span class="text-sm italic text-slate-400 dark:text-slate-500">Empty snipsel</span>
  {/if}

  {#if item.snipsel.reactions && item.snipsel.reactions.length > 0}
    <div class="mt-2 flex flex-wrap items-center gap-2">
      {#each item.snipsel.reactions as r (r.emoji)}
        <button
          type="button"
          class="flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium transition-colors {r.me ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300' : 'bg-slate-100 text-slate-600 dark:bg-white/5 dark:text-slate-400'}"
          onclick={(e) => {
            e.stopPropagation();
            onToggleReaction(item.snipsel_id, r.emoji);
          }}
        >
          <span>{r.emoji}</span>
          <span class="opacity-60">{r.count}</span>
        </button>
      {/each}
    </div>
  {/if}

  {#if item.snipsel.reminder_at}
    {@const expired = isExpired(item.snipsel.reminder_at)}
    <div class="mt-1 flex flex-wrap items-center gap-1 text-[10px]">
      <span 
        class="flex items-center gap-1 rounded px-1.5 py-0.5 {expired ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400' : ''}"
        style={expired ? undefined : `background-color: ${toolboxBg}; color: ${headerColor}`}
      >
        <Bell label="" size={10} strokeWidth={2.5} />
        {new Date(item.snipsel.reminder_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
        <span class="opacity-60">· {daysFromNow(item.snipsel.reminder_at)}</span>
        {#if item.snipsel.reminder_rrule}
          <Repeat label="" size={10} className="ml-1" strokeWidth={2.5} />
        {/if}
      </span>
    </div>
  {/if}

  {#if saveStatus}
    <div 
      class="absolute right-[1.0rem] top-1/2 h-2 w-2 -translate-y-1/2 rounded-full transition-opacity duration-500"
      style="background-color: {saveStatus === 'success' ? '#22c55e' : '#ef4444'}"
      aria-hidden="true"
    ></div>
  {/if}

  {#if item.snipsel.attachments.length > 0 && item.snipsel.card_view !== false}
    {#if media.length > 0}
      <div class="mt-3 grid grid-cols-3 gap-3">
        {#each media as a, mediaIdx}
          {@const imgIdx = images.findIndex((img) => img.id === a.id)}
          <button
            type="button"
            class="group relative aspect-square w-full overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all duration-200 hover:scale-[1.02] hover:shadow-md dark:border-white/10 dark:bg-slate-900"
            aria-label={isVideoAttachment(a) ? `Play ${a.filename}` : `View ${a.filename}`}
            onclick={(e) => {
              e.stopPropagation();
              if (isVideoAttachment(a)) {
                onOpenVideoModal(a.id, a.filename);
              } else {
                onOpenImageModal(images.map((img) => ({ id: img.id, filename: img.filename })), imgIdx);
              }
            }}
          >
            <img
              class="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
              src={a.has_thumbnail ? api.attachments.thumbnailUrl(a.id) : api.attachments.downloadUrl(a.id)}
              alt={a.filename}
              loading="lazy"
            />
            {#if isVideoAttachment(a)}
              <div class="absolute inset-0 flex items-center justify-center bg-black/20 transition-colors group-hover:bg-black/30">
                <CirclePlay label="" size={32} className="text-white drop-shadow-md" />
              </div>
            {:else}
              <div class="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 transition-opacity group-hover:opacity-100"></div>
            {/if}
          </button>
        {/each}
      </div>
    {/if}

    {#if others.length > 0}
      <div class="mt-3 space-y-2">
        {#each others as a}
          <AttachmentCard
            attachment={a}
            downloadUrl={api.attachments.downloadUrl(a.id)}
            thumbnailUrl={a.has_thumbnail ? api.attachments.thumbnailUrl(a.id) : undefined}
            accentColor={headerColor}
          />
        {/each}
      </div>
    {/if}
  {/if}
</div>
