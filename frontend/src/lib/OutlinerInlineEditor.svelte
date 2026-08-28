<script lang="ts">
  import { tick } from 'svelte';
  import FormattingToolbar from './FormattingToolbar.svelte';
  import DeezerCard from './DeezerCard.svelte';
  import SpotifyCard from './SpotifyCard.svelte';
  import YouTubeCard from './YouTubeCard.svelte';
  import MapCard from './MapCard.svelte';
  import HyperlinkCard from './HyperlinkCard.svelte';
  import CollectionLinkCard from './CollectionLinkCard.svelte';
  import {
    getDeezerLink,
    getSpotifyLink,
    getYouTubeLink,
    getMapLink,
    getGenericLink,
    getCollectionLink,
  } from './embeds';

  export interface AutocompleteSuggestion {
    id: string;
    type: 'tag' | 'mention' | 'collection';
    label: string;
    icon?: string;
  }

  interface Props {
    editContent: string;
    editIndent: number;
    editFullscreen: boolean;
    headerColor: string;
    isUploading: boolean;
    showCardView: boolean;
    collectionRefs?: Array<{ title: string; collection_id: string }>;
    suggestions: AutocompleteSuggestion[];
    showAutocomplete: boolean;
    autocompleteSelectedIndex: number;
    textareaFontSize?: 'base' | 'lg';
    onFormat?: (content: string) => void;
    onSaveAndNew?: () => void;
    onUploadAttachment?: (files: FileList) => void;
    onApplySuggestion?: (suggestion: AutocompleteSuggestion) => void;
    onInput?: () => void;
    onKeydown?: (e: KeyboardEvent) => void;
    onPaste?: (e: ClipboardEvent) => void;
    onFocusOut?: (e: FocusEvent) => void;
  }

  let {
    editContent = $bindable(''),
    editIndent = $bindable(0),
    editFullscreen = $bindable(false),
    headerColor,
    isUploading,
    showCardView,
    collectionRefs,
    suggestions,
    showAutocomplete,
    autocompleteSelectedIndex,
    textareaFontSize = 'lg',
    onFormat,
    onSaveAndNew,
    onUploadAttachment,
    onApplySuggestion,
    onInput,
    onKeydown,
    onPaste,
    onFocusOut,
  }: Props = $props();

  let textareaRef: HTMLTextAreaElement | null = $state(null);
  let editAttachmentsInputRef: HTMLInputElement | null = $state(null);

  export function focusTextarea() {
    textareaRef?.focus();
  }

  export function autosize() {
    if (!textareaRef) return;
    textareaRef.style.height = 'auto';
    textareaRef.style.height = `${textareaRef.scrollHeight}px`;
  }

  function handleFileInput(e: Event) {
    const input = e.target as HTMLInputElement;
    if (input.files && input.files.length > 0 && onUploadAttachment) {
      onUploadAttachment(input.files);
    }
  }

  let deezer = $derived(showCardView ? getDeezerLink(editContent) : null);
  let spotify = $derived(showCardView ? getSpotifyLink(editContent) : null);
  let youtube = $derived(showCardView ? getYouTubeLink(editContent) : null);
  let mapLink = $derived(showCardView ? getMapLink(editContent) : null);
  let genericLink = $derived(showCardView ? getGenericLink(editContent) : null);
  let collectionLink = $derived(showCardView ? getCollectionLink(editContent, collectionRefs) : null);
</script>

<div
  class="relative rounded-xl bg-slate-50 shadow-sm ring-1 ring-indigo-200 dark:bg-slate-800 dark:ring-indigo-500/50"
  class:!fixed={editFullscreen}
  class:inset-[5%]={editFullscreen}
  class:!z-50={editFullscreen}
  class:!flex={editFullscreen}
  class:!flex-col={editFullscreen}
  class:shadow-2xl={editFullscreen}
  class:overflow-hidden={editFullscreen}
  onfocusout={onFocusOut}
>
  <input
    bind:this={editAttachmentsInputRef}
    class="hidden"
    type="file"
    multiple
    onchange={handleFileInput}
    disabled={isUploading}
  />

  <FormattingToolbar
    textarea={textareaRef}
    onFormat={(content) => {
      editContent = content;
      if (onFormat) onFormat(content);
      if (onInput) onInput();
    }}
    accentColor={headerColor}
    isFullscreen={editFullscreen}
    onToggleFullscreen={() => {
      editFullscreen = !editFullscreen;
      tick().then(() => {
        autosize();
        textareaRef?.focus();
      });
    }}
    onIndent={() => {
      editIndent = Math.min(6, editIndent + 1);
      textareaRef?.focus();
    }}
    onOutdent={() => {
      editIndent = Math.max(0, editIndent - 1);
      textareaRef?.focus();
    }}
    onNewSnipsel={onSaveAndNew}
    onUploadAttachment={() => editAttachmentsInputRef?.click()}
  />

  <div
    class="overflow-y-auto px-2.5 py-3 rounded-b-lg"
    class:flex-1={editFullscreen}
    class:flex={editFullscreen}
    class:flex-col={editFullscreen}
  >
    <textarea
      bind:this={textareaRef}
      class="w-full resize-none bg-transparent outline-none dark:text-slate-100 {textareaFontSize === 'base' ? 'text-base' : 'text-lg'}"
      class:flex-1={editFullscreen}
      rows="2"
      bind:value={editContent}
      oninput={() => {
        autosize();
        if (onInput) onInput();
      }}
      onkeydown={onKeydown}
      onpaste={onPaste}
    ></textarea>

    {#if isUploading}
      <div class="absolute right-3 top-3 flex items-center gap-2 text-xs text-slate-400">
        <div class="h-3 w-3 animate-spin rounded-full border-2 border-slate-300 border-t-indigo-500"></div>
        Uploading...
      </div>
    {/if}

    {#if showCardView}
      {#if deezer}
        <DeezerCard url={deezer.url} type={deezer.type} id={deezer.id} accentColor={headerColor} />
      {/if}
      {#if spotify}
        <SpotifyCard url={spotify.url} accentColor={headerColor} />
      {/if}
      {#if youtube}
        <YouTubeCard url={youtube.url} accentColor={headerColor} />
      {/if}
      {#if mapLink}
        <MapCard lat={mapLink.lat} lng={mapLink.lng} url={mapLink.url} accentColor={headerColor} />
      {/if}
      {#if genericLink}
        <HyperlinkCard url={genericLink.url} accentColor={headerColor} />
      {/if}
      {#if collectionLink}
        <CollectionLinkCard collectionId={collectionLink} accentColor={headerColor} />
      {/if}
    {/if}

    {#if showAutocomplete && suggestions.length > 0}
      <div class="absolute left-0 right-0 top-full z-50 mt-1 overflow-hidden rounded-xl border border-slate-200 bg-white/95 shadow-xl ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/95 dark:ring-white/10">
        {#each suggestions as s, idx (s.id + s.type)}
          <button
            type="button"
            class="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-sm transition-colors {idx === autocompleteSelectedIndex ? 'bg-indigo-50 text-indigo-900 dark:bg-indigo-950/40 dark:text-indigo-200' : 'hover:bg-slate-50 dark:hover:bg-white/5'}"
            onmousedown={(e) => {
              e.preventDefault();
              if (onApplySuggestion) onApplySuggestion(s);
            }}
          >
            {#if s.icon}
              <span class="text-base">{s.icon}</span>
            {:else if s.type === 'tag'}
              <span class="font-mono text-xs text-slate-400">#</span>
            {:else if s.type === 'mention'}
              <span class="font-mono text-xs text-slate-400">@</span>
            {:else}
              <span class="text-base">📁</span>
            {/if}
            <span class="truncate font-medium">{s.label}</span>
          </button>
        {/each}
      </div>
    {/if}
  </div>
</div>
