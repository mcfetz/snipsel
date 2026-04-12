export type ApiError = {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
};

export type User = {
  id: string;
  username: string;
  email: string;
  created_at: string;
  default_collection_header_color?: string | null;
  carry_over_open_tasks?: boolean;
  theme?: 'light' | 'dark' | 'system';
  day_collection_template_id?: string | null;
  passcode_set?: boolean;
  otp_enabled?: boolean;
  passkeys_count?: number;
  max_upload_bytes?: number;
  ai_llm_url?: string | null;
  ai_model_name?: string | null;
  ai_api_key_set?: boolean;
  light_background_color?: string | null;
  dark_background_color?: string | null;
  is_admin?: boolean;
};

export type UserStats = {
  collections: number;
  snipsels: number;
  completed_tasks: number;
  attachments: number;
};

export type UserPasskey = {
  id: string;
  name: string;
  created_at: string;
};

export type ApiKey = {
  id: string;
  name: string;
  created_at: string;
  last_used_at: string | null;
};

export type Collection = {
  id: string;
  title: string;
  icon: string;
  header_image_url: string | null;
  header_color?: string | null;
  header_image_position?: string | null;
  header_image_x_position?: string | null;
  header_image_zoom?: number | null;
  is_favorite?: boolean;
  is_template: boolean;
  is_passcode_protected: boolean;
  show_completed_tasks: boolean;
  mute_notifications: boolean;
  default_snipsel_type: string | null;
  archived: boolean;
  list_for_day: string | null;
  created_at: string;
  modified_at: string;
  access_level?: 'owner' | 'write' | 'read';
  shared_by_username?: string | null;
  shared_out?: boolean;
  modified_by_id?: string;
  modified_by_username?: string | null;
  public_token?: string | null;
};
export type UserLite = { id: string; username: string };

export type CollectionBacklink = {
  snipsel_id: string;
  snipsel_content: string;
  collection_id: string;
  collection_title: string;
  collection_icon: string;
  position: number;
};


export type CollectionShare = {
  id: string;
  shared_with_user_id: string;
  shared_with_username?: string | null;
  permission: 'read' | 'write';
  created_at: string;
};

export type Notification = {
  id: string;
  message: string;
  is_read: boolean;
  snipsel_id?: string | null;
  collection_id?: string | null;
  created_at: string;
};

export type ReactionSummary = {
  emoji: string;
  count: number;
  me: boolean;
};

export type Snipsel = {
  id: string;
  type: string;
  card_view: boolean;
  content_markdown: string | null;
  task_done: boolean;
  done_at: string | null;
  done_by_id: string | null;
  done_by_username?: string | null;
  external_url: string | null;
  external_label: string | null;
  internal_target_snipsel_id: string | null;
  geo_lat?: number | null;
  geo_lng?: number | null;
  geo_accuracy_m?: number | null;
  reminder_at?: string | null;
  reminder_rrule?: string | null;
  created_at: string;
  created_by_id?: string;
  created_by_username?: string | null;
  modified_at: string;
  modified_by_id?: string;
  modified_by_username?: string | null;
  attachments: Array<{
    id: string;
    filename: string;
    mime_type: string | null;
    size_bytes: number;
    has_thumbnail: boolean;
  }>;
  tags?: string[];
  mentions?: string[];
  reactions?: ReactionSummary[];
};

export type SnipselDetailResponse = {
  snipsel: Snipsel;
  tags?: string[];
  mentions?: string[];
  placements?: Array<{ collection_id: string; position: number; indent: number }>;
  backlinks?: Array<{ from_snipsel_id: string; to_snipsel_id: string }>;
  has_collection_access?: boolean;
  has_write_access?: boolean;
  can_toggle_task_done?: boolean;
};

export type Attachment = {
  id: string;
  filename: string;
  mime_type: string | null;
  size_bytes: number;
  has_thumbnail: boolean;
};

export type CollectionItem = {
  collection_id: string;
  snipsel_id: string;
  position: number;
  indent: number;
  snipsel: Snipsel;
  collection_refs?: Array<{ title: string; collection_id: string }>;
};

export type SearchSnipselHit = {
  id: string;
  type: string;
  content_markdown: string | null;
  task_done: boolean;
  done_at: string | null;
  external_url: string | null;
  external_label: string | null;
  internal_target_snipsel_id: string | null;
  created_at: string;
  modified_at: string;
  collection_id?: string | null;
  collection_title?: string | null;
  collection_icon?: string | null;
  position?: number | null;
  has_collection_access?: boolean;
  has_write_access?: boolean;
  can_toggle_task_done?: boolean;
  reminder_at?: string | null;
  reminder_rrule?: string | null;
  attachments?: Attachment[];
  reactions?: ReactionSummary[];
  created_by_id?: string;
  created_by_username?: string | null;
  tags?: string[];
  mentions?: string[];
};

export type SearchCollectionHit = {
  id: string;
  title: string;
  icon: string;
  list_for_day: string | null;
};

export type SearchResponse = {
  snipsels: SearchSnipselHit[];
  collections: SearchCollectionHit[];
};

export type TagCount = { name: string; count: number };

/** Stable per-tab identifier sent with every API request so the backend can
 *  embed it as `origin_client_id` in SSE events. The originating tab then
 *  ignores those events since it already applied the optimistic update. */
export const CLIENT_ID: string = (() => {
  const KEY = '_snipsel_client_id';
  let id = sessionStorage.getItem(KEY);
  if (!id) { id = crypto.randomUUID(); sessionStorage.setItem(KEY, id); }
  return id;
})();

export async function requestJson<T>(path: string, init?: RequestInit & { timeout?: number }): Promise<T> {
  const { timeout = 10000, ...fetchInit } = init || {};
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  let res: Response;
  try {
    res = await fetch(path, {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-Client-Id': CLIENT_ID,
        ...(fetchInit?.headers ?? {}),
      },
      ...fetchInit,
      signal: controller.signal,
    });
  } catch (err: any) {
    if (err.name === 'AbortError') {
      throw {
        error: {
          code: 'network_error',
          message: 'Zeitüberschreitung bei der Verbindung zum Server.',
        },
      } as ApiError;
    }
    throw {
      error: {
        code: 'network_error',
        message: 'Keine Verbindung zum Server möglich.',
      },
    } as ApiError;
  } finally {
    clearTimeout(timeoutId);
  }

  if (res.status === 413) {
    throw {
      error: {
        code: 'payload_too_large',
        message: 'Die Datei ist zu groß für den Upload (Limit: 10MB).',
      },
    } as ApiError;
  }

  const contentType = res.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    const data = (await res.json()) as T | ApiError;
    if (!res.ok) {
      throw data;
    }
    return data as T;
  }

  if (!res.ok) {
    throw {
      error: {
        code: 'unknown_error',
        message: `Ein unerwarteter Fehler ist aufgetreten (${res.status}).`,
      },
    } as ApiError;
  }

  return {} as T;
}

import {
  idbGetAllCollections,
  idbGetCollection,
  idbSaveCollection,
  idbSaveCollections,
  idbDeleteCollection,
  idbEnqueueSync,
  idbSaveCollectionItems,
  idbReplaceCollectionItems,
  idbGetCollectionItems,
  idbDeleteCollectionItem,
  idbSaveCollectionItem,
  idbUpdateSnipselData,
  idbGetSyncQueue
} from './db';

/** Monotonically increasing counter. Incremented on every local mutation.
 *  Background refresh functions capture this before issuing a GET and discard
 *  the response if the counter changed, preventing stale overwrites. */
let mutationSeq = 0;

export const api = {
  getConfig: () => requestJson<{ registration_enabled: boolean; oidc_enabled: boolean; oidc_disable_password_login: boolean }>('/api/auth/config'),
  getOidcConfig: () => requestJson<{ enabled: boolean; provider_name: string | null }>('/api/auth/oidc/config'),
  oidcLogin: async () => {
    const { auth_url } = await requestJson<{ auth_url: string }>('/api/auth/oidc/login');
    const width = 500;
    const height = 600;
    const left = window.screenX + (window.outerWidth - width) / 2;
    const top = window.screenY + (window.outerHeight - height) / 2;
    const popup = window.open(
      auth_url,
      'oidc_login',
      `width=${width},height=${height},left=${left},top=${top},toolbar=no,menubar=no`
    );
    return popup;
  },
  register: (input: { username: string; email: string; password: string }) =>
    requestJson<{ user: User }>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(input),
    }),
  login: (input: { username: string; password: string }) =>
    requestJson<{ user?: User; status?: '2fa_required' }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(input),
    }),
  loginOtp: (code: string) =>
    requestJson<{ user: User }>('/api/auth/login/otp', {
      method: 'POST',
      body: JSON.stringify({ code }),
    }),
  twoFactor: {
    generate: () => requestJson<{ secret: string; provisioning_url: string }>('/api/auth/2fa/generate', { method: 'POST' }),
    qrUrl: () => '/api/auth/2fa/qr',
    enable: (input: { code: string; password_confirm: string }) =>
      requestJson<{ ok: true }>('/api/auth/2fa/enable', {
        method: 'POST',
        body: JSON.stringify(input),
      }),
    disable: (password_confirm: string) =>
      requestJson<{ ok: true }>('/api/auth/2fa/disable', {
        method: 'POST',
        body: JSON.stringify({ password_confirm }),
      }),
  },
  passkeys: {
    list: () => requestJson<{ passkeys: UserPasskey[] }>('/api/auth/passkeys'),
    registerBegin: () => requestJson<any>('/api/auth/passkeys/register/begin', { method: 'POST' }),
    registerComplete: (credential: any, name: string) =>
      requestJson<{ ok: true }>('/api/auth/passkeys/register/complete', {
        method: 'POST',
        body: JSON.stringify({ ...credential, name }),
      }),
    loginBegin: (username: string) =>
      requestJson<any>('/api/auth/passkeys/login/begin', {
        method: 'POST',
        body: JSON.stringify({ username }),
      }),
    loginComplete: (credential: any) =>
      requestJson<{ user: User }>('/api/auth/passkeys/login/complete', {
        method: 'POST',
        body: JSON.stringify(credential),
      }),
    delete: (id: string) => requestJson<{ ok: true }>(`/api/auth/passkeys/${id}`, { method: 'DELETE' }),
  },
  logout: () => requestJson<{ ok: true }>('/api/auth/logout', { method: 'POST' }),
  passcode: {
    set: (input: { passcode: string; password_confirm: string }) =>
      requestJson<{ ok: true }>('/api/auth/passcode/set', {
        method: 'POST',
        body: JSON.stringify(input),
      }),
    verify: (input: { passcode: string; collection_id: string }) =>
      requestJson<{ ok: true; unlocked_until: string }>('/api/auth/passcode/verify', {
        method: 'POST',
        body: JSON.stringify(input),
      }),
  },
  me: () => requestJson<{ user: User }>('/api/auth/me'),
  meStats: () => requestJson<{ stats: UserStats }>('/api/auth/me/stats'),
  updateMe: (input: {
    default_collection_header_color?: string | null;
    carry_over_open_tasks?: boolean;
    theme?: 'light' | 'dark' | 'system' | null;
    day_collection_template_id?: string | null;
    email?: string;
    password?: string;
    current_password?: string;
    ai_llm_url?: string | null;
    ai_model_name?: string | null;
    ai_api_key?: string | null;
  }) =>
    requestJson<{ user: User }>('/api/auth/me', {
      method: 'PATCH',
      body: JSON.stringify(input),
    }),
  
  ai: {
    generate: (input: { prompt: string; context?: string; attachment_ids?: string[] }) =>
      requestJson<{ text: string }>('/api/ai/generate', {
        method: 'POST',
        body: JSON.stringify(input),
      }),
    getModels: () =>
      requestJson<{ models: Array<{ id: string; name: string }> }>('/api/ai/models'),
  },

  collections: {
    list: async (includeArchived = false) => {
      const local = await idbGetAllCollections();
      const filteredLocal = includeArchived ? local : local.filter(c => !c.archived);
      
      const refresh = async () => {
        const seqBefore = mutationSeq;
        try {
          if (!navigator.onLine) return;
          const res = await requestJson<{ collections: Collection[] }>(
            `/api/collections${includeArchived ? '?include_archived=1' : ''}`,
            { timeout: 10000 }
          );
          if (mutationSeq !== seqBefore) return; // Discard stale response
          await idbSaveCollections(res.collections);
        } catch {}
      };

      if (filteredLocal.length > 0) {
        refresh(); // Background
        return { collections: filteredLocal };
      }

      try {
        if (!navigator.onLine) throw new Error('offline');
        const res = await requestJson<{ collections: Collection[] }>(
          `/api/collections${includeArchived ? '?include_archived=1' : ''}`,
          { timeout: 10000 }
        );
        await idbSaveCollections(res.collections);
        return res;
      } catch (err: any) {
        if (err?.error?.code === 'passcode_required' || (err?.error?.code && err.error.code !== 'network_error' && err.error.code !== 'unknown_error')) throw err;
        return { collections: filteredLocal };
      }
    },
    get: async (id: string) => {
      const local = await idbGetCollection(id);
      
      const refresh = async () => {
        try {
          if (!navigator.onLine) return;
          const res = await requestJson<{ collection: Collection }>(`/api/collections/${id}`, { timeout: 10000 });
          await idbSaveCollection(res.collection);
        } catch {}
      };

      if (local) {
        refresh(); // Background
        return { collection: local };
      }

      try {
        if (!navigator.onLine) throw new Error('offline');
        const res = await requestJson<{ collection: Collection }>(`/api/collections/${id}`, { timeout: 10000 });
        await idbSaveCollection(res.collection);
        return res;
      } catch (err: any) {
        if (err?.error?.code === 'passcode_required' || (err?.error?.code && err.error.code !== 'network_error' && err.error.code !== 'unknown_error')) throw err;
        throw err;
      }
    },
    today: (() => {
      let todayCache: Promise<{ collection: Collection }> | undefined;
      let lastDay: string | undefined;
      return async (day?: string) => {
        if (todayCache && lastDay === day) return todayCache;
        let promise: Promise<{ collection: Collection }> | undefined;
        promise = (async () => {
          try {
            if (!navigator.onLine) throw new Error('offline');
            const res = await requestJson<{ collection: Collection }>(
              `/api/collections/today${day ? `?day=${day}` : ''}`
            );
            await idbSaveCollection(res.collection);
            return res;
          } catch (err: any) {
            if (err?.error?.code === 'passcode_required' || (err?.error?.code && err.error.code !== 'network_error' && err.error.code !== 'unknown_error')) throw err;
            const all = await idbGetAllCollections();
            const match = all.find(c => c.list_for_day === (day || new Date().toISOString().slice(0, 10)));
            if (match) return { collection: match };
            throw err;
          } finally {
            if (todayCache === promise) todayCache = undefined;
          }
        })();
        todayCache = promise;
        lastDay = day;
        return promise;
      };
    })(),
    create: async (input: {
      title: string;
      icon?: string;
      header_image_url?: string | null;
      header_color?: string | null;
      default_snipsel_type?: string | null;
      show_completed_tasks?: boolean;
      mute_notifications?: boolean;
    }) => {
      const tempId = crypto.randomUUID();
      const collection: Collection = {
        id: tempId,
        title: input.title,
        icon: input.icon || '📝',
        header_image_url: input.header_image_url || null,
        header_color: input.header_color || null,
        is_template: false,
        is_passcode_protected: false,
        show_completed_tasks: input.show_completed_tasks ?? true,
        mute_notifications: input.mute_notifications ?? false,
        default_snipsel_type: input.default_snipsel_type || null,
        archived: false,
        list_for_day: null,
        created_at: new Date().toISOString(),
        modified_at: new Date().toISOString(),
        access_level: 'owner',
      };
      await idbSaveCollection(collection);
      await idbEnqueueSync('POST', '/api/collections', { ...input, _tempId: tempId });
      return { collection };
    },
    update: async (
      id: string,
      input: {
        title?: string;
        icon?: string;
        header_image_url?: string | null;
        header_color?: string | null;
        archived?: boolean;
        is_template?: boolean;
        default_snipsel_type?: string | null;
        is_passcode_protected?: boolean;
        show_completed_tasks?: boolean;
        mute_notifications?: boolean;
        header_image_position?: string | null;
        header_image_x_position?: string | null;
        header_image_zoom?: number | null;
      }
    ) => {
      const col = await idbGetCollection(id);
      if (col) {
        const updated = { ...col, ...input };
        await idbSaveCollection(updated);
        await idbEnqueueSync('PATCH', `/api/collections/${id}`, input);
        return { collection: updated };
      }
      throw { error: { code: 'not_found', message: 'Kollektion nicht gefunden.' } } as ApiError;
    },

    uploadHeaderImage: async (id: string, file: File, onProgress?: (percent: number) => void) => {
      return new Promise<{ collection: Collection }>((resolve, reject) => {
        const form = new FormData();
        form.append('file', file);

        const xhr = new XMLHttpRequest();
        xhr.open('POST', `/api/collections/${id}/header-image`);
        xhr.withCredentials = true;

        if (onProgress) {
          xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
              onProgress((e.loaded / e.total) * 100);
            }
          };
        }

        xhr.onload = () => {
          if (xhr.status === 413) {
            reject({
              error: {
                code: 'payload_too_large',
                message: 'Die Datei ist zu groß für den Upload.',
              },
            } as ApiError);
            return;
          }

          let data: any;
          try {
            data = JSON.parse(xhr.responseText);
          } catch {
            data = { error: { code: 'unknown_error', message: `Ein unerwarteter Fehler ist aufgetreten (${xhr.status}).` } };
          }

          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(data);
          } else {
            reject(data);
          }
        };

        xhr.onerror = () => {
          reject({ error: { code: 'network_error', message: 'Netzwerkfehler beim Upload.' } } as ApiError);
        };

        xhr.send(form);
      });
    },

    favorite: async (id: string) => {
      const col = await idbGetCollection(id);
      if (col) { col.is_favorite = true; await idbSaveCollection(col); }
      await idbEnqueueSync('POST', `/api/collections/${id}/favorite`);
      return { ok: true as const };
    },
    unfavorite: async (id: string) => {
      const col = await idbGetCollection(id);
      if (col) { col.is_favorite = false; await idbSaveCollection(col); }
      await idbEnqueueSync('DELETE', `/api/collections/${id}/favorite`);
      return { ok: true as const };
    },
    delete: async (id: string) => {
      await idbDeleteCollection(id);
      await idbEnqueueSync('DELETE', `/api/collections/${id}`);
      return { ok: true as const };
    },
    autocomplete: (q: string) =>
      requestJson<{ collections: Array<{ id: string; title: string; icon: string }> }>(
        `/api/collections/autocomplete?q=${encodeURIComponent(q)}`
      ),

    listShares: (() => {
      const shareCache: Record<string, Promise<{ shares: CollectionShare[] }> | undefined> = {};
      return async (id: string) => {
        if (shareCache[id]) return shareCache[id];
        const promise = (async () => {
          try {
            return await requestJson<{ shares: CollectionShare[] }>(`/api/collections/${id}/shares`);
          } finally {
            delete shareCache[id];
          }
        })();
        shareCache[id] = promise;
        return promise;
      };
    })(),
    createShare: (id: string, input: { shared_with_user_id: string; permission: 'read' | 'write' }) =>
      requestJson<{ share: { id: string } }>(`/api/collections/${id}/shares`, {
        method: 'POST',
        body: JSON.stringify(input),
      }),
    deleteShare: (id: string, shareId: string) =>
      requestJson<{ ok: true }>(`/api/collections/${id}/shares/${shareId}`, { method: 'DELETE' }),

    insertTemplate: (id: string, templateCollectionId: string) =>
      requestJson<{ ok: true }>(`/api/collections/${id}/insert_template`, {
        method: 'POST',
        body: JSON.stringify({ template_collection_id: templateCollectionId }),
      }),
    listBacklinks: (id: string) => requestJson<{ backlinks: CollectionBacklink[] }>(`/api/collections/${id}/backlinks`),
    listRecent: () => requestJson<{ collections: Array<{ id: string; title: string; icon: string }> }>('/api/collections/recent'),
    clearRecent: () => requestJson<{ ok: true }>('/api/collections/recent', { method: 'DELETE' }),
    deleteCompletedTasks: (id: string) => requestJson<{ ok: true; count: number }>(`/api/collections/${id}/snipsels/completed`, { method: 'DELETE' }),
    resetCompletedTasks: (id: string) => requestJson<{ ok: true; count: number }>(`/api/collections/${id}/snipsels/completed/reset`, { method: 'POST' }),
    trash: () => requestJson<{ collections: Collection[] }>('/api/collections/trash'),
    emptyTrash: () => requestJson<{ ok: true; deleted: number }>('/api/collections/trash', { method: 'DELETE' }),
    deleteTrashItem: (id: string) => requestJson<{ ok: true; deleted: number }>(`/api/collections/trash/${id}`, { method: 'DELETE' }),
    restore: (id: string) => requestJson<{ collection: Collection }>(`/api/collections/${id}/restore`, { method: 'POST' }),
  },

  users: {
    list: () => requestJson<{ users: UserLite[] }>('/api/users'),
  },

  snipsels: {
    list: async (collectionId: string) => {
      const local = await idbGetCollectionItems(collectionId);

      const refresh = async () => {
        const seqBefore = mutationSeq;
        try {
          if (!navigator.onLine) return;
          
          const syncQueue = await idbGetSyncQueue();
          if (syncQueue.length > 0) return; // Do not pull stale server state while local mutations are still flushing

          const res = await requestJson<{ items: CollectionItem[] }>(
            `/api/collections/${collectionId}/snipsels`,
            { timeout: 10000, cache: 'no-store' }
          );
          if (mutationSeq !== seqBefore) return; // Discard stale response
          await idbReplaceCollectionItems(collectionId, res.items);
          // Notify UI to update store with fresh server data
          if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('snipsel-items-refreshed', {
              detail: { collectionId, items: res.items }
            }));
          }
        } catch {}
      };

      if (local.length > 0) {
        refresh(); // Background
        return { items: local };
      }

      try {
        if (!navigator.onLine) throw new Error('offline');
        const res = await requestJson<{ items: CollectionItem[] }>(
          `/api/collections/${collectionId}/snipsels`,
          { timeout: 10000 }
        );
        await idbSaveCollectionItems(res.items);
        return res;
      } catch (err: any) {
        if (err?.error?.code === 'passcode_required' || (err?.error?.code && err.error.code !== 'network_error' && err.error.code !== 'unknown_error')) throw err;
        return { items: local };
      }
    },
    get: (snipselId: string) =>
      // We don't cache individual snipsels yet, but usually `list` caches them inside `CollectionItem`.
      // For now, `get` can just fail if offline, as it's rarely used directly offline.
      requestJson<{ snipsel: Snipsel }>(`/api/snipsels/${snipselId}`),
    create: async (
      collectionId: string,
      input: {
        type?: string;
        card_view?: boolean;
        content_markdown?: string;
        geo_lat?: number;
        geo_lng?: number;
        geo_accuracy_m?: number;
        indent?: number;
        position?: number;
      }
    ) => {
      const tempId = crypto.randomUUID();
      const snipsel: Snipsel = {
        id: tempId,
        type: input.type || 'text',
        card_view: input.card_view ?? true,
        content_markdown: input.content_markdown || null,
        task_done: false,
        done_at: null,
        done_by_id: null,
        external_url: null,
        external_label: null,
        internal_target_snipsel_id: null,
        geo_lat: input.geo_lat,
        geo_lng: input.geo_lng,
        geo_accuracy_m: input.geo_accuracy_m,
        created_at: new Date().toISOString(),
        modified_at: new Date().toISOString(),
        attachments: [],
        tags: [],
        mentions: [],
        reactions: []
      };

      let finalPosition = input.position;
      if (typeof finalPosition === 'undefined') {
        const items = await idbGetCollectionItems(collectionId);
        finalPosition = items.length > 0 ? items[items.length - 1].position + 100 : 100;
      }

      const item: CollectionItem = {
        collection_id: collectionId,
        snipsel_id: tempId,
        position: finalPosition,
        indent: input.indent || 0,
        snipsel
      };
      await idbSaveCollectionItem(item);
      mutationSeq++;
      const syncPayload = { ...input, _tempId: tempId, position: finalPosition };
      await idbEnqueueSync('POST', `/api/collections/${collectionId}/snipsels`, syncPayload);
      return { item };
    },
    update: async (
      snipselId: string,
      input: {
        type?: string;
        card_view?: boolean;
        content_markdown?: string | null;
        task_done?: boolean;
        external_url?: string | null;
        external_label?: string | null;
        internal_target_snipsel_id?: string | null;
        reminder_at?: string | null;
        reminder_rrule?: string | null;
      }
    ) => {
      await idbUpdateSnipselData(snipselId, input);
      mutationSeq++;
      await idbEnqueueSync('PATCH', `/api/snipsels/${snipselId}`, input);
      return { snipsel: { id: snipselId, ...input } as unknown as Snipsel };
    },
    delete: async (collectionId: string, snipselId: string) => {
      await idbDeleteCollectionItem(collectionId, snipselId);
      mutationSeq++;
      await idbEnqueueSync('DELETE', `/api/collections/${collectionId}/snipsels/${snipselId}`);
      return { ok: true as const };
    },
    copy: (collectionId: string, snipselId: string) =>
      requestJson<{ item: CollectionItem }>(
        `/api/collections/${collectionId}/snipsels/${snipselId}/copy`,
        { method: 'POST' }
      ),
    reference: (collectionId: string, snipselId: string, indent?: number) =>
      requestJson<{ item: CollectionItem }>(
        `/api/collections/${collectionId}/snipsels/${snipselId}/reference`,
        { method: 'POST', body: JSON.stringify({ indent }) }
      ),
    reorder: async (
      collectionId: string,
      items: Array<{ snipsel_id: string; position: number; indent: number }>
    ) => {
      const existing = await idbGetCollectionItems(collectionId);
      for (const i of items) {
        const m = existing.find(e => e.snipsel_id === i.snipsel_id);
        if (m) {
          m.position = i.position;
          m.indent = i.indent;
          await idbSaveCollectionItem(m);
        }
      }
      mutationSeq++;
      await idbEnqueueSync('PATCH', `/api/collections/${collectionId}/snipsels/reorder`, { items });
      return { ok: true as const };
    },
    toggleReaction: async (snipselId: string, emoji: string) => {
      // Local update helper logic is in the UI component, but we should update it in idb if possible.
      // However, idbUpdateSnipselData can be used. 
      // For now, consistent with others: enqueue and return.
      await idbEnqueueSync('POST', `/api/snipsels/${snipselId}/reactions`, { emoji });
      return { message: 'Queued', active: true };
    },
    trash: () => requestJson<{ snipsels: Snipsel[] }>('/api/snipsels/trash'),
    emptyTrash: () => requestJson<{ ok: true; deleted: number }>('/api/snipsels/trash', { method: 'DELETE' }),
    deleteTrashItem: (id: string) => requestJson<{ ok: true; deleted: number }>(`/api/snipsels/trash/${id}`, { method: 'DELETE' }),
    restore: (id: string, collectionId?: string) => requestJson<{ snipsel: Snipsel }>(`/api/snipsels/${id}/restore`, {
      method: 'POST',
      body: JSON.stringify(collectionId ? { collection_id: collectionId } : {}),
    }),
  },

  notifications: {
    list: (() => {
      let notifCache: Promise<{ notifications: Notification[] }> | undefined;
      return async () => {
        if (notifCache) return notifCache;
        let promise: Promise<{ notifications: Notification[] }> | undefined;
        promise = (async () => {
          try {
            return await requestJson<{ notifications: Notification[] }>('/api/notifications');
          } finally {
            if (notifCache === promise) notifCache = undefined;
          }
        })();
        notifCache = promise;
        return promise;
      };
    })(),
    markRead: (id: string) => requestJson<{ success: boolean }>(`/api/notifications/${id}/mark-read`, { method: 'POST' }),
    markAllRead: () => requestJson<{ success: boolean }>('/api/notifications/mark-all-read', { method: 'POST' }),
    deleteRead: () => requestJson<{ success: boolean }>('/api/notifications/read', { method: 'DELETE' }),
    testPush: () => requestJson<{ success: boolean }>('/api/notifications/test-push', { method: 'POST' }),
  },

  attachments: {
    upload: async (snipselId: string, file: File, onProgress?: (percent: number) => void) => {
      if (!navigator.onLine) {
        return Promise.reject({ error: { code: 'offline', message: 'You cannot upload attachments while offline.' } } as ApiError);
      }
      return new Promise<{ attachment: Attachment }>((resolve, reject) => {
        const form = new FormData();
        form.append('file', file);

        const xhr = new XMLHttpRequest();
        xhr.open('POST', `/api/snipsels/${snipselId}/attachments`);
        xhr.withCredentials = true;

        if (onProgress) {
          xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
              onProgress((e.loaded / e.total) * 100);
            }
          };
        }

        xhr.onload = () => {
          if (xhr.status === 413) {
            reject({
              error: {
                code: 'payload_too_large',
                message: 'Die Datei ist zu groß für den Upload.',
              },
            } as ApiError);
            return;
          }

          let data: any;
          try {
            data = JSON.parse(xhr.responseText);
          } catch {
            data = { error: { code: 'unknown_error', message: `Ein unerwarteter Fehler ist aufgetreten (${xhr.status}).` } };
          }

          if (xhr.status >= 200 && xhr.status < 300) {
            if (data.attachment) {
              import('./db').then(async ({ getDB }) => {
                const db = await getDB();
                const tx = db.transaction('collectionItems', 'readwrite');
                const items = await tx.store.getAll();
                const matched = items.filter((item) => item.snipsel_id === snipselId);
                for (const item of matched) {
                  const atts = item.snipsel.attachments || [];
                  // Only push if it's not already in there
                  if (!atts.find(a => a.id === data.attachment.id)) {
                    item.snipsel = { ...item.snipsel, attachments: [...atts, data.attachment] };
                    await tx.store.put(item);
                  }
                }
                await tx.done;
                resolve(data);
              }).catch((e) => {
                console.error("IDB attachment save failed", e);
                resolve(data);
              });
            } else {
              resolve(data);
            }
          } else {
            reject(data);
          }
        };

        xhr.onerror = () => {
          reject({ error: { code: 'network_error', message: 'Netzwerkfehler beim Upload.' } } as ApiError);
        };

        xhr.send(form);
      });
    },
    delete: async (attachmentId: string) => {
      if (!navigator.onLine) {
        await idbEnqueueSync('DELETE', `/api/attachments/${attachmentId}`);
        return { ok: true as const };
      }
      try {
        const res = await requestJson<{ ok: true }>(`/api/attachments/${attachmentId}`, {
          method: 'DELETE',
          timeout: 2000,
        });
        return res;
      } catch (err: any) {
        if (err?.error?.code && err.error.code !== 'network_error' && err.error.code !== 'unknown_error') throw err;
        await idbEnqueueSync('DELETE', `/api/attachments/${attachmentId}`);
        return { ok: true as const };
      }
    },
    downloadUrl: (attachmentId: string) => `/api/attachments/${attachmentId}`,
    thumbnailUrl: (attachmentId: string) => `/api/attachments/${attachmentId}/thumbnail`,
  },

  search: (params: {
    q?: string;
    tag?: string;
    mention?: string;
    mentions_me?: boolean;
    type?: string;
    task_done?: boolean;
    include_archived?: boolean;
    day?: string;
    scope?: 'my' | 'shared' | 'all';
  }) => {
    const sp = new URLSearchParams();
    if (params.q) sp.set('q', params.q);
    if (params.tag) sp.set('tag', params.tag);
    if (params.mention) sp.set('mention', params.mention);
    if (params.mentions_me) sp.set('mentions_me', '1');
    if (params.type) sp.set('type', params.type);
    if (typeof params.task_done === 'boolean') sp.set('task_done', params.task_done ? '1' : '0');
    if (params.include_archived) sp.set('include_archived', '1');
    if (params.day) sp.set('day', params.day);
    if (params.scope) sp.set('scope', params.scope);
    const qs = sp.toString();
    return requestJson<SearchResponse>(`/api/search${qs ? `?${qs}` : ''}`);
  },

  geo: {
    getSnipselsByBounds: (bounds: {
      ne_lat: number;
      ne_lng: number;
      sw_lat: number;
      sw_lng: number;
      scope?: 'my' | 'shared';
    }) => {
      const sp = new URLSearchParams();
      sp.set('ne_lat', bounds.ne_lat.toString());
      sp.set('ne_lng', bounds.ne_lng.toString());
      sp.set('sw_lat', bounds.sw_lat.toString());
      sp.set('sw_lng', bounds.sw_lng.toString());
      if (bounds.scope) sp.set('scope', bounds.scope);
      return requestJson<{
        snipsels: Array<{
          id: string;
          lat: number;
          lng: number;
          excerpt: string;
          type: string;
          task_done: boolean;
          collection: {
            id: string;
            title: string;
            icon: string;
            header_color: string | null;
          };
          created_at: string;
        }>;
        bounds: {
          ne: { lat: number; lng: number };
          sw: { lat: number; lng: number };
        };
        count: number;
      }>(`/api/geo/snipsels?${sp.toString()}`);
    },
    getAllSnipselsWithGeo: () => {
      return requestJson<{
        snipsels: Array<{
          id: string;
          lat: number;
          lng: number;
          excerpt: string;
          type: string;
          task_done: boolean;
          collection: {
            id: string;
            title: string;
            icon: string;
            header_color: string | null;
          };
          created_at: string;
        }>;
        count: number;
      }>('/api/geo/snipsels/all');
    },
  },

  tags: {
    list: (scope?: 'my' | 'shared' | 'all', q?: string) => {
      const sp = new URLSearchParams();
      if (scope) sp.set('scope', scope);
      if (q) sp.set('q', q);
      const qs = sp.toString();
      return requestJson<{ tags: TagCount[] }>(`/api/tags${qs ? `?${qs}` : ''}`);
    },
  },

  mentions: {
    list: (scope?: 'my' | 'shared' | 'all', q?: string) => {
      const sp = new URLSearchParams();
      if (scope) sp.set('scope', scope);
      if (q) sp.set('q', q);
      const qs = sp.toString();
      return requestJson<{ mentions: TagCount[] }>(`/api/mentions${qs ? `?${qs}` : ''}`);
    },
    getIncomingDayMentions: (day: string) => {
      return requestJson<{ snipsels: SearchSnipselHit[] }>(`/api/search/mentions/incoming?day=${encodeURIComponent(day)}`);
    },
  },

  importer: {
    twosLogin: (username: string, password: string) => {
      return requestJson<{ user: { id: string; username: string; token: string } }>(
        '/api/importer/twos/login',
        {
          method: 'POST',
          body: JSON.stringify({ username, password }),
        }
      );
    },
    twosLists: (lastSync: string, userId: string, token: string) => {
      return requestJson<{ lists: Array<{ id: string; name: string; isDaily: boolean; emoji: string }> }>(
        '/api/importer/twos/lists',
        {
          method: 'POST',
          body: JSON.stringify({ lastSync, userId, token }),
        }
      );
    },
    importFromTwoS: (input: { listIds: string[]; overwrite: boolean; token: string; userId: string }) => {
      return requestJson<{ imported: number; skipped: number; errors: string[] }>(
        '/api/importer/twos/import',
        {
          method: 'POST',
          body: JSON.stringify({ listIds: input.listIds, overwrite: input.overwrite, token: input.token, userId: input.userId }),
        }
      );
    },
    twosSearch: (query: string, userId: string, token: string) => {
      return requestJson<{ lists: Array<{ id: string; name: string; isDaily: boolean; emoji: string; thingsCount: number }> }>(
        '/api/importer/twos/search',
        {
          method: 'POST',
          body: JSON.stringify({ query, userId, token }),
        }
      );
    },
  },
  public: {
    getCollection: (token: string) =>
      requestJson<{
        collection: {
          id: string;
          title: string;
          icon: string;
          header_color: string | null;
          header_image_url: string | null;
          header_image_position: string | null;
          header_image_x_position: string | null;
          header_image_zoom: number | null;
          is_passcode_protected: boolean;
          is_unlocked: boolean;
          default_snipsel_type: string | null;
        }
      }>(`/api/public/collections/${token}`),
    verifyPasscode: (token: string, passcode: string) =>
      requestJson<{ ok: true }>(`/api/public/collections/${token}/passcode/verify`, {
        method: 'POST',
        body: JSON.stringify({ passcode }),
      }),
    listSnipsels: (token: string) =>
      requestJson<{ items: CollectionItem[], can_write: boolean }>(`/api/public/collections/${token}/snipsels`),
    createSnipsel: (token: string, input: { content_markdown: string; type: string; indent?: number }) =>
      requestJson<{ item: CollectionItem }>(`/api/public/collections/${token}/snipsels`, {
        method: 'POST',
        body: JSON.stringify(input),
      }),
    patchSnipsel: (token: string, snipselId: string, input: { content_markdown?: string; type?: string; task_done?: boolean }) =>
      requestJson<{ item: CollectionItem }>(`/api/public/collections/${token}/snipsels/${snipselId}`, {
        method: 'PATCH',
        body: JSON.stringify(input),
      }),
    deleteSnipsel: (token: string, snipselId: string) =>
      requestJson<{ ok: true }>(`/api/public/collections/${token}/snipsels/${snipselId}`, {
        method: 'DELETE',
      }),
  },
  apiKeys: {
    list: () => requestJson<{ api_keys: ApiKey[] }>('/api/api_keys'),
    create: (name: string) =>
      requestJson<{ api_key: ApiKey & { key: string } }>('/api/api_keys', {
        method: 'POST',
        body: JSON.stringify({ name }),
      }),
    delete: (id: string) =>
      requestJson<{ ok: true }>(`/api/api_keys/${id}`, {
        method: 'DELETE',
      }),
  },
  admin: {
    listUsers: () => requestJson<{ users: Array<{ id: string; username: string; email: string; is_admin: boolean; is_active: boolean; created_at: string; last_login: string | null }> }>('/api/admin/users'),
    createUser: (input: { username: string; email: string; password: string; is_admin?: boolean }) =>
      requestJson<{ user: { id: string; username: string; email: string; is_admin: boolean; is_active: boolean; created_at: string } }>('/api/admin/users', {
        method: 'POST',
        body: JSON.stringify(input),
      }),
    deleteUser: (id: string) =>
      requestJson<{ ok: true }>(`/api/admin/users/${id}`, {
        method: 'DELETE',
      }),
    updateUser: (id: string, input: { is_admin?: boolean; is_active?: boolean }) =>
      requestJson<{ user: { id: string; username: string; email: string; is_admin: boolean; is_active: boolean; created_at: string } }>(`/api/admin/users/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(input),
      }),
  },
};
