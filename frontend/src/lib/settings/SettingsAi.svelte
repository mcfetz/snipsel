<script lang="ts">
  import Check from '@animated-color-icons/lucide-svelte/Check.svelte';
  import Dices from '@animated-color-icons/lucide-svelte/Dices.svelte';
  import { api } from '../api';
  import { currentUser } from '../session';
  import { getContrastColor } from '../colors';

  interface Props {
    accent: string;
    isBusy: boolean;
  }

  let { accent, isBusy }: Props = $props();

  let dicedMomentsTags = $state($currentUser?.diced_moments_tags ?? '');
  let showDicedMomentsSaved = $state(false);
  let savingDiced = $state(false);

  let tagSuggestions = $state<string[]>([]);
  let showTagSuggestions = $state(false);
  let tagSearchQuery = $state('');

  let aiLlmUrl = $state($currentUser?.ai_llm_url ?? '');
  let aiModelName = $state($currentUser?.ai_model_name ?? '');
  let aiApiKey = $state('');
  let showAiSaved = $state(false);
  let savingAi = $state(false);

  let availableModels = $state<Array<{ id: string; name: string }>>([]);
  let isLoadingModels = $state(false);
  let modelsError = $state('');

  function handleTagInput(e: Event) {
    const target = e.target as HTMLInputElement;
    const val = target.value;
    const parts = val.split(',');
    const currentPart = parts[parts.length - 1].trim();

    if (currentPart.length > 0) {
      tagSearchQuery = currentPart;
      api.tags
        .list(1, 100)
        .then((res) => {
          tagSuggestions = res.tags
            .map((t) => t.tag)
            .filter((t) => t.toLowerCase().includes(tagSearchQuery.toLowerCase()) && !dicedMomentsTags.toLowerCase().includes(t.toLowerCase()));
          showTagSuggestions = tagSuggestions.length > 0;
        })
        .catch(() => {
          showTagSuggestions = false;
        });
    } else {
      showTagSuggestions = false;
    }
  }

  function handleTagKeyDown(e: KeyboardEvent) {
    if (showTagSuggestions && tagSuggestions.length > 0) {
      if (e.key === 'Tab' || e.key === 'Enter') {
        e.preventDefault();
        selectTag(tagSuggestions[0]);
      } else if (e.key === 'Escape') {
        showTagSuggestions = false;
      }
    }
  }

  function selectTag(tag: string) {
    let parts = dicedMomentsTags.split(',').map((p) => p.trim()).filter((p) => !!p);
    if (parts.length > 0 && !dicedMomentsTags.endsWith(',')) {
      parts[parts.length - 1] = tag;
    } else {
      parts.push(tag);
    }
    dicedMomentsTags = parts.join(', ') + ', ';
    showTagSuggestions = false;
  }

  async function saveDicedMomentsSettings() {
    savingDiced = true;
    try {
      const res = await api.updateMe({
        diced_moments_tags: dicedMomentsTags.trim() || null,
      });
      currentUser.set(res.user);
      showDicedMomentsSaved = true;
      setTimeout(() => {
        showDicedMomentsSaved = false;
      }, 2000);
    } catch (err) {
      console.error('Failed to save diced moments tags:', err);
    } finally {
      savingDiced = false;
    }
  }

  async function fetchModels() {
    isLoadingModels = true;
    modelsError = '';
    try {
      const res = await api.ai.getModels();
      availableModels = res.models;
    } catch (err: any) {
      modelsError = err?.message || 'Failed to fetch models';
    } finally {
      isLoadingModels = false;
    }
  }

  async function saveAiSettings() {
    if (!aiApiKey.trim() && !$currentUser?.ai_api_key_set) {
      alert('Please enter an API key');
      return;
    }
    savingAi = true;
    try {
      const payload: any = {
        ai_llm_url: aiLlmUrl.trim() || null,
        ai_model_name: aiModelName.trim() || null,
      };
      if (aiApiKey.trim()) {
        payload.ai_api_key = aiApiKey.trim();
      }
      const res = await api.updateMe(payload);
      currentUser.set(res.user);
      aiApiKey = '';
      showAiSaved = true;
      setTimeout(() => {
        showAiSaved = false;
      }, 2000);
    } catch (err) {
      console.error('Failed to save AI settings:', err);
    } finally {
      savingAi = false;
    }
  }
</script>

<div class="space-y-3">
  <!-- Diced Moments -->
  <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
    <div class="flex items-center gap-2 text-xs uppercase text-slate-500">
      <Dices label="" size={12} strokeWidth={2.5} />
      <span>Diced Moments</span>
    </div>
    <div class="mt-3 space-y-4">
      <div>
        <label for="diced-tags" class="block text-sm font-medium text-slate-700 dark:text-slate-300">
          Tags (comma separated)
        </label>
        <div class="mb-2 text-xs text-slate-500 dark:text-slate-400">
          Snipsels with these tags will be randomly picked for your daily collection.
        </div>
        <div class="relative">
          <input
            id="diced-tags"
            type="text"
            class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:ring-white/10"
            bind:value={dicedMomentsTags}
            oninput={handleTagInput}
            onkeydown={handleTagKeyDown}
            onblur={() => setTimeout(() => showTagSuggestions = false, 200)}
            placeholder="quote, thought, memory"
            autocomplete="off"
          />
          {#if showTagSuggestions && tagSuggestions.length > 0}
            <div class="absolute z-50 mt-1 max-h-40 w-full overflow-auto rounded-lg border border-slate-200 bg-white shadow-xl dark:border-white/10 dark:bg-slate-800">
              {#each tagSuggestions as tag}
                <button
                  type="button"
                  class="block w-full px-4 py-2 text-left text-sm hover:bg-slate-100 dark:hover:bg-white/5"
                  onclick={() => selectTag(tag)}
                >
                  {tag}
                </button>
              {/each}
            </div>
          {/if}
        </div>
      </div>
      <div class="flex justify-end">
        <button
          class="relative flex items-center justify-center gap-2 rounded-full px-6 py-2.5 text-sm font-bold shadow-xl transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-70"
          style={`background-color: ${accent}; color: ${getContrastColor(accent)}`}
          type="button"
          onclick={saveDicedMomentsSettings}
          disabled={isBusy || savingDiced || showDicedMomentsSaved}
        >
          {#if savingDiced}
            <div class="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></div>
            <span>Saving...</span>
          {:else if showDicedMomentsSaved}
            <div class="flex items-center gap-2">
              <Check label="" size={18} strokeWidth={3} />
              <span>Saved!</span>
            </div>
          {:else}
            <span>Save</span>
          {/if}
        </button>
      </div>
    </div>
  </div>

  <!-- AI Integration -->
  <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
    <div class="text-xs uppercase text-slate-500">AI Integration</div>
    <div class="mt-3 space-y-4">
      <div>
        <label for="ai-url" class="block text-sm font-medium text-slate-700 dark:text-slate-300">
          LLM API URL (OpenAI compatible)
        </label>
        <input
          id="ai-url"
          type="text"
          class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none dark:border-white/10 dark:bg-slate-800"
          bind:value={aiLlmUrl}
          placeholder="https://api.openai.com/v1/chat/completions"
        />
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <div class="flex items-center justify-between">
            <label for="ai-model" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Model Name</label>
            <button
              type="button"
              onclick={fetchModels}
              disabled={isLoadingModels}
              class="text-xs text-slate-500 hover:text-slate-700 disabled:opacity-50 dark:text-slate-400 dark:hover:text-slate-200"
            >
              {isLoadingModels ? 'Loading...' : 'Refresh'}
            </button>
          </div>
          {#if availableModels.length > 0}
            <select
              id="ai-model"
              class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none dark:border-white/10 dark:bg-slate-800"
              bind:value={aiModelName}
            >
              <option value="">Select a model...</option>
              {#each availableModels as model}
                <option value={model.id}>{model.name}</option>
              {/each}
            </select>
          {:else}
            <input
              id="ai-model"
              type="text"
              class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none dark:border-white/10 dark:bg-slate-800"
              bind:value={aiModelName}
              placeholder="gpt-3.5-turbo"
            />
          {/if}
          {#if modelsError}
            <div class="mt-1 text-xs text-red-500">{modelsError}</div>
          {/if}
        </div>
        <div>
          <label for="ai-key" class="block text-sm font-medium text-slate-700 dark:text-slate-300">
            API Key {($currentUser?.ai_api_key_set) ? '(Set)' : ''}
          </label>
          <input
            id="ai-key"
            type="password"
            class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none dark:border-white/10 dark:bg-slate-800"
            bind:value={aiApiKey}
            placeholder="sk-..."
          />
        </div>
      </div>
      <div class="flex justify-end pt-2">
        <button
          class="relative flex items-center justify-center gap-2 rounded-full px-6 py-2.5 text-sm font-bold shadow-xl transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-70"
          style={`background-color: ${accent}; color: ${getContrastColor(accent)}`}
          type="button"
          onclick={saveAiSettings}
          disabled={isBusy || savingAi || showAiSaved}
        >
          {#if savingAi}
            <div class="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></div>
            <span>Saving...</span>
          {:else if showAiSaved}
            <div class="flex items-center gap-2">
              <Check label="" size={18} strokeWidth={3} />
              <span>Saved!</span>
            </div>
          {:else}
            <span>Save AI Settings</span>
          {/if}
        </button>
      </div>
    </div>
  </div>
</div>
