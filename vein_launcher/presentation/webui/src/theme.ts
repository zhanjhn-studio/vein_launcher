export type Theme = 'account' | 'dark' | 'light' | 'clear' | 'system';

const KEY = 'vl.theme';

function resolved(theme: Theme): 'dark' | 'light' {
  if (theme === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return theme === 'light' ? 'light' : 'dark';
}

let fadeTimer: number | undefined;

export function applyTheme(theme: Theme): void {
  localStorage.setItem(KEY, theme);
  const base = resolved(theme);
  document.documentElement.dataset.theme = base;
  document.documentElement.dataset.skin = theme === 'account' ? 'account' : '';
  document.documentElement.dataset.transparent = theme === 'clear' ? 'on' : 'off';
  // 切换瞬间挂 340ms 的颜色过渡，避免整块颜色硬切；结束后摘掉，避免拖慢日常交互
  const root = document.documentElement;
  root.classList.add('theme-fade');
  window.clearTimeout(fadeTimer);
  fadeTimer = window.setTimeout(() => root.classList.remove('theme-fade'), 360);
}

export function currentTheme(): Theme {
  const saved = localStorage.getItem(KEY) as Theme | null;
  // 默认使用 account 深色纹理主题，用户可自行切换。
  return saved === 'dark' || saved === 'light' || saved === 'clear' || saved === 'system' ? saved : 'account';
}

export function initTheme(): Theme {
  const theme = currentTheme();
  applyTheme(theme);
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (currentTheme() === 'system') applyTheme('system');
  });
  return theme;
}
