import MarkdownIt from 'markdown-it';

export const md = new MarkdownIt({ html: false, linkify: true, breaks: true });

const defaultRender =
  md.renderer.rules.fence ||
  function (tokens, idx, options, _env, self) {
    return self.renderToken(tokens, idx, options);
  };

md.renderer.rules.fence = function (tokens, idx, options, env, self) {
  const token = tokens[idx];
  const info = token.info ? token.info.trim() : '';

  if (info.toLowerCase().startsWith('mermaid')) {
    return `<div class="mermaid-unprocessed" data-mermaid="${md.utils.escapeHtml(token.content)}"></div>\n`;
  }

  return defaultRender(tokens, idx, options, env, self);
};

const mdCache = new Map<string, string>();
const MAX_MD_CACHE = 500;

export function renderMarkdownCore(text: string, tokenBg: string, tokenFg: string): string {
  const preprocessed = text.trim().replace(/^[ \t]*$/gm, '\u00a0');
  const html = md.render(preprocessed).trim();
  return html
    .replace(
      /(^|[^\p{L}\p{N}_])(#[A-Za-z\p{L}][\p{L}\p{N}_-]*|@[A-Za-z\p{L}][\p{L}\p{N}_-]*)/gu,
      (m, p1, token) => {
        const isTag = token.startsWith('#');
        const value = token.slice(1);
        const attr = isTag ? `data-tag="${value}"` : `data-mention="${value}"`;
        return `${p1}<mark class="snip-token cursor-pointer" ${attr} style="background-color:${tokenBg}; color:${tokenFg}">${token}</mark>`;
      }
    )
    .replace(/==([^=]+)==/g, `<mark style="background-color:${tokenBg}; border-radius: 0.25rem; padding: 0 0.125rem">$1</mark>`)
    .replace(/<a /g, `<a style="color:${tokenFg}; text-decoration:underline" target="_blank" rel="noopener noreferrer" `)
    .replace(/<blockquote>/g, `<blockquote style="border-left: 3px solid ${tokenFg}; background-color:${tokenBg}; margin: 0.25rem 0; padding: 0.25rem 0.75rem; border-radius: 0 0.25rem 0.25rem 0; opacity: 0.9;">`)
    .replace(/>\s+</g, '><')
    .replace(/<br>\n/g, '<br>');
}

export function renderMarkdown(
  text: string | null,
  tokenBg = 'rgba(79, 70, 229, 0.14)',
  tokenFg = '#4f46e5'
): string {
  if (!text) return '';
  const key = `${tokenBg}|${tokenFg}|__raw__|${text}`;
  const cached = mdCache.get(key);
  if (cached !== undefined) return cached;

  const html = renderMarkdownCore(text, tokenBg, tokenFg);
  if (mdCache.size >= MAX_MD_CACHE) {
    const first = mdCache.keys().next().value;
    if (first) mdCache.delete(first);
  }
  mdCache.set(key, html);
  return html;
}

export function renderWithWikiLinks(
  content: string,
  refs?: Array<{ title: string; collection_id: string }>,
  tokenBg = 'rgba(79, 70, 229, 0.14)',
  tokenFg = '#4f46e5'
): string {
  if (!content) return '';
  const refsKey = refs && refs.length > 0 ? refs.map((r) => `${r.title}:${r.collection_id}`).join(',') : '';
  const key = `${tokenBg}|${tokenFg}|${refsKey}|${content}`;

  const cached = mdCache.get(key);
  if (cached !== undefined) return cached;

  let html = renderMarkdownCore(content, tokenBg, tokenFg);
  if (refs && refs.length > 0) {
    const refMap = new Map<string, string>();
    for (const r of refs) {
      refMap.set(r.title.toLowerCase(), r.collection_id);
    }
    html = html.replace(/\[\[([^\]]+)\]\]/g, (_match, title: string) => {
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
  } else {
    html = html.replace(/\[\[([^\]]+)\]\]/g, (_match, title: string) => {
      return `<span class="text-slate-400 text-xs">[[${title}]]</span>`;
    });
  }

  if (mdCache.size >= MAX_MD_CACHE) {
    const first = mdCache.keys().next().value;
    if (first) mdCache.delete(first);
  }
  mdCache.set(key, html);
  return html;
}
