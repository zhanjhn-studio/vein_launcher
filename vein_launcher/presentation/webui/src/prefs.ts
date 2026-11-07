/* 界面偏好（简洁模式 / 空闲透明 / 自定义壁纸）：后端持久化 + 前端订阅 */

import { useEffect, useReducer } from 'react';
import { rpc } from './bridge';
import { applyAccent } from './accent';

export type WallpaperKind = 'image' | 'video';

export interface Wallpaper {
  url: string;
  kind: WallpaperKind;
  name: string;
  /** 仅后端返回，前端不依赖 */
  path?: string;
}

export interface Prefs {
  compactMode: boolean;
  /** 启动页空闲多少秒后 UI 淡出；0 = 关闭 */
  idleSeconds: number;
  wallpaper: Wallpaper | null;
  /** 自定义主色 #rrggbb；空串 = 用内置配色 */
  accent: string;
}

const DEFAULTS: Prefs = { compactMode: false, idleSeconds: 60, wallpaper: null, accent: '' };

let prefs: Prefs = { ...DEFAULTS };
const listeners = new Set<(next: Prefs) => void>();

function syncDocument(): void {
  const root = document.documentElement;
  root.dataset.compact = prefs.compactMode ? 'on' : 'off';
  applyAccent(prefs.accent);
  // 壁纸只在启动页生效：由 LaunchPage 自己挂/摘 data-wall，
  // 全局设置会让所有页面都被玻璃风压成一片透明（曾经的实际 bug）。
}

export function getPrefs(): Prefs {
  return prefs;
}

export function applyPrefs(next: Partial<Prefs>): Prefs {
  const before = prefs.wallpaper?.url;
  prefs = { ...prefs, ...next };
  syncDocument();
  if (prefs.wallpaper?.kind === 'image' && prefs.wallpaper.url !== before) {
    // 预解码：首次切到启动页时直接命中已解码的位图，不再有「背景空一帧」的闪烁
    const img = new Image();
    img.src = prefs.wallpaper.url;
  }
  listeners.forEach((fn) => fn(prefs));
  return prefs;
}

export function subscribePrefs(fn: (next: Prefs) => void): () => void {
  listeners.add(fn);
  return () => {
    listeners.delete(fn);
  };
}

function fromPayload(raw: any): Partial<Prefs> {
  if (!raw || typeof raw !== 'object') return {};
  return {
    compactMode: Boolean(raw.compactMode),
    idleSeconds: Number.isFinite(Number(raw.idleSeconds)) ? Number(raw.idleSeconds) : 60,
    wallpaper: raw.wallpaper?.url ? (raw.wallpaper as Wallpaper) : null,
    accent: typeof raw.accent === 'string' ? raw.accent : '',
  };
}

export async function loadPrefs(): Promise<Prefs> {
  try {
    return applyPrefs(fromPayload(await rpc<any>('ui.prefs')));
  } catch {
    return applyPrefs({});
  }
}

export async function savePrefs(patch: {
  compactMode?: boolean;
  idleSeconds?: number;
  accent?: string;
}): Promise<Prefs> {
  const result = await rpc<any>('ui.setPrefs', [
    patch.compactMode ?? null,
    patch.idleSeconds ?? null,
    false, // clear_wallpaper
    '', // wallpaper
    patch.accent ?? null,
  ]);
  return applyPrefs(fromPayload(result));
}

export async function importWallpaper(): Promise<Prefs | null> {
  const result = await rpc<any>('ui.importWallpaper');
  if (result?.cancelled) return null;
  return applyPrefs(fromPayload(result));
}

export async function clearWallpaper(): Promise<Prefs> {
  const result = await rpc<any>('ui.setPrefs', [null, null, true]);
  return applyPrefs(fromPayload(result));
}

export function usePrefs(): Prefs {
  const [, force] = useReducer((x: number) => x + 1, 0);
  useEffect(() => subscribePrefs(() => force()), []);
  return prefs;
}
