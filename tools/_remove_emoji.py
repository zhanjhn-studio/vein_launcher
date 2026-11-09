"""移除首页表情图标，改为纯排版。"""

from pathlib import Path

p = Path(r"Z:\Vein Launche\tools\site_home_v6.py")
t = p.read_text(encoding="utf-8")
for emoji in ("⚡", "📖", "🧩", "🎨", "🪟", "🌐"):
    t = t.replace(f'<div class="fi">{emoji}</div>', "")
p.write_text(t, encoding="utf-8")
print("emoji icons removed")
