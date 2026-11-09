"""0.5.1：默认浅色 + 橙色主题 + 更多界面自定义（圆角/缩放/动效）。"""

from pathlib import Path

root = Path(r"Z:\Vein Launche")
web = root / "vein_launcher" / "presentation" / "webui"

# ---- 版本号
ctx = root / "vein_launcher" / "presentation" / "context.py"
t = ctx.read_text(encoding="utf-8")
t = t.replace('VERSION = "0.5.0"', 'VERSION = "0.5.1"')
ctx.write_text(t, encoding="utf-8")

# ---- 默认浅色
theme = web / "src" / "theme.ts"
t = theme.read_text(encoding="utf-8")
t = t.replace("""const KEY = 'vl.theme';
const MIGRATED = 'vl.theme.default-dark';""", """const KEY = 'vl.theme';""")
t = t.replace("""  // 旧版本默认浅色会把 light 自动写进 localStorage；一次性迁移到深色默认。
  if (localStorage.getItem(MIGRATED) !== '1') {
    localStorage.setItem(MIGRATED, '1');
    if (saved === 'light' || !saved) {
      localStorage.setItem(KEY, 'dark');
      return 'dark';
    }
  }
  return saved === 'light' || saved === 'clear' || saved === 'system' ? saved : 'dark';""",
"""  // 0.5.1 起默认浅色主题（橙色主色），用户可自行切到深色。
  return saved === 'dark' || saved === 'clear' || saved === 'system' ? saved : 'light';""")
theme.write_text(t, encoding="utf-8")

# ---- 橙色主题 token
css = web / "src" / "styles.css"
t = css.read_text(encoding="utf-8")
t = t.replace("""  --accent: #7ea6ff;
  --accent-2: #5cd3c4;
  --accent-soft: rgba(126, 166, 255, .13);
  --accent-grad: linear-gradient(135deg, var(--accent), var(--accent-2));
  --accent-glow: rgba(126, 166, 255, .30);
  --accent-faint: rgba(126, 166, 255, .07);""",
"""  --accent: #fb923c;
  --accent-2: #f59e0b;
  --accent-soft: rgba(251, 146, 60, .13);
  --accent-grad: linear-gradient(135deg, var(--accent), var(--accent-2));
  --accent-glow: rgba(251, 146, 60, .30);
  --accent-faint: rgba(251, 146, 60, .07);""")
t = t.replace("""  --accent: #2563eb;
  --accent-2: #0e9488;
  --accent-soft: rgba(37, 99, 235, .10);
  --accent-grad: linear-gradient(135deg, var(--accent), var(--accent-2));
  --accent-glow: rgba(37, 99, 235, .22);
  --accent-faint: rgba(37, 99, 235, .06);""",
"""  --accent: #f97316;
  --accent-2: #f59e0b;
  --accent-soft: rgba(249, 115, 22, .10);
  --accent-grad: linear-gradient(135deg, var(--accent), var(--accent-2));
  --accent-glow: rgba(249, 115, 22, .22);
  --accent-faint: rgba(249, 115, 22, .06);""")
t = t.replace("rgba(126, 166, 255,", "rgba(251, 146, 60,")

# 自定义：圆角 / 缩放 / 动效
t += """

/* ---------- 0.5.1 界面自定义 ---------- */
:root[data-radius='small'] { --radius: 9px; --radius-sm: 7px; }
:root[data-radius='large'] { --radius: 18px; --radius-sm: 12px; }
:root[data-zoom='95'] body { zoom: .95; }
:root[data-zoom='105'] body { zoom: 1.05; }
:root[data-motion='off'] *,
:root[data-motion='off'] *::before,
:root[data-motion='off'] *::after {
  animation: none !important;
  transition: none !important;
}
"""
css.write_text(t, encoding="utf-8")

# ---- 橙色优先的调色板
accent = web / "src" / "accent.ts"
t = accent.read_text(encoding="utf-8")
t = t.replace("""export const ACCENT_PRESETS = [
  '#2563eb',
  '#0e9488',
  '#22c55e',
  '#f59e0b',
  '#ef4444',
  '#06b6d4',
  '#84cc16',
  '#c9a227',
];""",
"""export const ACCENT_PRESETS = [
  '#f97316',
  '#fb923c',
  '#f59e0b',
  '#ef4444',
  '#22c55e',
  '#0e9488',
  '#2563eb',
  '#8b5cf6',
];""")
accent.write_text(t, encoding="utf-8")

# ---- 自定义模块
(web / "src" / "uiCustom.ts").write_text(
"""/* 0.5.1 界面自定义：圆角 / 缩放 / 动效开关（localStorage 持久化） */

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
""",
    encoding="utf-8",
)

# main.tsx 初始化
main = web / "src" / "main.tsx"
t = main.read_text(encoding="utf-8")
if "uiCustom" not in t:
    t = t.replace("import App", "import { applyUiCustom } from './uiCustom';\nimport App", 1)
    t = t.replace("createRoot(", "applyUiCustom();\ncreateRoot(", 1)
    main.write_text(t, encoding="utf-8")
print("0.5.1 theme + custom module")
