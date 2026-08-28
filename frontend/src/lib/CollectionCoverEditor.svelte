<script lang="ts">
  import UnsplashSearchModal from './UnsplashSearchModal.svelte';

  interface Props {
    headerImageUrl: string;
    headerImagePosition: string;
    headerImageXPosition: string;
    headerImageZoom: number;
    headerColor: string;
    accent: string;
    saving: boolean;
    initialQuery?: string;
    onFileSelected: (e: Event) => void;
    onSelectUnsplash?: (url: string) => void;
  }

  let {
    headerImageUrl = $bindable(''),
    headerImagePosition = $bindable('50%'),
    headerImageXPosition = $bindable('50%'),
    headerImageZoom = $bindable(1.0),
    headerColor = $bindable(''),
    accent,
    saving,
    initialQuery = '',
    onFileSelected,
    onSelectUnsplash,
  }: Props = $props();

  let showUnsplashModal = $state(false);
</script>

<div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
  <div class="text-xs font-medium uppercase text-slate-500">Appearance</div>
  <div class="mt-4 space-y-4">
    <div class="block">
      <span class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">Header image</span>
      <div class="space-y-3">
        <div class="flex items-center gap-3">
          <input
            class="flex-1 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-slate-100 dark:ring-white/10"
            bind:value={headerImageUrl}
            placeholder="https://..."
          />
          <label
            class="cursor-pointer rounded-full border border-slate-200 bg-white px-6 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
            style={`color: ${accent}`}
          >
            Upload
            <input type="file" accept="image/*" class="hidden" onchange={onFileSelected} disabled={saving} />
          </label>
          <button
            class="rounded-full border border-slate-200 bg-white px-6 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
            style={`color: ${accent}`}
            type="button"
            onclick={() => (showUnsplashModal = true)}
            disabled={saving}
          >
            Unsplash
          </button>
        </div>

        {#if headerImageUrl}
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-medium text-slate-500">Vertical position</span>
              <span class="font-mono text-xs text-slate-400">{headerImagePosition}</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              step="1"
              class="h-1.5 w-full cursor-pointer appearance-none rounded-lg bg-slate-200 dark:bg-slate-700"
              value={parseInt(headerImagePosition) || 50}
              oninput={(e) => (headerImagePosition = `${e.currentTarget.value}%`)}
              style={`--accent: ${accent}`}
            />

            <div class="flex items-center justify-between">
              <span class="text-xs font-medium text-slate-500">Horizontal position</span>
              <span class="font-mono text-xs text-slate-400">{headerImageXPosition}</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              step="1"
              class="h-1.5 w-full cursor-pointer appearance-none rounded-lg bg-slate-200 dark:bg-slate-700"
              value={parseInt(headerImageXPosition) || 50}
              oninput={(e) => (headerImageXPosition = `${e.currentTarget.value}%`)}
              style={`--accent: ${accent}`}
            />

            <div class="flex items-center justify-between">
              <span class="text-xs font-medium text-slate-500">Zoom</span>
              <span class="font-mono text-xs text-slate-400">{headerImageZoom.toFixed(2)}x</span>
            </div>
            <input
              type="range"
              min="1"
              max="3"
              step="0.05"
              class="h-1.5 w-full cursor-pointer appearance-none rounded-lg bg-slate-200 dark:bg-slate-700"
              value={headerImageZoom}
              oninput={(e) => (headerImageZoom = parseFloat(e.currentTarget.value))}
              style={`--accent: ${accent}`}
            />

            <!-- Preview -->
            <div class="relative h-28 w-full overflow-hidden rounded-lg border border-slate-200 bg-slate-100 dark:border-white/10 dark:bg-slate-800">
              <div
                class="absolute inset-0 bg-cover"
                style="background-image: url('{headerImageUrl}{ headerImageUrl.startsWith('/api/attachments/') ? '/thumbnail' : '' }'); background-position: {headerImageXPosition} {headerImagePosition}; transform: scale({headerImageZoom}) translate({(50 - (parseFloat(headerImageXPosition) || 50)) * (1 - 1 / headerImageZoom)}%, {(50 - (parseFloat(headerImagePosition) || 50)) * (1 - 1 / headerImageZoom)}%)"
              ></div>
            </div>
          </div>
        {/if}
      </div>
    </div>

    <div class="block">
      <span class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">Header color</span>
      <div class="flex items-center gap-3">
        <div class="flex flex-1 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:ring-white/10">
          <input class="h-8 w-8 cursor-pointer overflow-hidden rounded border-none bg-transparent" type="color" bind:value={headerColor} />
          <input class="min-w-0 flex-1 border-none bg-transparent font-mono text-sm text-slate-700 focus:outline-none focus:ring-0 dark:text-slate-100" bind:value={headerColor} placeholder="#4f46e5" />
        </div>
        {#if headerColor}
          <button
            class="rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50 dark:border-white/10 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
            type="button"
            onclick={() => (headerColor = '')}
          >
            Clear
          </button>
        {/if}
      </div>
    </div>
  </div>
</div>

{#if showUnsplashModal}
  <UnsplashSearchModal
    {initialQuery}
    effectiveAccent={accent}
    onSelect={(url) => {
      headerImageUrl = url;
      showUnsplashModal = false;
      if (onSelectUnsplash) onSelectUnsplash(url);
    }}
    onClose={() => (showUnsplashModal = false)}
  />
{/if}
