import { writable } from 'svelte/store';

export const debugLog = writable<string[]>([]);

export function logDebug(msg: string) {
  const t = new Date();
  const ts = `${String(t.getHours()).padStart(2, '0')}:${String(t.getMinutes()).padStart(2, '0')}:${String(t.getSeconds()).padStart(2, '0')}.${String(t.getMilliseconds()).padStart(3, '0')}`;
  const line = `${ts} ${msg}`;
  debugLog.update((lines) => {
    const next = [...lines, line];
    return next.slice(-60);
  });
  try {
    console.log('[snipsel-debug]', line);
  } catch {}
}

export function clearDebugLog() {
  debugLog.set([]);
}
