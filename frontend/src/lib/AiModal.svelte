<script lang="ts">
  import { fly, fade } from 'svelte/transition';
  import Sparkles from '@animated-color-icons/lucide-svelte/Sparkles.svelte';
  import X from '@animated-color-icons/lucide-svelte/X.svelte';
  import Copy from '@animated-color-icons/lucide-svelte/Copy.svelte';
  import { api } from './api';
  import { currentUser } from './session';
  import History from '@animated-color-icons/lucide-svelte/History.svelte';
  import Heart from '@animated-color-icons/lucide-svelte/Heart.svelte';
  import Clock from '@animated-color-icons/lucide-svelte/Clock.svelte';

  interface HistoryItem {
    id: string;
    text: string;
    starred: boolean;
    last_used_at: string;
  }

  interface Props {
    context: string;
    attachmentIds?: string[];
    onClose: () => void;
    onInsert: (text: string) => void;
    onReplace: (text: string) => void;
  }

  let { context, attachmentIds = [], onClose, onInsert, onReplace }: Props = $props();

  let prompt = $state('');
  let response = $state('');
  let isGenerating = $state(false);
  let error = $state('');
  let showHistory = $state(false);
  let isHistoryLoading = $state(false);

  let historyItems = $state<HistoryItem[]>([]);

  async function fetchHistory() {
    isHistoryLoading = true;
    try {
      const res = await api.ai.getHistory();
      historyItems = res.history;
    } catch (e) {
      console.error('Failed to fetch AI history', e);
    } finally {
      isHistoryLoading = false;
    }
  }

  $effect(() => {
    fetchHistory();
  });

  async function toggleStar(item: HistoryItem, e: MouseEvent) {
    e.stopPropagation();
    const original = item.starred;
    // Optimistic update
    item.starred = !original;
    try {
      const res = await api.ai.toggleStarPrompt({ id: item.id });
      item.starred = res.starred;
    } catch (e) {
      item.starred = original;
      console.error('Failed to toggle star', e);
    }
  }

  async function deleteHistoryItem(item: HistoryItem, e: MouseEvent) {
    e.stopPropagation();
    if (!confirm('Remove this prompt from history?')) return;
    
    const originalItems = [...historyItems];
    historyItems = historyItems.filter(i => i.id !== item.id);
    try {
      await api.ai.deleteHistoryItem(item.id);
    } catch (e) {
      historyItems = originalItems;
      console.error('Failed to delete history item', e);
    }
  }

  function selectHistoryItem(item: HistoryItem) {
    prompt = item.text;
    showHistory = false;
  }

  async function generate() {
    if (!prompt.trim()) return;
    isGenerating = true;
    error = '';
    try {
      const res = await api.ai.generate({ prompt, context, attachment_ids: attachmentIds });
      response = res.text;
      fetchHistory(); // Refresh history to include the new/updated entry
    } catch (e: any) {
      error = e.error?.message || 'AI request failed. Please check your settings.';
    } finally {
      isGenerating = false;
    }
  }

  function copyToClipboard() {
    navigator.clipboard.writeText(response);
  }

  function getAccent(): string {
    return ($currentUser?.default_collection_header_color || '#4f46e5');
  }

  function isLightColor(color: string): boolean {
    const hex = color.replace('#', '');
    if (hex.length !== 6) return false;
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
    return brightness > 128;
  }

  function getContrastColor(bgColor: string): string {
    return isLightColor(bgColor) ? '#1e293b' : 'white';
  }
</script>

<div class="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6">
  <div 
    class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" 
    onclick={onClose}
    onkeydown={(e) => e.key === 'Escape' && onClose()}
    role="button"
    tabindex="-1"
    aria-label="Close modal"
  ></div>
  
  <div class="relative w-full max-w-lg overflow-hidden rounded-2xl border border-white/20 bg-white/90 shadow-2xl ring-1 ring-black/5 backdrop-blur-md transition-all dark:border-white/10 dark:bg-slate-900/90" in:fly={{ y: 20, duration: 200 }} out:fade={{ duration: 150 }}>
    <div class="flex items-center justify-between border-b border-slate-100 px-6 py-4 dark:border-white/5">
      <h3 class="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
        <Sparkles label="" size={20} />
        AI Assistant
      </h3>
      <button 
        class="al-icon-wrapper rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-white/5" 
        onclick={onClose}
        aria-label="Close"
      >
        <X label="" size={20} strokeWidth={2} />
      </button>
    </div>

    <div class="p-6 space-y-4">
      {#if !response}
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <label for="ai-prompt" class="block text-sm font-medium text-slate-700 dark:text-slate-300">What should AI do with this snipsel?</label>
            <button 
              class="flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full transition-all"
              style={`background-color: ${getAccent()}15; color: ${getAccent()}; border: 1px solid ${getAccent()}30`}
              onclick={() => showHistory = !showHistory}
            >
              <History label="" size={14} />
              {showHistory ? 'Hide History' : 'History'}
            </button>
          </div>

          {#if showHistory}
            <div class="space-y-2 max-h-[200px] overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-slate-200 dark:scrollbar-thumb-white/10" in:fly={{ y: -10, duration: 200 }}>
              {#if historyItems.length === 0}
                <div class="py-4 text-center text-xs text-slate-400 dark:text-slate-500 italic">No history yet</div>
              {:else}
                <div class="grid gap-2">
                  {#each historyItems as item}
                    <div 
                      class="flex items-center gap-3 w-full text-left p-2.5 rounded-xl border border-slate-100 bg-white/50 hover:bg-slate-50 hover:border-slate-200 transition-all dark:border-white/5 dark:bg-white/5 dark:hover:bg-white/10 dark:hover:border-white/10 group cursor-pointer"
                      onclick={() => selectHistoryItem(item)}
                      onkeydown={(e) => e.key === 'Enter' && selectHistoryItem(item)}
                      role="button"
                      tabindex="0"
                    >
                      <div class="flex-1 min-w-0">
                        <div class="text-sm text-slate-700 dark:text-white font-medium break-words">{item.text}</div>
                        <div class="flex items-center gap-1.5 mt-0.5">
                          <Clock label="" size={10} className="text-slate-400" />
                          <span class="text-[10px] text-slate-400">{new Date(item.last_used_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      <div class="flex items-center gap-1">
                        <button 
                          class="al-icon-wrapper p-1.5 rounded-lg hover:bg-white dark:hover:bg-slate-800 transition-colors opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-500"
                          onclick={(e) => deleteHistoryItem(item, e)}
                          title="Remove from history"
                        >
                          <X label="" size={14} />
                        </button>
                        <button 
                          class="al-icon-wrapper p-1.5 rounded-lg hover:bg-white dark:hover:bg-slate-800 transition-colors {item.starred ? '' : 'text-slate-300 dark:text-slate-600 opacity-0 group-hover:opacity-100'}"
                          style={item.starred ? `color: ${getAccent()}` : ''}
                          onclick={(e) => toggleStar(item, e)}
                          title={item.starred ? 'Unfavorite prompt' : 'Favorite as template'}
                        >
                          <Heart label="" size={16} fill={item.starred ? 'currentColor' : 'none'} className={item.starred ? 'fill-current' : ''} />
                        </button>
                      </div>
                    </div>
                  {/each}
                </div>
              {/if}
            </div>
          {/if}
          
          <div class="relative">
            <textarea
              id="ai-prompt"
              class="mt-2 block w-full min-h-[100px] rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 dark:border-white/10 dark:bg-slate-800 dark:text-white"
              placeholder="e.g. Summarize this, Fix grammar, Translate to German..."
              bind:value={prompt}
              disabled={isGenerating}
              onkeydown={(e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) generate(); }}
            ></textarea>
          </div>
        </div>
      {:else}
        <div class="space-y-4">
          <div class="text-sm font-medium text-slate-700 dark:text-slate-300">AI Response:</div>
          <div class="max-h-[300px] overflow-y-auto rounded-xl border border-slate-100 bg-slate-50/50 p-4 text-sm whitespace-pre-wrap dark:border-white/5 dark:bg-white/5 dark:text-slate-200">
            {response}
          </div>
        </div>
      {/if}

      {#if error}
        <div class="rounded-lg bg-red-50 p-3 text-xs font-medium text-red-600 dark:bg-red-950/20 dark:text-red-400">
          {error}
        </div>
      {/if}

      <div class="flex items-center gap-2 pt-2">
        {#if !response}
          <button
            class="flex-1 rounded-full px-6 py-2.5 text-sm font-semibold shadow-lg shadow-indigo-500/20 transition-all hover:scale-[1.02] active:scale-95 disabled:opacity-50"
            style={`background-color: ${getAccent()}; color: ${getContrastColor(getAccent())}`}
            onclick={generate}
            disabled={isGenerating || !prompt.trim()}
          >
            {isGenerating ? 'Generating...' : 'Generate Response'}
          </button>
        {:else}
          <button
            class="flex-1 rounded-full border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-white/10 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            onclick={() => { response = ''; prompt = ''; }}
          >
            New Prompt
          </button>
          <button
            class="flex-1 rounded-full px-4 py-2.5 text-sm font-semibold shadow-lg transition-all hover:scale-[1.02] active:scale-95"
            style={`background-color: ${getAccent()}; color: ${getContrastColor(getAccent())}`}
            onclick={() => onInsert(response)}
          >
            Insert
          </button>
          <button
            class="flex-1 rounded-full border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-white/10 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            onclick={() => onReplace(response)}
          >
            Replace
          </button>
          <button
            class="al-icon-wrapper grid h-10 w-10 place-items-center rounded-full border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-white/10 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
            title="Copy to clipboard"
            onclick={copyToClipboard}
          >
            <Copy label="" size={20} strokeWidth={2} />
          </button>
        {/if}
      </div>
    </div>
  </div>
</div>
