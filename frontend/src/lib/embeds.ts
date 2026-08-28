export type DeezerEmbed = {
  type: 'track' | 'album' | 'artist' | null;
  id: string | null;
  url: string;
};

export type SpotifyEmbed = {
  url: string;
};

export type YouTubeEmbed = {
  id: string;
  url: string;
};

export type MapEmbed = {
  lat?: number;
  lng?: number;
  url: string;
};

export type GenericLinkEmbed = {
  url: string;
};

export type ParsedEmbeds = {
  deezer: DeezerEmbed | null;
  spotify: SpotifyEmbed | null;
  youtube: YouTubeEmbed | null;
  map: MapEmbed | null;
  generic: GenericLinkEmbed | null;
  collectionId: string | null;
  strippedText: string;
};

export function getDeezerLink(text: string | null): DeezerEmbed | null {
  if (!text) return null;
  const stdMatch = text.match(/https?:\/\/(?:www\.)?deezer\.com\/(track|album|artist)\/(\d+)/);
  if (stdMatch) {
    return { type: stdMatch[1] as 'track' | 'album' | 'artist', id: stdMatch[2], url: stdMatch[0] };
  }
  const shortMatch = text.match(/https?:\/\/link\.deezer\.com\/s\/[A-Za-z0-9]+/);
  if (shortMatch) {
    return { type: null, id: null, url: shortMatch[0] };
  }
  return null;
}

export function getSpotifyLink(text: string | null): SpotifyEmbed | null {
  if (!text) return null;
  const match = text.match(/https?:\/\/open\.spotify\.com\/(track|album|artist|playlist|episode|show)\/[a-zA-Z0-9]+/);
  if (match) {
    return { url: match[0] };
  }
  const shortMatch = text.match(/https?:\/\/spotify\.link\/[a-zA-Z0-9]+/);
  if (shortMatch) {
    return { url: shortMatch[0] };
  }
  return null;
}

export function getYouTubeLink(text: string | null): YouTubeEmbed | null {
  if (!text) return null;
  const match = text.match(/https?:\/\/(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|v\/|shorts\/)|youtu\.be\/)([A-Za-z0-9_-]{11})(?:[^\s\)]*)/);
  if (match) {
    return { id: match[1], url: match[0] };
  }
  return null;
}

export function getMapLink(text: string | null): MapEmbed | null {
  if (!text) return null;
  const googleShortMatch = text.match(/https?:\/\/maps\.app\.goo\.gl\/[A-Za-z0-9]+/);
  const appleShortMatch = text.match(/https?:\/\/maps\.apple(?:\.com)?\/p\/[^\s]*/);
  if (googleShortMatch || appleShortMatch) {
    const match = googleShortMatch || appleShortMatch;
    return { url: match![0] };
  }
  const googleAtMatch = text.match(/https?:\/\/(?:www\.)?google\.com\/maps\/[^\s]*@(-?\d+\.\d+),(-?\d+\.\d+)[^\s]*/);
  const googleQMatch = text.match(/https?:\/\/(?:www\.)?google\.com\/maps\?[^\s]*[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)[^\s]*/);
  const mapsGoogleQMatch = text.match(/https?:\/\/maps\.google\.[a-z]+\/?\?[^\s]*[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)[^\s]*/);
  const appleLlMatch = text.match(/https?:\/\/(?:www\.)?maps\.apple\.com\/?[^\s]*[?&]ll=(-?\d+\.\d+),(-?\d+\.\d+)[^\s]*/);
  const appleQMatch = text.match(/https?:\/\/(?:www\.)?maps\.apple\.com\/?[^\s]*[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)[^\s]*/);
  const appleCenterMatch = text.match(/https?:\/\/(?:www\.)?maps\.apple\.com\/?[^\s]*[?&]center=(-?\d+\.\d+),(-?\d+\.\d+)[^\s]*/);
  const appleCoordMatch = text.match(/https?:\/\/(?:www\.)?maps\.apple\.com\/?[^\s]*[?&]coordinate=(-?\d+\.\d+),(-?\d+\.\d+)[^\s]*/);

  if (googleAtMatch) return { lat: parseFloat(googleAtMatch[1]), lng: parseFloat(googleAtMatch[2]), url: googleAtMatch[0] };
  if (googleQMatch) return { lat: parseFloat(googleQMatch[1]), lng: parseFloat(googleQMatch[2]), url: googleQMatch[0] };
  if (mapsGoogleQMatch) return { lat: parseFloat(mapsGoogleQMatch[1]), lng: parseFloat(mapsGoogleQMatch[2]), url: mapsGoogleQMatch[0] };
  if (appleLlMatch) return { lat: parseFloat(appleLlMatch[1]), lng: parseFloat(appleLlMatch[2]), url: appleLlMatch[0] };
  if (appleQMatch) return { lat: parseFloat(appleQMatch[1]), lng: parseFloat(appleQMatch[2]), url: appleQMatch[0] };
  if (appleCenterMatch) return { lat: parseFloat(appleCenterMatch[1]), lng: parseFloat(appleCenterMatch[2]), url: appleCenterMatch[0] };
  if (appleCoordMatch) return { lat: parseFloat(appleCoordMatch[1]), lng: parseFloat(appleCoordMatch[2]), url: appleCoordMatch[0] };
  return null;
}

export function getGenericLink(text: string | null): GenericLinkEmbed | null {
  if (!text) return null;
  if (getDeezerLink(text) || getSpotifyLink(text) || getYouTubeLink(text) || getMapLink(text)) return null;
  const trimmed = text.trim();
  const urlMatch = trimmed.match(/^(https?:\/\/\S+)$/);
  if (urlMatch) {
    return { url: urlMatch[1] };
  }
  return null;
}

export function getCollectionLink(
  text: string | null,
  refs?: Array<{ title: string; collection_id: string }>
): string | null {
  if (!text || !refs || refs.length === 0) return null;
  const trimmed = text.trim();
  const match = trimmed.match(/^\[\[([^\]]+)\]\]$/);
  if (!match) return null;

  const title = match[1]
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");

  const ref = refs.find((r) => r.title.toLowerCase() === title.toLowerCase());
  return ref ? ref.collection_id : null;
}

const embedCache = new Map<string, ParsedEmbeds>();
const MAX_EMBED_CACHE = 400;

export function parseSnipselEmbeds(
  text: string | null,
  refs?: Array<{ title: string; collection_id: string }>
): ParsedEmbeds {
  if (!text) {
    return { deezer: null, spotify: null, youtube: null, map: null, generic: null, collectionId: null, strippedText: '' };
  }
  const refsKey = refs && refs.length > 0 ? refs.map((r) => `${r.title}:${r.collection_id}`).join(',') : '';
  const cacheKey = `${refsKey}|${text}`;
  const cached = embedCache.get(cacheKey);
  if (cached) return cached;

  const dz = getDeezerLink(text);
  const sp = getSpotifyLink(text);
  const yt = getYouTubeLink(text);
  const ml = getMapLink(text);
  const gl = (!dz && !sp && !yt && !ml) ? getGenericLink(text) : null;
  const cid = getCollectionLink(text, refs);

  let stripped = text;
  if (dz) stripped = stripped.replace(dz.url, '');
  if (sp) stripped = stripped.replace(sp.url, '');
  if (yt) stripped = stripped.replace(yt.url, '');
  if (ml) stripped = stripped.replace(ml.url, '');
  if (gl) stripped = stripped.replace(gl.url, '');
  if (cid) {
    stripped = '';
  } else {
    stripped = stripped.trim();
  }

  const result: ParsedEmbeds = {
    deezer: dz,
    spotify: sp,
    youtube: yt,
    map: ml,
    generic: gl,
    collectionId: cid,
    strippedText: stripped,
  };

  if (embedCache.size >= MAX_EMBED_CACHE) {
    const first = embedCache.keys().next().value;
    if (first) embedCache.delete(first);
  }
  embedCache.set(cacheKey, result);
  return result;
}

export function stripMediaLinks(
  text: string | null,
  refs?: Array<{ title: string; collection_id: string }>
): string {
  if (!text) return '';
  return parseSnipselEmbeds(text, refs).strippedText;
}
