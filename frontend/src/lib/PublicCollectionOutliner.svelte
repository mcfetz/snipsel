<script lang="ts">
  import { tick } from 'svelte';
  import { api, type Attachment, type CollectionItem } from './api';
  import ImageModal from './ImageModal.svelte';
  import VideoModal from './VideoModal.svelte';
  import DeezerCard from './DeezerCard.svelte';
  import SpotifyCard from './SpotifyCard.svelte';
  import YouTubeCard from './YouTubeCard.svelte';
  import HyperlinkCard from './HyperlinkCard.svelte';
  import MapCard from './MapCard.svelte';
  import ChevronDown from '@animated-color-icons/lucide-svelte/ChevronDown.svelte';
  import Check from '@animated-color-icons/lucide-svelte/Check.svelte';
  import CirclePlay from '@animated-color-icons/lucide-svelte/CirclePlay.svelte';
  import Trash2 from '@animated-color-icons/lucide-svelte/Trash2.svelte';
  import {
    computeHeaderColor,
    computeToolboxBg,
  } from './colors';
  import {
    getDeezerLink,
    getSpotifyLink,
    getYouTubeLink,
    getMapLink,
    getGenericLink,
    stripMediaLinks,
  } from './embeds';
  import { renderMarkdown as renderMarkdownExt } from './markdown';
  import { renderMermaidDiagrams } from './mermaid';
  import {
    computeVisibleItems,
    computeCollapsibleParentIds,
    computeTaskProgress,
  } from './tree';

  let { token, collection, items, canWrite = false, onReload } = $props<{
    token: string;
    collection: {
      id: string;
      title: string;
      icon: string;
      header_color: string | null;
      header_image_url: string | null;
      header_image_position: string | null;
      header_image_x_position: string | null;
      header_image_zoom: number | null;
      default_snipsel_type: string | null;
    };
    items: CollectionItem[];
    canWrite?: boolean;
    onReload?: () => void;
  }>();

  $effect(() => {
    // Process mermaid diagrams when data changes
    const _items = sortedItems;
    if (!_items || !_items.some(i => i?.snipsel?.content_markdown?.includes('mermaid'))) return;

    tick().then(() => renderMermaidDiagrams());
  });

  let expandedSnipsels = $state<Set<string>>(new Set());
  let modalImages = $state<Array<{ id: string; filename: string }>>([]);
  let modalImageIndex = $state<number>(-1);
  let modalVideo = $state<{ id: string; filename: string } | null>(null);

  let newContent = $state('');
  let creating = $state(false);
  let saving = $state(false);
  let editingSnipselId = $state<string | null>(null);
  let editContent = $state('');
  let textareaRef: HTMLTextAreaElement | null = $state(null);

  let sortedItems = $derived([...items].sort((a, b) => a.position - b.position));

  function autosizeTextarea() {
    if (!textareaRef) return;
    textareaRef.style.height = 'auto';
    textareaRef.style.height = textareaRef.scrollHeight + 'px';
  }

  function startEdit(item: CollectionItem) {
    if (!canWrite) return;
    editingSnipselId = item.snipsel_id;
    editContent = item.snipsel.content_markdown || '';
    setTimeout(() => {
      textareaRef?.focus();
      autosizeTextarea();
    }, 0);
  }

  async function saveEdit() {
    if (!editingSnipselId || saving) return;
    saving = true;
    try {
      await api.public.patchSnipsel(token, editingSnipselId, {
        content_markdown: editContent.trim()
      });
      editingSnipselId = null;
      if (onReload) onReload();
    } catch (err) {
      console.error('Failed to save snipsel:', err);
      alert('Fehler beim Speichern.');
    } finally {
      saving = false;
    }
  }

  function cancelEdit() {
    editingSnipselId = null;
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      saveEdit();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      cancelEdit();
    }
  }

  async function handleCreate() {
    if (!newContent.trim() || creating) return;
    creating = true;
    try {
      await api.public.createSnipsel(token, {
        content_markdown: newContent.trim(),
        type: collection.default_snipsel_type || 'text'
      });
      newContent = '';
      if (onReload) onReload();
    } catch (err) {
      console.error('Failed to create snipsel:', err);
      alert('Fehler beim Erstellen des Snipsels.');
    } finally {
      creating = false;
    }
  }

  async function handleToggleTask(item: CollectionItem) {
    if (!canWrite) return;
    try {
      await api.public.patchSnipsel(token, item.snipsel_id, {
        task_done: !item.snipsel.task_done
      });
      if (onReload) onReload();
    } catch (err) {
      console.error('Failed to toggle task:', err);
    }
  }

  async function handleDelete(snipselId: string) {
    if (!canWrite) return;
    if (!confirm('Delete this snipsel?')) return;
    try {
      await api.public.deleteSnipsel(token, snipselId);
      if (onReload) onReload();
    } catch (err) {
      console.error('Failed to delete snipsel:', err);
    }
  }

  let collapsibleParentIds = $derived(computeCollapsibleParentIds(sortedItems));

  function toggleExpand(id: string) {
    const next = new Set(expandedSnipsels);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    expandedSnipsels = next;
  }

  function getHeaderColor(): string {
    return computeHeaderColor(collection.header_color);
  }

  function getToolboxBg(): string {
    const isDark = typeof document !== 'undefined' && document.documentElement.classList.contains('dark');
    return computeToolboxBg(getHeaderColor(), isDark);
  }

  function renderMarkdown(text: string | null): string {
    return renderMarkdownExt(text, getToolboxBg(), getHeaderColor());
  }

  function isImageAttachment(a: any) {
    return a.mime_type?.startsWith('image/') || a.has_thumbnail;
  }

  function isVideoAttachment(a: any) {
    return a.mime_type?.startsWith('video/');
  }

  function taskProgress() {
    return computeTaskProgress(sortedItems);
  }

  function visibleItems(items: CollectionItem[]): CollectionItem[] {
    return computeVisibleItems(items, expandedSnipsels, false);
  }
</script>

<div class="max-w-3xl mx-auto px-4 py-8 space-y-6">
  <div class="relative overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900">
    <div
      class="relative h-28 w-full overflow-hidden"
      style="background-color: {getHeaderColor()}"
    >
      {#if collection.header_image_url}
        <div 
          class="absolute inset-0 bg-cover bg-center"
          style="background-image: url('{collection.header_image_url}'); background-position: {collection.header_image_x_position || '50%'} {collection.header_image_position || '50%'}; transform: scale({collection.header_image_zoom || 1.0})"
        ></div>
      {/if}
    </div>

    <div class="relative px-4 py-3">
      <div class="absolute left-4 top-0 -translate-y-1/2 z-10">
        <div class="grid h-16 w-16 place-items-center rounded-xl border border-slate-200 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900">
          <span class="text-4xl leading-none">{collection.icon}</span>
        </div>
      </div>

      {#if taskProgress().total > 0}
        <div class="absolute left-[5.5rem] right-4 top-0 -translate-y-1/2 rounded-full border border-slate-200 bg-white/80 p-1 shadow-sm backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80">
          <div class="h-2 w-full overflow-hidden rounded-full bg-black/10 dark:bg-white/10">
            <div
              class="h-full rounded-full transition-all duration-500"
              style="width: {Math.round(taskProgress().ratio * 100)}%; background-color: {getHeaderColor()}"
            ></div>
          </div>
        </div>
      {/if}

      <div class="pl-20 text-xl font-bold dark:text-slate-100">
        {collection.title}
      </div>
    </div>
  </div>

  <div class="space-y-1">
    {#each visibleItems(sortedItems) as item (item.snipsel_id)}
      {@const isExpanded = expandedSnipsels.has(item.snipsel_id)}
      {@const isCollapsible = collapsibleParentIds.has(item.snipsel_id)}
      
      <div 
        class="group relative py-1 pr-8 transition-colors hover:bg-slate-50/50 dark:hover:bg-white/[0.02] rounded-lg"
        style="padding-left: calc(3.25rem + {item.indent * 1.25}rem)"
      >
        {#if item.snipsel_id === editingSnipselId}
          <div
            class="relative rounded-lg bg-slate-50 px-4 py-3 ring-1 ring-indigo-200 shadow-sm dark:bg-slate-800 dark:ring-indigo-500/50"
            onfocusout={(e) => {
              const related = e.relatedTarget as Node | null;
              if (related instanceof HTMLElement && e.currentTarget.contains(related)) return;
              saveEdit();
            }}
          >
            <textarea
              bind:this={textareaRef}
              class="w-full resize-none bg-transparent text-lg outline-none dark:text-slate-100"
              rows="1"
              bind:value={editContent}
              oninput={autosizeTextarea}
              onkeydown={handleKeydown}
            ></textarea>
          </div>
        {:else}
          {#if isCollapsible}
            <button
              type="button"
              class="al-icon-wrapper absolute top-1/2 z-20 grid h-6 w-6 -translate-y-1/2 place-items-center rounded-full hover:bg-slate-100 dark:hover:bg-white/10 transition-transform {isExpanded ? '' : '-rotate-90'}"
              style="left: calc(1.625rem + {item.indent * 1.25}rem)"
              onclick={() => toggleExpand(item.snipsel_id)}
              aria-label={isExpanded ? 'Collapse' : 'Expand'}
              title={isExpanded ? 'Collapse' : 'Expand'}
            >
              <ChevronDown label="" size={14} className="text-slate-400" strokeWidth={2} />
            </button>
          {/if}

          {#if item.snipsel.type === 'task'}
            <button
              type="button"
              class="al-icon-wrapper absolute top-1/2 grid h-5 w-5 -translate-y-1/2 place-items-center rounded-full border border-slate-300 bg-white dark:border-white/20 dark:bg-slate-800 transition-colors"
              style="left: calc(1.75rem + {item.indent * 1.25}rem); {item.snipsel.task_done ? `border-color: ${getHeaderColor()}; background-color: ${getHeaderColor()}; color: white;` : ''}"
              onclick={() => handleToggleTask(item)}
              disabled={!canWrite}
            >
              {#if item.snipsel.task_done}
                <Check label="" size={14} strokeWidth={3} />
              {/if}
            </button>
          {/if}

          <div 
            class="flex-1 min-w-0 px-2 py-1 cursor-pointer"
            role="button"
            tabindex="0"
            onclick={() => startEdit(item)}
            onkeydown={(e) => e.key === 'Enter' && startEdit(item)}
          >
            {#if getDeezerLink(item.snipsel.content_markdown)}
              {@const dz = getDeezerLink(item.snipsel.content_markdown)!}
              <DeezerCard type={dz.type} id={dz.id} url={dz.url} accentColor={getHeaderColor()} />
            {/if}
            {#if getSpotifyLink(item.snipsel.content_markdown)}
              {@const sp = getSpotifyLink(item.snipsel.content_markdown)!}
              <SpotifyCard url={sp.url} accentColor={getHeaderColor()} />
            {/if}
            {#if getYouTubeLink(item.snipsel.content_markdown)}
              {@const yt = getYouTubeLink(item.snipsel.content_markdown)!}
              <YouTubeCard url={yt.url} />
            {/if}
            {#if getMapLink(item.snipsel.content_markdown)}
              {@const ml = getMapLink(item.snipsel.content_markdown)!}
              <MapCard lat={ml.lat} lng={ml.lng} url={ml.url} />
            {/if}
            {#if getGenericLink(item.snipsel.content_markdown)}
              {@const gl = getGenericLink(item.snipsel.content_markdown)!}
              <HyperlinkCard url={gl.url} />
            {/if}

            <div 
              class="prose prose-sm max-w-none text-lg prose-p:my-0 prose-headings:my-2 prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg whitespace-pre-wrap dark:prose-invert break-words {item.snipsel.task_done === 2 ? 'line-through' : ''} {item.snipsel.task_done > 0 ? 'opacity-50' : ''}"
            >
              {@html renderMarkdown(stripMediaLinks(item.snipsel.content_markdown))}
            </div>

            {#if item.snipsel.attachments?.length}
              {@const images = item.snipsel.attachments.filter(isImageAttachment)}
              <div class="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-3">
                {#each item.snipsel.attachments as a, imgIdx}
                  {#if isImageAttachment(a)}
                    <button
                      class="group relative aspect-square overflow-hidden rounded-xl border border-slate-200 bg-slate-50 dark:border-white/10 dark:bg-white/5"
                      onclick={(e) => { e.stopPropagation(); modalImages = images.map(img => ({ id: img.id, filename: img.filename })); modalImageIndex = imgIdx; }}
                    >
                      <img 
                        src={`/api/attachments/${a.id}/thumbnail`} 
                        alt={a.filename} 
                        class="h-full w-full object-cover transition-transform group-hover:scale-105"
                      />
                      <div class="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors"></div>
                    </button>
                  {:else if isVideoAttachment(a)}
                    <button
                      class="al-icon-wrapper group relative aspect-square overflow-hidden rounded-xl border border-slate-200 bg-slate-50 dark:border-white/10 dark:bg-white/5"
                      onclick={(e) => { e.stopPropagation(); modalVideo = a; }}
                    >
                      <img 
                        src={`/api/attachments/${a.id}/thumbnail`} 
                        alt={a.filename} 
                        class="h-full w-full object-cover transition-transform group-hover:scale-105"
                      />
                      <div class="absolute inset-0 flex items-center justify-center bg-black/20 group-hover:bg-black/30 transition-colors">
                        <CirclePlay label="" size={32} className="text-white drop-shadow-md" />
                      </div>
                    </button>
                  {:else}
                    <a 
                      href="/api/attachments/{a.id}" 
                      class="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 hover:bg-slate-50 dark:border-white/10 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                      target="_blank"
                      onclick={(e) => e.stopPropagation()}
                    >
                      <span class="text-base">📎</span>
                      <span class="truncate">{a.filename}</span>
                    </a>
                  {/if}
                {/each}
              </div>
            {/if}
          </div>
        {/if}

        {#if canWrite}
          <button 
            class="al-icon-wrapper absolute right-0 top-1/2 -translate-y-1/2 p-2 text-slate-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
            onclick={() => handleDelete(item.snipsel_id)}
            aria-label="Delete snipsel"
            title="Delete snipsel"
          >
            <Trash2 label="" size={16} strokeWidth={2} />
          </button>
        {/if}
      </div>
    {/each}
  </div>

  {#if canWrite}
    <div class="mt-8 pt-6 border-t border-slate-100 dark:border-white/5">
      <div class="flex flex-col gap-2 p-3 bg-slate-50 border border-slate-200 rounded-2xl dark:bg-slate-800/50 dark:border-white/10">
        <textarea
          bind:value={newContent}
          placeholder="Add something anonymously..."
          class="w-full bg-transparent border-none focus:ring-0 text-lg resize-none placeholder:text-slate-400 dark:text-slate-100"
          rows="2"
          onkeydown={(e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
              handleCreate();
            }
          }}
        ></textarea>
        <div class="flex items-center justify-between mt-2">
          <span class="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Cmd+Enter to add</span>
          <button
            class="px-4 py-1.5 rounded-full font-bold text-sm text-white transition-all hover:brightness-110 active:scale-95 disabled:opacity-50"
            style="background-color: {getHeaderColor()}"
            onclick={handleCreate}
            disabled={creating || !newContent.trim()}
          >
            {creating ? 'Adding...' : 'Add Snipsel'}
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>

{#if modalImages.length > 0 && modalImageIndex >= 0}
  <ImageModal
    attachments={modalImages}
    currentIndex={modalImageIndex}
    onClose={() => { modalImages = []; modalImageIndex = -1; }}
    onNavigate={(idx) => modalImageIndex = idx}
  />
{/if}

{#if modalVideo}
  <VideoModal
    attachmentId={modalVideo.id}
    filename={modalVideo.filename}
    onClose={() => modalVideo = null}
  />
{/if}
