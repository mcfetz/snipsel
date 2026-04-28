<script lang="ts">
  import { currentUser } from './session';
  import { api, type Collection, type CollectionItem } from './api';
  import Check from '@animated-color-icons/lucide-svelte/Check.svelte';
  import Copy from '@animated-color-icons/lucide-svelte/Copy.svelte';
  import FileDown from '@animated-color-icons/lucide-svelte/FileDown.svelte';

  interface Props {
    collection: Collection;
    onClose: () => void;
  }

  let { collection, onClose }: Props = $props();

  let items = $state<CollectionItem[]>([]);
  let loading = $state(true);
  let copied = $state(false);

  const DEFAULT_ACCENT = '#4f46e5';

  function getAccent(): string {
    const raw = ($currentUser?.default_collection_header_color || '').trim() || DEFAULT_ACCENT;
    return /^#[0-9a-fA-F]{6}$/.test(raw) ? raw : DEFAULT_ACCENT;
  }

  function formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleString('de-DE', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  function escapeMetadata(value: string): string {
    return value.replace(/\\/g, '\\\\').replace(/\n/g, '\\n');
  }

  function getIndentPrefix(indent: number): string {
    return '  '.repeat(indent);
  }

  function snipselToMarkdown(item: CollectionItem): string {
    const snipsel = item.snipsel;
    let content = '';
    const indent = getIndentPrefix(item.indent);

    switch (snipsel.type) {
      case 'task':
        const checkbox = snipsel.task_done === 1 ? '[x]' : '[ ]';
        content = `${indent}- ${checkbox} ${snipsel.content_markdown || ''}`;
        break;
      case 'link_external':
        if (snipsel.external_url) {
          const label = snipsel.external_label || snipsel.external_url;
          content = `${indent}- [${label}](${snipsel.external_url})`;
        } else {
          content = `${indent}- ${snipsel.content_markdown || ''}`;
        }
        break;
      case 'link_internal':
        content = `${indent}- 🔗 ${snipsel.content_markdown || ''}`;
        break;
      case 'image':
        content = `${indent}- 📷 ${snipsel.content_markdown || ''}`;
        break;
      case 'attachment':
        const attachments = snipsel.attachments || [];
        if (attachments.length > 0) {
          const attNames = attachments.map(a => `[${a.filename}]`).join(', ');
          content = `${indent}- 📎 ${attNames} ${snipsel.content_markdown || ''}`;
        } else {
          content = `${indent}- 📎 ${snipsel.content_markdown || ''}`;
        }
        break;
      default:
        content = `${indent}- ${snipsel.content_markdown || ''}`;
    }

    // Add tags if present
    if (snipsel.tags && snipsel.tags.length > 0) {
      content += ` ${snipsel.tags.map(t => `#${t}`).join(' ')}`;
    }

    // Add mentions if present
    if (snipsel.mentions && snipsel.mentions.length > 0) {
      content += ` ${snipsel.mentions.map(m => `@${m}`).join(' ')}`;
    }

    return content;
  }

  function generateMarkdown(): string {
    const lines: string[] = [];

    // YAML frontmatter with metadata
    lines.push('---');
    lines.push(`title: "${escapeMetadata(collection.title)}"`);
    lines.push(`icon: "${collection.icon}"`);
    lines.push(`collection_id: "${collection.id}"`);
    lines.push(`owner: "${collection.modified_by_username || 'Unknown'}"`);
    lines.push(`created_at: "${formatDate(collection.created_at)}"`);
    lines.push(`created_by: "${collection.modified_by_username || 'Unknown'}"`);
    lines.push(`modified_at: "${formatDate(collection.modified_at)}"`);
    lines.push(`modified_by: "${collection.modified_by_username || 'Unknown'}"`);
    if (collection.header_color) {
      lines.push(`header_color: "${collection.header_color}"`);
    }
    if (collection.default_snipsel_type) {
      lines.push(`default_snipsel_type: "${collection.default_snipsel_type}"`);
    }
    lines.push(`show_completed_tasks: ${collection.show_completed_tasks}`);
    lines.push(`mute_notifications: ${collection.mute_notifications}`);
    lines.push(`exclude_from_todo_list: ${collection.exclude_from_todo_list}`);
    lines.push(`is_template: ${collection.is_template}`);
    lines.push(`archived: ${collection.archived}`);
    lines.push('---');
    lines.push('');

    // Collection title
    lines.push(`# ${collection.icon} ${collection.title}`);
    lines.push('');

    // Snipsels
    if (items.length === 0) {
      lines.push('*No items in this collection*');
    } else {
      for (const item of items) {
        lines.push(snipselToMarkdown(item));
      }
    }

    lines.push('');
    lines.push('---');
    lines.push('');
    lines.push(`*Exported from Snipsel on ${new Date().toLocaleString('de-DE')}*`);

    return lines.join('\n');
  }

  async function copyToClipboard() {
    const markdown = generateMarkdown();
    try {
      await navigator.clipboard.writeText(markdown);
      copied = true;
      setTimeout(() => {
        copied = false;
      }, 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  }

  function downloadMarkdown() {
    const markdown = generateMarkdown();
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${collection.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  async function loadItems() {
    try {
      const res = await api.snipsels.list(collection.id);
      items = res.items.sort((a, b) => a.position - b.position);
    } catch (err) {
      console.error('Failed to load items:', err);
    } finally {
      loading = false;
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      onClose();
    }
  }

  loadItems();
</script>

<div
  class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
  onclick={onClose}
  onkeydown={handleKeydown}
  role="dialog"
  aria-modal="true"
  tabindex="-1"
>
  <div
    class="flex h-[80vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-white/10 dark:bg-slate-900"
    onclick={(e) => e.stopPropagation()}
    role="document"
  >
    <!-- Header -->
    <div class="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-white/10">
      <div>
        <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
          Export Collection
        </h3>
        <p class="text-sm text-slate-500 dark:text-slate-400">
          {collection.icon} {collection.title}
        </p>
      </div>
      <button
        class="al-icon-wrapper grid h-9 w-9 place-items-center rounded-full text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-300"
        type="button"
        onclick={onClose}
        aria-label="Close"
        title="Close"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
      </button>
    </div>

    <!-- Content -->
    <div class="flex flex-1 flex-col overflow-hidden">
      {#if loading}
        <div class="flex flex-1 items-center justify-center p-8">
          <div class="animate-pulse text-slate-500 dark:text-slate-400">Loading...</div>
        </div>
      {:else}
        <!-- Preview -->
        <div class="flex-1 overflow-auto p-6">
          <div class="mb-2 text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Preview
          </div>
          <pre class="whitespace-pre-wrap rounded-lg border border-slate-200 bg-slate-50 p-4 font-mono text-sm text-slate-700 dark:border-white/10 dark:bg-slate-800 dark:text-slate-300" style="max-height: calc(80vh - 220px); overflow: auto;">{generateMarkdown()}</pre>
        </div>

        <!-- Actions -->
        <div class="flex items-center justify-between border-t border-slate-200 px-6 py-4 dark:border-white/10">
          <button
            class="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition-colors hover:bg-slate-50 dark:border-white/10 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
            type="button"
            onclick={onClose}
          >
            Close
          </button>
          <div class="flex gap-3">
            <button
              class="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition-colors hover:bg-slate-50 dark:border-white/10 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
              type="button"
              onclick={downloadMarkdown}
            >
              <FileDown size={16} />
              Download
            </button>
            <button
              class="flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:opacity-90 disabled:opacity-50"
              type="button"
              style="background-color: {getAccent()}"
              onclick={copyToClipboard}
            >
              {#if copied}
                <Check size={16} />
                <span>Copied!</span>
              {:else}
                <Copy size={16} />
                <span>Copy to Clipboard</span>
              {/if}
            </button>
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>
