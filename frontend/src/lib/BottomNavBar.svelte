<script lang="ts">
  import { fly } from 'svelte/transition';
  import CalendarIcon from '@animated-color-icons/lucide-svelte/Calendar.svelte';
  import SquareCheck from '@animated-color-icons/lucide-svelte/SquareCheck.svelte';
  import PlusIcon from '@animated-color-icons/lucide-svelte/Plus.svelte';
  import List from '@animated-color-icons/lucide-svelte/List.svelte';
  import Flame from '@animated-color-icons/lucide-svelte/Flame.svelte';
  import { currentView } from './stores';

  interface LongPressHandlers {
    onclick: (e: MouseEvent) => void;
    onpointerdown: (e: PointerEvent) => void;
    onpointerup: (e: PointerEvent) => void;
    onpointercancel: (e: PointerEvent) => void;
    oncontextmenu: (e: MouseEvent) => void;
  }

  interface Props {
    navPlusColor: string;
    navPlusIconColor: string;
    plusPressState: 'idle' | 'holding' | 'long';
    lpNewSnipsel: LongPressHandlers;
    isEditing: boolean;
    onOpenCollections: () => void;
  }

  let {
    navPlusColor,
    navPlusIconColor,
    plusPressState,
    lpNewSnipsel,
    isEditing,
    onOpenCollections,
  }: Props = $props();
</script>

<!-- Progressive blur layer behind navbar -->
<div
  class="pointer-events-none fixed bottom-0 left-0 right-0 z-[5]"
  style="height: 120px;"
  in:fly={{ y: 100, duration: 250 }}
  out:fly={{ y: 100, duration: 200 }}
>
  <div
    class="absolute inset-0 backdrop-blur-lg"
    style="mask-image: linear-gradient(to top, black 0%, black 40%, transparent 100%); -webkit-mask-image: linear-gradient(to top, black 0%, black 40%, transparent 100%);"
  ></div>
</div>

<!-- Navbar -->
<nav
  class="pointer-events-none fixed bottom-0 left-0 right-0 z-10 transition-all duration-500"
  class:blur-sm={isEditing}
  class:opacity-40={isEditing}
  in:fly={{ y: 100, duration: 250 }}
  out:fly={{ y: 100, duration: 200 }}
>
  <div class="mx-auto max-w-3xl px-4 pt-2" style="padding-bottom: calc(env(safe-area-inset-bottom) + 2rem);">
    <div class="pointer-events-auto mx-auto flex w-fit items-center gap-2 rounded-full border border-slate-200 bg-white/85 px-3 py-2 text-slate-700 shadow-lg ring-1 ring-black/5 backdrop-blur-xl dark:border-white/10 dark:bg-slate-900/85 dark:text-slate-200 dark:ring-white/10">
      <button
        class="al-icon-wrapper grid h-12 w-12 place-items-center rounded-full transition-colors {$currentView.type === 'calendar'
          ? 'bg-black/10 text-slate-900 dark:bg-white/10 dark:text-slate-100'
          : 'hover:bg-black/5 hover:text-slate-900 dark:hover:bg-white/5 dark:hover:text-slate-100'}"
        type="button"
        onclick={() => currentView.set({ type: 'calendar' })}
        aria-label="Calendar"
        title="Calendar"
      >
        <CalendarIcon label="" size={24} />
      </button>

      <button
        class="al-icon-wrapper grid h-12 w-12 place-items-center rounded-full transition-colors {$currentView.type === 'todos'
          ? 'bg-black/10 text-slate-900 dark:bg-white/10 dark:text-slate-100'
          : 'hover:bg-black/5 hover:text-slate-900 dark:hover:bg-white/5 dark:hover:text-slate-100'}"
        type="button"
        onclick={() => currentView.set({ type: 'todos' })}
        aria-label="Todos"
        title="Todos"
      >
        <SquareCheck label="" size={24} />
      </button>

      <button
        class="al-icon-wrapper relative grid h-12 w-12 select-none place-items-center rounded-full transition-all duration-200 {plusPressState === 'long'
          ? 'scale-115 shadow-2xl ring-4 ring-indigo-300 dark:ring-indigo-400/50'
          : plusPressState === 'holding'
            ? 'scale-90 opacity-90'
            : 'hover:-translate-y-0.5 hover:shadow-lg'}"
        style={`background-color: ${navPlusColor}; color: ${navPlusIconColor}; touch-action: none; -webkit-touch-callout: none; -webkit-user-select: none;`}
        type="button"
        onpointerdown={lpNewSnipsel.onpointerdown}
        onpointerup={lpNewSnipsel.onpointerup}
        onpointercancel={lpNewSnipsel.onpointercancel}
        oncontextmenu={lpNewSnipsel.oncontextmenu}
        onclick={lpNewSnipsel.onclick}
        aria-label="New snipsel (today) - long press to paste clipboard"
        title="New snipsel (today) - long press to paste clipboard"
      >
        <PlusIcon label="" size={24} strokeWidth={2.5} />
      </button>

      <button
        class="al-icon-wrapper grid h-12 w-12 place-items-center rounded-full transition-colors {$currentView.type === 'collections'
          ? 'bg-black/10 text-slate-900 dark:bg-white/10 dark:text-slate-100'
          : 'hover:bg-black/5 hover:text-slate-900 dark:hover:bg-white/5 dark:hover:text-slate-100'}"
        type="button"
        onclick={onOpenCollections}
        aria-label="Collections"
        title="Collections"
      >
        <List label="" size={24} />
      </button>

      <button
        class="al-icon-wrapper grid h-12 w-12 place-items-center rounded-full transition-colors {$currentView.type === 'habits'
          ? 'bg-black/10 text-slate-900 dark:bg-white/10 dark:text-slate-100'
          : 'hover:bg-black/5 hover:text-slate-900 dark:hover:bg-white/5 dark:hover:text-slate-100'}"
        type="button"
        onclick={() => currentView.set({ type: 'habits' })}
        aria-label="Habits"
        title="Habits"
      >
        <Flame label="" size={24} />
      </button>
    </div>
  </div>
</nav>
