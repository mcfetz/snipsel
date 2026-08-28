<script lang="ts">
  import { fly, fade } from 'svelte/transition';
  import Clock from '@animated-color-icons/lucide-svelte/Clock.svelte';
  import Bell from '@animated-color-icons/lucide-svelte/Bell.svelte';
  import SettingsIcon from '@animated-color-icons/lucide-svelte/Settings.svelte';
  import { api } from './api';
  import { currentView, searchQuery, notificationsStore, recentCollectionsStore } from './stores';
  import { currentUser } from './session';

  interface Props {
    accent: string;
    navPlusColor: string;
    navPlusIconColor: string;
    isEditing: boolean;
    onOpenToday: () => void;
    onRunSearch: () => void;
    onClearRecent: () => void;
  }

  let {
    accent,
    navPlusColor,
    navPlusIconColor,
    isEditing,
    onOpenToday,
    onRunSearch,
    onClearRecent,
  }: Props = $props();

  let showRecentPopup = $state(false);
  let recentContainerRef: HTMLDivElement | null = $state(null);

  let unreadNotificationsCount = $derived(
    $notificationsStore.filter((n) => !n.is_read).length
  );

  async function openRecentPopup() {
    try {
      const res = await api.collections.listRecent();
      recentCollectionsStore.set(res.collections);
    } catch {
      // ignore
    }
    showRecentPopup = true;
  }

  async function toggleRecentPopup() {
    if (!showRecentPopup) {
      await openRecentPopup();
    } else {
      showRecentPopup = false;
    }
  }

  $effect(() => {
    if (!showRecentPopup) return;
    const onClick = (e: MouseEvent) => {
      if (recentContainerRef && !recentContainerRef.contains(e.target as Node)) {
        showRecentPopup = false;
      }
    };
    window.addEventListener('mousedown', onClick);
    return () => window.removeEventListener('mousedown', onClick);
  });
</script>

<!-- Progressive blur layer behind header -->
<div class="pointer-events-none fixed left-0 right-0 top-0 z-[15]" style="height: 120px;">
  <div
    class="absolute inset-0 backdrop-blur-lg"
    style="mask-image: linear-gradient(to bottom, black 0%, black 40%, transparent 100%); -webkit-mask-image: linear-gradient(to bottom, black 0%, black 40%, transparent 100%);"
  ></div>
</div>

<header
  class="sticky top-4 z-20 mx-auto max-w-3xl pointer-events-none px-4 transition-all duration-500"
  class:blur-sm={isEditing}
  class:opacity-40={isEditing}
>
  <div class="pointer-events-auto flex items-center gap-3 rounded-full border border-slate-200 bg-white/80 px-3 py-2 shadow-lg ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/5">
    <button
      class="group flex items-center gap-2 pl-2 pr-1 text-lg font-bold text-slate-800 transition-colors dark:text-slate-200"
      style="--logo-hover: {navPlusColor}"
      type="button"
      onclick={onOpenToday}
      onmouseenter={(e) => (e.currentTarget.style.color = navPlusColor)}
      onmouseleave={(e) => (e.currentTarget.style.color = '')}
    >
      <img
        src="/logo.svg"
        alt="snipsel logo"
        class="h-6 w-6 transition-transform duration-200 group-hover:scale-110 dark:invert dark:brightness-110"
      />
      <span class="hidden origin-left transition-transform duration-200 group-hover:scale-105 sm:inline">snipsel</span>
    </button>

    <input
      class="min-w-0 flex-1 rounded-full border border-slate-200 bg-slate-100/50 px-4 py-2 text-base transition-all focus:bg-white focus:outline-none focus:ring-2 dark:border-white/5 dark:bg-slate-800/50 dark:text-slate-100 dark:focus:bg-slate-800"
      style={`--tw-ring-color: ${accent}33; --accent: ${accent}`}
      onfocus={(e) => {
        e.currentTarget.style.borderColor = accent;
        if ($currentUser && $currentView.type !== 'search') {
          currentView.set({ type: 'search' });
        }
      }}
      onblur={(e) => (e.currentTarget.style.borderColor = '')}
      placeholder="Search"
      type="search"
      bind:value={$searchQuery}
      onkeydown={(e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          onRunSearch();
        }
      }}
    />

    <div
      bind:this={recentContainerRef}
      class="relative"
      onmouseleave={() => (showRecentPopup = false)}
      role="region"
      aria-label="Recent items dropdown"
    >
      <button
        class="al-icon-wrapper grid h-10 w-10 shrink-0 place-items-center rounded-full transition-colors {showRecentPopup
          ? 'bg-black/10 text-slate-900 dark:bg-white/10 dark:text-white'
          : 'text-slate-600 hover:bg-black/5 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-slate-100'}"
        type="button"
        onmouseenter={() => {
          if (!showRecentPopup) {
            openRecentPopup();
          }
        }}
        onclick={(e) => {
          e.stopPropagation();
          toggleRecentPopup();
        }}
        aria-label="Recent collections"
        title="Recent"
      >
        <Clock label="" size={20} />
      </button>

      {#if showRecentPopup}
        <div
          class="absolute right-0 top-full z-50 w-64 pt-2"
          in:fly={{ y: -10, duration: 150 }}
          out:fade={{ duration: 100 }}
        >
          <div class="pointer-events-auto overflow-hidden rounded-xl border border-slate-200 bg-white/95 shadow-xl ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/95 dark:ring-white/10">
            <div class="border-b border-slate-100 bg-slate-50/50 px-3 py-2 text-left text-xs font-bold uppercase tracking-wider text-slate-500 dark:border-white/5 dark:bg-slate-950/50 dark:text-slate-400">
              Recently visited
            </div>
            <div class="max-h-80 overflow-y-auto py-1">
              {#if $recentCollectionsStore.length === 0}
                <div class="px-4 py-3 text-left text-sm italic text-slate-500 dark:text-slate-400">
                  No recent history
                </div>
              {:else}
                {#each $recentCollectionsStore as rc (rc.id)}
                  <button
                    class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm transition-colors hover:bg-slate-50 dark:hover:bg-white/5"
                    type="button"
                    onclick={(e) => {
                      e.stopPropagation();
                      showRecentPopup = false;
                      currentView.set({ type: 'collection', id: rc.id });
                    }}
                  >
                    <span class="shrink-0 text-xl">{rc.icon}</span>
                    <span class="truncate font-medium text-slate-800 dark:text-slate-200">{rc.title}</span>
                  </button>
                {/each}
              {/if}
              {#if $recentCollectionsStore.length > 0}
                <div class="mt-1 border-t border-slate-100 p-1 dark:border-white/5">
                  <button
                    class="w-full rounded-lg px-3 py-2 text-left text-xs font-medium text-red-600 transition-colors hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/30"
                    type="button"
                    onclick={(e) => {
                      e.stopPropagation();
                      onClearRecent();
                      showRecentPopup = false;
                    }}
                  >
                    Clear history
                  </button>
                </div>
              {/if}
            </div>
          </div>
        </div>
      {/if}
    </div>

    <button
      class="al-icon-wrapper relative grid h-10 w-10 shrink-0 place-items-center rounded-full transition-colors {$currentView.type === 'notifications'
        ? 'bg-black/10 text-slate-900 dark:bg-white/10 dark:text-slate-100'
        : 'text-slate-600 hover:bg-black/5 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-slate-100'}"
      type="button"
      onclick={() => currentView.set({ type: 'notifications' })}
      aria-label="Notifications"
      title="Notifications"
    >
      {#if unreadNotificationsCount > 0}
        <span
          class="al-icon-wrapper absolute -right-1 -top-1 flex h-5 min-w-[1.25rem] items-center justify-center rounded-full px-1 text-xs font-bold shadow-sm ring-2 ring-white dark:ring-slate-900"
          style={`background-color: ${navPlusColor}; color: ${navPlusIconColor}`}
        >
          {unreadNotificationsCount}
        </span>
      {/if}
      <Bell label="" size={20} />
    </button>

    <button
      class="al-icon-wrapper grid h-10 w-10 shrink-0 place-items-center rounded-full transition-colors {$currentView.type === 'settings'
        ? 'bg-black/10 text-slate-900 dark:bg-white/10 dark:text-slate-100'
        : 'text-slate-600 hover:bg-black/5 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-slate-100'}"
      type="button"
      onclick={() => currentView.set({ type: 'settings' })}
      aria-label="Settings"
      title="Settings"
    >
      <SettingsIcon label="" size={20} />
    </button>
  </div>
</header>
