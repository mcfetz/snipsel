import DOMPurify from 'dompurify';
import mermaid from 'mermaid';
import { decodeHtmlEntities } from './html';

export async function renderMermaidDiagrams(isDark?: boolean): Promise<void> {
  if (typeof document === 'undefined') return;

  const containers = document.querySelectorAll('.mermaid-unprocessed');
  if (containers.length === 0) return;

  const dark = isDark ?? document.documentElement.classList.contains('dark');
  mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', theme: dark ? 'dark' : 'default' });

  for (const el of Array.from(containers)) {
    try {
      const raw = el.getAttribute('data-mermaid');
      if (raw) {
        el.className = 'mermaid my-4';
        const content = decodeHtmlEntities(raw);

        const id = `mermaid-${Math.random().toString(36).slice(2, 11)}`;
        const { svg } = await mermaid.render(id, content);
        el.innerHTML = DOMPurify.sanitize(svg, {
          USE_PROFILES: { svg: true, svgFilters: true, html: true },
          ADD_TAGS: ['foreignObject'],
        });
      }
    } catch (err) {
      console.error('Mermaid error', err);
      el.className = 'mermaid-error my-4';
      const pre = document.createElement('pre');
      pre.style.cssText =
        'color:#ef4444;font-size:12px;background:rgba(239,68,68,0.1);padding:10px;border-radius:4px;overflow-x:auto;';
      pre.textContent = `Mermaid syntax error:\n${String(err)}`;
      el.replaceChildren(pre);
    }
  }
}
