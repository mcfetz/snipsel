<script lang="ts">
  import { getContrastColor } from './colors';

  interface Props {
    rrule: string | null;
    accent: string;
    disabled?: boolean;
    onChange?: (rrule: string | null) => void;
  }

  let { rrule = $bindable(null), accent, disabled = false, onChange }: Props = $props();

  let showBuilder = $state(false);
  let rrFreq = $state<'DAILY' | 'WEEKLY' | 'MONTHLY' | 'YEARLY'>('WEEKLY');
  let rrInterval = $state(1);
  let rrByDay = $state<string[]>([]);

  function parseCurrentRRule() {
    if (!rrule) return;
    const parts = rrule.split(';');
    rrByDay = [];
    for (const p of parts) {
      const [key, val] = p.split('=');
      if (key === 'FREQ') rrFreq = val as any;
      if (key === 'INTERVAL') rrInterval = parseInt(val, 10) || 1;
      if (key === 'BYDAY') rrByDay = val.split(',');
    }
  }

  function toggleDay(day: string) {
    if (rrByDay.includes(day)) {
      rrByDay = rrByDay.filter((d) => d !== day);
    } else {
      rrByDay = [...rrByDay, day];
    }
  }

  function applyBuilder() {
    let parts = [`FREQ=${rrFreq}`];
    if (rrInterval > 1) parts.push(`INTERVAL=${rrInterval}`);
    if (rrFreq === 'WEEKLY' && rrByDay.length > 0) {
      parts.push(`BYDAY=${rrByDay.join(',')}`);
    }
    const next = parts.join(';');
    rrule = next;
    showBuilder = false;
    if (onChange) onChange(next);
  }

  function handleBlur() {
    if (onChange) onChange(rrule);
  }
</script>

<div>
  <label for="reminder-rrule" class="block text-xs font-medium text-slate-500 dark:text-slate-400">
    Recurrence (RRule)
  </label>
  <div class="mt-1 flex items-center gap-2">
    <input
      id="reminder-rrule"
      type="text"
      placeholder="e.g. FREQ=DAILY"
      class="flex-1 rounded-md border border-slate-200 bg-white/50 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:border-white/10 dark:bg-slate-900/50"
      bind:value={rrule}
      onblur={handleBlur}
      {disabled}
    />
    <button
      type="button"
      class="rounded-full border border-slate-200 bg-white px-6 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
      style={`color: ${accent}`}
      onclick={() => {
        parseCurrentRRule();
        showBuilder = !showBuilder;
      }}
      {disabled}
    >
      {showBuilder ? 'Close' : 'Builder'}
    </button>
  </div>

  {#if showBuilder}
    <div class="mt-3 space-y-3 rounded-lg border border-slate-200 bg-slate-50/50 p-3 dark:border-white/5 dark:bg-white/5">
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label for="rr-freq" class="block text-[10px] uppercase tracking-wider text-slate-400">Frequency</label>
          <select
            id="rr-freq"
            bind:value={rrFreq}
            class="mt-1 w-full rounded-md border border-slate-200 bg-white px-2 py-1 text-sm dark:border-white/10 dark:bg-slate-800"
          >
            <option value="DAILY">Daily</option>
            <option value="WEEKLY">Weekly</option>
            <option value="MONTHLY">Monthly</option>
            <option value="YEARLY">Yearly</option>
          </select>
        </div>
        <div>
          <label for="rr-interval" class="block text-[10px] uppercase tracking-wider text-slate-400">Interval</label>
          <input
            id="rr-interval"
            type="number"
            min="1"
            bind:value={rrInterval}
            class="mt-1 w-full rounded-md border border-slate-200 bg-white px-2 py-1 text-sm dark:border-white/10 dark:bg-slate-800"
          />
        </div>
      </div>

      {#if rrFreq === 'WEEKLY'}
        <div>
          <div class="block text-[10px] uppercase tracking-wider text-slate-400">Days</div>
          <div class="mt-1 flex flex-wrap gap-1">
            {#each ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'] as day}
              <button
                type="button"
                class="h-7 w-8 rounded text-[10px] font-bold transition-colors {rrByDay.includes(day)
                  ? ''
                  : 'bg-white text-slate-600 hover:bg-slate-100 dark:bg-slate-800 dark:text-slate-400'}"
                style={rrByDay.includes(day) ? `background-color: ${accent}; color: ${getContrastColor(accent)}` : undefined}
                onclick={() => toggleDay(day)}
              >
                {day}
              </button>
            {/each}
          </div>
        </div>
      {/if}

      <div class="flex justify-end pt-1">
        <button
          type="button"
          class="rounded-full border border-slate-200 bg-white px-6 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
          style={`color: ${accent}`}
          onclick={applyBuilder}
        >
          Apply
        </button>
      </div>
    </div>
  {/if}
</div>
