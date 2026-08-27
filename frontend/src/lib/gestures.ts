export function longPress(
  onLongPress: () => void,
  onShortPress: () => void,
  ms = 400,
  onStateChange?: (state: 'idle' | 'holding' | 'long') => void,
  debug?: (msg: string) => void
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
    debug?.('start() — timer armed');
    timer = setTimeout(() => {
      isLong = true;
      onStateChange?.('long');
      debug?.('timer fired — isLong=true');
      try {
        if (typeof navigator !== 'undefined' && 'vibrate' in navigator) {
          navigator.vibrate(40);
        }
      } catch {}
    }, ms);
  }

  function end() {
    if (ended) {
      debug?.('end() called but already ended — ignored');
      return;
    }
    ended = true;
    const elapsed = Date.now() - startTime;
    const wasLong = isLong || elapsed >= ms;
    clearTimer();
    isLong = false;
    onStateChange?.('idle');
    debug?.(`end() elapsed=${elapsed}ms wasLong=${wasLong}`);

    if (wasLong) {
      suppressClickUntil = Date.now() + 800;
      debug?.('calling onLongPress()');
      onLongPress();
    } else {
      debug?.('calling onShortPress()');
      onShortPress();
    }
  }

  function cancel() {
    if (ended) return;
    ended = true;
    clearTimer();
    isLong = false;
    onStateChange?.('idle');
    debug?.('cancel()');
  }

  return {
    onpointerdown: (e: PointerEvent) => {
      sawPointer = true;
      activePointerId = e.pointerId;
      debug?.(`pointerdown type=${e.pointerType} id=${e.pointerId}`);
      // Capture keeps pointerup on the button even if the pointer drifts
      // (e.g. while the button shrinks/grows during the hold animation).
      try {
        (e.currentTarget as HTMLElement | null)?.setPointerCapture(e.pointerId);
        debug?.('setPointerCapture ok');
      } catch (err) {
        debug?.(`setPointerCapture failed: ${err}`);
      }
      start();
    },
    onpointerup: (e: PointerEvent) => {
      debug?.(`pointerup type=${e.pointerType} id=${e.pointerId} activeId=${activePointerId}`);
      if (activePointerId !== null && e.pointerId !== activePointerId) {
        debug?.('pointerup ignored — id mismatch');
        return;
      }
      activePointerId = null;
      end();
    },
    onpointercancel: (e: PointerEvent) => {
      debug?.(`pointercancel type=${e.pointerType} id=${e.pointerId}`);
      activePointerId = null;
      cancel();
    },
    // Intentionally a no-op: pointer capture keeps the event stream on the
    // original target, so drifting off the element must not abort a hold.
    onpointerleave: (e: PointerEvent) => {
      debug?.(`pointerleave type=${e.pointerType} (ignored)`);
    },

    onclick: (e: MouseEvent) => {
      debug?.(`click suppressUntilDelta=${suppressClickUntil - Date.now()} sawPointer=${sawPointer}`);
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
