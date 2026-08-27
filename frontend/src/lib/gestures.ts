export function longPress(
  onLongPress: () => void,
  onShortPress: () => void,
  ms = 400,
  onStateChange?: (state: 'idle' | 'holding' | 'long') => void
) {
  let timer: ReturnType<typeof setTimeout> | null = null;
  let isLong = false;
  let isTouch = false;
  let touchStartTime = 0;

  function clearTimer() {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
  }

  function start() {
    clearTimer();
    isLong = false;
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

  function end(e?: Event) {
    const elapsed = Date.now() - touchStartTime;
    const wasLong = isLong || elapsed >= ms;
    clearTimer();
    isLong = false;
    onStateChange?.('idle');

    if (wasLong) {
      if (e && e.cancelable) {
        e.preventDefault();
        e.stopPropagation();
      }
      onLongPress();
    } else {
      onShortPress();
    }
  }

  function cancel() {
    clearTimer();
    isLong = false;
    onStateChange?.('idle');
  }

  return {
    ontouchstart: (e: TouchEvent) => {
      isTouch = true;
      start();
    },
    ontouchend: (e: TouchEvent) => {
      if (!isTouch) return;
      end(e);
      setTimeout(() => {
        isTouch = false;
      }, 500);
    },
    ontouchcancel: () => {
      cancel();
      isTouch = false;
    },

    onpointerdown: (e: PointerEvent) => {
      if (isTouch || e.pointerType === 'touch') return;
      start();
    },
    onpointerup: (e: PointerEvent) => {
      if (isTouch || e.pointerType === 'touch') return;
      end(e);
    },
    onpointercancel: () => {
      if (isTouch) return;
      cancel();
    },
    onpointerleave: () => {
      if (isTouch) return;
      cancel();
    },

    onclick: (e: MouseEvent) => {
      if (isTouch) {
        e.preventDefault();
        e.stopPropagation();
        return;
      }
    },
    oncontextmenu: (e: MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
    },
  };
}
