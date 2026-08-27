export function longPress(
  onLongPress: () => void,
  onShortPress: () => void,
  ms = 400,
  onStateChange?: (state: 'idle' | 'holding' | 'long') => void
) {
  let timer: ReturnType<typeof setTimeout> | null = null;
  let isLong = false;
  let ended = true;
  let sawPointer = false;
  let startTime = 0;
  let suppressClickUntil = 0;
  let activePointerId: number | null = null;

  function clearTimer() {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
  }

  function start() {
    clearTimer();
    isLong = false;
    ended = false;
    startTime = Date.now();
    onStateChange?.('holding');
    timer = setTimeout(() => {
      isLong = true;
      onStateChange?.('long');
      try {
        if (typeof navigator !== 'undefined' && 'vibrate' in navigator) {
          navigator.vibrate(40);
        }
      } catch {}
    }, ms);
  }

  function end() {
    if (ended) return;
    ended = true;
    const wasLong = isLong || Date.now() - startTime >= ms;
    clearTimer();
    isLong = false;
    onStateChange?.('idle');

    if (wasLong) {
      suppressClickUntil = Date.now() + 800;
      onLongPress();
    } else {
      onShortPress();
    }
  }

  function cancel() {
    if (ended) return;
    ended = true;
    clearTimer();
    isLong = false;
    onStateChange?.('idle');
  }

  return {
    onpointerdown: (e: PointerEvent) => {
      sawPointer = true;
      activePointerId = e.pointerId;
      // Capture keeps pointerup on the button even if the pointer drifts
      // (e.g. while the button shrinks/grows during the hold animation).
      try {
        (e.currentTarget as HTMLElement | null)?.setPointerCapture(e.pointerId);
      } catch {}
      start();
    },
    onpointerup: (e: PointerEvent) => {
      if (activePointerId !== null && e.pointerId !== activePointerId) return;
      activePointerId = null;
      end();
    },
    onpointercancel: () => {
      activePointerId = null;
      cancel();
    },
    // Intentionally a no-op: pointer capture keeps the event stream on the
    // original target, so drifting off the element must not abort a hold.
    onpointerleave: () => {},

    onclick: (e: MouseEvent) => {
      if (Date.now() < suppressClickUntil) {
        e.preventDefault();
        e.stopPropagation();
        suppressClickUntil = 0;
        return;
      }
      if (sawPointer) {
        // Already handled via pointerup
        sawPointer = false;
        return;
      }
      // Keyboard activation fallback
      onShortPress();
    },
    oncontextmenu: (e: MouseEvent) => {
      // Suppress the long-press context menu on touch devices
      if (isLong || Date.now() < suppressClickUntil) {
        e.preventDefault();
      }
    },
  };
}
