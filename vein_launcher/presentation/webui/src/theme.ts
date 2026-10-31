export type Theme = 'dark' | 'light' | 'clear' | 'system';

const KEY = 'vl.theme';

function resolved(theme: Theme): 'dark' | 'light' {
  if (theme === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return theme === 'light' ? 'light' : 'dark';
}

export function applyTheme(theme: Theme): void {
  localStorage.setItem(KEY, theme);
  const base = resolved(theme);
  document.documentElement.dataset.theme = base;
  document.documentElement.dataset.transparent = theme === 'clear' ? 'on' : 'off';
}

export function currentTheme(): Theme {
  const saved = localStorage.getItem(KEY) as Theme | null;
  return saved === 'light' || saved === 'clear' || saved === 'system' ? saved : 'dark';
}

export function initTheme(): Theme {
  const theme = currentTheme();
  applyTheme(theme);
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (currentTheme() === 'system') applyTheme('system');
  });
  return theme;
}
