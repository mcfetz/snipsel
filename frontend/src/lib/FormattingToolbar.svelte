<script lang="ts">
  import Bold from '@animated-color-icons/lucide-svelte/Bold.svelte';
  import Italic from '@animated-color-icons/lucide-svelte/Italic.svelte';
  import Strikethrough from '@animated-color-icons/lucide-svelte/Strikethrough.svelte';
  import Link from '@animated-color-icons/lucide-svelte/Link.svelte';
  import Code from '@animated-color-icons/lucide-svelte/Code.svelte';
  import Quote from '@animated-color-icons/lucide-svelte/Quote.svelte';
  import List from '@animated-color-icons/lucide-svelte/List.svelte';
  import Terminal from '@animated-color-icons/lucide-svelte/Terminal.svelte';
  import Heading1 from '@animated-color-icons/lucide-svelte/Heading1.svelte';
  import Heading2 from '@animated-color-icons/lucide-svelte/Heading2.svelte';
  import ListOrdered from '@animated-color-icons/lucide-svelte/ListOrdered.svelte';
  import Table from '@animated-color-icons/lucide-svelte/Table.svelte';
  import SeparatorHorizontal from '@animated-color-icons/lucide-svelte/SeparatorHorizontal.svelte';
  import Maximize from '@animated-color-icons/lucide-svelte/Maximize.svelte';
  import Minimize from '@animated-color-icons/lucide-svelte/Minimize.svelte';
  import Indent from '@animated-color-icons/lucide-svelte/Indent.svelte';
  import Outdent from '@animated-color-icons/lucide-svelte/Outdent.svelte';
  import ListPlus from '@animated-color-icons/lucide-svelte/ListPlus.svelte';
  import Network from '@animated-color-icons/lucide-svelte/Network.svelte';

  interface Props {
    textarea: HTMLTextAreaElement | undefined;
    onFormat: (content: string) => void;
    accentColor: string;
    isFullscreen?: boolean;
    onToggleFullscreen?: () => void;
    onIndent?: () => void;
    onOutdent?: () => void;
    onNewSnipsel?: () => void;
  }

  let { textarea, onFormat, accentColor, isFullscreen, onToggleFullscreen, onIndent, onOutdent, onNewSnipsel }: Props = $props();

  function applyFormat(prefix: string, suffix: string = '') {
    if (!textarea) return;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const value = textarea.value;
    const selection = value.substring(start, end);

    const before = value.substring(0, start);
    const after = value.substring(end);

    let newContent = '';
    let newCursorStart = 0;
    let newCursorEnd = 0;

    if (start === end) {
      // No selection
      if (prefix === '[' && suffix === '](url)') {
        newContent = before + '[' + suffix + after;
        newCursorStart = start + 1;
        newCursorEnd = start + 1;
      } else {
        newContent = before + prefix + suffix + after;
        newCursorStart = newCursorEnd = start + prefix.length;
      }
    } else {
      // Wrap selection
      if (prefix === '[' && suffix === '](url)') {
        newContent = before + '[' + selection + '](url)' + after;
        newCursorStart = end + 3; // Position inside (url)
        newCursorEnd = end + 6;
      } else {
        newContent = before + prefix + selection + suffix + after;
        newCursorStart = start + prefix.length;
        newCursorEnd = end + prefix.length;
      }
    }

    onFormat(newContent);

    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(newCursorStart, newCursorEnd);
    }, 0);
  }

  const groups = [
    [
      { icon: Bold, label: 'Bold', prefix: '**', suffix: '**' },
      { icon: Italic, label: 'Italic', prefix: '*', suffix: '*' },
      { icon: Strikethrough, label: 'Strikethrough', prefix: '~~', suffix: '~~' },
    ],
    [
      { icon: Heading1, label: 'H1', prefix: '# ', suffix: '' },
      { icon: Heading2, label: 'H2', prefix: '## ', suffix: '' },
    ],
    [
      { icon: List, label: 'Bullet List', prefix: '- ', suffix: '' },
      { icon: ListOrdered, label: 'Ordered List', prefix: '1. ', suffix: '' },
    ],
    [
      { icon: Code, label: 'Inline Code', prefix: '`', suffix: '`' },
      { icon: Terminal, label: 'Code Block', prefix: '```\n', suffix: '\n```' },
      { icon: Network, label: 'Mermaid Diagram', prefix: '```mermaid\n', suffix: '\n```' },
    ],
    [
      { icon: Link, label: 'Link', prefix: '[', suffix: '](url)' },
      { icon: Quote, label: 'Quote', prefix: '> ', suffix: '' },
      { icon: Table, label: 'Table', prefix: '| Header | Header |\n| --- | --- |\n| Cell | Cell |', suffix: '' },
      { icon: SeparatorHorizontal, label: 'Horizontal Line', prefix: '\n\n---\n\n', suffix: '' },
    ],
  ];
</script>

<div 
  class="flex flex-wrap items-center gap-0.5 rounded-t-lg border-b border-slate-200 bg-white/50 p-1 backdrop-blur-sm dark:border-white/10 dark:bg-slate-900/50"
  style="--accent-color: {accentColor}"
>
  {#each groups as group, gi}
    {#if gi > 0}
      <div class="mx-1 h-4 w-px bg-slate-200 dark:bg-white/10"></div>
    {/if}
    {#each group as btn}
      {@const Icon = btn.icon}
      <button
        type="button"
        class="flex h-8 w-8 items-center justify-center rounded-md text-slate-500 transition-all hover:bg-white hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/10 dark:hover:text-slate-100"
        onpointerdown={(e) => e.preventDefault()}
        onmousedown={(e) => e.preventDefault()}
        ontouchstart={(e) => e.preventDefault()}
        onclick={() => applyFormat(btn.prefix, btn.suffix)}
        title={btn.label}
        aria-label={btn.label}
      >
        <Icon size={16} strokeWidth={2.5} />
      </button>
    {/each}
  {/each}

  {#if onOutdent}
    <div class="mx-1 h-4 w-px bg-slate-200 dark:bg-white/10"></div>
    <button
      type="button"
      class="flex h-8 w-8 items-center justify-center rounded-md text-slate-500 transition-all hover:bg-white hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/10 dark:hover:text-slate-100"
      onpointerdown={(e) => e.preventDefault()}
      onmousedown={(e) => e.preventDefault()}
      ontouchstart={(e) => e.preventDefault()}
      onclick={onOutdent}
      title="Outdent"
      aria-label="Outdent"
    >
      <Outdent size={16} strokeWidth={2.5} />
    </button>
  {/if}

  {#if onIndent}
    <button
      type="button"
      class="flex h-8 w-8 items-center justify-center rounded-md text-slate-500 transition-all hover:bg-white hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/10 dark:hover:text-slate-100"
      onpointerdown={(e) => e.preventDefault()}
      onmousedown={(e) => e.preventDefault()}
      ontouchstart={(e) => e.preventDefault()}
      onclick={onIndent}
      title="Indent"
      aria-label="Indent"
    >
      <Indent size={16} strokeWidth={2.5} />
    </button>
  {/if}

  {#if onNewSnipsel}
    <div class="mx-1 h-4 w-px bg-slate-200 dark:bg-white/10"></div>
    <button
      type="button"
      class="flex h-8 w-8 items-center justify-center rounded-md text-slate-500 transition-all hover:bg-white hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/10 dark:hover:text-slate-100"
      onpointerdown={(e) => e.preventDefault()}
      onmousedown={(e) => e.preventDefault()}
      ontouchstart={(e) => e.preventDefault()}
      onclick={onNewSnipsel}
      title="Save & New Snipsel"
      aria-label="Save & New Snipsel"
    >
      <ListPlus size={16} strokeWidth={2.5} />
    </button>
  {/if}

  {#if onToggleFullscreen}
    <div class="mx-1 h-4 w-px bg-slate-200 dark:bg-white/10"></div>
    <button
      type="button"
      class="flex h-8 w-8 items-center justify-center rounded-md text-slate-500 transition-all hover:bg-white hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/10 dark:hover:text-slate-100"
      onpointerdown={(e) => e.preventDefault()}
      onmousedown={(e) => e.preventDefault()}
      ontouchstart={(e) => e.preventDefault()}
      onclick={onToggleFullscreen}
      title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
      aria-label={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
    >
      {#if isFullscreen}
        <Minimize size={16} strokeWidth={2.5} />
      {:else}
        <Maximize size={16} strokeWidth={2.5} />
      {/if}
    </button>
  {/if}

  <div class="flex-1"></div>
</div>

<style>
  button:hover {
    color: var(--accent-color, #4f46e5);
  }
</style>
