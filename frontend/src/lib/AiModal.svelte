<script lang="ts">
  import Sparkles from '@animated-color-icons/lucide-svelte/Sparkles.svelte';
  import X from '@animated-color-icons/lucide-svelte/X.svelte';
  import Copy from '@animated-color-icons/lucide-svelte/Copy.svelte';
  import { api } from './api';
  import { currentUser } from './session';

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

  async function generate() {
    if (!prompt.trim()) return;
    isGenerating = true;
    error = '';
    try {
      const res = await api.ai.generate({ prompt, context, attachment_ids: attachmentIds });
      response = res.text;
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
  
  <div class="relative w-full max-w-lg overflow-hidden rounded-2xl border border-white/20 bg-white/90 shadow-2xl ring-1 ring-black/5 backdrop-blur-md transition-all dark:border-white/10 dark:bg-slate-900/90">
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
        <div>
          <label for="ai-prompt" class="block text-sm font-medium text-slate-700 dark:text-slate-300">What should AI do with this snipsel?</label>
          <textarea
            id="ai-prompt"
            class="mt-2 block w-full min-h-[100px] rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 dark:border-white/10 dark:bg-slate-800 dark:text-white"
            placeholder="e.g. Summarize this, Fix grammar, Translate to German..."
            bind:value={prompt}
            disabled={isGenerating}
            onkeydown={(e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) generate(); }}
          ></textarea>
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
            class="flex-1 rounded-full px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 transition-all hover:scale-[1.02] active:scale-95 disabled:opacity-50"
            style={`background-color: ${getAccent()}`}
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
            class="flex-1 rounded-full px-4 py-2.5 text-sm font-semibold text-white shadow-lg transition-all hover:scale-[1.02] active:scale-95"
            style={`background-color: ${getAccent()}`}
            onclick={() => onInsert(response)}
          >
            Insert
          </button>
          <button
            class="flex-1 rounded-full border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-white/10 dark:bg-slate-800 dark:text-slate-200"
            onclick={() => onReplace(response)}
          >
            Replace
          </button>
          <button
            class="al-icon-wrapper grid h-10 w-10 place-items-center rounded-full border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-white/10 dark:bg-slate-800 dark:text-slate-300"
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
