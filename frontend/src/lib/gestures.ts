export function longPress(onLongPress: () => void, onShortPress: () => void, ms = 450) {
  let timer: ReturnType<typeof setTimeout> | null = null;
  let firedLong = false;
  let handledByPointer = false;
  let activePointerId: number | null = null;

  function cancel() {
    if (timer) clearTimeout(timer);
    timer = null;
  }

  function reset() {
    cancel();
    firedLong = false;
    handledByPointer = false;
    activePointerId = null;
  }

  return {
    onpointerdown: (e: PointerEvent) => {
      reset();
      activePointerId = e.pointerId;
      try {
        (e.currentTarget as HTMLElement | null)?.setPointerCapture(e.pointerId);
      } catch {
        // Ignore (some browsers/targets may not support capture).
      }

      timer = setTimeout(() => {
        firedLong = true;
        handledByPointer = true;
        onLongPress();
      }, ms);
    },
    onpointerup: (e: PointerEvent) => {
      cancel();

      if (!firedLong) {
        handledByPointer = true;
        onShortPress();
      }

      if (activePointerId !== null) {
        try {
          (e.currentTarget as HTMLElement | null)?.releasePointerCapture(activePointerId);
        } catch {
          // Ignore.
        }
      }

      activePointerId = null;
    },
    onpointercancel: () => reset(),
    onpointerleave: () => cancel(),
    onclick: (e: MouseEvent) => {
      if (handledByPointer) {
        e.preventDefault();
        e.stopPropagation();
        handledByPointer = false;
        return;
      }
      onShortPress();
    },
    oncontextmenu: (e: MouseEvent) => {
      if (firedLong) e.preventDefault();
    },
  };
}
