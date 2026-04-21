<script lang="ts">
  import Bold from '@animated-color-icons/lucide-svelte/Bold.svelte';
  import Italic from '@animated-color-icons/lucide-svelte/Italic.svelte';
  import Strikethrough from '@animated-color-icons/lucide-svelte/Strikethrough.svelte';
  import Link from '@animated-color-icons/lucide-svelte/Link.svelte';
  import Code from '@animated-color-icons/lucide-svelte/Code.svelte';
  import Quote from '@animated-color-icons/lucide-svelte/Quote.svelte';
  import List from '@animated-color-icons/lucide-svelte/List.svelte';
  import ListChecks from '@animated-color-icons/lucide-svelte/ListChecks.svelte';

  interface Props {
    textarea: HTMLTextAreaElement | undefined;
    onFormat: (content: string) => void;
    accentColor: string;
  }

  let { textarea, onFormat, accentColor }: Props = $props();

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

  const buttons = [
    { icon: Bold, label: 'Bold', prefix: '**', suffix: '**' },
    { icon: Italic, label: 'Italic', prefix: '*', suffix: '*' },
    { icon: Strikethrough, label: 'Strikethrough', prefix: '~~', suffix: '~~' },
    { icon: Code, label: 'Code', prefix: '`', suffix: '`' },
    { icon: Link, label: 'Link', prefix: '[', suffix: '](url)' },
    { icon: Quote, label: 'Quote', prefix: '> ', suffix: '' },
    { icon: List, label: 'List', prefix: '- ', suffix: '' },
    { icon: ListChecks, label: 'Task', prefix: '- [ ] ', suffix: '' },
  ];
</script>

<div 
  class="flex items-center gap-0.5 rounded-t-lg border-b border-slate-200 bg-white/50 p-1 backdrop-blur-sm dark:border-white/10 dark:bg-slate-900/50"
  style="--accent-color: {accentColor}"
>
  {#each buttons as btn}
    {@const Icon = btn.icon}
    <button
      type="button"
      class="flex h-8 w-8 items-center justify-center rounded-md text-slate-500 transition-all hover:bg-white hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/10 dark:hover:text-slate-100"
      onclick={() => applyFormat(btn.prefix, btn.suffix)}
      title={btn.label}
      aria-label={btn.label}
    >
      <Icon size={16} strokeWidth={2.5} />
    </button>
  {/each}
</div>

<style>
  button:hover {
    color: var(--accent-color, #4f46e5);
  }
</style>
