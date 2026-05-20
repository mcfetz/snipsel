import type { View } from './stores';

export type Route =
  | { v: 'collections' }
  | { v: 'collection'; id: string; sn?: string; pos?: number }
  | { v: 'collection_settings'; id: string }
  | { v: 'snipsel'; id: string; returnTo?: string }
  | { v: 'tags_mentions' }
  | { v: 'habits' }
  | { v: 'habit_detail'; id: string }
  | { v: 'search'; q?: string }
  | { v: 'todos' }
  | { v: 'calendar' }
  | { v: 'settings' }
  | { v: 'notifications' }
  | { v: 'public'; token: string }
  | { v: 'loading' };

const KNOWN_VIEWS = new Set<Route['v']>([
  'collections',
  'collection',
  'collection_settings',
  'snipsel',
  'tags_mentions',
  'habits',
  'habit_detail',
  'search',
  'todos',
  'calendar',
  'settings',
  'notifications',
  'public',
  'loading',
]);

function clampPos(n: number): number {
  if (!Number.isFinite(n)) return 1;
  return Math.max(1, Math.floor(n));
}

export function parseRouteFromLocation(loc: Location): Route | null {
  const sp = new URLSearchParams(loc.search);
  const vRaw = sp.get('v') ?? '';
  if (!vRaw) return null;
  if (!KNOWN_VIEWS.has(vRaw as Route['v'])) return null;

  const v = vRaw as Route['v'];

  if (v === 'collection') {
    const id = sp.get('id') ?? '';
    if (!id) return null;
    const sn = sp.get('sn') ?? undefined;
    const posRaw = sp.get('pos');
    const pos = posRaw ? clampPos(Number(posRaw)) : undefined;
    return { v, id, sn: sn || undefined, pos };
  }

  if (v === 'collection_settings') {
    const id = sp.get('id') ?? '';
    if (!id) return null;
    return { v, id };
  }

  if (v === 'snipsel') {
    const id = sp.get('id') ?? '';
    if (!id) return null;
    const returnTo = sp.get('returnTo') ?? undefined;
    return { v, id, returnTo: returnTo || undefined };
  }

  if (v === 'search') {
    const q = sp.get('q') ?? undefined;
    return { v, q: q || undefined };
  }

  if (v === 'public') {
    const token = sp.get('token') ?? '';
    if (!token) return null;
    return { v, token };
  }

  if (v === 'habit_detail') {
    const id = sp.get('id') ?? '';
    if (!id) return null;
    return { v, id };
  }

  // Simple routes without additional parameters
  if (
    v === 'collections' ||
    v === 'tags_mentions' ||
    v === 'habits' ||
    v === 'todos' ||
    v === 'calendar' ||
    v === 'settings' ||
    v === 'notifications' ||
    v === 'loading'
  ) {
    return { v };
  }

  return null;
}

export function routeToView(route: Route): View {
  if (route.v === 'collections') return { type: 'collections' };
  if (route.v === 'collection') return { type: 'collection', id: route.id };
  if (route.v === 'collection_settings') return { type: 'collection_settings', id: route.id };
  if (route.v === 'snipsel') return { type: 'snipsel', id: route.id, returnTo: route.returnTo };
  if (route.v === 'tags_mentions') return { type: 'tags_mentions' };
  if (route.v === 'habits') return { type: 'habits' };
  if (route.v === 'habit_detail') return { type: 'habit_detail', id: route.id };
  if (route.v === 'search') return { type: 'search' };
  if (route.v === 'todos') return { type: 'todos' };
  if (route.v === 'calendar') return { type: 'calendar' };
  if (route.v === 'settings') return { type: 'settings' };
  if (route.v === 'notifications') return { type: 'notifications' };
  if (route.v === 'public') return { type: 'public', token: route.token };
  return { type: 'loading' };
}
export function viewToRoute(view: View): Route {
  if (view.type === 'collections') return { v: 'collections' };
  if (view.type === 'collection') return { v: 'collection', id: view.id };
  if (view.type === 'collection_settings') return { v: 'collection_settings', id: view.id };
  if (view.type === 'snipsel') return { v: 'snipsel', id: view.id, returnTo: view.returnTo };
  if (view.type === 'tags_mentions') return { v: 'tags_mentions' };
  if (view.type === 'habits') return { v: 'habits' };
  if (view.type === 'habit_detail') return { v: 'habit_detail', id: view.id };
  if (view.type === 'search') return { v: 'search' };
  if (view.type === 'todos') return { v: 'todos' };
  if (view.type === 'calendar') return { v: 'calendar' };
  if (view.type === 'settings') return { v: 'settings' };
  if (view.type === 'notifications') return { v: 'notifications' };
  if (view.type === 'public') return { v: 'public', token: view.token };
  return { v: 'loading' };
}
export function routeToUrl(route: Route, pathname = location.pathname): string {
  const sp = new URLSearchParams();
  sp.set('v', route.v);

  if (route.v === 'collection') {
    sp.set('id', route.id);
    if (route.sn) sp.set('sn', route.sn);
    if (typeof route.pos === 'number') sp.set('pos', String(clampPos(route.pos)));
  } else if (route.v === 'collection_settings' || route.v === 'snipsel') {
    sp.set('id', route.id);
    if (route.v === 'snipsel' && route.returnTo) sp.set('returnTo', route.returnTo);
  } else if (route.v === 'search') {
    if (route.q) sp.set('q', route.q);
  } else if (route.v === 'public') {
    sp.set('token', route.token);
  } else if (route.v === 'habit_detail') {
    sp.set('id', route.id);
  }

  const qs = sp.toString();
  return `${pathname}${qs ? `?${qs}` : ''}`;
}

export function getCurrentUrl(): string {
  return `${location.pathname}${location.search}`;
}

export function replaceUrl(nextUrl: string): void {
  if (getCurrentUrl() === nextUrl) return;
  history.replaceState(null, '', nextUrl);
}

export function pushUrl(nextUrl: string): void {
  if (getCurrentUrl() === nextUrl) return;
  history.pushState(null, '', nextUrl);
}
