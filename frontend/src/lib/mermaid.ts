import mermaid from 'mermaid';

export async function renderMermaidDiagrams(isDark?: boolean): Promise<void> {
  if (typeof document === 'undefined') return;

  const containers = document.querySelectorAll('.mermaid-unprocessed');
  if (containers.length === 0) return;

  const dark = isDark ?? document.documentElement.classList.contains('dark');
  mermaid.initialize({ startOnLoad: false, theme: dark ? 'dark' : 'default' });

  for (const el of Array.from(containers)) {
    try {
      let content = el.getAttribute('data-mermaid');
      if (content) {
        el.className = 'mermaid my-4';
        content = content
          .replace(/&amp;/g, '&')
          .replace(/&lt;/g, '<')
          .replace(/&gt;/g, '>')
          .replace(/&quot;/g, '"')
          .replace(/&#39;/g, "'");

        const id = `mermaid-${Math.random().toString(36).slice(2, 11)}`;
        const { svg } = await mermaid.render(id, content);
        el.innerHTML = svg;
      }
    } catch (err) {
      console.error('Mermaid error', err);
      el.className = 'mermaid-error my-4';
      el.innerHTML = `<pre style="color:#ef4444;font-size:12px;background:rgba(239,68,68,0.1);padding:10px;border-radius:4px;overflow-x:auto;">Mermaid syntax error:\n${err}</pre>`;
    }
  }
}
