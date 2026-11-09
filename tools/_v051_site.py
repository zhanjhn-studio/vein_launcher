"""把网站更新到 0.5.1（版本、下载、SHA、更新日志、截图说明）。"""

from pathlib import Path

TOOLS = Path(r"Z:\Vein Launche\tools")
OLD_ZIP = "VeinLauncher-0.5.0-win64.zip"
NEW_ZIP = "VeinLauncher-0.5.1-win64.zip"
OLD_SHA = "1F3FDBFE…A176C"
NEW_SHA = "BD6ADBC3…BC5E0"
NEW_DATE = "2026-11-09"

for name in ("site_home_v6.py", "site_pages.py"):
    p = TOOLS / name
    t = p.read_text(encoding="utf-8")
    t = t.replace(OLD_ZIP, NEW_ZIP)
    t = t.replace("/v0.5.0/", "/v0.5.1/")
    t = t.replace("/releases/tag/v0.5.0", "/releases/tag/v0.5.1")
    t = t.replace("v0.5.0", "v0.5.1")
    t = t.replace("0.5.0 长什么样", "0.5.1 长什么样")
    t = t.replace("What 0.5.0 looks like", "What 0.5.1 looks like")
    t = t.replace(OLD_SHA, NEW_SHA)
    t = t.replace("2026-11-08", NEW_DATE)
    p.write_text(t, encoding="utf-8")
    print("updated", name)

# gen_site：版本常量与发布链接
g = TOOLS / "gen_site.py"
t = g.read_text(encoding="utf-8")
t = t.replace('VERSION = "0.5.0"', 'VERSION = "0.5.1"')
t = t.replace("/v0.5.0/", "/v0.5.1/")
t = t.replace(OLD_ZIP, NEW_ZIP)

# releases 表：插入 0.5.1
t = t.replace(
    """<tr><td><a href="{ZIP.split('/releases/')[0]}/releases/tag/v0.5.0" target="_blank" rel="noopener">v0.5.0</a></td><td>MLC 原版控制、附魔书指令、插件能力、总开关</td><td>2026-11-08</td></tr>""",
    """<tr><td><a href="{ZIP.split('/releases/')[0]}/releases/tag/v0.5.1" target="_blank" rel="noopener">v0.5.1</a></td><td>界面自定义、默认浅色 + 橙色主题、全新截图</td><td>2026-11-09</td></tr>
<tr><td><a href="{ZIP.split('/releases/')[0]}/releases/tag/v0.5.0" target="_blank" rel="noopener">v0.5.0</a></td><td>MLC 原版控制、附魔书指令、插件能力</td><td>2026-11-08</td></tr>""",
)
t = t.replace(
    """<tr><td><a href="{ZIP.split('/releases/')[0]}/releases/tag/v0.5.0" target="_blank" rel="noopener">v0.5.0</a></td><td>MLC control, command palette, plugin capabilities, master switch</td><td>2026-11-08</td></tr>""",
    """<tr><td><a href="{ZIP.split('/releases/')[0]}/releases/tag/v0.5.1" target="_blank" rel="noopener">v0.5.1</a></td><td>UI customization, light default, orange theme, new screenshots</td><td>2026-11-09</td></tr>
<tr><td><a href="{ZIP.split('/releases/')[0]}/releases/tag/v0.5.0" target="_blank" rel="noopener">v0.5.0</a></td><td>MLC control, command palette, plugin capabilities</td><td>2026-11-08</td></tr>""",
)

# changelog：新增 0.5.1 段落
t = t.replace(
    '<h2>v0.5.0 · 2026-11-08</h2>',
    """<h2>v0.5.1 · 2026-11-09</h2>
<h3>新增</h3><ul><li>界面自定义：圆角（小/中/大）、界面缩放（95%/100%/105%）、动效开关</li><li>默认浅色 + 橙色主题，主色仍可自由更换</li><li>启动器内全部截图与图标重制</li></ul>
<h3>修复</h3><ul><li>旧主题配色残留</li></ul>
<h3>破坏性改动</h3><ul><li>默认主题从深色改为浅色；可在设置中切回深色</li></ul>
<h2>v0.5.0 · 2026-11-08</h2>""",
)
t = t.replace(
    '<h2>v0.5.0 · 2026-11-08</h2>',
    """<h2>v0.5.1 · 2026-11-09</h2>
<h3>Added</h3><ul><li>UI customization: corner radius, interface zoom, motion toggle</li><li>Light theme by default with an orange accent; accent remains customizable</li><li>All launcher screenshots and icons refreshed</li></ul>
<h3>Breaking</h3><ul><li>Default theme changed from dark to light; switch back in Settings</li></ul>
<h2>v0.5.0 · 2026-11-08</h2>""",
)
g.write_text(t, encoding="utf-8")
print("updated gen_site.py")

# docs 内容里的下载链接 / 打包命令
for name in ("site_content.py", "site_content_en.py"):
    p = TOOLS / name
    t = p.read_text(encoding="utf-8")
    t = t.replace(OLD_ZIP, NEW_ZIP)
    t = t.replace("/v0.5.0/", "/v0.5.1/")
    t = t.replace("--version 0.5.0", "--version 0.5.1")
    p.write_text(t, encoding="utf-8")
    print("updated", name)
