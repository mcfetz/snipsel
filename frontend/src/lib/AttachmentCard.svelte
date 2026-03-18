<script lang="ts">
  import FileTextIcon from '@animated-color-icons/lucide-svelte/FileText.svelte';
  import FileCodeIcon from '@animated-color-icons/lucide-svelte/FileCode.svelte';
  import FileSpreadsheet from '@animated-color-icons/lucide-svelte/FileSpreadsheet.svelte';
  import FileArchiveIcon from '@animated-color-icons/lucide-svelte/FileArchive.svelte';
  import FileMusicIcon from '@animated-color-icons/lucide-svelte/FileMusic.svelte';
  import FileVideoIcon from '@animated-color-icons/lucide-svelte/FileVideo2.svelte';
  import FileIcon from '@animated-color-icons/lucide-svelte/File.svelte';
  import Download from '@animated-color-icons/lucide-svelte/Download.svelte';
  import type { Attachment } from './api';

  interface Props {
    attachment: Attachment;
    downloadUrl: string;
    thumbnailUrl?: string;
  }

  let { attachment, downloadUrl, thumbnailUrl }: Props = $props();

  function formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  }

  const mime = $derived(attachment.mime_type || '');
  const ext = $derived(attachment.filename.split('.').pop()?.toLowerCase() || '');

  const category = $derived.by(() => {
    if (mime === 'application/pdf') return 'pdf';
    if (mime.startsWith('text/') || mime === 'application/json') return 'code';
    if (['csv', 'xlsx', 'xls', 'ods'].includes(ext) || mime.includes('spreadsheet') || mime === 'text/csv') return 'spreadsheet';
    if (['zip', 'rar', 'tar', 'gz', '7z', 'bz2', 'xz'].includes(ext) || mime.includes('archive') || mime.includes('zip') || mime.includes('compressed')) return 'archive';
    if (mime.startsWith('audio/')) return 'audio';
    if (mime.startsWith('video/')) return 'video';
    return 'file';
  });

  const categoryLabel = $derived.by(() => {
    switch (category) {
      case 'pdf': return 'PDF';
      case 'code': return 'Document';
      case 'spreadsheet': return 'Spreadsheet';
      case 'archive': return 'Archive';
      case 'audio': return 'Audio';
      case 'video': return 'Video';
      default: return ext.toUpperCase() || 'File';
    }
  });
</script>

<div class="al-icon-wrapper group relative overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all hover:shadow-md dark:border-white/10 dark:bg-slate-900">
  <div class="absolute inset-0 z-0 bg-gradient-to-br from-slate-500/5 to-blue-500/5 opacity-0 transition-opacity group-hover:opacity-100"></div>

  <div class="relative z-10 flex items-center gap-4 p-4">
    {#if thumbnailUrl}
      <div class="relative h-14 w-14 flex-shrink-0 overflow-hidden rounded-xl bg-slate-100 shadow-sm dark:bg-white/5">
        <img src={thumbnailUrl} alt={attachment.filename} class="h-full w-full object-cover" />
      </div>
    {:else}
      <div class="flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-xl bg-slate-100 dark:bg-white/5">
        {#if category === 'pdf'}
          <FileTextIcon label="" size={24} />
        {:else if category === 'code'}
          <FileCodeIcon label="" size={24} />
        {:else if category === 'spreadsheet'}
          <FileSpreadsheet label="" size={24} />
        {:else if category === 'archive'}
          <FileArchiveIcon label="" size={24} />
        {:else if category === 'audio'}
          <FileMusicIcon label="" size={24} />
        {:else if category === 'video'}
          <FileVideoIcon label="" size={24} />
        {:else}
          <FileIcon label="" size={24} />
        {/if}
      </div>
    {/if}

    <div class="min-w-0 flex-1">
      <h4 class="truncate text-base font-semibold text-slate-900 dark:text-slate-100">
        {attachment.filename}
      </h4>
      <p class="text-sm text-slate-500 dark:text-slate-400">
        {formatSize(attachment.size_bytes)}
      </p>
      <div class="mt-1 flex items-center gap-1.5">
        <FileIcon label="" size={12} className="text-slate-400" />
        <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">{categoryLabel}</span>
      </div>
    </div>

    <a
      href={downloadUrl}
      target="_blank"
      rel="noreferrer"
      class="grid h-10 w-10 place-items-center rounded-full bg-slate-50 text-slate-400 transition-all hover:bg-slate-100 hover:text-blue-600 active:scale-90 dark:bg-white/5 dark:hover:bg-white/10 dark:hover:text-blue-400"
      onclick={(e) => e.stopPropagation()}
      aria-label="Download {attachment.filename}"
    >
      <Download label="" size={20} strokeWidth={2} />
    </a>
  </div>
</div>
