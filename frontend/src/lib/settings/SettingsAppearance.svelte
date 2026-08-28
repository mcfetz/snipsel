<script lang="ts">
  import Check from '@animated-color-icons/lucide-svelte/Check.svelte';
  import { api } from '../api';
  import { currentUser } from '../session';
  import { getContrastColor } from '../colors';

  interface Props {
    accent: string;
    isBusy: boolean;
  }

  let { accent, isBusy }: Props = $props();

  let defaultHeaderColor = $state($currentUser?.default_collection_header_color ?? '#4f46e5');
  let lightBackgroundColor = $state($currentUser?.light_background_color ?? '');
  let darkBackgroundColor = $state($currentUser?.dark_background_color ?? '');
  let showAppearanceSaved = $state(false);
  let saving = $state(false);

  async function saveAppearanceSettings() {
    saving = true;
    try {
      const res = await api.updateMe({
        default_collection_header_color: defaultHeaderColor || null,
        light_background_color: lightBackgroundColor || null,
        dark_background_color: darkBackgroundColor || null,
      });
      currentUser.set(res.user);
      showAppearanceSaved = true;
      setTimeout(() => {
        showAppearanceSaved = false;
      }, 2000);
    } catch (err) {
      console.error('Failed to save appearance settings:', err);
    } finally {
      saving = false;
    }
  }

  async function updateTheme(t: 'system' | 'light' | 'dark') {
    try {
      const res = await api.updateMe({ theme: t });
      currentUser.set(res.user);
    } catch (err) {
      console.error('Failed to update theme:', err);
    }
  }
</script>

<div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/60">
  <div class="text-xs uppercase text-slate-500">Appearance</div>

  <div class="mt-4">
    <span class="block text-sm font-medium text-slate-700 dark:text-slate-300">Color Theme</span>
    <div class="mt-2 grid grid-cols-3 gap-2">
      {#each ['system', 'light', 'dark'] as const as t}
        <button
          class="rounded-lg border px-3 py-2 text-sm font-medium transition-all {$currentUser?.theme === t ? 'border-slate-900 bg-slate-900 text-white dark:border-white dark:bg-white dark:text-slate-900' : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700'}"
          type="button"
          onclick={() => updateTheme(t)}
          disabled={isBusy || saving}
        >
          {t.charAt(0).toUpperCase() + t.slice(1)}
        </button>
      {/each}
    </div>
  </div>

  <div class="mt-6">
    <label for="accent-color-picker" class="block text-sm font-medium text-slate-700 dark:text-slate-300">
      Default collection header color
    </label>
    <div class="mt-2 flex items-center gap-2">
      <div class="flex flex-1 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-sm ring-1 ring-black/5 dark:border-slate-700 dark:bg-slate-800">
        <label class="relative block h-8 w-8 cursor-pointer">
          <input
            id="accent-color-picker"
            class="h-full w-full cursor-pointer rounded border-0 p-0"
            type="color"
            value={defaultHeaderColor}
            oninput={(e) => defaultHeaderColor = (e.target as HTMLInputElement).value}
          />
        </label>
        <input
          class="min-w-0 flex-1 border-none bg-transparent font-mono text-sm text-slate-700 focus:outline-none focus:ring-0 dark:text-slate-300"
          value={defaultHeaderColor}
          oninput={(e) => {
            let v = (e.target as HTMLInputElement).value;
            if (v && !v.startsWith('#')) v = '#' + v;
            if (/^#[0-9a-fA-F]{6}$/.test(v)) defaultHeaderColor = v;
          }}
        />
      </div>
    </div>
  </div>

  <div class="mt-6">
    <span class="block text-sm font-medium text-slate-700 dark:text-slate-300">Background colors</span>
    <div class="mt-3 grid grid-cols-2 gap-4">
      <div>
        <label for="light-bg-color-picker" class="mb-1 block text-xs text-slate-500 dark:text-slate-400">Light mode</label>
        <div class="flex items-center gap-2">
          <div class="flex max-w-[160px] flex-1 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-sm ring-1 ring-black/5 md:max-w-none dark:border-slate-700 dark:bg-slate-800">
            <label class="relative block h-8 w-8 cursor-pointer">
              <input
                id="light-bg-color-picker"
                class="h-full w-full cursor-pointer rounded border-0 p-0"
                type="color"
                value={lightBackgroundColor || '#ffffff'}
                oninput={(e) => lightBackgroundColor = (e.target as HTMLInputElement).value}
              />
            </label>
            <input
              class="min-w-0 flex-1 border-none bg-transparent font-mono text-sm text-slate-700 focus:outline-none focus:ring-0 dark:text-slate-300"
              value={lightBackgroundColor || ''}
              placeholder="#ffffff"
              oninput={(e) => {
                let v = (e.target as HTMLInputElement).value;
                if (v && !v.startsWith('#')) v = '#' + v;
                if (/^#[0-9a-fA-F]{6}$/.test(v)) lightBackgroundColor = v;
              }}
            />
          </div>
        </div>
      </div>
      <div>
        <label for="dark-bg-color-picker" class="mb-1 block text-xs text-slate-500 dark:text-slate-400">Dark mode</label>
        <div class="flex items-center gap-2">
          <div class="flex max-w-[160px] flex-1 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-sm ring-1 ring-black/5 md:max-w-none dark:border-slate-700 dark:bg-slate-800">
            <label class="relative block h-8 w-8 cursor-pointer">
              <input
                id="dark-bg-color-picker"
                class="h-full w-full cursor-pointer rounded border-0 p-0"
                type="color"
                value={darkBackgroundColor || '#0f172a'}
                oninput={(e) => darkBackgroundColor = (e.target as HTMLInputElement).value}
              />
            </label>
            <input
              class="min-w-0 flex-1 border-none bg-transparent font-mono text-sm text-slate-700 focus:outline-none focus:ring-0 dark:text-slate-300"
              value={darkBackgroundColor || ''}
              placeholder="#0f172a"
              oninput={(e) => {
                let v = (e.target as HTMLInputElement).value;
                if (v && !v.startsWith('#')) v = '#' + v;
                if (/^#[0-9a-fA-F]{6}$/.test(v)) darkBackgroundColor = v;
              }}
            />
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="mt-6 flex justify-end">
    <button
      class="relative flex items-center justify-center gap-2 rounded-full px-6 py-2.5 text-sm font-bold shadow-xl transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-70"
      style={`background-color: ${accent}; color: ${getContrastColor(accent)}`}
      type="button"
      onclick={saveAppearanceSettings}
      disabled={isBusy || saving || showAppearanceSaved}
    >
      {#if saving}
        <div class="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></div>
        <span>Saving...</span>
      {:else if showAppearanceSaved}
        <div class="flex items-center gap-2">
          <Check label="" size={18} strokeWidth={3} />
          <span>Saved!</span>
        </div>
      {:else}
        <span>Save Appearance</span>
      {/if}
    </button>
  </div>
</div>
