export function longPress(
  onLongPress: () => void,
  onShortPress: () => void,
  ms = 400,
  onStateChange?: (state: 'idle' | 'holding' | 'long') => void
) {
  let timer: ReturnType<typeof setTimeout> | null = null;
  let isLong = false;
  let fired = false;
  let activeTouchId: number | null = null;
  let touchStartTime = 0;
  let suppressClickUntil = 0;

  function clearTimer() {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
  }

  function start(touchId?: number) {
    clearTimer();
    isLong = false;
    fired = false;
    if (touchId !== undefined) activeTouchId = touchId;
    touchStartTime = Date.now();
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

  function finish(syntheticClick: boolean) {
    const elapsed = Date.now() - touchStartTime;
    const wasLong = isLong || elapsed >= ms;
    clearTimer();

    if (wasLong) {
      fired = true;
      suppressClickUntil = Date.now() + 800;
      onLongPress();
    } else if (!fired) {
      fired = true;
      onShortPress();
    }

    isLong = false;
    activeTouchId = null;
    onStateChange?.('idle');

    // If a synthetic click is arriving, suppress it
    void syntheticClick;
  }

  function cancel() {
    clearTimer();
    isLong = false;
    activeTouchId = null;
    onStateChange?.('idle');
  }

  return {
    // Native touch events (preferred path on iOS / Android)
    ontouchstart: (e: TouchEvent) => {
      const t = e.changedTouches[0] ?? e.touches[0];
      if (!t) return;
      start(t.identifier);
    },
    ontouchmove: () => {
      // Touch is moving → user is scrolling, cancel long press
      cancel();
    },
    ontouchend: (e: TouchEvent) => {
      finish(true);
    },
    ontouchcancel: () => {
      cancel();
    },

    // Pointer events (desktop path)
    onpointerdown: (e: PointerEvent) => {
      if (e.pointerType === 'touch') return;
      start();
    },
    onpointerup: () => {
      if (activeTouchId !== null) return;
      finish(true);
    },
    onpointercancel: () => {
      if (activeTouchId !== null) return;
      cancel();
    },
    onpointerleave: () => {
      if (activeTouchId !== null) return;
      cancel();
    },

    // Synthetic click (e.g. desktop mouse or iOS post-touch)
    onclick: (e: MouseEvent) => {
      if (Date.now() < suppressClickUntil) {
        e.preventDefault();
        e.stopPropagation();
        suppressClickUntil = 0;
      }
    },
    oncontextmenu: (e: MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
    },
  };
}
