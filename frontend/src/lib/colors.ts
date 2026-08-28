export type Rgb = { r: number; g: number; b: number };

export const DEFAULT_HEADER_COLOR = '#4f46e5';
export const TOOLBOX_BASE_COLOR = '#ffffff';

export function clampByte(n: number): number {
  return Math.max(0, Math.min(255, Math.round(n)));
}

export function hexToRgb(hex: string): Rgb | null {
  const h = hex.trim();
  const m = /^#([0-9a-fA-F]{6})$/.exec(h);
  if (!m) return null;
  const v = m[1];
  const r = parseInt(v.slice(0, 2), 16);
  const g = parseInt(v.slice(2, 4), 16);
  const b = parseInt(v.slice(4, 6), 16);
  return { r, g, b };
}

export function mixRgb(a: Rgb, b: Rgb, t: number): Rgb {
  const tt = Math.max(0, Math.min(1, t));
  return {
    r: clampByte(a.r + (b.r - a.r) * tt),
    g: clampByte(a.g + (b.g - a.g) * tt),
    b: clampByte(a.b + (b.b - a.b) * tt),
  };
}

export function rgba(c: Rgb, alpha: number): string {
  const a = Math.max(0, Math.min(1, alpha));
  return `rgba(${c.r}, ${c.g}, ${c.b}, ${a})`;
}

export function isLightColor(color: string): boolean {
  const hex = color.replace('#', '');
  if (hex.length < 6) return false;
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  const brightness = (r * 299 + g * 587 + b * 114) / 1000;
  return brightness > 128;
}

export function getContrastColor(bgColor: string): string {
  return isLightColor(bgColor) ? '#1e293b' : 'white';
}

export function computeHeaderColor(
  collectionHeaderColor?: string | null,
  userDefaultColor?: string | null
): string {
  const raw =
    (collectionHeaderColor || '').trim() ||
    (userDefaultColor || '').trim() ||
    DEFAULT_HEADER_COLOR;

  return /^#[0-9a-fA-F]{6}$/.test(raw) ? raw : DEFAULT_HEADER_COLOR;
}

export function computeHeaderGradient(headerColor: string): string {
  const base = hexToRgb(headerColor);
  if (!base) return headerColor;
  const lighter = mixRgb(base, { r: 255, g: 255, b: 255 }, 0.45);
  const mid = mixRgb(base, { r: 255, g: 255, b: 255 }, 0.2);
  return `linear-gradient(135deg, ${headerColor} 0%, ${rgba(mid, 1)} 50%, ${rgba(lighter, 1)} 100%)`;
}

export function computeToolboxBg(headerColor: string, isDark: boolean): string {
  const baseColor = isDark ? '#1e293b' : TOOLBOX_BASE_COLOR;
  const base = hexToRgb(baseColor) ?? { r: 255, g: 255, b: 255 };
  const header = hexToRgb(headerColor);
  const mixed = header ? mixRgb(base, header, 0.14) : base;
  return rgba(mixed, 0.8);
}

export function computeCardTileBg(headerColor: string, isDark: boolean): string {
  const baseColor = isDark ? '#1e293b' : '#ffffff';
  const base = hexToRgb(baseColor) ?? { r: 255, g: 255, b: 255 };
  const header = hexToRgb(headerColor);
  const mixed = header ? mixRgb(base, header, isDark ? 0.22 : 0.14) : base;
  return rgba(mixed, 0.96);
}

export function computeCardTileBorder(headerColor: string): string {
  const header = hexToRgb(headerColor);
  if (!header) return 'rgba(0, 0, 0, 0.08)';
  return rgba(header, 0.28);
}
