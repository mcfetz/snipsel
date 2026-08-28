<script lang="ts">
  import { scale, fly, fade } from 'svelte/transition';
  import CirclePlay from '@animated-color-icons/lucide-svelte/CirclePlay.svelte';
  import Bell from '@animated-color-icons/lucide-svelte/Bell.svelte';
  import DeezerCard from './DeezerCard.svelte';
  import SpotifyCard from './SpotifyCard.svelte';
  import YouTubeCard from './YouTubeCard.svelte';
  import MapCard from './MapCard.svelte';
  import HyperlinkCard from './HyperlinkCard.svelte';
  import CollectionLinkCard from './CollectionLinkCard.svelte';
  import AttachmentCard from './AttachmentCard.svelte';
  import { api, type Attachment, type CollectionItem } from './api';
  import { isExpired } from './dates';
  import { parseSnipselEmbeds } from './embeds';
  import { renderWithWikiLinks } from './markdown';
  import { currentView, searchQuery } from './stores';

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
    cardTileBg: string;
    cardTileBorder: string;
    isSelected: boolean;
    isAnchorHighlighted: boolean;
    isEditingOther: boolean;
    rangeLongPress: RangeLongPressHandlers;
    onStartEdit: (item: CollectionItem) => void;
    onToggleTask: (item: CollectionItem) => void;
    onToggleReaction: (snipselId: string, emoji: string) => void;
    onOpenImageModal: (images: Array<{ id: string; filename: string }>, index: number) => void;
    onOpenVideoModal: (id: string, filename: string) => void;
  }

  let {
    item,
    headerColor,
    toolboxBg,
    cardTileBg,
    cardTileBorder,
    isSelected,
    isAnchorHighlighted,
    isEditingOther,
    rangeLongPress,
    onStartEdit,
    onToggleTask,
    onToggleReaction,
    onOpenImageModal,
    onOpenVideoModal,
  }: Props = $props();

  const isImageAttachment = (a: Attachment) =>
    Boolean(a.mime_type?.startsWith('image/') || (a.has_thumbnail && !a.mime_type?.startsWith('video/')));
  const isVideoAttachment = (a: Attachment) =>
    Boolean(a.mime_type?.startsWith('video/') || (a.has_thumbnail && a.filename.toLowerCase().match(/\.(mp4|mov|webm|avi|mkv)$/)));
  const isMediaAttachment = (a: Attachment) => isImageAttachment(a) || isVideoAttachment(a);

  let media = $derived(item.snipsel.attachments ? item.snipsel.attachments.filter(isMediaAttachment) : []);
  let others = $derived(item.snipsel.attachments ? item.snipsel.attachments.filter((a) => !isMediaAttachment(a)) : []);
  let images = $derived(media.filter(isImageAttachment));
</script>

<div
  id={`snipsel-${item.snipsel_id}`}
  class="group relative flex flex-col gap-2 overflow-hidden rounded-2xl border p-3 shadow-sm transition-all hover:shadow-md {isAnchorHighlighted ? 'ring-2' : ''} {isSelected ? 'ring-2 !border-transparent' : ''} {item.snipsel.task_done > 0 ? 'task-faded' : ''} {item.snipsel.task_done === 2 ? 'task-cancelled' : ''}"
  class:blur-sm={isEditingOther}
  class:opacity-40={isEditingOther}
  class:pointer-events-none={isEditingOther}
  style={`background-color: ${cardTileBg}; border-color: ${cardTileBorder}; --tw-ring-color: ${headerColor};`}
  in:fly={{ y: 10, duration: 200 }}
  out:fade={{ duration: 150 }}
>
  <!-- Selection Bar on Right -->
  <button
    type="button"
    class="absolute right-0 top-0 bottom-0 z-10 w-4 flex justify-end cursor-pointer group-hover:opacity-100 transition-opacity"
    aria-label={isSelected ? 'Deselect item' : 'Select item'}
    onpointerdown={(e) => {
      e.stopPropagation();
      rangeLongPress.onpointerdown(e);
    }}
    onpointerup={(e) => {
      e.stopPropagation();
      rangeLongPress.onpointerup(e);
    }}
    onpointercancel={(e) => {
      e.stopPropagation();
      rangeLongPress.onpointercancel(e);
    }}
    onpointerleave={(e) => {
      e.stopPropagation();
      rangeLongPress.onpointerleave(e);
    }}
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
      class="h-full w-1.5 origin-right transition-all duration-150 ease-out {isSelected ? '' : 'scale-x-0 group-hover:scale-x-100'} hover:scale-x-150 active:scale-x-75"
      style={isSelected ? `background-color: ${headerColor}` : 'background-color: #94a3b8'}
    ></div>
  </button>

  <!-- Media Banner on top of Card -->
  {#if media.length > 0 && item.snipsel.card_view !== false}
    <div class="-mx-1 -mt-1 overflow-hidden rounded-xl bg-slate-100 dark:bg-slate-800">
      {#if media.length === 1}
        {@const a = media[0]}
        <button
          type="button"
          class="relative block w-full overflow-hidden"
          onclick={(e) => {
            e.stopPropagation();
            if (isVideoAttachment(a)) onOpenVideoModal(a.id, a.filename);
            else onOpenImageModal(images.map((img) => ({ id: img.id, filename: img.filename })), 0);
          }}
        >
          <img
            class="max-h-60 w-full object-cover transition-transform duration-300 hover:scale-105"
            src={a.has_thumbnail ? api.attachments.thumbnailUrl(a.id) : api.attachments.downloadUrl(a.id)}
            alt={a.filename}
            loading="lazy"
          />
          {#if isVideoAttachment(a)}
            <div class="absolute inset-0 flex items-center justify-center bg-black/25">
              <CirclePlay label="" size={32} className="text-white drop-shadow-md" />
            </div>
          {/if}
        </button>
      {:else}
        <div class="grid grid-cols-2 gap-1">
          {#each media.slice(0, 4) as a, mediaIdx}
            {@const imgIdx = images.findIndex((img) => img.id === a.id)}
            <button
              type="button"
              class="relative aspect-square w-full overflow-hidden"
              onclick={(e) => {
                e.stopPropagation();
                if (isVideoAttachment(a)) onOpenVideoModal(a.id, a.filename);
                else onOpenImageModal(images.map((img) => ({ id: img.id, filename: img.filename })), imgIdx);
              }}
            >
              <img
                class="h-full w-full object-cover transition-transform duration-300 hover:scale-105"
                src={a.has_thumbnail ? api.attachments.thumbnailUrl(a.id) : api.attachments.downloadUrl(a.id)}
                alt={a.filename}
                loading="lazy"
              />
              {#if isVideoAttachment(a)}
                <div class="absolute inset-0 flex items-center justify-center bg-black/25">
                  <CirclePlay label="" size={24} className="text-white drop-shadow-md" />
                </div>
              {/if}
              {#if mediaIdx === 3 && media.length > 4}
                <div class="absolute inset-0 flex items-center justify-center bg-black/50 text-xs font-bold text-white">
                  +{media.length - 4}
                </div>
              {/if}
            </button>
          {/each}
        </div>
      {/if}
    </div>
  {/if}

  <!-- Embed Cards -->
  {#if item.snipsel.content_markdown && item.snipsel.card_view !== false}
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

  <!-- Main Card Body (Task checkbox + Content) -->
  <div
    class="flex cursor-pointer items-start gap-2 pr-3"
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
      onStartEdit(item);
    }}
    onkeydown={(e) => {
      if (e.target === e.currentTarget && e.key === 'Enter') onStartEdit(item);
    }}
  >
    {#if item.snipsel.type === 'task'}
      <button
        class="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full border border-slate-300 bg-white transition-all duration-150 hover:scale-110 active:scale-95 dark:border-white/20 dark:bg-slate-800"
        type="button"
        aria-label={item.snipsel.task_done ? 'Toggle task status' : 'Mark task done'}
        title={item.snipsel.task_done === 1 ? 'Done' : item.snipsel.task_done === 2 ? 'Cancelled' : 'Open'}
        onclick={(e) => {
          e.stopPropagation();
          onToggleTask(item);
        }}
        style={item.snipsel.task_done > 0
          ? `border-color: ${headerColor}; background-color: ${toolboxBg}; color: ${headerColor}; font-size: 10px`
          : ''}
      >
        {#if item.snipsel.task_done === 1}
          <span in:scale={{ start: 0.5, duration: 150 }}>✓</span>
        {:else if item.snipsel.task_done === 2}
          <span in:scale={{ start: 0.5, duration: 150 }}>✕</span>
        {/if}
      </button>
    {/if}

    <div class="min-w-0 flex-1">
      {#if item.snipsel.content_markdown}
        <div
          class="prose prose-sm max-w-none break-words whitespace-pre-wrap text-sm prose-headings:my-1.5 prose-h1:text-lg prose-h2:text-base prose-h3:text-sm prose-p:my-0 dark:prose-invert"
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
      {:else if !item.snipsel.attachments || !item.snipsel.attachments.length}
        <span class="text-xs italic text-slate-400 dark:text-slate-500">Empty snipsel</span>
      {/if}
    </div>
  </div>

  <!-- Non-media files -->
  {#if others.length > 0}
    <div class="space-y-1.5">
      {#each others.slice(0, 2) as a}
        <AttachmentCard
          attachment={a}
          downloadUrl={api.attachments.downloadUrl(a.id)}
          thumbnailUrl={a.has_thumbnail ? api.attachments.thumbnailUrl(a.id) : undefined}
          accentColor={headerColor}
        />
      {/each}
      {#if others.length > 2}
        <div class="text-[10px] text-slate-400">+{others.length - 2} more files</div>
      {/if}
    </div>
  {/if}

  <!-- Footer: Tags, Mentions, Reminders, Reactions -->
  {#if (item.snipsel.tags?.length ?? 0) > 0 || (item.snipsel.mentions?.length ?? 0) > 0 || item.snipsel.reminder_at || (item.snipsel.reactions && item.snipsel.reactions.length > 0)}
    <div class="mt-auto flex flex-wrap items-center gap-1.5 border-t border-slate-100 pt-1.5 pr-3 dark:border-white/5">
      {#each item.snipsel.tags ?? [] as t (t)}
        <span 
          class="rounded-full px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wider"
          style="background-color: {toolboxBg}; color: {headerColor}; border: 1px solid rgba(0,0,0,0.05)"
        >
          #{t}
        </span>
      {/each}
      {#each item.snipsel.mentions ?? [] as m (m)}
        <span 
          class="rounded-full px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wider"
          style="background-color: {toolboxBg}; color: {headerColor}; border: 1px solid rgba(0,0,0,0.05)"
        >
          @{m}
        </span>
      {/each}
      {#if item.snipsel.reminder_at}
        {@const expired = isExpired(item.snipsel.reminder_at)}
        <span 
          class="flex items-center gap-1 rounded px-1.5 py-0.5 text-[9px] {expired ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400' : ''}"
          style={expired 
            ? undefined 
            : `background-color: ${toolboxBg}; color: ${headerColor}`}
        >
          <Bell label="" size={9} strokeWidth={2.5} />
          {new Date(item.snipsel.reminder_at).toLocaleDateString([], { month: 'numeric', day: 'numeric' })}
        </span>
      {/if}
      {#if item.snipsel.reactions && item.snipsel.reactions.length > 0}
        {#each item.snipsel.reactions as r (r.emoji)}
          <button
            type="button"
            class="flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-[10px] font-medium transition-colors {r.me ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300' : 'bg-slate-100 text-slate-600 dark:bg-white/5 dark:text-slate-400'}"
            onclick={(e) => {
              e.stopPropagation();
              onToggleReaction(item.snipsel_id, r.emoji);
            }}
          >
            <span>{r.emoji}</span>
            <span class="opacity-60">{r.count}</span>
          </button>
        {/each}
      {/if}
    </div>
  {/if}
</div>
