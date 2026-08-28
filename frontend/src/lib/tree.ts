import type { CollectionItem } from './api';

export function hasChildren(item: CollectionItem, allItems: CollectionItem[]): boolean {
  const idx = allItems.findIndex((i) => i.snipsel_id === item.snipsel_id);
  if (idx < 0 || idx === allItems.length - 1) return false;
  return allItems[idx + 1].indent > item.indent;
}

export function getChildIds(parentId: string, allItems: CollectionItem[]): string[] {
  const idx = allItems.findIndex((i) => i.snipsel_id === parentId);
  if (idx < 0 || idx === allItems.length - 1) return [];

  const parentIndent = allItems[idx].indent;
  const childIds: string[] = [];

  for (let i = idx + 1; i < allItems.length; i++) {
    if (allItems[i].indent > parentIndent) {
      childIds.push(allItems[i].snipsel_id);
    } else {
      break;
    }
  }

  return childIds;
}

export function isDoneTask(item: CollectionItem): boolean {
  return item.snipsel.type === 'task' && Boolean(item.snipsel.task_done);
}

export function computeVisibleItems(
  items: CollectionItem[],
  expandedIds: Set<string>,
  hideDoneTasks = false
): CollectionItem[] {
  const filtered = hideDoneTasks ? items.filter((i) => !isDoneTask(i)) : items;
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
    const itemHasChildren = nextItem && nextItem.indent > item.indent;

    if (itemHasChildren && !expandedIds.has(item.snipsel_id)) {
      skipUntilIndent = item.indent;
    }
  }

  return result;
}

export function computeCollapsibleParentIds(items: CollectionItem[]): Set<string> {
  const ids = new Set<string>();
  for (let i = 0; i < items.length - 1; i++) {
    if (items[i + 1].indent > items[i].indent) {
      ids.add(items[i].snipsel_id);
    }
  }
  return ids;
}

export function computeHiddenDoneCount(items: CollectionItem[], hideDoneTasks = false): number {
  if (!hideDoneTasks) return 0;
  return items.filter(isDoneTask).length;
}

export function computeTaskProgress(items: CollectionItem[]): { total: number; done: number; ratio: number } {
  const tasks = items.filter((i) => i.snipsel.type === 'task');
  const total = tasks.length;
  const done = tasks.filter((i) => Boolean(i.snipsel.task_done)).length;
  return { total, done, ratio: total > 0 ? done / total : 0 };
}
