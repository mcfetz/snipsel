<script lang="ts">
  import { fly, fade, scale } from 'svelte/transition';
  import ChevronsUp from '@animated-color-icons/lucide-svelte/ChevronsUp.svelte';
  import ChevronsDown from '@animated-color-icons/lucide-svelte/ChevronsDown.svelte';
  import Loader2 from '@animated-color-icons/lucide-svelte/Loader2.svelte';
  import ArrowUp from '@animated-color-icons/lucide-svelte/ArrowUp.svelte';
  import ArrowDown from '@animated-color-icons/lucide-svelte/ArrowDown.svelte';
  import Heart from '@animated-color-icons/lucide-svelte/Heart.svelte';
  import LayoutTemplate from '@animated-color-icons/lucide-svelte/LayoutTemplate.svelte';
  import Archive from '@animated-color-icons/lucide-svelte/Archive.svelte';
  import Lock from '@animated-color-icons/lucide-svelte/Lock.svelte';
  import Plus from '@animated-color-icons/lucide-svelte/Plus.svelte';
  import ChevronDown from '@animated-color-icons/lucide-svelte/ChevronDown.svelte';
  import ChevronUp from '@animated-color-icons/lucide-svelte/ChevronUp.svelte';
  import Bell from '@animated-color-icons/lucide-svelte/Bell.svelte';
  import Repeat from '@animated-color-icons/lucide-svelte/Repeat.svelte';
  import CirclePlay from '@animated-color-icons/lucide-svelte/CirclePlay.svelte';
  import Outdent from '@animated-color-icons/lucide-svelte/Outdent.svelte';
  import Indent from '@animated-color-icons/lucide-svelte/Indent.svelte';
  import Type from '@animated-color-icons/lucide-svelte/Type.svelte';
  import Copy from '@animated-color-icons/lucide-svelte/Copy.svelte';
  import Sparkles from '@animated-color-icons/lucide-svelte/Sparkles.svelte';
  import Paperclip from '@animated-color-icons/lucide-svelte/Paperclip.svelte';
  import ArrowRightLeft from '@animated-color-icons/lucide-svelte/ArrowRightLeft.svelte';
  import CornerDownRight from '@animated-color-icons/lucide-svelte/CornerDownRight.svelte';
  import Info from '@animated-color-icons/lucide-svelte/Info.svelte';
  import Trash2 from '@animated-color-icons/lucide-svelte/Trash2.svelte';
  import X from '@animated-color-icons/lucide-svelte/X.svelte';
  import FileText from '@animated-color-icons/lucide-svelte/FileText.svelte';
  import ImageIcon from '@animated-color-icons/lucide-svelte/Image.svelte';
  import SquareCheck from '@animated-color-icons/lucide-svelte/SquareCheck.svelte';

  import MarkdownIt from 'markdown-it';
  import { api, type Attachment, type CollectionItem, type SearchSnipselHit } from '../lib/api';
  import ImageModal from '../lib/ImageModal.svelte';
  import CollectionSelectModal from '../lib/CollectionSelectModal.svelte';
  import DeleteConfirmModal from '../lib/DeleteConfirmModal.svelte';
  import InfoModal from '../lib/InfoModal.svelte';
  import ProgressModal from '../lib/ProgressModal.svelte';
  import DeezerCard from '../lib/DeezerCard.svelte';
  import YouTubeCard from '../lib/YouTubeCard.svelte';
  import HyperlinkCard from '../lib/HyperlinkCard.svelte';
  import MapCard from '../lib/MapCard.svelte';
  import VideoModal from '../lib/VideoModal.svelte';
  import AiModal from '../lib/AiModal.svelte';
  import AttachmentCard from '../lib/AttachmentCard.svelte';

  import {
    collectionItems,
    collectionAnchor,
    currentCollection,
    currentView,
    editingSnipselId,
    isLoading,
    newSnipselRequest,
    pendingReference,
    sortedItems,
    createSnipselCallback,
    createSnipselOnLoad,
    snipselsSelected,
  } from '../lib/stores';
  import { currentUser } from '../lib/session';
  import { getCurrentUrl } from '../lib/router';

  const md = new MarkdownIt({ html: false, linkify: true, breaks: false });

  let textareaRef: HTMLTextAreaElement | undefined = $state();
  let editContainerRef: HTMLDivElement | undefined = $state();
  let focusProxyRef: HTMLInputElement | undefined = $state();
  let editContent = $state('');
  let editIndent = $state(0);
  let saving = $state(false);
  let creatingFromTripleEmptyLines = $state(false);
  let saveStatuses = $state<Record<string, 'success' | 'error' | null>>({});


  let selectedIds = $state<Set<string>>(new Set());
  let selectionPulse = $state(false);
  let previousSelectionSize = $state(0);

  $effect(() => {
    const size = selectedIds.size;
    if (size !== previousSelectionSize && size > 0) {
      selectionPulse = true;
      setTimeout(() => { selectionPulse = false; }, 400);
    }
    previousSelectionSize = size;
  });

  // Prevent stale list fetches from overwriting optimistic mutations.
  let itemsLoadSeq = 0;
  let itemsMutationSeq = 0;

  let hideDoneTasks = $state(false);

  let showCollectionModal = $state(false);
  let collectionModalMode = $state<'copy' | 'move' | 'link'>('copy');
  let collectionModalTitle = $state('');

  let lastAnchorKey = $state<string | null>(null);
  let anchorHighlightId = $state<string | null>(null);

  let lastCollectionId = $state<string | null>(null);

  // Incoming mentions from other users' daily collections
  let incomingMentions = $state<SearchSnipselHit[]>([]);
  let incomingMentionsLoading = $state(false);

  function canWrite(): boolean {
    return $currentCollection?.access_level !== 'read';
  }

  let attachmentsInputRef: HTMLInputElement | undefined = $state();
  let uploadingAttachments = $state(false);

  let templates = $state<Array<{ id: string; title: string; icon: string }>>([]);
  let showTemplateMenu = $state(false);
  
  type AutocompleteSuggestion = { id: string; label: string; icon?: string; type: 'collection' | 'tag' | 'mention' };
  let suggestions = $state<AutocompleteSuggestion[]>([]);
  let showAutocomplete = $state(false);
  let autocompleteSelectedIndex = $state(0);
  let autocompleteQuery = $state('');
  let autocompleteDebounce: ReturnType<typeof setTimeout> | null = null;

  let shareCount = $state(0);

  let modalImage = $state<{ id: string; filename: string } | null>(null);
  let modalVideo = $state<{ id: string; filename: string } | null>(null);

  let showTypeMenu = $state(false);
  let showScrollTop = $state(false);
  let showDeleteModal = $state(false);
  let errorModal = $state<{ title: string; message: string } | null>(null);
  let uploadProgress = $state<{ filename: string; percent: number } | null>(null);

  // Swipe navigation state (for daily collections)
  let swipeTouchStartX = $state(0);
  let swipeTouchStartY = $state(0);
  let swipeNavigating = $state(false);

  // Pull-to-reload state
  const PULL_THRESHOLD = 70; // px to trigger reload
  const PULL_MAX = 110;      // max visual rubber-band distance
  let pullStartY = $state(0);
  let pullDeltaY = $state(0); // clamped pull distance for UI
  let pullActive = $state(false);
  let pullTriggered = $state(false);
  let pullReloading = $state(false);

  let showAiModal = $state(false);
  let aiModalContext = $state('');
  let aiModalSelectedIds = $state<string[]>([]);
  let aiModalSelectedAttachments = $state<string[]>([]);

  function offsetDate(dateStr: string, days: number): string {
    const d = new Date(dateStr + 'T12:00:00'); // noon to avoid DST issues
    d.setDate(d.getDate() + days);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }

  async function navigateDayCollection(direction: -1 | 1) {
    const col = $currentCollection;
    if (!col?.list_for_day || swipeNavigating) return;
    swipeNavigating = true;
    try {
      const targetDate = offsetDate(col.list_for_day, direction);
      const res = await api.collections.today(targetDate);
      currentCollection.set(res.collection);
      currentView.set({ type: 'collection', id: res.collection.id });
    } catch (err) {
      console.error('Failed to navigate day collection:', err);
    } finally {
      swipeNavigating = false;
    }
  }

  function isScrolledToTop(): boolean {
    return window.scrollY <= 0;
  }

  function handleSwipeTouchStart(e: TouchEvent) {
    const t = e.touches[0];
    swipeTouchStartX = t.clientX;
    swipeTouchStartY = t.clientY;
    // Pull-to-reload: start tracking if at top
    if (isScrolledToTop()) {
      pullStartY = t.clientY;
      pullActive = false;
      pullTriggered = false;
      pullDeltaY = 0;
    }
  }

  function handleSwipeTouchMove(e: TouchEvent) {
    if (pullReloading) return;
    const t = e.touches[0];
    const dy = t.clientY - pullStartY;
    // Only activate pull if dragging downward from the top
    if (dy > 10 && isScrolledToTop()) {
      pullActive = true;
      // Rubber-band: use a damping formula for pleasant feel
      const raw = Math.max(0, dy);
      pullDeltaY = Math.min(PULL_MAX, raw * (PULL_MAX / (PULL_MAX + raw)));
      pullTriggered = pullDeltaY >= PULL_THRESHOLD * (PULL_MAX / (PULL_MAX + PULL_THRESHOLD));
      // Prevent the browser from scrolling up while pulling
      if (pullActive) e.preventDefault();
    } else {
      pullActive = false;
      pullDeltaY = 0;
      pullTriggered = false;
    }
  }

  async function handleSwipeTouchEnd(e: TouchEvent) {
    // Pull-to-reload release
    if (pullActive) {
      if (pullTriggered && !pullReloading) {
        pullReloading = true;
        pullActive = false;
        pullDeltaY = 0;
        try {
          await Promise.all([loadItems(), loadIncomingMentions()]);
        } finally {
          pullReloading = false;
          pullTriggered = false;
        }
      } else {
        pullActive = false;
        pullDeltaY = 0;
        pullTriggered = false;
      }
    }

    // Horizontal swipe navigation (daily collections only)
    if (!$currentCollection?.list_for_day) return;
    const t = e.changedTouches[0];
    const dx = t.clientX - swipeTouchStartX;
    const dy = t.clientY - swipeTouchStartY;
    const THRESHOLD = 60;
    // Ignore mostly-vertical swipes
    if (Math.abs(dx) < THRESHOLD || Math.abs(dy) > Math.abs(dx)) return;
    if (dx < 0) {
      // Swipe left → next day
      navigateDayCollection(1);
    } else {
      // Swipe right → previous day
      navigateDayCollection(-1);
    }
  }

  let expandedSnipsels = $state<Set<string>>(new Set());

  let collapsibleParentIds = $derived.by(() => {
    const ids = new Set<string>();
    const items = $sortedItems;
    for (let i = 0; i < items.length - 1; i++) {
      if (items[i + 1].indent > items[i].indent) {
        ids.add(items[i].snipsel_id);
      }
    }
    return ids;
  });

  let allExpanded = $derived.by(() => {
    if (collapsibleParentIds.size === 0) return false;
    for (const id of collapsibleParentIds) {
      if (!expandedSnipsels.has(id)) return false;
    }
    return true;
  });

  function toggleExpand(id: string) {
    const next = new Set(expandedSnipsels);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    expandedSnipsels = next;
  }

  function toggleAllExpanded() {
    if (allExpanded) {
      expandedSnipsels = new Set();
    } else {
      expandedSnipsels = new Set(collapsibleParentIds);
    }
  }

  function hasChildren(item: CollectionItem, allItems: CollectionItem[]): boolean {
    const idx = allItems.findIndex((i) => i.snipsel_id === item.snipsel_id);
    if (idx < 0 || idx === allItems.length - 1) return false;
    // Children are any following items with higher indentation
    return allItems[idx + 1].indent > item.indent;
  }

  let showEmojiPicker = $state(false);
  const commonEmojis = [
    '🗒', '📅', '✅', '📌', '💡', '🏷', '📁', '🏠', '🚀', '🎨', 
    '🛠', '⚙️', '🔒', '🔑', '🌍', '📊', '📈', '💬', '👥', '👤', 
    '⭐', '❤️', '🔥', '⚡', '🌈', '☀', '🌙', '☁', '🍎', '🍔', 
    '🍕', '🍺', '☕', '⚽', '🎮', '🎵', '📷', '✈️', '🚗', '💡'
  ];

  async function updateIcon(icon: string) {
    if (!$currentCollection || !canWrite()) return;
    try {
      const res = await api.collections.update($currentCollection.id, { icon });
      currentCollection.set(res.collection);
      showEmojiPicker = false;
    } catch (err) {
      console.error('Failed to update icon:', err);
    }
  }

  async function togglePasscodeProtection() {
    if (!$currentCollection || $currentCollection.access_level !== 'owner') return;
    if (!$currentUser?.passcode_set) return;
    try {
      const next = !$currentCollection.is_passcode_protected;
      const res = await api.collections.update($currentCollection.id, { is_passcode_protected: next });
      currentCollection.set(res.collection);
    } catch (err) {
      console.error('Failed to toggle passcode protection:', err);
    }
  }

  function closeTemplateMenu() {
    showTemplateMenu = false;
  }

  let activeReactionPickerId = $state<string | null>(null);
  let showCustomEmojiInputId = $state<string | null>(null);
  let customEmojiInput = $state('');
  const REACTION_EMOJIS = ['👍', '❤️', '😂', '🔥', '✨', '📌'];

  function updateReactionsArray(reactions: any[], emoji: string, active: boolean) {
    const next = [...reactions];
    const idx = next.findIndex((r: any) => r.emoji === emoji);
    if (active) {
      if (idx >= 0) {
        next[idx] = { emoji, count: next[idx].count + 1, me: true };
      } else {
        next.push({ emoji, count: 1, me: true });
      }
    } else {
      if (idx >= 0) {
        if (next[idx].count > 1) {
          next[idx] = { emoji, count: Math.max(0, next[idx].count - 1), me: false };
        } else {
          next.splice(idx, 1);
        }
      }
    }
    return next;
  }

  async function toggleSnipselReaction(snipselId: string, emoji: string) {
    try {
      const res = await api.snipsels.toggleReaction(snipselId, emoji);
      
      // Update in main list
      collectionItems.update(items => items.map(i => {
        if (i.snipsel_id === snipselId) {
            return { ...i, snipsel: { ...i.snipsel, reactions: updateReactionsArray(i.snipsel.reactions || [], emoji, res.active) } };
        }
        return i;
      }));

      // Update in incoming mentions
      incomingMentions = incomingMentions.map(m => {
        if (m.id === snipselId) {
            return { ...m, reactions: updateReactionsArray(m.reactions || [], emoji, res.active) };
        }
        return m;
      });

      activeReactionPickerId = null;
    } catch (err) {
      console.error('Failed to toggle reaction:', err);
    }
  }

  function openAiModal(item?: CollectionItem) {
    if (item) {
      aiModalSelectedIds = [item.snipsel_id];
      aiModalContext = item.snipsel.content_markdown || '';
      aiModalSelectedAttachments = (item.snipsel.attachments || []).map(a => a.id);
    } else if (selectedIds.size > 0) {
      // Sort selection results by position to maintain order in prompt
      const items = $sortedItems.filter(i => selectedIds.has(i.snipsel_id));
      aiModalSelectedIds = items.map(i => i.snipsel_id);
      aiModalContext = items.map(i => i.snipsel.content_markdown || '').join('\n\n');
      aiModalSelectedAttachments = items.flatMap(i => (i.snipsel.attachments || []).map(a => a.id));
    } else {
      return;
    }
    showAiModal = true;
  }

  async function handleAiInsert(text: string) {
    if (aiModalSelectedIds.length === 0 || !$currentCollection) return;
    isLoading.set(true);
    try {
      // Find the last item in the group to insert after it
      const lastId = aiModalSelectedIds[aiModalSelectedIds.length - 1];
      const idx = $sortedItems.findIndex(i => i.snipsel_id === lastId);
      
      if (idx >= 0) {
        const sourceItem = $sortedItems[idx];
        
        // 1. Create the snipsel
        const res = await api.snipsels.create($currentCollection.id, {
          content_markdown: text,
          indent: sourceItem.indent,
          type: 'text'
        });

        // 2. Insert into local list at the correct position
        const list = [...$sortedItems];
        const insertAt = idx + 1;
        const next = [...list.slice(0, insertAt), { ...res.item, indent: sourceItem.indent }, ...list.slice(insertAt)];

        // 3. Reorder everything
        const reordered = next.map((i, index) => ({ ...i, position: index + 1 }));
        collectionItems.set(reordered);
        itemsMutationSeq += 1;

        // 4. Persist reorder
        const payload = reordered.map((i) => ({ snipsel_id: i.snipsel_id, position: i.position, indent: i.indent }));
        await api.snipsels.reorder($currentCollection.id, payload);
      }
      showAiModal = false;
      clearSelection();
    } catch (err) {
      console.error('AI insert failed:', err);
    } finally {
      isLoading.set(false);
    }
  }

  async function handleAiReplace(text: string) {
    if (aiModalSelectedIds.length === 0) return;
    isLoading.set(true);
    try {
      const firstId = aiModalSelectedIds[0];
      const otherIds = aiModalSelectedIds.slice(1);

      // 1. Update the first snipsel
      await api.snipsels.update(firstId, { content_markdown: text });

      // 2. Delete the others
      for (const id of otherIds) {
        await api.snipsels.delete(id);
      }

      await loadItems();
      showAiModal = false;
      clearSelection();
    } catch (err) {
      console.error('AI replace failed:', err);
    } finally {
      isLoading.set(false);
    }
  }

  function focusOnMount(node: HTMLInputElement) {
    node.focus();
  }

  const DEFAULT_HEADER_COLOR = '#4f46e5';
  const TOOLBOX_BASE_COLOR = '#ffffff';

  function getHeaderColor(): string {
    const raw =
      ($currentCollection?.header_color || '').trim() ||
      ($currentUser?.default_collection_header_color || '').trim() ||
      DEFAULT_HEADER_COLOR;

    return /^#[0-9a-fA-F]{6}$/.test(raw) ? raw : DEFAULT_HEADER_COLOR;
  }

  function isExpired(dateStr: string): boolean {
    return new Date(dateStr).getTime() < Date.now();
  }

  function daysFromNow(dateStr: string): string {
    const d = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.round((new Date(dateStr).setHours(0,0,0,0) - new Date().setHours(0,0,0,0)) / 86400000);
    
    if (diffDays === 0) {
      const diffMs = d.getTime() - now.getTime();
      if (diffMs > 0) {
        const hours = Math.floor(diffMs / 3600000);
        const minutes = Math.floor((diffMs % 3600000) / 60000);
        if (hours > 0) {
          return `fällig in ${hours}h ${minutes}m`;
        }
        return `fällig in ${minutes}m`;
      }
      return 'heute fällig';
    }
    if (diffDays > 0) return `in ${diffDays}d`;
    return `${-diffDays}d ago`;
  }

  type Rgb = { r: number; g: number; b: number };

  function clampByte(n: number): number {
    return Math.max(0, Math.min(255, Math.round(n)));
  }

  function hexToRgb(hex: string): Rgb | null {
    const h = hex.trim();
    const m = /^#([0-9a-fA-F]{6})$/.exec(h);
    if (!m) return null;
    const v = m[1];
    const r = parseInt(v.slice(0, 2), 16);
    const g = parseInt(v.slice(2, 4), 16);
    const b = parseInt(v.slice(4, 6), 16);
    return { r, g, b };
  }

  function mixRgb(a: Rgb, b: Rgb, t: number): Rgb {
    const tt = Math.max(0, Math.min(1, t));
    return {
      r: clampByte(a.r + (b.r - a.r) * tt),
      g: clampByte(a.g + (b.g - a.g) * tt),
      b: clampByte(a.b + (b.b - a.b) * tt),
    };
  }

  function rgba(c: Rgb, alpha: number): string {
    const a = Math.max(0, Math.min(1, alpha));
    return `rgba(${c.r}, ${c.g}, ${c.b}, ${a})`;
  }

  function getToolboxBg(): string {
    const isDark = document.documentElement.classList.contains('dark');
    const baseColor = isDark ? '#1e293b' : TOOLBOX_BASE_COLOR;
    const base = hexToRgb(baseColor) ?? { r: 255, g: 255, b: 255 };
    const header = hexToRgb(getHeaderColor());
    const mixed = header ? mixRgb(base, header, 0.14) : base;
    return rgba(mixed, 0.8);
  }

  function getHeaderGradient(): string {
    const headerColor = getHeaderColor();
    const base = hexToRgb(headerColor);
    if (!base) return headerColor;
    const lighter = mixRgb(base, { r: 255, g: 255, b: 255 }, 0.45);
    const mid = mixRgb(base, { r: 255, g: 255, b: 255 }, 0.2);
    return `linear-gradient(135deg, ${headerColor} 0%, ${rgba(mid, 1)} 50%, ${rgba(lighter, 1)} 100%)`;
  }

  function openImageModal(id: string, filename: string) {
    modalImage = { id, filename };
  }

  function closeImageModal() {
    modalImage = null;
  }

  function openVideoModal(id: string, filename: string) {
    modalVideo = { id, filename };
  }

  function closeVideoModal() {
    modalVideo = null;
  }

  function closeTypeMenu() {
    showTypeMenu = false;
  }

  function toggleSelection(id: string) {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    selectedIds = next;
  }

  function clearSelection() {
    selectedIds = new Set();
    showDeleteModal = false;
  }

  function toggleHideDoneTasks() {
    hideDoneTasks = !hideDoneTasks;
    clearSelection();
    editingSnipselId.set(null);
  }

  function openDetail(id: string) {
    currentView.set({ type: 'snipsel', id, returnTo: getCurrentUrl() });
  }

  async function toggleTaskDone(item: CollectionItem) {
    if (!$currentCollection) return;
    if (!canWrite()) return;
    if (item.snipsel.type !== 'task') return;

    const nextDone = !item.snipsel.task_done;
    try {
      await api.snipsels.update(item.snipsel_id, { task_done: nextDone });
      collectionItems.update((items) =>
        items.map((i) => (i.snipsel_id === item.snipsel_id ? { ...i, snipsel: { ...i.snipsel, task_done: nextDone } } : i))
      );
      
      // If we marked as done, reload to show potential new recurring tasks
      if (nextDone) {
        await loadItems();
      }
      
      // Set success indicator
      saveStatuses[item.snipsel_id] = 'success';
      setTimeout(() => {
        if (saveStatuses[item.snipsel_id] === 'success') saveStatuses[item.snipsel_id] = null;
      }, 5000);
    } catch (err) {
      console.error('Failed to toggle task:', err);
      // Set error indicator
      saveStatuses[item.snipsel_id] = 'error';
      setTimeout(() => {
        if (saveStatuses[item.snipsel_id] === 'error') saveStatuses[item.snipsel_id] = null;
      }, 5000);
    }
  }
  
  function formatSize(bytes: number) {
    if (bytes < 1024 * 1024) return Math.round(bytes / 1024) + ' KB';
    return Math.round(bytes / (1024 * 1024)) + ' MB';
  }

  function openDetailSelected() {
    if (selectedIds.size === 0) return;
    const id = Array.from(selectedIds)[0];
    if (id) openDetail(id);
  }

  async function uploadAttachmentsSelected(e: Event) {
    const input = e.currentTarget as HTMLInputElement;
    const files = input.files;
    if (!files || files.length === 0) return;
    if (selectedIds.size === 0) {
      input.value = '';
      return;
    }

    const fileArray = Array.from(files);
    
    // Client-side check
    const maxBytes = $currentUser?.max_upload_bytes ?? (10 * 1024 * 1024);
    const oversizedFiles = fileArray.filter(f => f.size > maxBytes);
    if (oversizedFiles.length > 0) {
      errorModal = {
        title: 'Datei zu groß',
        message: `Die folgende(n) Datei(en) überschreiten das Limit von ${formatSize(maxBytes)}:\n${oversizedFiles.map(f => f.name).join(', ')}`
      };
      input.value = '';
      return;
    }

    const hasMedia = fileArray.some((f) => f.type.startsWith('image/') || f.type.startsWith('video/'));

    uploadingAttachments = true;
    isLoading.set(true);
    try {
      const ids = Array.from(selectedIds);
      for (const snipselId of ids) {
        for (const file of fileArray) {
          uploadProgress = { filename: file.name, percent: 0 };
          await api.attachments.upload(snipselId, file, (p) => {
            if (uploadProgress) uploadProgress.percent = p;
          });
        }
        // Auto-switch type to image if any uploaded file is an image
        if (hasMedia) {
          await api.snipsels.update(snipselId, { type: 'image' });
        }
      }
      await loadItems();
      clearSelection();
    } catch (err: any) {
      console.error('Upload failed:', err);
      if (err.error?.code === 'payload_too_large') {
        errorModal = {
          title: 'Datei zu groß',
          message: err.error.message || 'Die Datei überschreitet das Upload-Limit von 10 MB.'
        };
      } else {
        errorModal = {
          title: 'Upload fehlgeschlagen',
          message: err.error?.message || 'Ein unerwarteter Fehler ist aufgetreten.'
        };
      }
    } finally {
      uploadProgress = null;
      uploadingAttachments = false;
      isLoading.set(false);
      input.value = '';
    }
  }

  async function loadTemplates() {
    const res = await api.collections.list();
    templates = res.collections
      .filter((c) => Boolean(c.is_template) && c.access_level === 'owner')
      .map((c) => ({ id: c.id, title: c.title, icon: c.icon }));
  }

  async function loadShareCount() {
    if (!$currentCollection) {
      shareCount = 0;
      return;
    }
    if ($currentCollection.access_level !== 'owner') {
      shareCount = 0;
      return;
    }
    try {
      const res = await api.collections.listShares($currentCollection.id);
      shareCount = res.shares.length;
    } catch {
      shareCount = 0;
    }
  }

  async function insertTemplateSelected(templateCollectionId: string) {
    if (!$currentCollection) return;
    if (!canWrite()) return;
    isLoading.set(true);
    try {
      await api.collections.insertTemplate($currentCollection.id, templateCollectionId);
      await loadItems();
      closeTemplateMenu();
    } finally {
      isLoading.set(false);
    }
  }

  async function loadItems() {
    if (!$currentCollection) return;
    const loadSeq = ++itemsLoadSeq;
    const mutationAtStart = itemsMutationSeq;
    isLoading.set(true);
    try {
      const res = await api.snipsels.list($currentCollection.id);
      if (loadSeq !== itemsLoadSeq) return;
      if (mutationAtStart !== itemsMutationSeq) return;
      collectionItems.set(res.items);
    } finally {
      isLoading.set(false);
    }
  }

  async function loadIncomingMentions() {
    if (!$currentCollection?.list_for_day) {
      incomingMentions = [];
      return;
    }
    incomingMentionsLoading = true;
    try {
      const res = await api.mentions.getIncomingDayMentions($currentCollection.list_for_day);
      incomingMentions = res.snipsels;
    } catch {
      incomingMentions = [];
    } finally {
      incomingMentionsLoading = false;
    }
  }

function startEdit(item: CollectionItem, scrollToBottom: boolean = false) {
    $editingSnipselId = item.snipsel_id;
    editContent = item.snipsel.content_markdown || '';
    editIndent = item.indent;
    
    // Scroll to the new item first
    const el = document.getElementById(`snipsel-${item.snipsel_id}`);
    
    // Only scroll to bottom when creating via nav bar + button
    if (scrollToBottom) {
      setTimeout(() => {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
      }, 100);
      
      // Also scroll the element into view as backup
      el?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
    
    // Focus the textarea with multiple attempts for mobile compatibility
    // Mobile browsers often require focus to be within a user gesture context
    const tryFocus = (attempts: number) => {
      if (attempts <= 0) return;
      textareaRef?.focus();
      autosizeTextarea();
      // If still not focused, try again after a short delay
      if (document.activeElement !== textareaRef) {
        setTimeout(() => tryFocus(attempts - 1), 50);
      }
    };
    
    // Start with requestAnimationFrame for DOM readiness, then try multiple times
    requestAnimationFrame(() => tryFocus(3));
  }

  async function saveEdit() {
    const snipselId = $editingSnipselId;
    if (!snipselId || !$currentCollection) return;
    saving = true;
    try {
      const currentItem = $collectionItems.find((i) => i.snipsel_id === snipselId);
      const hasAttachments = (currentItem?.snipsel.attachments?.length ?? 0) > 0;
      const isEmpty = editContent.trim().length === 0;

      if (isEmpty && !hasAttachments) {
        await api.snipsels.delete($currentCollection.id, snipselId);
        collectionItems.update((items) => items.filter((i) => i.snipsel_id !== snipselId));
        return;
      }

      await api.snipsels.update(snipselId, { content_markdown: isEmpty ? null : editContent });

      if (currentItem && currentItem.indent !== editIndent) {
        const items = $sortedItems.map((i, idx) => ({
          snipsel_id: i.snipsel_id,
          position: idx + 1,
          indent: i.snipsel_id === snipselId ? editIndent : i.indent,
        }));
        await api.snipsels.reorder($currentCollection.id, items);
      }

      await loadItems();
      
      // Set success indicator
      saveStatuses[snipselId] = 'success';
      setTimeout(() => {
        if (saveStatuses[snipselId] === 'success') saveStatuses[snipselId] = null;
      }, 5000);
    } catch (err) {
      console.error('Failed to save snipsel:', err);
      // Set error indicator
      saveStatuses[snipselId] = 'error';
      setTimeout(() => {
        if (saveStatuses[snipselId] === 'error') saveStatuses[snipselId] = null;
      }, 5000);
    } finally {
      saving = false;
      editingSnipselId.set(null);
    }
  }

  function cancelEdit() {
    editingSnipselId.set(null);
  }

  function handleKeydown(e: KeyboardEvent) {
    if (showAutocomplete) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        autocompleteSelectedIndex = Math.min(autocompleteSelectedIndex + 1, suggestions.length - 1);
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        autocompleteSelectedIndex = Math.max(autocompleteSelectedIndex - 1, 0);
        return;
      }
      if (e.key === 'Enter') {
        e.preventDefault();
        const sel = suggestions[autocompleteSelectedIndex];
        if (sel) insertAutocomplete(sel);
        return;
      }
      if (e.key === 'Escape') {
        e.preventDefault();
        showAutocomplete = false;
        suggestions = [];
        return;
      }
    }

    if (e.key === 'Tab') {
      e.preventDefault();
      if (e.shiftKey) {
        editIndent = Math.max(0, editIndent - 1);
      } else {
        editIndent = Math.min(6, editIndent + 1);
      }
    } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      const currentId = $editingSnipselId;
      const currentItem = currentId ? $sortedItems.find((i) => i.snipsel_id === currentId) : null;
      
      saveEdit().then(() => {
        if (currentItem) {
          createSnipselAfterPosition(currentItem.position, currentItem.indent, currentItem.snipsel.type as any);
        }
      });
    } else if (e.key === 'Escape') {
      e.preventDefault();
      cancelEdit();
    }
  }

  async function handleEditInput() {
    autosizeTextarea();
    if (creatingFromTripleEmptyLines) return;

    const el = textareaRef;
    if (!el) return;

    const atEnd = (el.selectionStart ?? 0) === el.value.length && (el.selectionEnd ?? 0) === el.value.length;
    if (atEnd && editContent.endsWith('\n\n\n')) {
      const currentId = $editingSnipselId;
      const currentItem = currentId ? $sortedItems.find((i) => i.snipsel_id === currentId) : null;
      if (!currentId || !currentItem) return;

      creatingFromTripleEmptyLines = true;
      try {
        // Remove the 3 empty lines.
        const nextContent = editContent.slice(0, -3);
        editContent = nextContent;

        // Persist current snipsel update immediately so we don't lose edits when switching focus.
        const contentToSave = nextContent.trim().length === 0 ? null : nextContent;
        itemsMutationSeq += 1;
        await api.snipsels.update(currentId, { content_markdown: contentToSave });
        collectionItems.update((items) =>
          items.map((i) =>
            i.snipsel_id === currentId
              ? { ...i, snipsel: { ...i.snipsel, content_markdown: contentToSave } }
              : i
          )
        );

        await createSnipselAfterPosition(currentItem.position, currentItem.indent);
      } finally {
        creatingFromTripleEmptyLines = false;
      }
    }

    // Autocomplete: detect [[, #, or @ trigger
    const el2 = textareaRef;
    if (el2) {
      const cursor = el2.selectionStart ?? 0;
      const before = editContent.slice(0, cursor);

      const wikiMatch = /\[\[([^\[\]]*)$/.exec(before);
      const tagMatch = /(?:^|\s)#([\p{L}\p{N}_]*)$/u.exec(before);
      const mentionMatch = /(?:^|\s)@([\p{L}\p{N}_]*)$/u.exec(before);

      let q = '';
      let type: 'collection' | 'tag' | 'mention' | null = null;

      if (wikiMatch) {
        q = wikiMatch[1];
        type = 'collection';
      } else if (tagMatch) {
        q = tagMatch[1];
        type = 'tag';
      } else if (mentionMatch) {
        q = mentionMatch[1];
        type = 'mention';
      }

      if (type) {
        autocompleteQuery = q;
        autocompleteSelectedIndex = 0;
        if (autocompleteDebounce) clearTimeout(autocompleteDebounce);
        autocompleteDebounce = setTimeout(async () => {
          try {
            let results: AutocompleteSuggestion[] = [];
            if (type === 'collection') {
              const res = await api.collections.autocomplete(q);
              results = res.collections.map((c) => ({ id: c.id, label: c.title, icon: c.icon, type: 'collection' }));
            } else if (type === 'tag') {
              const res = await api.tags.list('all', q);
              results = res.tags.map((t) => ({ id: t.name, label: t.name, type: 'tag' }));
            } else if (type === 'mention') {
              const res = await api.mentions.list('all', q);
              results = res.mentions.map((m) => ({ id: m.name, label: m.name, type: 'mention' }));
            }
            if (autocompleteQuery !== q) return;
            suggestions = results;
            showAutocomplete = suggestions.length > 0;
          } catch {
            showAutocomplete = false;
          }
        }, 200);
      } else {
        showAutocomplete = false;
        suggestions = [];
      }
    }
  }

  function insertAutocomplete(suggestion: AutocompleteSuggestion) {
    const el = textareaRef;
    if (!el) return;
    const cursor = el.selectionStart ?? 0;
    const before = editContent.slice(0, cursor);
    const after = editContent.slice(cursor);

    let newBefore = before;
    if (suggestion.type === 'collection') {
      newBefore = before.replace(/\[\[([^\[\]]*)$/, `[[${suggestion.label}]]`);
    } else if (suggestion.type === 'tag') {
      newBefore = before.replace(/#([\p{L}\p{N}_]*)$/u, `#${suggestion.label} `);
    } else if (suggestion.type === 'mention') {
      newBefore = before.replace(/@([\p{L}\p{N}_]*)$/u, `@${suggestion.label} `);
    }

    editContent = newBefore + after;
    showAutocomplete = false;
    suggestions = [];
    setTimeout(() => {
      el.selectionStart = el.selectionEnd = newBefore.length;
      el.focus();
    }, 0);
  }

  async function handlePaste(e: ClipboardEvent) {
    const items = e.clipboardData?.items;
    if (!items) return;

    let mediaFile: File | null = null;
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.startsWith('image/') || items[i].type.startsWith('video/')) {
        const blob = items[i].getAsFile();
        if (blob) {
          const isImage = items[i].type.startsWith('image/');
          const extension = items[i].type.split('/')[1] || (isImage ? 'png' : 'mp4');
          const prefix = isImage ? 'pasted-image' : 'pasted-video';
          const filename = `${prefix}-${Date.now()}.${extension}`;
          mediaFile = new File([blob], filename, { type: items[i].type });
          break;
        }
      }
    }

    if (mediaFile) {
      const snipselId = $editingSnipselId;
      if (!snipselId) return;
      
      e.preventDefault();
      
      uploadingAttachments = true;
      try {
        await api.attachments.upload(snipselId, mediaFile);
        // Auto-switch type to image (which now also means media in our UI)
        await api.snipsels.update(snipselId, { type: 'image' });
        await loadItems();
      } catch (err) {
        console.error('Failed to upload pasted media:', err);
      } finally {
        uploadingAttachments = false;
      }
    }
  }

  function autosizeTextarea() {
    const el = textareaRef;
    if (!el) return;
    el.style.height = '0px';
    el.style.height = `${el.scrollHeight}px`;
  }

  function handleEditFocusOut(e: FocusEvent) {
    if (creatingFromTripleEmptyLines) return;
    const related = e.relatedTarget as Node | null;
    if (related && editContainerRef?.contains(related)) return;
    showAutocomplete = false;
    suggestions = [];
    if (!saving) saveEdit();
  }

  async function createSnipsel() {
    if (!$currentCollection) return;
    if (!canWrite()) return;
    
    // Get indent from last snipsel
    let indent = 0;
    const items = $sortedItems;
    if (items.length > 0) {
      const lastItem = items[items.length - 1];
      indent = lastItem.indent ?? 0;
    }
    
    isLoading.set(true);
    try {
      let geo:
        | { geo_lat: number; geo_lng: number; geo_accuracy_m?: number }
        | null = null;
      try {
        geo = await new Promise((resolve) => {
          if (!('geolocation' in navigator)) return resolve(null);
          navigator.geolocation.getCurrentPosition(
            (pos) =>
              resolve({
                geo_lat: pos.coords.latitude,
                geo_lng: pos.coords.longitude,
                geo_accuracy_m: pos.coords.accuracy,
              }),
            () => resolve(null),
            { enableHighAccuracy: false, maximumAge: 60_000, timeout: 1500 }
          );
        });
      } catch {
        geo = null;
      }

      const res = await api.snipsels.create($currentCollection.id, {
        type: $currentCollection.default_snipsel_type || 'text',
        indent: indent,
        ...(geo ?? {}),
      });

      itemsMutationSeq += 1;
      collectionItems.update((items) => [...items, res.item]);
      startEdit(res.item, true);  // Scroll to bottom when creating via nav bar
    } finally {
      isLoading.set(false);
    }
  }

  async function createSnipselAfterPosition(position: number, indent: number, type?: 'text' | 'image' | 'attachment' | 'task') {
    if (!$currentCollection) return;
    if (!canWrite()) return;
    isLoading.set(true);
    try {
      let geo:
        | { geo_lat: number; geo_lng: number; geo_accuracy_m?: number }
        | null = null;
      try {
        geo = await new Promise((resolve) => {
          if (!('geolocation' in navigator)) return resolve(null);
          navigator.geolocation.getCurrentPosition(
            (pos) =>
              resolve({
                geo_lat: pos.coords.latitude,
                geo_lng: pos.coords.longitude,
                geo_accuracy_m: pos.coords.accuracy,
              }),
            () => resolve(null),
            { enableHighAccuracy: false, maximumAge: 60_000, timeout: 1500 }
          );
        });
      } catch {
        geo = null;
      }

      const res = await api.snipsels.create($currentCollection.id, {
        type: type || $currentCollection.default_snipsel_type || 'text',
        indent: indent,
        ...(geo ?? {}),
      });

      const newId = res.item.snipsel_id;

      const list = [...$sortedItems];
      const idx = list.findIndex((i) => i.position === position);
      const insertAt = idx >= 0 ? idx + 1 : list.length;
      const next = [...list.slice(0, insertAt), { ...res.item, indent }, ...list.slice(insertAt)];

      const reordered = next.map((i, index) => ({ ...i, position: index + 1 }));
      collectionItems.set(reordered);

      // Mark mutation so any in-flight loadItems doesn't overwrite local optimistic state.
      itemsMutationSeq += 1;

      const payload = reordered.map((i) => ({ snipsel_id: i.snipsel_id, position: i.position, indent: i.indent }));
      await api.snipsels.reorder($currentCollection.id, payload);

      const createdItem = reordered.find((i) => i.snipsel_id === newId);
      if (createdItem) startEdit(createdItem);

      // Ensure we don't immediately auto-delete the newly created empty snipsel
      // due to a focus-out save on the previous snipsel.
      itemsMutationSeq += 1;
    } finally {
      isLoading.set(false);
    }
  }

  async function createSnipselFromUserGesture() {
    // On mobile, we need to focus within the user gesture context
    // The focus proxy is a hidden input that triggers the keyboard
    focusProxyRef?.focus();
    await createSnipsel();
    // Focus the actual textarea now that it exists
    textareaRef?.focus();
    focusProxyRef?.blur();
  }

  // Register callback for mobile keyboard support (called from App.svelte)
  $effect(() => {
    createSnipselCallback.set(createSnipselFromUserGesture);
    return () => createSnipselCallback.set(null);
  });

  // Handle create snipsel on load (from nav bar + button)
  // Triggers when collection is loaded, regardless of whether it has items
  $effect(() => {
    if ($createSnipselOnLoad && $currentCollection) {
      createSnipselOnLoad.set(false);
      focusProxyRef?.focus();
      createSnipsel().then(() => {
        focusProxyRef?.blur();
      });
    }
  });

  $effect(() => {
    if ($newSnipselRequest > 0 && $currentCollection) {
      // Consume the request so we don't create multiple.
      newSnipselRequest.set(0);
      clearSelection();
      closeTypeMenu();
      closeTemplateMenu();
      // Focus proxy immediately within user gesture context (before any await)
      // This opens the keyboard on mobile
      focusProxyRef?.focus();
      // Ensure we start from the correct collection's list before optimistic append.
      loadItems().then(async () => {
        await createSnipsel();
        // The startEdit function will handle focusing the textarea
        focusProxyRef?.blur();
      });
    }
  });

  $effect(() => {
    loadTemplates();
  });

  $effect(() => {
    loadShareCount();
  });

  $effect(() => {
    snipselsSelected.set(selectedIds.size);
    return () => snipselsSelected.set(0);
  });

  function deleteSelected() {
    if (!$currentCollection) return;
    if (!canWrite()) return;
    if (selectedIds.size === 0) return;
    showDeleteModal = true;
  }

  function cancelDeleteSelected() {
    showDeleteModal = false;
  }

  async function confirmDeleteSelected() {
    if (!$currentCollection) return;
    showDeleteModal = false;
    isLoading.set(true);
    try {
      const ids = Array.from(selectedIds);
      for (const id of ids) {
        await api.snipsels.delete($currentCollection.id, id);
      }
      collectionItems.update((items) => items.filter((i) => !selectedIds.has(i.snipsel_id)));
      clearSelection();
    } finally {
      isLoading.set(false);
    }
  }

  async function setTypeSelected(nextType: 'text' | 'image' | 'attachment' | 'task') {
    if (!canWrite()) return;
    if (selectedIds.size === 0) return;

    isLoading.set(true);
    try {
      const ids = Array.from(selectedIds);
      for (const id of ids) {
        await api.snipsels.update(id, { type: nextType });
      }
      await loadItems();
      closeTypeMenu();
    } finally {
      isLoading.set(false);
    }
  }

  async function toggleCardViewSelected() {
    if (!canWrite()) return;
    if (selectedIds.size === 0) return;

    const firstId = Array.from(selectedIds)[0];
    const firstItem = $collectionItems.find(item => item.snipsel_id === firstId);
    const newValue = firstItem ? !(firstItem.snipsel.card_view ?? true) : true;

    isLoading.set(true);
    try {
      const ids = Array.from(selectedIds);
      for (const id of ids) {
        await api.snipsels.update(id, { card_view: newValue });
      }
      await loadItems();
      closeTypeMenu();
    } finally {
      isLoading.set(false);
    }
  }

  function getSelectedCardView(): boolean {
    const firstId = Array.from(selectedIds)[0];
    const firstItem = $collectionItems.find(item => item.snipsel_id === firstId);
    return firstItem?.snipsel.card_view ?? true;
  }

  function getEditingSnipselCardView(): boolean {
    const editingItem = $sortedItems.find(item => item.snipsel_id === $editingSnipselId);
    return editingItem?.snipsel.card_view ?? true;
  }

  function openCollectionModal(mode: 'copy' | 'move' | 'link') {
    if (!$currentCollection) return;
    if (!canWrite()) return;
    if (selectedIds.size === 0) return;
    
    collectionModalMode = mode;
    if (mode === 'copy') {
      collectionModalTitle = `Copy ${selectedIds.size} ${selectedIds.size === 1 ? 'snipsel' : 'snipsels'}`;
    } else if (mode === 'move') {
      collectionModalTitle = `Move ${selectedIds.size} ${selectedIds.size === 1 ? 'snipsel' : 'snipsels'}`;
    } else {
      collectionModalTitle = `Link ${selectedIds.size} ${selectedIds.size === 1 ? 'snipsel' : 'snipsels'}`;
    }
    showCollectionModal = true;
  }

  async function handleCollectionSelected(targetCollectionId: string) {
    if (!$currentCollection) return;
    showCollectionModal = false;
    isLoading.set(true);
    
    try {
      const ids = Array.from(selectedIds);
      let newItems = [];
      let removedItems = new Set<string>();

      for (const id of ids) {
        if (collectionModalMode === 'copy') {
          const res = await api.snipsels.copy(targetCollectionId, id);
          if (targetCollectionId === $currentCollection.id) {
             newItems.push(res.item);
          }
        } else if (collectionModalMode === 'link') {
          const res = await api.snipsels.reference(targetCollectionId, id);
          if (targetCollectionId === $currentCollection.id) {
             newItems.push(res.item);
          }
        } else if (collectionModalMode === 'move') {
          await api.snipsels.reference(targetCollectionId, id);
          if (targetCollectionId !== $currentCollection.id) {
            await api.snipsels.delete($currentCollection.id, id);
            removedItems.add(id);
          }
        }
      }

      if (newItems.length > 0) {
        collectionItems.update((items) => [...items, ...newItems]);
      }
      if (removedItems.size > 0) {
        collectionItems.update((items) => items.filter((item) => !removedItems.has(item.snipsel_id)));
      }

      clearSelection();
      // Force reload to get correct order & refs if we added locally
      if (newItems.length > 0 || removedItems.size > 0) {
        await loadItems();
      }
    } catch (err) {
      console.error(`Failed to ${collectionModalMode} snipsels:`, err);
    } finally {
      isLoading.set(false);
    }
  }

  async function createCollectionFromSnipsel() {
    if (!$currentCollection || !canWrite() || selectedIds.size !== 1) return;
    
    const baseId = Array.from(selectedIds)[0];
    const items = $sortedItems;
    const baseIdx = items.findIndex(i => i.snipsel_id === baseId);
    if (baseIdx === -1) return;
    
    const baseItem = items[baseIdx];
    const baseIndent = baseItem.indent;
    
    // Find children
    const children: CollectionItem[] = [];
    for (let i = baseIdx + 1; i < items.length; i++) {
      if (items[i].indent > baseIndent) {
        children.push(items[i]);
      } else {
        break;
      }
    }
    
    isLoading.set(true);
    try {
      // 1. Create new collection
      const title = baseItem.snipsel.content_markdown?.split('\n')[0].trim() || 'New Collection';
      const createRes = await api.collections.create({ title });
      const newCol = createRes.collection;
      
      // 2. Move children and normalize indent
      // Calculate min indent of children to bring it to 0
      const minChildIndent = children.length > 0 ? Math.min(...children.map(c => c.indent)) : 0;
      const indentOffset = minChildIndent;
      
      for (const child of children) {
        await api.snipsels.reference(newCol.id, child.snipsel_id, Math.max(0, child.indent - indentOffset));
        await api.snipsels.delete($currentCollection.id, child.snipsel_id);
      }
      
      // 3. Update original snipsel with wiki link
      await api.snipsels.update(baseId, { 
        content_markdown: `[[${newCol.title}]]` 
      });
      
      // 4. Refresh
      clearSelection();
      await loadItems();
    } catch (err) {
      console.error('Failed to create collection from snipsel:', err);
    } finally {
      isLoading.set(false);
    }
  }

  async function adjustIndentSelected(delta: number) {
    if (!$currentCollection) return;
    if (!canWrite()) return;
    if (selectedIds.size === 0) return;

    const current = $sortedItems;
    const updated = current.map((i) => {
      if (!selectedIds.has(i.snipsel_id)) return i;
      const indent = Math.max(0, Math.min(6, i.indent + delta));
      return { ...i, indent };
    });

    const payload = updated.map((i, idx) => ({
      snipsel_id: i.snipsel_id,
      position: idx + 1,
      indent: i.indent,
    }));

    await api.snipsels.reorder($currentCollection.id, payload);
    collectionItems.set(updated.map((i, idx) => ({ ...i, position: idx + 1 })));
  }

  async function setIndentSelected(indent: number) {
    if (!$currentCollection) return;
    if (!canWrite()) return;
    if (selectedIds.size === 0) return;

    const nextIndent = Math.max(0, Math.min(6, indent));
    const current = $sortedItems;
    const updated = current.map((i) => {
      if (!selectedIds.has(i.snipsel_id)) return i;
      return { ...i, indent: nextIndent };
    });

    const payload = updated.map((i, idx) => ({
      snipsel_id: i.snipsel_id,
      position: idx + 1,
      indent: i.indent,
    }));

    await api.snipsels.reorder($currentCollection.id, payload);
    collectionItems.set(updated.map((i, idx) => ({ ...i, position: idx + 1 })));
  }

  async function moveSelectedToEdge(edge: 'top' | 'bottom') {
    if (!$currentCollection) return;
    if (!canWrite()) return;
    if (selectedIds.size === 0) return;

    const list = [...$sortedItems];
    const selected = list.filter((i) => selectedIds.has(i.snipsel_id));
    const rest = list.filter((i) => !selectedIds.has(i.snipsel_id));
    const next = edge === 'top' ? [...selected, ...rest] : [...rest, ...selected];

    const payload = next.map((i, index) => ({
      snipsel_id: i.snipsel_id,
      position: index + 1,
      indent: i.indent,
    }));

    await api.snipsels.reorder($currentCollection.id, payload);
    collectionItems.set(next.map((i, index) => ({ ...i, position: index + 1 })));
  }

  function longPress(onLongPress: () => void, onShortPress: () => void, ms = 450) {
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

        // Make pointerup reliable even if the finger drifts slightly.
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
        // If we already handled via pointer events, suppress the synthetic click.
        if (handledByPointer) {
          e.preventDefault();
          e.stopPropagation();
          handledByPointer = false;
          return;
        }

        // Keyboard / non-pointer activation fallback.
        onShortPress();
      },
      oncontextmenu: (e: MouseEvent) => {
        if (firedLong) e.preventDefault();
      },
    };
  }

  const lpMoveTop = longPress(
    () => void moveSelectedToEdge('top'),
    () => void moveSelected(-1)
  );
  const lpMoveBottom = longPress(
    () => void moveSelectedToEdge('bottom'),
    () => void moveSelected(1)
  );
  const lpOutdentToZero = longPress(
    () => void setIndentSelected(0),
    () => void adjustIndentSelected(-1)
  );

  async function moveSelected(dir: -1 | 1) {
    if (!$currentCollection) return;
    if (!canWrite()) return;
    if (selectedIds.size === 0) return;
    const list = [...$sortedItems];

    const indices = list
      .map((i, idx) => ({ id: i.snipsel_id, idx }))
      .filter((x) => selectedIds.has(x.id))
      .map((x) => x.idx);

    if (dir === -1) {
      for (const idx of indices.sort((a, b) => a - b)) {
        if (idx === 0) continue;
        const tmp = list[idx - 1];
        list[idx - 1] = list[idx];
        list[idx] = tmp;
      }
    } else {
      for (const idx of indices.sort((a, b) => b - a)) {
        if (idx === list.length - 1) continue;
        const tmp = list[idx + 1];
        list[idx + 1] = list[idx];
        list[idx] = tmp;
      }
    }

    const payload = list.map((i, index) => ({
      snipsel_id: i.snipsel_id,
      position: index + 1,
      indent: i.indent,
    }));

    await api.snipsels.reorder($currentCollection.id, payload);
    collectionItems.set(list.map((i, index) => ({ ...i, position: index + 1 })));
  }

  function renderMarkdown(text: string | null): string {
    if (!text) return '';
    const html = md.render(text.trim()).trim();
    const tokenBg = getToolboxBg();
    const tokenFg = getHeaderColor();
    return html
      .replace(
        /(^|[^\p{L}\p{N}_])(#[A-Za-z\p{L}][\p{L}\p{N}_-]*|@[A-Za-z\p{L}][\p{L}\p{N}_-]*)/gu,
        (m, p1, token) =>
          `${p1}<mark class="snip-token" style="background-color:${tokenBg}; color:${tokenFg}">${token}</mark>`
      )
      .replace(/==([^=]+)==/g, `<mark style="background-color:${tokenBg}; border-radius: 0.25rem; padding: 0 0.125rem">$1</mark>`)
      .replace(/<a /g, `<a style="color:${tokenFg}; text-decoration:underline" target="_blank" rel="noopener noreferrer" `)
      .replace(/<blockquote>/g, `<blockquote style="border-left: 3px solid ${tokenFg}; background-color:${tokenBg}; margin: 0.25rem 0; padding: 0.25rem 0.75rem; border-radius: 0 0.25rem 0.25rem 0; opacity: 0.9;">`)
      .replace(/>\s+</g, '><');
  }

  function renderWithWikiLinks(content: string, refs: Array<{title: string; collection_id: string}> | undefined): string {
    let html = renderMarkdown(content);
    const refMap = new Map<string, string>();
    if (refs) {
      for (const r of refs) {
        refMap.set(r.title.toLowerCase(), r.collection_id);
      }
    }
    const tokenBg = getToolboxBg();
    const tokenFg = getHeaderColor();
    html = html.replace(/\[\[([^\]]+)\]\]/g, (_match, title: string) => {
      // Unescape HTML entities (like &amp;) because markdown-it escapes them
      const unescapedTitle = title
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'");

      const collectionId = refMap.get(unescapedTitle.toLowerCase());
      if (collectionId) {
        return `<a class="snip-token cursor-pointer" style="background-color:${tokenBg}; color:${tokenFg}" data-collection-id="${collectionId}">[[${title}]]</a>`;
      }
      return `<span class="text-slate-400 text-xs">[[${title}]]</span>`;
    });
    return html;
  }

  function isImageAttachment(a: Attachment): boolean {
    return Boolean(a.mime_type?.startsWith('image/') || a.has_thumbnail);
  }

  function isDoneTask(item: CollectionItem): boolean {
    return item.snipsel.type === 'task' && Boolean(item.snipsel.task_done);
  }

  function visibleItems(items: CollectionItem[]): CollectionItem[] {
    let filtered = items;
    if (hideDoneTasks) {
      filtered = filtered.filter((i) => !isDoneTask(i));
    }

    const result: CollectionItem[] = [];
    let skipUntilIndent: number | null = null;

    for (let i = 0; i < filtered.length; i++) {
      const item = filtered[i];
      if (skipUntilIndent !== null) {
        if (item.indent > skipUntilIndent) {
          continue;
        } else {
          skipUntilIndent = null;
        }
      }

      result.push(item);

      const nextItem = filtered[i + 1];
      const itemsHasChildren = nextItem && nextItem.indent > item.indent;

      if (itemsHasChildren && !expandedSnipsels.has(item.snipsel_id)) {
        skipUntilIndent = item.indent;
      }
    }
    return result;
  }

  function hiddenDoneCount(items: CollectionItem[]): number {
    if (!hideDoneTasks) return 0;
    return items.filter((i) => isDoneTask(i)).length;
  }

  $effect(() => {
    const nextId = $currentCollection?.id ?? null;
    if (nextId && nextId !== lastCollectionId) {
      // Initialize hideDoneTasks based on collection setting
      if ($currentCollection) {
        hideDoneTasks = !$currentCollection.show_completed_tasks;
      }
      lastCollectionId = nextId;
      collectionItems.set([]);
      lastAnchorKey = null;
      anchorHighlightId = null;
      selectedIds = new Set();
      editingSnipselId.set(null);

      loadItems();
      loadIncomingMentions();
    }
  });

  $effect(() => {
    const a = $collectionAnchor;
    const c = $currentCollection;
    if (!a || !c) return;
    if (a.collectionId !== c.id) return;

    const key = `${a.collectionId}:${a.snipselId ?? ''}:${a.pos ?? ''}`;
    if (key === lastAnchorKey) return;

    const target = a.snipselId
      ? $sortedItems.find((i) => i.snipsel_id === a.snipselId)
      : typeof a.pos === 'number'
        ? $sortedItems.find((i) => i.position === a.pos)
        : null;

    if (!target) return;

    lastAnchorKey = key;
    anchorHighlightId = target.snipsel_id;

    setTimeout(() => {
      const el = document.getElementById(`snipsel-${target.snipsel_id}`);
      el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      setTimeout(() => {
        if (anchorHighlightId === target.snipsel_id) anchorHighlightId = null;
      }, 10000);
    }, 0);
  });

  function taskProgress() {
    const tasks = $sortedItems.filter((i) => i.snipsel.type === 'task');
    const total = tasks.length;
    const done = tasks.filter((i) => Boolean(i.snipsel.task_done)).length;
    return { total, done, ratio: total > 0 ? done / total : 0 };
  }

  function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  $effect(() => {
    const onScroll = () => {
      showScrollTop = window.scrollY > 300;
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  });

  function formatModifiedAt(iso: string) {
    const d = new Date(iso);
    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    const yesterdayStart = todayStart - 86400000;
    const itemDate = new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();

    const timeStr = d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });

    if (itemDate === todayStart) {
      return timeStr;
    }
    if (itemDate === yesterdayStart) {
      return `Yesterday, ${timeStr}`;
    }
    return d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
  }
  function getDeezerLink(text: string | null) {
    if (!text) return null;
    // Standard link
    const stdMatch = text.match(/https?:\/\/(?:www\.)?deezer\.com\/(track|album|artist)\/(\d+)/);
    if (stdMatch) {
      return { type: stdMatch[1] as 'track' | 'album' | 'artist', id: stdMatch[2], url: stdMatch[0] };
    }
    // Short link
    const shortMatch = text.match(/https?:\/\/link\.deezer\.com\/s\/[A-Za-z0-9]+/);
    if (shortMatch) {
      return { type: null, id: null, url: shortMatch[0] };
    }
    return null;
  }

  function getYouTubeLink(text: string | null) {
    if (!text) return null;
    const match = text.match(/https?:\/\/(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|v\/|shorts\/)|youtu\.be\/)([A-Za-z0-9_-]{11})(?:[^\s\)]*)/);
    if (match) {
      return { id: match[1], url: match[0] };
    }
    return null;
  }

  function getMapLink(text: string | null) {
    if (!text) return null;
    // Short links that need server-side resolution (no coords in URL)
    const googleShortMatch = text.match(/https?:\/\/maps\.app\.goo\.gl\/[A-Za-z0-9]+/);
    const appleShortMatch = text.match(/https?:\/\/maps\.apple(?:\.com)?\/p\/[^\s]*/);
    if (googleShortMatch || appleShortMatch) {
      const match = googleShortMatch || appleShortMatch;
      return { url: match![0] };
    }
    // Google Maps patterns (full URL)
    const googleAtMatch = text.match(/https?:\/\/(?:www\.)?google\.com\/maps\/[^\s]*@(-?\d+\.\d+),(-?\d+\.\d+)[^\s]*/);
    const googleQMatch = text.match(/https?:\/\/(?:www\.)?google\.com\/maps\?[^\s]*[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)[^\s]*/);
    const mapsGoogleQMatch = text.match(/https?:\/\/maps\.google\.[a-z]+\/?\?[^\s]*[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)[^\s]*/);
    // Apple Maps patterns (full URL)
    const appleLlMatch = text.match(/https?:\/\/(?:www\.)?maps\.apple\.com\/?[^\s]*[?&]ll=(-?\d+\.\d+),(-?\d+\.\d+)[^\s]*/);
    const appleQMatch = text.match(/https?:\/\/(?:www\.)?maps\.apple\.com\/?[^\s]*[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)[^\s]*/);
    const appleCenterMatch = text.match(/https?:\/\/(?:www\.)?maps\.apple\.com\/?[^\s]*[?&]center=(-?\d+\.\d+),(-?\d+\.\d+)[^\s]*/);
    const appleCoordMatch = text.match(/https?:\/\/(?:www\.)?maps\.apple\.com\/?[^\s]*[?&]coordinate=(-?\d+\.\d+),(-?\d+\.\d+)[^\s]*/);
    
    if (googleAtMatch) {
      return { lat: parseFloat(googleAtMatch[1]), lng: parseFloat(googleAtMatch[2]), url: googleAtMatch[0] };
    }
    if (googleQMatch) {
      return { lat: parseFloat(googleQMatch[1]), lng: parseFloat(googleQMatch[2]), url: googleQMatch[0] };
    }
    if (mapsGoogleQMatch) {
      return { lat: parseFloat(mapsGoogleQMatch[1]), lng: parseFloat(mapsGoogleQMatch[2]), url: mapsGoogleQMatch[0] };
    }
    if (appleLlMatch) {
      return { lat: parseFloat(appleLlMatch[1]), lng: parseFloat(appleLlMatch[2]), url: appleLlMatch[0] };
    }
    if (appleQMatch) {
      return { lat: parseFloat(appleQMatch[1]), lng: parseFloat(appleQMatch[2]), url: appleQMatch[0] };
    }
    if (appleCenterMatch) {
      return { lat: parseFloat(appleCenterMatch[1]), lng: parseFloat(appleCenterMatch[2]), url: appleCenterMatch[0] };
    }
    if (appleCoordMatch) {
      return { lat: parseFloat(appleCoordMatch[1]), lng: parseFloat(appleCoordMatch[2]), url: appleCoordMatch[0] };
    }
    return null;
  }

  function getGenericLink(text: string | null) {
    if (!text) return null;
    if (getDeezerLink(text)) return null;
    if (getYouTubeLink(text)) return null;
    if (getMapLink(text)) return null;
    const trimmed = text.trim();
    const urlMatch = trimmed.match(/^(https?:\/\/\S+)$/);
    if (urlMatch) {
      return { url: urlMatch[1] };
    }
    return null;
  }

  function stripMediaLinks(text: string | null): string {
    if (!text) return '';
    let result = text;
    
    const dz = getDeezerLink(text);
    if (dz) result = result.replace(dz.url, '');
    
    const yt = getYouTubeLink(text);
    if (yt) result = result.replace(yt.url, '');
    
    const ml = getMapLink(text);
    if (ml) result = result.replace(ml.url, '');
    
    const gl = getGenericLink(text);
    if (gl) result = result.replace(gl.url, '');
    
    return result.trim();
  }
</script>


<div class="space-y-3"
  role="none"
  ontouchstart={handleSwipeTouchStart}
  ontouchmove={handleSwipeTouchMove}
  ontouchend={handleSwipeTouchEnd}
>
  <!-- Pull-to-reload indicator -->
  {#if pullActive || pullReloading}
    <div
      class="pointer-events-none flex flex-col items-center justify-center overflow-hidden transition-all duration-200"
      style="height: {pullReloading ? 52 : pullDeltaY}px; opacity: {pullReloading ? 1 : Math.min(1, pullDeltaY / 30)};"
    >
      <div
        class="flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white shadow-md dark:border-white/10 dark:bg-slate-900"
        style="transform: scale({pullReloading ? 1 : 0.6 + 0.4 * Math.min(1, pullDeltaY / PULL_THRESHOLD)});"
      >
        {#if pullReloading || pullTriggered}
          <!-- Spinning loader -->
          <Loader2 label="" size={20} className="animate-spin" color={getHeaderColor()} />
        {:else}
          <!-- Arrow down -->
          <ArrowDown label="" size={20} className="transition-transform duration-150" color={getHeaderColor()} style={`transform: rotate(${Math.min(180, pullDeltaY * 180 / PULL_THRESHOLD)}deg)`} />
        {/if}
      </div>
    </div>
  {/if}
  <input
    bind:this={focusProxyRef}
    class="pointer-events-none absolute left-0 top-0 h-0 w-0 opacity-0"
    tabindex="-1"
    aria-hidden="true"
  />

  <div class="relative">
    <div class="rounded-xl border border-slate-200 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900">
      <div
        class="relative h-28 w-full rounded-t-[calc(0.75rem-1px)] overflow-hidden dark:brightness-75"
        style="background: {$currentCollection?.header_image_url ? getHeaderColor() : getHeaderGradient()}"
      >
        {#if $currentCollection?.header_image_url}
          <div 
            class="absolute inset-0 bg-cover"
            style="background-image: url('{$currentCollection.header_image_url}{ $currentCollection.header_image_url.startsWith('/api/attachments/') ? '/thumbnail' : '' }'); background-position: {$currentCollection.header_image_x_position || '50%'} {$currentCollection.header_image_position || '50%'}; transform: scale({$currentCollection.header_image_zoom || 1.0}) translate({(50 - (parseFloat($currentCollection.header_image_x_position || '50') || 50)) * (1 - 1 / ($currentCollection.header_image_zoom || 1.0))}%, {(50 - (parseFloat($currentCollection.header_image_position || '50') || 50)) * (1 - 1 / ($currentCollection.header_image_zoom || 1.0))}%)"
          ></div>
        {/if}
      </div>

      <div class="relative px-4 py-3">
        <div class="absolute left-4 top-0 -translate-y-1/2 z-10">
          <button
            class="grid h-16 w-16 place-items-center rounded-xl border border-slate-200 bg-white shadow-sm hover:bg-slate-50 transition-colors disabled:hover:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 dark:border-white/10 dark:bg-slate-900 dark:hover:bg-white/5 dark:disabled:hover:bg-slate-900"
            type="button"
            onclick={() => canWrite() && (showEmojiPicker = !showEmojiPicker)}
            disabled={!canWrite()}
            aria-label="Change collection icon"
          >
            <span class="text-4xl leading-none">{$currentCollection?.icon}</span>
          </button>

          {#if showEmojiPicker}
            <div 
              class="absolute left-0 top-full mt-2 z-50 w-64 p-2 rounded-xl border border-slate-200 bg-white/95 shadow-xl ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/95 dark:ring-white/10"
              onfocusout={(e) => {
                const related = e.relatedTarget as Node | null;
                if (related instanceof HTMLElement && e.currentTarget.contains(related)) return;
                showEmojiPicker = false;
              }}
            >
              <div class="grid grid-cols-8 gap-1 overflow-y-auto max-h-48 p-1 text-center">
                {#each commonEmojis as emoji}
                  <button
                    class="grid h-7 w-7 place-items-center rounded hover:bg-slate-100 transition-colors text-lg dark:hover:bg-white/10"
                    type="button"
                    onclick={() => updateIcon(emoji)}
                  >
                    {emoji}
                  </button>
                {/each}
              </div>
              <div class="mt-2 border-t border-slate-100 pt-2 px-1 dark:border-white/5">
                <input
                  type="text"
                  placeholder="Custom emoji..."
                  maxlength="4"
                  class="w-full rounded border border-slate-200 bg-white px-2 py-1 text-sm outline-none focus:ring-2 focus:ring-indigo-500/20 dark:border-white/10 dark:bg-slate-800 dark:text-slate-100"
                  onkeydown={(e) => {
                    if (e.key === 'Enter') {
                      const val = (e.currentTarget as HTMLInputElement).value.trim();
                      if (val) updateIcon(val);
                    } else if (e.key === 'Escape') {
                      showEmojiPicker = false;
                    }
                  }}
                />
              </div>
            </div>
          {/if}
        </div>

        {#if taskProgress().total > 0}
          <button
            class="absolute left-[5.5rem] right-4 top-0 -translate-y-1/2 rounded-full border border-slate-200 bg-white/80 p-1 shadow-sm backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80"
            type="button"
            aria-label="Toggle done tasks"
            title={hideDoneTasks ? 'Show done tasks' : 'Hide done tasks'}
            onclick={toggleHideDoneTasks}
            in:fly={{ y: -10, duration: 200 }}
            out:fly={{ y: -10, duration: 150 }}
          >
            <div class="h-2 w-full overflow-hidden rounded-full bg-black/10 dark:bg-white/10">
              <div
                class="h-full rounded-full transition-all duration-300 ease-out"
                style={`width: ${Math.round(taskProgress().ratio * 100)}%; background-color: ${getHeaderColor()}`}
              ></div>
            </div>
          </button>
        {/if}

        <button
          class="pl-20 text-lg font-semibold hover:underline dark:text-slate-100"
          type="button"
          onclick={() => $currentCollection && currentView.set({ type: 'collection_settings', id: $currentCollection.id })}
        >
          {$currentCollection?.title}
        </button>

      </div>
    </div>
    {#if $currentCollection}
      <div class="mt-1 flex items-center justify-between px-1 text-[10px] text-slate-400">
        <div class="flex items-center" style="padding-left: 1.625rem">
          {#if collapsibleParentIds.size > 0}
            <button
              type="button"
              class="al-icon-wrapper grid h-6 w-6 place-items-center text-slate-400 hover:text-slate-600 transition-all focus:outline-none"
              onclick={toggleAllExpanded}
              title={allExpanded ? 'Collapse All' : 'Expand All'}
            >
              {#if allExpanded}
                <ChevronsUp label="" size={14} strokeWidth={2} />
              {:else}
                <ChevronsDown label="" size={14} strokeWidth={2} />
              {/if}
            </button>
          {/if}
        </div>
        <div class="flex items-center gap-1.5 ml-auto">
          <span>Last modified: {formatModifiedAt($currentCollection.modified_at)}</span>
          {#if $currentCollection.modified_by_username && $currentCollection.modified_by_id !== $currentUser?.id}
            <span>by {$currentCollection.modified_by_username}</span>
          {/if}
        </div>
      </div>
    {/if}

    {#if $currentCollection}
      {@const level = $currentCollection.access_level}
      {@const showSharedByYou = level === 'owner' && shareCount > 0}
      {@const showSharedWithYou = level === 'read' || level === 'write'}
      {@const showStatusPill = Boolean(
        $currentCollection.is_favorite ||
          showSharedByYou ||
          showSharedWithYou ||
          $currentCollection.is_template ||
          $currentCollection.archived ||
          $currentCollection.is_passcode_protected
      )}

      {#if showStatusPill}
        <div
          class="absolute right-4 top-0 z-5 -translate-y-1/2 flex items-center gap-3 rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-lg text-slate-800 shadow-sm backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:text-slate-200"
          aria-label="Collection status"
        >
          {#if $currentCollection.is_favorite}
            <span class="al-icon-wrapper" title="Favorite">
              <Heart label="" size={16} className="text-slate-700 fill-current dark:text-slate-300" />
            </span>
          {/if}

          {#if showSharedByYou}
            <span class="al-icon-wrapper" title="Shared by you">
              <ArrowUp label="" size={16} className="text-slate-700 dark:text-slate-300" strokeWidth={2} />
            </span>
          {/if}
          {#if showSharedWithYou}
            <span class="al-icon-wrapper" title="Shared with you">
              <ArrowDown label="" size={16} className="text-slate-700 dark:text-slate-300" strokeWidth={2} />
            </span>
          {/if}

          {#if $currentCollection.is_template}
            <span class="al-icon-wrapper" title="Template">
              <LayoutTemplate label="" size={16} className="text-slate-700 dark:text-slate-300" strokeWidth={2} />
            </span>
          {/if}

          {#if $currentCollection.archived}
            <span class="al-icon-wrapper" title="Archived">
              <Archive label="" size={16} className="text-slate-700 dark:text-slate-300" strokeWidth={2} />
            </span>
          {/if}

          {#if $currentCollection.is_passcode_protected}
            <span class="al-icon-wrapper" title="Passcode protected">
              <Lock label="" size={16} className="text-slate-700 dark:text-slate-300" strokeWidth={2} />
            </span>
          {/if}
        </div>
      {/if}
    {/if}
  </div>

  {#if $isLoading && $sortedItems.length === 0}
    <div class="py-8 text-center text-sm text-slate-500">Loading...</div>
  {:else if $sortedItems.length === 0}
    <div class="flex flex-col">
      <div class="py-8 text-center text-base text-slate-500">No snipsels yet</div>
      <button
        class="mt-2 flex h-24 w-full items-center justify-center rounded-lg border border-dashed border-slate-200 bg-slate-50/50 text-base text-slate-400 hover:bg-slate-50 dark:border-white/10 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Add new snipsel"
        onclick={() => {
          if (selectedIds.size > 0) {
            clearSelection();
            return;
          }
          createSnipselFromUserGesture();
        }}
        disabled={!canWrite()}
      >
        add new snipsel
      </button>

      {#if incomingMentions.length > 0}
        <div class="mt-6 border-t border-slate-200 pt-4">
          <h3 class="mb-3 text-sm font-medium text-slate-500">
            Mentioned by others on this day
          </h3>
          <div class="space-y-2">
            {#each incomingMentions as snip (snip.id)}
              <div
                class="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 dark:border-white/10 dark:bg-white/5"
              >
                {#if snip.created_by_username}
                  <div class="mb-1 text-xs font-medium text-slate-500">
                    @{snip.created_by_username}
                  </div>
                {/if}

                {#if snip.content_markdown}
                  {#if getDeezerLink(snip.content_markdown)}
                    {@const dz = getDeezerLink(snip.content_markdown)!}
                    <DeezerCard type={dz.type} id={dz.id} url={dz.url} accentColor={getHeaderColor()} />
                  {/if}
                  {#if getYouTubeLink(snip.content_markdown)}
                    {@const yt = getYouTubeLink(snip.content_markdown)!}
                    <YouTubeCard url={yt.url} accentColor={getHeaderColor()} />
                  {/if}
                  {#if getMapLink(snip.content_markdown)}
                    {@const ml = getMapLink(snip.content_markdown)!}
                    <MapCard lat={ml.lat} lng={ml.lng} url={ml.url} accentColor={getHeaderColor()} />
                  {/if}
                  {#if getGenericLink(snip.content_markdown)}
                    {@const gl = getGenericLink(snip.content_markdown)!}
                    <HyperlinkCard url={gl.url} accentColor={getHeaderColor()} />
                  {/if}
                  <div class="flex items-start gap-2">
                    <div class="prose prose-sm max-w-none text-lg prose-p:my-0 prose-ul:my-0 prose-ol:my-0 prose-li:my-0 whitespace-pre-wrap dark:prose-invert flex-1 min-w-0">
                      {@html renderMarkdown(stripMediaLinks(snip.content_markdown))}
                    </div>

                    {#if snip.created_by_id !== $currentUser?.id && snip.created_by_username !== $currentUser?.username}
                      <div class="relative shrink-0 self-center ml-1">
                        <button
                          type="button"
                          class="al-icon-wrapper flex h-6 w-6 items-center justify-center rounded-full bg-slate-100 text-slate-400 hover:bg-slate-200 dark:bg-white/5 dark:hover:bg-white/10"
                          onclick={(e) => { e.stopPropagation(); activeReactionPickerId = activeReactionPickerId === snip.id ? null : snip.id; }}
                          aria-label="Add reaction"
                        >
                          <Plus label="" size={14} strokeWidth={2.5} />
                        </button>

                        {#if activeReactionPickerId === snip.id}
                          <div class="absolute bottom-full right-0 z-50 mb-2 flex items-center gap-1 overflow-hidden rounded-full border border-slate-200 bg-white/95 p-1 shadow-xl ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/95">
                            {#if showCustomEmojiInputId === snip.id}
                              <input
                                type="text"
                                class="h-8 w-24 bg-transparent px-3 py-1 text-sm focus:outline-none dark:text-white"
                                placeholder="Emoji..."
                                bind:value={customEmojiInput}
                                use:focusOnMount
                                onkeydown={(e) => {
                                  if (e.key === 'Enter' && customEmojiInput.trim()) {
                                    toggleSnipselReaction(snip.id, customEmojiInput.trim());
                                    showCustomEmojiInputId = null;
                                    customEmojiInput = '';
                                  } else if (e.key === 'Escape') {
                                    showCustomEmojiInputId = null;
                                  }
                                }}
                                onclick={(e) => e.stopPropagation()}
                              />
                            {:else}
                              {#each REACTION_EMOJIS as emoji}
                                <button
                                  type="button"
                                  class="flex h-8 w-8 items-center justify-center rounded-full text-base transition-all hover:scale-110 hover:bg-slate-100 dark:hover:bg-white/10"
                                  onclick={(e) => { e.stopPropagation(); toggleSnipselReaction(snip.id, emoji); }}
                                >
                                  {emoji}
                                </button>
                              {/each}
                              <button
                                type="button"
                                class="flex h-8 w-8 items-center justify-center rounded-full text-base font-medium text-slate-400 transition-all hover:scale-110 hover:bg-slate-100 dark:hover:bg-white/10"
                                onclick={(e) => { e.stopPropagation(); showCustomEmojiInputId = snip.id; customEmojiInput = ''; }}
                              >
                                +
                              </button>
                            {/if}
                          </div>
                        {/if}
                      </div>
                    {/if}
                  </div>
                {:else if !snip.attachments || !snip.attachments.length}
                  <span class="text-sm italic text-slate-400 dark:text-slate-500">Empty snipsel</span>
                {/if}

                {#if snip.reactions && snip.reactions.length > 0}
                <div class="mt-3 flex flex-wrap items-center gap-2">
                  {#each snip.reactions as r (r.emoji)}
                    <button
                      type="button"
                      class="flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium transition-colors {r.me ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300' : 'bg-slate-100 text-slate-600 dark:bg-white/5 dark:text-slate-400'}"
                      onclick={(e) => { e.stopPropagation(); toggleSnipselReaction(snip.id, r.emoji); }}
                    >
                      <span>{r.emoji}</span>
                      <span class="opacity-60">{r.count}</span>
                    </button>
                  {/each}
                </div>
                {/if}

                {#if snip.attachments && snip.attachments.length > 0 && snip.card_view !== false}
                  {@const images = snip.attachments.filter((a) => a.mime_type?.startsWith('image/') || a.has_thumbnail)}
                  {#if images.length > 0}
                    <div class="mt-3 grid grid-cols-3 gap-3">
                      {#each images as a (a.id)}
                        <button
                          class="group relative aspect-square overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all duration-200 hover:scale-[1.02] hover:shadow-md active:scale-95 dark:border-white/10 dark:bg-slate-900"
                          type="button"
                          aria-label="View image"
                          onclick={(e) => {
                            e.stopPropagation();
                            openImageModal(a.id, a.filename);
                          }}
                        >
                          <img
                            class="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
                            src={a.has_thumbnail ? api.attachments.thumbnailUrl(a.id) : api.attachments.downloadUrl(a.id)}
                            alt={a.filename}
                            loading="lazy"
                          />
                          <div class="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 transition-opacity group-hover:opacity-100"></div>
                        </button>
                      {/each}
                    </div>
                  {/if}
                {/if}
              </div>
            {/each}
          </div>
        </div>
      {:else if incomingMentionsLoading && $currentCollection?.list_for_day}
        <div class="mt-6 border-t border-slate-200 pt-4">
          <div class="text-sm text-slate-400">Loading mentions...</div>
        </div>
      {/if}
    </div>
  {:else}
    <div class="flex flex-col">
      {#each visibleItems($sortedItems) as item (item.snipsel_id)}
        <div
          id={`snipsel-${item.snipsel_id}`}
          class="group relative pr-10 {anchorHighlightId === item.snipsel_id ? 'ring-2 rounded-lg' : ''}"
          in:fly={{ y: -5, duration: 150 }}
          out:fade={{ duration: 100 }}
          style={
            anchorHighlightId === item.snipsel_id
              ? `padding-left: calc(3.25rem + ${(item.snipsel_id === $editingSnipselId ? editIndent : item.indent) * 1.25}rem); --tw-ring-color: ${getHeaderColor()}`
              : `padding-left: calc(3.25rem + ${(item.snipsel_id === $editingSnipselId ? editIndent : item.indent) * 1.25}rem)`
          }
        >
          {#if item.snipsel_id === $editingSnipselId}
            <div
              bind:this={editContainerRef}
              class="relative rounded-lg bg-slate-50 px-4 py-3 ring-1 ring-indigo-200 shadow-sm dark:bg-slate-800 dark:ring-indigo-500/50"
              onfocusout={handleEditFocusOut}
            >
              <textarea
                bind:this={textareaRef}
                class="w-full resize-none bg-transparent text-lg outline-none dark:text-slate-100"
                rows="1"
                bind:value={editContent}
                oninput={handleEditInput}
                onkeydown={handleKeydown}
                onpaste={handlePaste}
              ></textarea>
              {#if uploadingAttachments}
                <div class="absolute right-3 top-3 flex items-center gap-2 text-xs text-slate-400">
                  <div class="h-3 w-3 animate-spin rounded-full border-2 border-slate-300 border-t-indigo-500"></div>
                  Uploading...
                </div>
              {/if}
              {#if getEditingSnipselCardView()}
                {#if getDeezerLink(editContent)}
                  {@const dz = getDeezerLink(editContent)!}
                  <DeezerCard url={dz.url} type={dz.type} id={dz.id} accentColor={getHeaderColor()} />
                {/if}
                {#if getYouTubeLink(editContent)}
                  {@const yt = getYouTubeLink(editContent)!}
                  <YouTubeCard url={yt.url} accentColor={getHeaderColor()} />
                {/if}
                {#if getMapLink(editContent)}
                  {@const ml = getMapLink(editContent)!}
                  <MapCard lat={ml.lat} lng={ml.lng} url={ml.url} accentColor={getHeaderColor()} />
                {/if}
                {#if getGenericLink(editContent)}
                  {@const gl = getGenericLink(editContent)!}
                  <HyperlinkCard url={gl.url} accentColor={getHeaderColor()} />
                {/if}
              {/if}
              {#if showAutocomplete && suggestions.length > 0}
                <div class="absolute left-0 right-0 top-full z-50 mt-1 overflow-hidden rounded-xl border border-slate-200 bg-white/95 shadow-xl ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/95 dark:ring-white/10">
                  {#each suggestions as suggestion, i (suggestion.id + suggestion.type)}
                    <button
                      class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm transition-colors {i === autocompleteSelectedIndex ? 'bg-slate-100 text-slate-900 dark:bg-white/10 dark:text-white' : 'text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-white/5'}"
                      type="button"
                      onmousedown={(e) => {
                        e.preventDefault();
                        insertAutocomplete(suggestion);
                      }}
                    >
                      {#if suggestion.icon}
                        <span class="text-base">{suggestion.icon}</span>
                      {:else if suggestion.type === 'tag'}
                        <span class="text-xs text-slate-400 font-mono">#</span>
                      {:else if suggestion.type === 'mention'}
                        <span class="text-xs text-slate-400 font-mono">@</span>
                      {/if}
                      <span class="truncate font-medium">{suggestion.label}</span>
                    </button>
                  {/each}
                </div>
              {/if}
            </div>
          {:else}
            {#if item.snipsel.type === 'task'}
              {#if hasChildren(item, $sortedItems)}
                <button
                  type="button"
                  class="al-icon-wrapper absolute top-1/2 z-20 grid h-6 w-6 -translate-y-1/2 place-items-center rounded-full hover:bg-slate-100 dark:hover:bg-white/10 transition-transform {expandedSnipsels.has(item.snipsel_id) ? '' : '-rotate-90'}"
                  style="left: calc(0.125rem + {item.indent * 1.25}rem)"
                  onclick={(e) => {
                    e.stopPropagation();
                    toggleExpand(item.snipsel_id);
                  }}
                  aria-label={expandedSnipsels.has(item.snipsel_id) ? 'Collapse' : 'Expand'}
                >
                  <ChevronDown label="" size={14} className="text-slate-400 dark:text-slate-500" strokeWidth={2} />
                </button>
              {/if}

<button
                  type="button"
                  aria-label={item.snipsel.task_done ? 'Mark task not done' : 'Mark task done'}
                  class="absolute top-1/2 grid h-5 w-5 -translate-y-1/2 place-items-center rounded-full border border-slate-300 bg-white transition-all duration-150 hover:scale-110 active:scale-95 dark:border-white/20 dark:bg-slate-800"
                  onclick={(e) => {
                    e.stopPropagation();
                    toggleTaskDone(item);
                  }}
                  style="left: calc(1.75rem + {item.indent * 1.25}rem); {item.snipsel.task_done
                    ? `border-color: ${getHeaderColor()}; background-color: ${getToolboxBg()}; color: ${getHeaderColor()}; font-size: 10px`
                    : ''}"
                >
                  {#if item.snipsel.task_done}
                    <span in:scale={{ start: 0.5, duration: 150 }}>✓</span>
                  {/if}
                </button>

                <button
                  type="button"
                  aria-label="Select snipsel"
                  class="absolute right-0 top-0 bottom-0 w-6 flex items-center justify-end transition-opacity {selectedIds.has(item.snipsel_id) ? '' : 'opacity-0 group-hover:opacity-100'}"
                  onclick={(e) => {
                    e.stopPropagation();
                    toggleSelection(item.snipsel_id);
                  }}
                >
                  <div
                    class="w-1.5 h-full transition-all duration-150 ease-out origin-right {selectedIds.has(item.snipsel_id) ? '' : 'scale-x-0 group-hover:scale-x-100'} hover:scale-x-150 active:scale-x-75"
                    style={selectedIds.has(item.snipsel_id) ? `background-color: ${getHeaderColor()}` : 'background-color: #94a3b8'}
                  ></div>
                </button>
            {:else}
              <button
                type="button"
                aria-label="Select snipsel"
                class="absolute right-0 top-0 bottom-0 w-6 flex items-center justify-end transition-opacity {selectedIds.has(item.snipsel_id) ? '' : 'opacity-0 group-hover:opacity-100'}"
                onclick={(e) => {
                  e.stopPropagation();
                  toggleSelection(item.snipsel_id);
                }}
              >
                <div
                  class="w-1.5 h-full transition-all duration-150 ease-out origin-right hover:scale-x-150 active:scale-x-75"
                  style={selectedIds.has(item.snipsel_id) ? `background-color: ${getHeaderColor()}` : 'background-color: #94a3b8'}
                ></div>
              </button>
            {/if}

            {#if item.snipsel.type !== 'task'}
              {#if hasChildren(item, $sortedItems)}
                <button
                  type="button"
                  class="al-icon-wrapper absolute top-1/2 z-20 grid h-6 w-6 -translate-y-1/2 place-items-center rounded-full hover:bg-slate-100 dark:hover:bg-white/10 transition-transform {expandedSnipsels.has(item.snipsel_id) ? '' : '-rotate-90'}"
                  style="left: calc(1.625rem + {item.indent * 1.25}rem)"
                  onclick={(e) => {
                    e.stopPropagation();
                    toggleExpand(item.snipsel_id);
                  }}
                  aria-label={expandedSnipsels.has(item.snipsel_id) ? 'Collapse' : 'Expand'}
                >
                  <ChevronDown label="" size={14} className="text-slate-400" strokeWidth={2} />
                </button>
              {:else}
                <div 
                  class="absolute top-1/2 -translate-y-1/2 h-1 w-1 rounded-full bg-slate-400" 
                  style="left: calc(2.25rem + {item.indent * 1.25}rem)"
                  aria-hidden="true"
                ></div>
              {/if}
            {/if}
            <div
              class="rounded px-4 py-3 {selectedIds.has(item.snipsel_id)
                ? 'bg-slate-100 dark:bg-white/5'
                : 'hover:bg-slate-50 dark:hover:bg-white/[0.02]'}"
              role="button"
              tabindex="0"
              onclick={(e) => {
                const target = (e.target as HTMLElement).closest('[data-collection-id]');
                if (target) {
                  e.preventDefault();
                  e.stopPropagation();
                  const id = target.getAttribute('data-collection-id');
                  if (id) currentView.set({ type: 'collection', id });
                  return;
                }
                startEdit(item);
              }}
              onkeydown={(e) => e.key === 'Enter' && startEdit(item)}
            >
              {#if item.snipsel.content_markdown}
                  {#if item.snipsel.card_view !== false}
                    {#if getDeezerLink(item.snipsel.content_markdown)}
                      {@const dz = getDeezerLink(item.snipsel.content_markdown)!}
                      <DeezerCard type={dz.type} id={dz.id} url={dz.url} accentColor={getHeaderColor()} />
                    {/if}
                    {#if getYouTubeLink(item.snipsel.content_markdown)}
                      {@const yt = getYouTubeLink(item.snipsel.content_markdown)!}
                      <YouTubeCard url={yt.url} accentColor={getHeaderColor()} />
                    {/if}
                    {#if getMapLink(item.snipsel.content_markdown)}
                      {@const ml = getMapLink(item.snipsel.content_markdown)!}
                      <MapCard lat={ml.lat} lng={ml.lng} url={ml.url} accentColor={getHeaderColor()} />
                    {/if}
                    {#if getGenericLink(item.snipsel.content_markdown)}
                      {@const gl = getGenericLink(item.snipsel.content_markdown)!}
                      <HyperlinkCard url={gl.url} accentColor={getHeaderColor()} />
                    {/if}
                  {/if}

                  <div class="flex items-start gap-2">
                    <div
                      class="prose prose-sm max-w-none text-lg prose-p:my-0 prose-ul:my-0 prose-ol:my-0 prose-li:my-0 prose-headings:my-2 prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg whitespace-pre-wrap dark:prose-invert flex-1 min-w-0"
                      style="--accent-light: {getToolboxBg()}"
                    >
                      {@html renderWithWikiLinks(item.snipsel.card_view !== false ? stripMediaLinks(item.snipsel.content_markdown) : item.snipsel.content_markdown, item.collection_refs)}
                    </div>

                    {#if item.snipsel.created_by_id !== $currentUser?.id}
                      <div class="relative shrink-0 self-center ml-1">
                        <button
                          type="button"
                          class="al-icon-wrapper flex h-6 w-6 items-center justify-center rounded-full bg-slate-100 text-slate-400 hover:bg-slate-200 dark:bg-white/5 dark:hover:bg-white/10"
                          onclick={(e) => { e.stopPropagation(); activeReactionPickerId = activeReactionPickerId === item.snipsel_id ? null : item.snipsel_id; }}
                          aria-label="Add reaction"
                        >
                          <Plus label="" size={14} strokeWidth={2.5} />
                        </button>

                        {#if activeReactionPickerId === item.snipsel_id}
                          <div class="absolute bottom-full right-0 z-50 mb-2 flex items-center gap-1 overflow-hidden rounded-full border border-slate-200 bg-white/95 p-1 shadow-xl ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/95">
                            {#if showCustomEmojiInputId === item.snipsel_id}
                              <input
                                type="text"
                                class="h-8 w-24 bg-transparent px-3 py-1 text-sm focus:outline-none dark:text-white"
                                placeholder="Emoji..."
                                bind:value={customEmojiInput}
                                use:focusOnMount
                                onkeydown={(e) => {
                                  if (e.key === 'Enter' && customEmojiInput.trim()) {
                                    toggleSnipselReaction(item.snipsel_id, customEmojiInput.trim());
                                    showCustomEmojiInputId = null;
                                    customEmojiInput = '';
                                  } else if (e.key === 'Escape') {
                                    showCustomEmojiInputId = null;
                                  }
                                }}
                                onclick={(e) => e.stopPropagation()}
                              />
                            {:else}
                              {#each REACTION_EMOJIS as emoji}
                                <button
                                  type="button"
                                  class="flex h-8 w-8 items-center justify-center rounded-full text-base transition-all hover:scale-110 hover:bg-slate-100 dark:hover:bg-white/10"
                                  onclick={(e) => { e.stopPropagation(); toggleSnipselReaction(item.snipsel_id, emoji); }}
                                >
                                  {emoji}
                                </button>
                              {/each}
                              <button
                                type="button"
                                class="flex h-8 w-8 items-center justify-center rounded-full text-base font-medium text-slate-400 transition-all hover:scale-110 hover:bg-slate-100 dark:hover:bg-white/10"
                                onclick={(e) => { e.stopPropagation(); showCustomEmojiInputId = item.snipsel_id; customEmojiInput = ''; }}
                              >
                                +
                              </button>
                            {/if}
                          </div>
                        {/if}
                      </div>
                    {/if}
                  </div>

                  {#if (item.snipsel.tags?.length ?? 0) > 0 || (item.snipsel.mentions?.length ?? 0) > 0}
                    <div class="mt-2 flex flex-wrap gap-1.5">
                      {#each item.snipsel.tags ?? [] as t (t)}
                        <span 
                          class="rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider"
                          style="background-color: {getToolboxBg()}; color: {getHeaderColor()}; border: 1px solid rgba(0,0,0,0.05)"
                        >
                          #{t}
                        </span>
                      {/each}
                      {#each item.snipsel.mentions ?? [] as m (m)}
                        <span 
                          class="rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider"
                          style="background-color: {getToolboxBg()}; color: {getHeaderColor()}; border: 1px solid rgba(0,0,0,0.05)"
                        >
                          @{m}
                        </span>
                      {/each}
                    </div>
                  {/if}

              {:else}
                <span class="text-sm italic text-slate-400 dark:text-slate-500">Empty snipsel</span>
              {/if}

              {#if item.snipsel.reactions && item.snipsel.reactions.length > 0}
              <div class="mt-2 flex flex-wrap items-center gap-2">
                {#each item.snipsel.reactions as r (r.emoji)}
                  <button
                    type="button"
                    class="flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium transition-colors {r.me ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300' : 'bg-slate-100 text-slate-600 dark:bg-white/5 dark:text-slate-400'}"
                    onclick={(e) => { e.stopPropagation(); toggleSnipselReaction(item.snipsel_id, r.emoji); }}
                  >
                    <span>{r.emoji}</span>
                    <span class="opacity-60">{r.count}</span>
                  </button>
                {/each}
              </div>
              {/if}

              {#if item.snipsel.reminder_at}
                {@const expired = isExpired(item.snipsel.reminder_at)}
                <div class="mt-1 flex flex-wrap items-center gap-1 text-[10px]">
                  <span 
                    class="flex items-center gap-1 rounded px-1.5 py-0.5 {expired ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400' : ''}"
                    style={expired 
                      ? undefined 
                      : `background-color: ${getToolboxBg()}; color: ${getHeaderColor()}`}
                  >
                    <Bell label="" size={10} strokeWidth={2.5} />
                    {new Date(item.snipsel.reminder_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                    <span class="opacity-60">· {daysFromNow(item.snipsel.reminder_at)}</span>
                    {#if item.snipsel.reminder_rrule}
                      <Repeat label="" size={10} className="ml-1" strokeWidth={2.5} />
                    {/if}
                  </span>
                </div>
              {/if}

              {#if saveStatuses[item.snipsel_id]}
                <div 
                  class="absolute top-1/2 -translate-y-1/2 right-[2.5rem] h-2 w-2 rounded-full transition-opacity duration-500"
                  style="background-color: {saveStatuses[item.snipsel_id] === 'success' ? '#22c55e' : '#ef4444'}"
                  aria-hidden="true"
                ></div>
              {/if}



              {#if item.snipsel.attachments.length > 0}
                {#if item.snipsel.card_view !== false}
                  {@const isImageAttachment = (a: Attachment) => Boolean(a.mime_type?.startsWith('image/') || (a.has_thumbnail && !a.mime_type?.startsWith('video/')))}
                  {@const isVideoAttachment = (a: Attachment) => Boolean(a.mime_type?.startsWith('video/') || (a.has_thumbnail && a.filename.toLowerCase().match(/\.(mp4|mov|webm|avi|mkv)$/)))}
                  {@const isMediaAttachment = (a: Attachment) => isImageAttachment(a) || isVideoAttachment(a)}
                  {@const media = item.snipsel.attachments.filter(isMediaAttachment)}
                  {@const others = item.snipsel.attachments.filter((a) => !isMediaAttachment(a))}

                  {#if media.length > 0}
                    <div class="mt-3 grid grid-cols-3 gap-3">
                      {#each media as a}
                        <button
                          type="button"
                          class="group relative aspect-square w-full overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all duration-200 hover:scale-[1.02] hover:shadow-md dark:border-white/10 dark:bg-slate-900"
                          aria-label={isVideoAttachment(a) ? `Play ${a.filename}` : `View ${a.filename}`}
                          onclick={(e) => {
                            e.stopPropagation();
                            if (isVideoAttachment(a)) {
                              openVideoModal(a.id, a.filename);
                            } else {
                              openImageModal(a.id, a.filename);
                            }
                          }}
                        >
                          <img
                            class="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
                            src={a.has_thumbnail ? api.attachments.thumbnailUrl(a.id) : api.attachments.downloadUrl(a.id)}
                            alt={a.filename}
                            loading="lazy"
                          />
                          {#if isVideoAttachment(a)}
                            <div class="absolute inset-0 flex items-center justify-center bg-black/20 group-hover:bg-black/30 transition-colors">
                              <CirclePlay label="" size={32} className="text-white drop-shadow-md" />
                            </div>
                          {:else}
                            <div class="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 transition-opacity group-hover:opacity-100"></div>
                          {/if}
                        </button>
                      {/each}
                    </div>
                  {/if}

                  {#if others.length > 0}
                    <div class="mt-3 space-y-2">
                      {#each others.slice(0, 3) as a}
                        <AttachmentCard attachment={a} downloadUrl={api.attachments.downloadUrl(a.id)} thumbnailUrl={a.has_thumbnail ? api.attachments.thumbnailUrl(a.id) : undefined} accentColor={getHeaderColor()} />
                      {/each}
                      {#if others.length > 3}
                        <div class="text-[11px] text-slate-400">+{others.length - 3} more files</div>
                      {/if}
                    </div>
                  {/if}
                {:else}
                  <div class="mt-1 flex items-center gap-1 text-[11px] text-slate-400">
                    <Paperclip label="" size={12} strokeWidth={2} />
                    <span>{item.snipsel.attachments.length}</span>
                  </div>
                {/if}
              {/if}
            </div>
          {/if}
        </div>
      {/each}

      {#if incomingMentions.length > 0}
        <div class="mt-6 border-t border-slate-200 pt-4">
          <h3 class="mb-3 text-sm font-medium text-slate-500">
            Mentioned by others on this day
          </h3>
          <div class="space-y-2">
            {#each incomingMentions as snip (snip.id)}
              <div
                class="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 dark:border-white/10 dark:bg-white/5"
              >
                {#if snip.created_by_username}
                  <div class="mb-1 text-xs font-medium text-slate-500">
                    @{snip.created_by_username}
                  </div>
                {/if}

                {#if snip.content_markdown}
                  {#if getDeezerLink(snip.content_markdown)}
                    {@const dz = getDeezerLink(snip.content_markdown)!}
                    <DeezerCard type={dz.type} id={dz.id} url={dz.url} accentColor={getHeaderColor()} />
                  {/if}
                  {#if getYouTubeLink(snip.content_markdown)}
                    {@const yt = getYouTubeLink(snip.content_markdown)!}
                    <YouTubeCard url={yt.url} accentColor={getHeaderColor()} />
                  {/if}
                  {#if getMapLink(snip.content_markdown)}
                    {@const ml = getMapLink(snip.content_markdown)!}
                    <MapCard lat={ml.lat} lng={ml.lng} url={ml.url} accentColor={getHeaderColor()} />
                  {/if}
                  {#if getGenericLink(snip.content_markdown)}
                    {@const gl = getGenericLink(snip.content_markdown)!}
                    <HyperlinkCard url={gl.url} accentColor={getHeaderColor()} />
                  {/if}
                  <div class="flex items-start gap-2">
                    <div class="prose prose-sm max-w-none text-lg prose-p:my-0 prose-ul:my-0 prose-ol:my-0 prose-li:my-0 whitespace-pre-wrap dark:prose-invert flex-1 min-w-0">
                      {@html renderMarkdown(stripMediaLinks(snip.content_markdown))}
                    </div>

                    {#if snip.created_by_id !== $currentUser?.id && snip.created_by_username !== $currentUser?.username}
                      <div class="relative shrink-0 self-center ml-1">
                        <button
                          type="button"
                          class="al-icon-wrapper flex h-6 w-6 items-center justify-center rounded-full bg-slate-100 text-slate-400 hover:bg-slate-200 dark:bg-white/5 dark:hover:bg-white/10"
                          onclick={(e) => { e.stopPropagation(); activeReactionPickerId = activeReactionPickerId === snip.id ? null : snip.id; }}
                          aria-label="Add reaction"
                        >
                          <Plus label="" size={14} strokeWidth={2.5} />
                        </button>

                        {#if activeReactionPickerId === snip.id}
                          <div class="absolute bottom-full right-0 z-50 mb-2 flex items-center gap-1 overflow-hidden rounded-full border border-slate-200 bg-white/95 p-1 shadow-xl ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/95">
                            {#if showCustomEmojiInputId === snip.id}
                              <input
                                type="text"
                                class="h-8 w-24 bg-transparent px-3 py-1 text-sm focus:outline-none dark:text-white"
                                placeholder="Emoji..."
                                bind:value={customEmojiInput}
                                use:focusOnMount
                                onkeydown={(e) => {
                                  if (e.key === 'Enter' && customEmojiInput.trim()) {
                                    toggleSnipselReaction(snip.id, customEmojiInput.trim());
                                    showCustomEmojiInputId = null;
                                    customEmojiInput = '';
                                  } else if (e.key === 'Escape') {
                                    showCustomEmojiInputId = null;
                                  }
                                }}
                                onclick={(e) => e.stopPropagation()}
                              />
                            {:else}
                              {#each REACTION_EMOJIS as emoji}
                                <button
                                  type="button"
                                  class="flex h-8 w-8 items-center justify-center rounded-full text-base transition-all hover:scale-110 hover:bg-slate-100 dark:hover:bg-white/10"
                                  onclick={(e) => { e.stopPropagation(); toggleSnipselReaction(snip.id, emoji); }}
                                >
                                  {emoji}
                                </button>
                              {/each}
                              <button
                                type="button"
                                class="flex h-8 w-8 items-center justify-center rounded-full text-base font-medium text-slate-400 transition-all hover:scale-110 hover:bg-slate-100 dark:hover:bg-white/10"
                                onclick={(e) => { e.stopPropagation(); showCustomEmojiInputId = snip.id; customEmojiInput = ''; }}
                              >
                                +
                              </button>
                            {/if}
                          </div>
                        {/if}
                      </div>
                    {/if}
                  </div>
                {:else if !snip.attachments || !snip.attachments.length}
                  <span class="text-sm italic text-slate-400 dark:text-slate-500">Empty snipsel</span>
                {/if}

                {#if snip.reactions && snip.reactions.length > 0}
                <div class="mt-3 flex flex-wrap items-center gap-2">
                  {#each snip.reactions as r (r.emoji)}
                    <button
                      type="button"
                      class="flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium transition-colors {r.me ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300' : 'bg-slate-100 text-slate-600 dark:bg-white/5 dark:text-slate-400'}"
                      onclick={(e) => { e.stopPropagation(); toggleSnipselReaction(snip.id, r.emoji); }}
                    >
                      <span>{r.emoji}</span>
                      <span class="opacity-60">{r.count}</span>
                    </button>
                  {/each}
                </div>
                {/if}

                {#if snip.attachments && snip.attachments.length > 0 && snip.card_view !== false}
                  {@const images = snip.attachments.filter((a) => a.mime_type?.startsWith('image/') || a.has_thumbnail)}
                  {#if images.length > 0}
                    <div class="mt-3 grid grid-cols-3 gap-3">
                      {#each images as a (a.id)}
                        <button
                          class="group relative aspect-square overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all duration-200 hover:scale-[1.02] hover:shadow-md active:scale-95 dark:border-white/10 dark:bg-slate-900"
                          type="button"
                          aria-label="View image"
                          onclick={(e) => {
                            e.stopPropagation();
                            openImageModal(a.id, a.filename);
                          }}
                        >
                          <img
                            class="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
                            src={a.has_thumbnail ? api.attachments.thumbnailUrl(a.id) : api.attachments.downloadUrl(a.id)}
                            alt={a.filename}
                            loading="lazy"
                          />
                          <div class="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 transition-opacity group-hover:opacity-100"></div>
                        </button>
                      {/each}
                    </div>
                  {/if}
                {/if}
              </div>
            {/each}
          </div>
        </div>
      {:else if incomingMentionsLoading && $currentCollection?.list_for_day}
        <div class="mt-6 border-t border-slate-200 pt-4">
          <div class="text-sm text-slate-400">Loading mentions...</div>
        </div>
      {/if}

      <button
        class="mt-6 flex h-24 w-full items-center justify-center rounded-lg border border-dashed border-slate-200 bg-slate-50/50 text-base text-slate-400 transition-all hover:scale-[1.01] hover:border-slate-300 hover:bg-slate-50 hover:text-slate-500 active:scale-[0.99] dark:border-white/10 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Add new snipsel"
        onclick={() => {
          if (selectedIds.size > 0) {
            clearSelection();
            return;
          }
          createSnipselFromUserGesture();
        }}
        disabled={!canWrite()}
      >
        add new snipsel
      </button>

      {#if hideDoneTasks && hiddenDoneCount($sortedItems) > 0}
        <div class="mt-3 text-center text-sm text-slate-500">
          {hiddenDoneCount($sortedItems)} completed tasks hidden
        </div>
      {/if}
    </div>
  {/if}
</div>

{#if selectedIds.size > 0}
  <!-- Progressive blur layer behind toolbox -->
  <div class="fixed bottom-0 left-0 right-0 z-10 pointer-events-none" style="height: 120px;" in:fly={{ y: 100, duration: 250 }} out:fly={{ y: 100, duration: 200 }}>
    <div class="absolute inset-0 backdrop-blur-lg" style="mask-image: linear-gradient(to top, black 0%, black 40%, transparent 100%); -webkit-mask-image: linear-gradient(to top, black 0%, black 40%, transparent 100%);"></div>
  </div>
  <!-- Toolbox -->
  <div class="fixed bottom-0 left-0 right-0 z-20 px-4 pb-4" style="padding-bottom: calc(env(safe-area-inset-bottom) + 2rem);" in:fly={{ y: 100, duration: 250 }} out:fly={{ y: 100, duration: 200 }}>
    <div
      class="mx-auto flex max-w-3xl flex-wrap items-center justify-center gap-2 rounded-xl px-3 py-3 text-slate-900 shadow-lg ring-1 ring-black/5 backdrop-blur-xl dark:text-slate-100 dark:ring-white/10"
      style={`background-color: ${getToolboxBg()}`}
    >
      <div class="flex items-center justify-center min-w-[2rem] px-2 py-1 rounded-full bg-black/10 dark:bg-white/10">
        <span class="text-sm font-bold transition-transform duration-150 {selectionPulse ? 'scale-125' : ''}" style="color: {getHeaderColor()}">{selectedIds.size}</span>
      </div>

       <input
         bind:this={attachmentsInputRef}
         class="hidden"
         type="file"
         multiple
         onchange={uploadAttachmentsSelected}
         disabled={uploadingAttachments}
       />

      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Move up"
        title="Move up"
        onclick={lpMoveTop.onclick}
        onpointerdown={lpMoveTop.onpointerdown}
        onpointerup={lpMoveTop.onpointerup}
        onpointercancel={lpMoveTop.onpointercancel}
        onpointerleave={lpMoveTop.onpointerleave}
        oncontextmenu={lpMoveTop.oncontextmenu}
        disabled={!canWrite()}
      >
          <ChevronUp label="" size={20} strokeWidth={2} />
      </button>
      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Move down"
        title="Move down"
        onclick={lpMoveBottom.onclick}
        onpointerdown={lpMoveBottom.onpointerdown}
        onpointerup={lpMoveBottom.onpointerup}
        onpointercancel={lpMoveBottom.onpointercancel}
        onpointerleave={lpMoveBottom.onpointerleave}
        oncontextmenu={lpMoveBottom.oncontextmenu}
        disabled={!canWrite()}
      >
          <ChevronDown label="" size={20} strokeWidth={2} />
      </button>

      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Outdent"
        title="Outdent"
        onclick={lpOutdentToZero.onclick}
        onpointerdown={lpOutdentToZero.onpointerdown}
        onpointerup={lpOutdentToZero.onpointerup}
        onpointercancel={lpOutdentToZero.onpointercancel}
        onpointerleave={lpOutdentToZero.onpointerleave}
        oncontextmenu={lpOutdentToZero.oncontextmenu}
        disabled={!canWrite()}
      >
          <Outdent label="" size={20} strokeWidth={2} />
      </button>
      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Indent"
        title="Indent"
        onclick={() => adjustIndentSelected(1)}
        disabled={!canWrite()}
      >
          <Indent label="" size={20} strokeWidth={2} />
      </button>

      <div class="relative">
        <button
          class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
          type="button"
          aria-label="Change type"
          title="Change type"
          onclick={() => (showTypeMenu = !showTypeMenu)}
          disabled={!canWrite()}
        >
          <Type label="" size={20} strokeWidth={2} />
        </button>
        {#if showTypeMenu}
          <div class="absolute bottom-12 right-0 z-50 w-48 overflow-hidden rounded-xl border border-slate-200 bg-white/95 shadow-xl ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/95 dark:ring-white/10">
<div class="border-b border-slate-100 bg-slate-50/50 px-3 py-2 text-left text-xs font-bold uppercase tracking-wider text-slate-500 dark:border-white/5 dark:bg-slate-950/50 dark:text-slate-400">Change type</div>
             <div class="py-1">
               <button class="al-icon-wrapper flex w-full items-center gap-2.5 px-3 py-2 text-left text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-white/5" type="button" onclick={() => setTypeSelected('text')}>
                 <FileText label="" size={16} strokeWidth={2} />
                 Note
               </button>
               <button class="al-icon-wrapper flex w-full items-center gap-2.5 px-3 py-2 text-left text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-white/5" type="button" onclick={() => setTypeSelected('task')}>
                 <SquareCheck label="" size={16} strokeWidth={2} />
                 Task
               </button>
             </div>
            <div class="border-t border-slate-100 px-3 py-2 dark:border-white/5">
              <label class="flex items-center justify-between cursor-pointer">
                <span class="text-sm text-slate-600 dark:text-slate-400">Card view</span>
                <button
                  type="button"
                  class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none {getSelectedCardView() ? 'bg-indigo-600' : 'bg-slate-200 dark:bg-slate-700'}"
                  onclick={toggleCardViewSelected}
                  role="switch"
                  aria-checked={getSelectedCardView()}
                  aria-label="Toggle card view"
                >
                  <span class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out {getSelectedCardView() ? 'translate-x-5' : 'translate-x-0'}"></span>
                </button>
              </label>
            </div>
            <div class="border-t border-slate-100 p-1 dark:border-white/5">
              <button
                class="w-full rounded-lg px-3 py-2 text-left text-xs font-medium text-slate-500 transition-colors hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-white/5"
                type="button"
                onclick={closeTypeMenu}
              >
                Cancel
              </button>
            </div>
          </div>
        {/if}
      </div>



      {#if $currentUser?.ai_llm_url && selectedIds.size > 0}
        <button
          class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
          type="button"
          aria-label="AI Assistant"
          title="AI Assistant"
          onclick={() => openAiModal()}
          disabled={!canWrite()}
        >
          <Sparkles label="" size={20} />
        </button>
      {/if}

      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Insert template"
        title="Insert template"
        onclick={() => (showTemplateMenu = !showTemplateMenu)}
        disabled={!canWrite()}
      >
          <LayoutTemplate label="" size={20} strokeWidth={2} />
      </button>
      {#if showTemplateMenu}
        <div class="absolute bottom-12 right-0 w-64 max-h-80 overflow-y-auto rounded-lg border border-slate-200 bg-white text-slate-900 shadow-xl dark:border-white/10 dark:bg-slate-900 dark:text-slate-100">
          <div class="px-3 py-2 text-xs font-bold uppercase tracking-wider text-slate-500 bg-slate-50 border-b border-slate-100 dark:bg-slate-950 dark:border-white/5">Templates</div>
          {#if templates.length === 0}
            <div class="px-3 py-4 text-sm text-slate-500 italic dark:text-slate-400">No templates found</div>
          {:else}
            {#each templates as t (t.id)}
              <button
                class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-slate-50 dark:hover:bg-white/5"
                type="button"
                onclick={() => insertTemplateSelected(t.id)}
              >
                <span class="text-xl">{t.icon}</span>
                <span class="truncate font-medium">{t.title}</span>
              </button>
            {/each}
          {/if}
          <button
            class="w-full border-t px-3 py-2 text-left text-sm text-slate-500 hover:bg-slate-50 dark:border-white/5 dark:hover:bg-white/5"
            type="button"
            onclick={closeTemplateMenu}
          >
            Cancel
          </button>
        </div>
      {/if}

      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Upload files"
        title="Upload files"
        onclick={() => attachmentsInputRef?.click()}
        disabled={uploadingAttachments || !canWrite()}
      >
          <Paperclip label="" size={20} strokeWidth={2} />
      </button>
      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Copy"
        title="Copy"
        onclick={() => openCollectionModal('copy')}
        disabled={!canWrite()}
      >
          <Copy label="" size={20} strokeWidth={2} />
      </button>
      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Move"
        title="Move"
        onclick={() => openCollectionModal('move')}
        disabled={!canWrite()}
      >
          <ArrowRightLeft label="" size={20} strokeWidth={2} />
      </button>
      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10 disabled:opacity-50"
        type="button"
        aria-label="Create collection"
        title="Create collection from snipsel"
        onclick={createCollectionFromSnipsel}
        disabled={selectedIds.size !== 1 || !canWrite()}
      >
          <CornerDownRight label="" size={20} strokeWidth={2} />
      </button>
      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Add to collection"
        title="Add to collection"
        onclick={() => openCollectionModal('link')}
        disabled={!canWrite()}
      >
          <Plus label="" size={20} strokeWidth={2} />
      </button>
      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10"
        type="button"
        aria-label="Info"
        title="Info"
        onclick={openDetailSelected}
      >
          <Info label="" size={20} strokeWidth={2} />
      </button>
      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md bg-red-600/90 text-lg text-white hover:bg-red-600 dark:bg-red-700 dark:hover:bg-red-600"
        type="button"
        aria-label="Delete"
        title="Delete"
        onclick={deleteSelected}
        disabled={!canWrite()}
      >
        <Trash2 label="" size={20} strokeWidth={2} />
      </button>
      <button
        class="al-icon-wrapper grid h-11 w-11 place-items-center rounded-md text-lg text-slate-600 hover:bg-black/5 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-slate-100"
        type="button"
        aria-label="Clear selection"
        title="Clear selection"
        onclick={() => {
          clearSelection();
          closeTypeMenu();
          closeTemplateMenu();
        }}
>
          <X label="" size={20} strokeWidth={2} />
      </button>
    </div>
  </div>
{/if}

{#if showScrollTop && selectedIds.size === 0}
  <div class="fixed bottom-32 left-0 right-0 z-10 flex justify-center pointer-events-none" in:fly={{ y: 20, duration: 200 }} out:fade={{ duration: 150 }}>
    <button 
      class="al-icon-wrapper pointer-events-auto grid h-12 w-12 place-items-center rounded-full border border-slate-200 bg-white/80 text-slate-600 shadow-lg ring-1 ring-black/5 backdrop-blur-md transition-all hover:-translate-y-1 hover:bg-white hover:shadow-xl dark:border-white/10 dark:bg-slate-900/80 dark:text-slate-300 dark:hover:bg-slate-900" 
      type="button" 
      onclick={scrollToTop} 
      aria-label="Scroll to top" 
      title="Scroll to top"
    >
      <ChevronUp label="" size={24} strokeWidth={2.5} />
    </button>
  </div>
{/if}

<ImageModal
  attachmentId={modalImage?.id ?? null}
  filename={modalImage?.filename ?? ''}
  onClose={closeImageModal}
/>

{#if showCollectionModal}
  <CollectionSelectModal
    title={collectionModalTitle}
    onClose={() => (showCollectionModal = false)}
    onSelect={handleCollectionSelected}
  />
{/if}

{#if showDeleteModal}
  <DeleteConfirmModal
    title="Delete snipsels?"
    message={selectedIds.size === 1 ? 'Are you sure you want to permanently delete this snipsel?' : `Are you sure you want to permanently delete these ${selectedIds.size} snipsels?`}
    onConfirm={confirmDeleteSelected}
    onCancel={cancelDeleteSelected}
  />
{/if}

{#if uploadProgress}
  <ProgressModal
    filename={uploadProgress.filename}
    percent={uploadProgress.percent}
  />
{/if}

{#if errorModal}
  <InfoModal
    title={errorModal.title}
    message={errorModal.message}
    onClose={() => (errorModal = null)}
  />
{/if}
{#if modalVideo}
  <VideoModal
    attachmentId={modalVideo.id}
    filename={modalVideo.filename}
    />
{/if}

{#if showAiModal}
<AiModal
  context={aiModalContext}
  attachmentIds={aiModalSelectedAttachments}
  onClose={() => showAiModal = false}
  onInsert={handleAiInsert}
  onReplace={handleAiReplace}
/>
{/if}
