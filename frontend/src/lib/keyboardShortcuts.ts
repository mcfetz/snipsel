export interface KeyboardShortcutHandlers {
  onOpenCalendar: () => void;
  onOpenTodos: () => void;
  onOpenCollections: () => void;
  onOpenHabits: () => void;
  onNewSnipsel: () => void;
  onNewSnipselInCurrentCollection: () => void;
  onClearSelection: () => void;
  onDeleteSelection: () => void;
  hasSelectedSnipsels: () => boolean;
  onMoveSelection: (direction: 'up' | 'down') => void;
  onIndentSelection: (direction: 'left' | 'right') => void;
  onAiAssistant: () => void;
  onToggleType: () => void;
  onToggleCardView: () => void;
  onCopySnipsels: () => void;
  onMoveSnipsels: () => void;
  onInfoSnipsels: () => void;
  onUploadAttachment: () => void;
}

export function setupKeyboardShortcuts(handlers: KeyboardShortcutHandlers): () => void {
  function onKeyDown(e: KeyboardEvent) {
    // Ignore if in an input or editable element
    const target = e.target as HTMLElement;
    if (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.isContentEditable ||
      target.getAttribute('role') === 'textbox'
    ) {
      return;
    }

    const isMetaOrCtrl = e.metaKey || e.ctrlKey;

    // Cmd/Ctrl + Shift + 1 -> Calendar
    if (isMetaOrCtrl && e.shiftKey && e.key === '1') {
      e.preventDefault();
      handlers.onOpenCalendar();
    }
    // Cmd/Ctrl + Shift + 2 -> Todos
    else if (isMetaOrCtrl && e.shiftKey && e.key === '2') {
      e.preventDefault();
      handlers.onOpenTodos();
    }
    // Cmd/Ctrl + Shift + 3 -> Collections
    else if (isMetaOrCtrl && e.shiftKey && e.key === '3') {
      e.preventDefault();
      handlers.onOpenCollections();
    }
    // Cmd/Ctrl + Shift + 4 -> Habits
    else if (isMetaOrCtrl && e.shiftKey && e.key === '4') {
      e.preventDefault();
      handlers.onOpenHabits();
    }
    // Cmd/Ctrl + Shift + N -> New snipsel in Today's collection
    else if (isMetaOrCtrl && e.shiftKey && (e.key === 'n' || e.key === 'N')) {
      e.preventDefault();
      handlers.onNewSnipsel();
    }
    // Cmd/Ctrl + Shift + Enter -> New snipsel in current collection
    else if (isMetaOrCtrl && e.shiftKey && e.key === 'Enter') {
      e.preventDefault();
      handlers.onNewSnipselInCurrentCollection();
    }
    // Escape -> Deselect
    else if (e.key === 'Escape') {
      handlers.onClearSelection();
    }
    // Delete key -> Delete selected snipsels
    else if (handlers.hasSelectedSnipsels() && (e.key === 'Delete' || e.key === 'Backspace')) {
      e.preventDefault();
      handlers.onDeleteSelection();
    }
    // Cmd/Ctrl + Shift + S -> Focus search
    else if (isMetaOrCtrl && e.shiftKey && (e.key === 's' || e.key === 'S')) {
      e.preventDefault();
      const searchInput = document.querySelector('input[type="search"]') as HTMLInputElement;
      if (searchInput) {
        searchInput.focus();
      }
    }
    // Shortcuts for selected snipsels (only when snipsels are selected)
    else if (handlers.hasSelectedSnipsels() && e.ctrlKey && e.shiftKey) {
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        handlers.onMoveSelection('up');
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        handlers.onMoveSelection('down');
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        handlers.onIndentSelection('left');
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        handlers.onIndentSelection('right');
      } else if (e.key === 'a' || e.key === 'A') {
        e.preventDefault();
        handlers.onAiAssistant();
      } else if (e.key === 't' || e.key === 'T') {
        e.preventDefault();
        handlers.onToggleType();
      } else if (e.key === 'v' || e.key === 'V') {
        e.preventDefault();
        handlers.onToggleCardView();
      } else if (e.key === 'c' || e.key === 'C') {
        e.preventDefault();
        handlers.onCopySnipsels();
      } else if (e.key === 'm' || e.key === 'M') {
        e.preventDefault();
        handlers.onMoveSnipsels();
      } else if (e.key === 'i' || e.key === 'I') {
        e.preventDefault();
        handlers.onInfoSnipsels();
      } else if (e.key === 'u' || e.key === 'U') {
        e.preventDefault();
        handlers.onUploadAttachment();
      }
    }
  }

  window.addEventListener('keydown', onKeyDown);
  return () => window.removeEventListener('keydown', onKeyDown);
}
