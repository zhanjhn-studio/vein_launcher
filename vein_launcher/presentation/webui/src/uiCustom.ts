/* 0.5.1 界面自定义：圆角 / 缩放 / 动效开关（localStorage 持久化） */

export type UiRadius = 'small' | 'medium' | 'large';
export type UiZoom = '95' | '100' | '105';
export type UiMotion = 'on' | 'off';

const KEYS = { radius: 'vl.ui.radius', zoom: 'vl.ui.zoom', motion: 'vl.ui.motion' } as const;

export function applyUiCustom(): void {
  const root = document.documentElement;
  const radius = (localStorage.getItem(KEYS.radius) as UiRadius) || 'medium';
  const zoom = (localStorage.getItem(KEYS.zoom) as UiZoom) || '100';
  const motion = (localStorage.getItem(KEYS.motion) as UiMotion) || 'on';
  root.dataset.radius = radius;
  root.dataset.zoom = zoom;
  root.dataset.motion = motion;
}

export function getUiCustom() {
  return {
    radius: (localStorage.getItem(KEYS.radius) as UiRadius) || 'medium',
    zoom: (localStorage.getItem(KEYS.zoom) as UiZoom) || '100',
    motion: (localStorage.getItem(KEYS.motion) as UiMotion) || 'on',
  };
}

export function setUiCustom(patch: { radius?: UiRadius; zoom?: UiZoom; motion?: UiMotion }): void {
  if (patch.radius) localStorage.setItem(KEYS.radius, patch.radius);
  if (patch.zoom) localStorage.setItem(KEYS.zoom, patch.zoom);
  if (patch.motion) localStorage.setItem(KEYS.motion, patch.motion);
  applyUiCustom();
}
