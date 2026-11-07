/** 自定义主色：把 #rrggbb 换算成一组 CSS 变量，覆盖内置 accent 配色 */

export const ACCENT_VARS = [
  '--accent',
  '--accent-2',
  '--accent-soft',
  '--accent-glow',
  '--accent-faint',
] as const;

/** 预设色板（第一个是内置主色） */
export const ACCENT_PRESETS = [
  '#6f97f0',
  '#8a7ff0',
  '#46b39e',
  '#f0916f',
  '#e06c8b',
  '#6fb0f0',
  '#a3d977',
  '#c9a227',
];

export function isHex(value: string): boolean {
  return /^#([0-9a-f]{6})$/i.test(value || '');
}

function hexToRgb(hex: string): [number, number, number] {
  const v = parseInt(hex.slice(1), 16);
  return [(v >> 16) & 255, (v >> 8) & 255, v & 255];
}

function rgbToHsl(r: number, g: number, b: number): [number, number, number] {
  const rr = r / 255;
  const gg = g / 255;
  const bb = b / 255;
  const max = Math.max(rr, gg, bb);
  const min = Math.min(rr, gg, bb);
  const l = (max + min) / 2;
  if (max === min) return [0, 0, l * 100];
  const d = max - min;
  const s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
  let h: number;
  if (max === rr) h = ((gg - bb) / d + (gg < bb ? 6 : 0)) / 6;
  else if (max === gg) h = ((bb - rr) / d + 2) / 6;
  else h = ((rr - gg) / d + 4) / 6;
  return [h * 360, s * 100, l * 100];
}

function hslToHex(h: number, s: number, l: number): string {
  const hue = ((h % 360) + 360) % 360 / 360;
  const sat = Math.max(0, Math.min(100, s)) / 100;
  const lig = Math.max(0, Math.min(100, l)) / 100;
  const q = lig < 0.5 ? lig * (1 + sat) : lig + sat - lig * sat;
  const p = 2 * lig - q;
  const channel = (t: number): number => {
    let tt = t;
    if (tt < 0) tt += 1;
    if (tt > 1) tt -= 1;
    if (tt < 1 / 6) return p + (q - p) * 6 * tt;
    if (tt < 1 / 2) return q;
    if (tt < 2 / 3) return p + (q - p) * (2 / 3 - tt) * 6;
    return p;
  };
  const toHex = (x: number) =>
    Math.round(x * 255)
      .toString(16)
      .padStart(2, '0');
  return `#${toHex(channel(hue + 1 / 3))}${toHex(channel(hue))}${toHex(channel(hue - 1 / 3))}`;
}

/** 读当前实际生效的主色（用于取色器初值） */
export function currentAccent(): string {
  const value = getComputedStyle(document.documentElement)
    .getPropertyValue('--accent')
    .trim()
    .toLowerCase();
  return isHex(value) ? value : ACCENT_PRESETS[0];
}

/**
 * 应用主色。传空串 / 非法值 = 移除覆盖，回退到 styles.css 里的内置配色。
 */
export function applyAccent(hex: string): void {
  const root = document.documentElement;
  const value = (hex || '').trim().toLowerCase();
  if (!isHex(value)) {
    ACCENT_VARS.forEach((name) => root.style.removeProperty(name));
    return;
  }

  const [r, g, b] = hexToRgb(value);
  const [h, s, l] = rgbToHsl(r, g, b);
  // 渐变的第二个色：色相轻移 + 提亮，避免和主色撞成一片
  const second = hslToHex(h + 16, s + 4, Math.min(86, l + 8));

  root.style.setProperty('--accent', value);
  root.style.setProperty('--accent-2', second);
  root.style.setProperty('--accent-soft', `rgba(${r}, ${g}, ${b}, .13)`);
  root.style.setProperty('--accent-glow', `rgba(${r}, ${g}, ${b}, .30)`);
  root.style.setProperty('--accent-faint', `rgba(${r}, ${g}, ${b}, .07)`);
}
