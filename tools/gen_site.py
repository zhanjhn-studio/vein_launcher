"""生成 Vein Launcher 官网（中英双语多页面静态站）。

运行：python tools/gen_site.py
输出：veinwebsite-don'tupdategithub/**（中文）+ en/**（英文）
"""

from __future__ import annotations

import html
from pathlib import Path

from site_content import PAGES
from site_content_en import PAGES_EN
from site_home_v6 import HOME_EN as HOME_EN_V6, HOME_ZH as HOME_ZH_V6

ROOT = Path(__file__).resolve().parents[1] / "veinwebsite-don'tupdategithub"
ZIP = "https://github.com/zhanjhn-studio/vein_launcher/releases/download/v0.5.0/VeinLauncher-0.5.0-win64.zip"
REL = "https://github.com/zhanjhn-studio/vein_launcher/releases/tag/v0.5.0"
GH = "https://github.com/zhanjhn-studio/vein_launcher"

ROOT_ORDER = ["index.html", "docs.html", "download.html", "releases.html", "changelog.html", "about.html", "privacy.html"]

L10N = {
    "zh": dict(
        nav=[("index.html", "首页"), ("docs.html", "文档"), ("download.html", "下载")],
        brand_tail="Launcher",
        groups=["开始使用", "玩家", "二次开发", "插件开发", "MLC", "参考"],
        lang_label="EN",
        footer="Vein Launcher · Zhanjhn Studio",
        footer_links=[("docs.html", "文档"), ("download.html", "下载"), ("privacy.html", "隐私")],
        html_lang="zh-CN",
    ),
    "en": dict(
        nav=[("index.html", "Home"), ("docs.html", "Docs"), ("download.html", "Download")],
        brand_tail="Launcher",
        groups=["Getting started", "Playing", "Development", "Plugins", "MLC", "Reference"],
        lang_label="中文",
        footer="Vein Launcher · Zhanjhn Studio",
        footer_links=[("docs.html", "Docs"), ("download.html", "Download"), ("privacy.html", "Privacy")],
        html_lang="en",
    ),
}

EN_GROUP_OF_ZH = {
    "开始使用": "Getting started", "玩家": "Playing", "二次开发": "Development",
    "插件开发": "Plugins", "MLC": "MLC", "参考": "Reference",
}


def pages_for(lang: str):
    if lang == "zh":
        return PAGES
    # 英文页复用 path，但分组换成英文
    out = []
    for p in PAGES_EN:
        q = dict(p)
        zh = next((x for x in PAGES if x["path"] == p["path"]), None)
        q["group"] = EN_GROUP_OF_ZH.get(zh["group"], p["group"]) if zh else p["group"]
        out.append(q)
    return out


def build_orders(lang: str):
    pages = pages_for(lang)
    paths = list(ROOT_ORDER) + [p["path"] for p in pages]
    return paths


def prefix(lang: str, path: str) -> str:
    """页面自身到站点根（assets 所在层）的相对前缀。"""
    logical = path[3:] if path.startswith("en/") else path
    nested = "/" in logical
    if lang == "en":
        return "../../" if nested else "../"
    return "../" if nested else ""


def header(lang: str, current: str, order: list[str]) -> str:
    l = L10N[lang]
    base = prefix(lang, current)
    logical = current[3:] if current.startswith("en/") else current
    nav_base = "../" if "/" in logical else ""
    other = "zh" if lang == "en" else "en"
    # 语言切换目标
    if other == "en":
        lang_href = base + "en/" + current
    else:
        lang_href = base + current[3:] if current.startswith("en/") else base + current
    navs = []
    for href, label in l["nav"]:
        active = ' aria-current="page"' if href == current else ""
        navs.append(f'<a href="{nav_base}{href}" data-order="{order.index(href)}"{active}>{label}</a>')
    navs.append(f'<a href="{GH}" target="_blank" rel="noopener">GitHub</a>')
    return f"""<header class="site-header">
    <div class="wrap">
      <a class="brand" href="{base}index.html"><img src="{base}assets/logo.png" alt="" /><span>Vein<b>Launcher</b></span></a>
      <nav class="site-nav">
        {chr(10).join('        ' + n for n in navs)}
      </nav>
      <div class="header-actions">
        <a class="icon-btn" href="{lang_href}">{l["lang_label"]}</a>
        <button class="icon-btn" type="button" data-theme-toggle>深色</button>
        <button class="icon-btn nav-toggle" type="button" data-nav-toggle aria-label="menu">≡</button>
      </div>
    </div>
  </header>"""


def footer(lang: str, base: str) -> str:
    l = L10N[lang]
    links = " · ".join(f'<a href="{base}{h}">{t}</a>' for h, t in l["footer_links"])
    return f"""<footer class="site-footer">
    <div class="wrap">
      <span>{l["footer"]}</span>
      <span>{links} · <a href="{GH}" target="_blank" rel="noopener">GitHub</a></span>
    </div>
  </footer>"""


def sidebar(lang: str, current: str, order: list[str]) -> str:
    pages = pages_for(lang)
    groups = L10N[lang]["groups"]
    # 英文页的 current 是 en/xxx
    cur_rel = current[3:] if lang == "en" else current
    out = []
    for group in groups:
        items = []
        for p in pages:
            if p["group"] != group:
                continue
            active = " active" if p["path"] == cur_rel else ""
            href = "../" + p["path"]
            items.append(f'<a href="{href}" data-order="{order.index(p["path"])}" class="{active.strip()}">{p["title"]}</a>')
        out.append('<div class="group"><h4>' + group + "</h4>" + "".join(items) + "</div>")
    return '<aside class="docs-side">' + "".join(out) + "</aside>"


def shell(lang: str, *, path: str, title: str, body: str, order: list[str]) -> str:
    """path 为站点内相对路径（英文页带 en/ 前缀）。"""
    base = prefix(lang, path)
    return f"""<!doctype html>
<html lang="{L10N[lang]['html_lang']}" data-theme="light">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <link rel="icon" href="{base}assets/favicon.ico" />
  <link rel="stylesheet" href="{base}assets/site.css" />
</head>
<body data-order="{order.index(path.replace('en/', '', 1) if lang == 'en' else path)}">
  {header(lang, path, order)}
  {body}
  {footer(lang, base)}
  <script src="{base}assets/site.js"></script>
</body>
</html>
"""


def doc_page(lang: str, p: dict, order: list[str]) -> str:
    pages = pages_for(lang)
    docs = [x for x in pages if x["group"] == p["group"]]
    pos = docs.index(p)
    prev_p = docs[pos - 1] if pos > 0 else None
    next_p = docs[pos + 1] if pos + 1 < len(docs) else None

    def href(x):
        return "../" + x["path"]

    pager = '<div class="pager">'
    pager += (f'<a href="{href(prev_p)}" data-order="{order.index(prev_p["path"])}">← {prev_p["title"]}</a>'
              if prev_p else "<span></span>")
    pager += (f'<a href="{href(next_p)}" data-order="{order.index(next_p["path"])}">{next_p["title"]} →</a>'
              if next_p else "<span></span>")
    pager += "</div>"
    tags = "".join(f"<span>{html.escape(t)}</span>" for t in p["tags"])
    body = f"""<main class="wrap docs-wrap">
    {sidebar(lang, (p['path'] if lang == 'zh' else 'en/' + p['path']), order)}
    <article class="docs-main">
      <h1>{p["title"]}</h1>
      <p class="subtitle">{p["subtitle"]}</p>
      <div class="docs-tags">{tags}</div>
      {p["body"]}
      {pager}
    </article>
  </main>"""
    full_path = p["path"] if lang == "zh" else "en/" + p["path"]
    title = f'{p["title"]} — Vein Launcher {"文档" if lang == "zh" else "Docs"}'
    return shell(lang, path=full_path, title=title, body=body, order=order)


# ---------------------------------------------------------------- 首页 / 根页面内容
HOME_ZH = f"""<main>
    <section class="hero"><div class="wrap hero-grid">
      <div>
        <span class="eyebrow">Minecraft Java Edition · Windows</span>
        <h1>Minecraft，<br />但更干净。<em>安装、管理、启动，一步到位；还能在不装 mod 的原版里直接执行指令。</em></h1>
        <p class="lead">Vein Launcher 是面向 Minecraft Java 版的便携启动器：镜像优先下载、真实例管理、LittleSkin 皮肤、沙箱插件宿主，以及 MLC 控制层。</p>
        <div style="display:flex;gap:12px;flex-wrap:wrap;">
          <a class="btn primary lg" href="{ZIP}">下载 v0.5.0</a>
          <a class="btn lg" href="docs.html" data-order="1">阅读文档</a>
        </div>
        <div class="meta-row"><span><i></i>便携 · 免安装</span><span><i></i>51 项单元测试</span><span><i></i>English &amp; 简体中文</span></div>
      </div>
      <div class="shot"><img src="assets/shot-launch.png" alt="启动页" /></div>
    </div></section>

    <section class="identity"><div class="wrap">
      <div class="identity-head"><span class="eyebrow">Choose your path</span><h2>你是来玩的，还是来造的？</h2><p>三种入口，都有可直接复制的命令与完整文档。</p></div>
      <div class="role-row"><div><div class="role-kicker">01 · For players</div><h3>我只想玩游戏</h3>
        <p>下载、选版本、进游戏。皮肤、附魔书指令速查、多实例，都在五分钟里。</p>
        <ul class="role-points"><li>附魔书风格指令速查，回车直接发进游戏</li><li>LittleSkin 账号皮肤直接进游戏</li><li>多实例并行，每实例独立进程与端口</li></ul>
        <a class="btn primary" href="docs.html" data-order="1">玩家文档 →</a></div>
        <div class="role-visual"><img src="assets/shot-launch.png" alt="" /></div></div>
      <div class="role-row"><div><div class="role-kicker">02 · For builders</div><h3>我要改它 / 扩展它</h3>
        <p>五层架构、JSON-RPC 桥、沙箱插件宿主、Lua UI 与 MLC 控制层，全部开放。</p>
        <ul class="role-points"><li>严格分层 + 全局事件总线</li><li>Bridge 注册一个方法就能扩展一个 RPC</li><li>构建、测试、打包流程齐全</li></ul>
        <a class="btn primary" href="docs.html" data-order="1">开发文档 →</a></div>
        <div class="role-visual"><img src="assets/shot-tools.png" alt="" /></div></div>
      <div class="role-row"><div><div class="role-kicker">03 · For plugin devs</div><h3>我要写插件</h3>
        <p>Node 独立进程、权限沙箱、Lua UI、示例与调试。</p>
        <ul class="role-points"><li>package.json 声明权限，越权直接拒绝</li><li>MLC 事件、运行中游戏、实例列表都能读</li><li>自带 status-panel 示例，抄一个就能跑</li></ul>
        <a class="btn primary" href="docs.html" data-order="1">插件文档 →</a></div>
        <div class="role-visual"><img src="assets/shot-palette.png" alt="" /></div></div>
    </div></section>

    <section class="download"><div class="wrap"><div class="download-card">
      <div><span class="eyebrow">Download</span><h2>下载 Windows 版</h2>
        <p>解压即用，不写注册表；删除目录即卸载。需要 Java 时启动器会自动下载。</p>
        <div style="display:flex;gap:12px;flex-wrap:wrap;">
          <a class="btn primary lg" href="{ZIP}">下载 v0.5.0（199 MB）</a>
          <a class="btn lg" href="download.html" data-order="2">全部版本</a>
        </div>
        <div class="download-meta"><span>v0.5.0</span><span>Windows 10/11 x64</span><span>便携 · 免安装</span><span>51 项单元测试</span></div>
      </div>
      <div class="role-visual"><img src="assets/shot-download.png" alt="" /></div>
    </div></div></section>

    <section class="section section-soft"><div class="wrap">
      <div class="section-head"><span class="eyebrow">Screenshots</span><h2>0.5.0 长什么样</h2></div>
      <div class="gallery">
        <figure><img src="assets/shot-launch.png" alt="" /><figcaption>启动页</figcaption></figure>
        <figure><img src="assets/shot-download.png" alt="" /><figcaption>下载页</figcaption></figure>
        <figure><img src="assets/shot-skins.png" alt="" /><figcaption>皮肤</figcaption></figure>
        <figure><img src="assets/shot-mlc-switch.png" alt="" /><figcaption>MLC 总开关</figcaption></figure>
        <figure><img src="assets/shot-palette.png" alt="" /><figcaption>指令速查</figcaption></figure>
        <figure><img src="assets/shot-tools.png" alt="" /><figcaption>工具箱</figcaption></figure>
      </div>
    </div></section>

    <section class="section"><div class="wrap">
      <div class="section-head"><span class="eyebrow">Documentation</span><h2>文档</h2><p>安装到插件开发，每一节都有独立页面。</p></div>
      <div style="text-align:center;"><a class="btn primary lg" href="docs.html" data-order="1">浏览全部文档 →</a></div>
    </div></section>
  </main>"""

HOME_EN = f"""<main>
    <section class="hero"><div class="wrap hero-grid">
      <div>
        <span class="eyebrow">Minecraft Java Edition · Windows</span>
        <h1>Minecraft,<br />but cleaner.<em>Install, manage, launch — and drive vanilla Minecraft without a single mod.</em></h1>
        <p class="lead">A portable launcher for Minecraft Java Edition: mirror-first downloads, real instance management, LittleSkin skins, a sandboxed plugin host and the MLC control layer.</p>
        <div style="display:flex;gap:12px;flex-wrap:wrap;">
          <a class="btn primary lg" href="{ZIP}">Download v0.5.0</a>
          <a class="btn lg" href="docs.html" data-order="1">Read the docs</a>
        </div>
        <div class="meta-row"><span><i></i>Portable, no installer</span><span><i></i>51 unit tests</span><span><i></i>English &amp; 简体中文</span></div>
      </div>
      <div class="shot"><img src="assets/shot-launch.png" alt="Launch page" /></div>
    </div></section>

    <section class="identity"><div class="wrap">
      <div class="identity-head"><span class="eyebrow">Choose your path</span><h2>Here to play, or here to build?</h2><p>Three entry points, each with copy-paste commands and complete docs.</p></div>
      <div class="role-row"><div><div class="role-kicker">01 · For players</div><h3>I just want to play</h3>
        <p>Download, pick a version, launch. Skins, the command palette and multi-instance support in five minutes.</p>
        <ul class="role-points"><li>Enchanted-book command palette — Enter sends</li><li>LittleSkin skins work in-game</li><li>Multiple instances with separate ports</li></ul>
        <a class="btn primary" href="docs.html" data-order="1">Player docs →</a></div>
        <div class="role-visual"><img src="assets/shot-launch.png" alt="" /></div></div>
      <div class="role-row"><div><div class="role-kicker">02 · For builders</div><h3>I want to change it</h3>
        <p>Five layers, a JSON-RPC bridge, a sandboxed plugin host, Lua UI and MLC — all open.</p>
        <ul class="role-points"><li>Strict layering + global event bus</li><li>Add one handler to expose one RPC</li><li>Build, test and packaging scripts included</li></ul>
        <a class="btn primary" href="docs.html" data-order="1">Developer docs →</a></div>
        <div class="role-visual"><img src="assets/shot-tools.png" alt="" /></div></div>
      <div class="role-row"><div><div class="role-kicker">03 · For plugin devs</div><h3>I want to write plugins</h3>
        <p>Isolated Node processes, permission sandbox, Lua UI, examples and debugging.</p>
        <ul class="role-points"><li>Permissions declared in package.json</li><li>Read MLC events, running games and instances</li><li>A ready-made status-panel example</li></ul>
        <a class="btn primary" href="docs.html" data-order="1">Plugin docs →</a></div>
        <div class="role-visual"><img src="assets/shot-palette.png" alt="" /></div></div>
    </div></section>

    <section class="download"><div class="wrap"><div class="download-card">
      <div><span class="eyebrow">Download</span><h2>Download for Windows</h2>
        <p>Unzip and run. No registry writes, delete the folder to uninstall. Java is downloaded automatically if needed.</p>
        <div style="display:flex;gap:12px;flex-wrap:wrap;">
          <a class="btn primary lg" href="{ZIP}">Download v0.5.0 (199 MB)</a>
          <a class="btn lg" href="download.html" data-order="2">All versions</a>
        </div>
        <div class="download-meta"><span>v0.5.0</span><span>Windows 10/11 x64</span><span>Portable</span><span>51 unit tests</span></div>
      </div>
      <div class="role-visual"><img src="assets/shot-download.png" alt="" /></div>
    </div></div></section>

    <section class="section section-soft"><div class="wrap">
      <div class="section-head"><span class="eyebrow">Screenshots</span><h2>What 0.5.0 looks like</h2></div>
      <div class="gallery">
        <figure><img src="assets/shot-launch.png" alt="" /><figcaption>Launch</figcaption></figure>
        <figure><img src="assets/shot-download.png" alt="" /><figcaption>Download</figcaption></figure>
        <figure><img src="assets/shot-skins.png" alt="" /><figcaption>Skins</figcaption></figure>
        <figure><img src="assets/shot-mlc-switch.png" alt="" /><figcaption>MLC switch</figcaption></figure>
        <figure><img src="assets/shot-palette.png" alt="" /><figcaption>Command palette</figcaption></figure>
        <figure><img src="assets/shot-tools.png" alt="" /><figcaption>Tools</figcaption></figure>
      </div>
    </div></section>

    <section class="section"><div class="wrap">
      <div class="section-head"><span class="eyebrow">Documentation</span><h2>Docs</h2><p>From install to plugin development, one page per topic.</p></div>
      <div style="text-align:center;"><a class="btn primary lg" href="docs.html" data-order="1">Browse all docs →</a></div>
    </div></section>
  </main>"""


def docs_hub(lang: str, order: list[str]) -> str:
    pages = pages_for(lang)
    groups = L10N[lang]["groups"]
    title = "文档" if lang == "zh" else "Docs"
    lead = ("按主题拆分的完整文档。每一页都可以单独打开、单独收藏。" if lang == "zh"
            else "Complete documentation split by topic. Every page can be opened and bookmarked on its own.")
    blocks = []
    for group in groups:
        items = []
        for p in pages:
            if p["group"] != group:
                continue
            href = p["path"]
            items.append(f'<a href="{href}" data-order="{order.index(p["path"])}"><b>{p["title"]}</b><span>{p["subtitle"]}</span></a>')
        blocks.append(f'<section class="doc-group"><h2>{group}</h2><div class="doc-list">{"".join(items)}</div></section>')
    return f"""<main class="wrap doc-index">
    <h1>{title}</h1>
    <p class="lead">{lead}</p>
    {''.join(blocks)}
  </main>"""


def download_page(lang: str) -> str:
    shot = "assets/shot-download.png" if lang == "zh" else "../assets/shot-download.png"
    if lang == "zh":
        return f"""<main class="wrap doc-index">
    <h1>下载</h1>
    <p class="lead">Windows 10/11 x64。解压即用，删除目录即卸载。</p>
    <div class="download-card" style="margin:30px 0 50px;">
      <div><span class="eyebrow">Latest</span><h2>Vein Launcher 0.5.0</h2>
        <p>MLC 原版控制、附魔书指令速查、插件能力补全、总开关硬拦截。</p>
        <div style="display:flex;gap:12px;flex-wrap:wrap;">
          <a class="btn primary lg" href="{ZIP}">下载 zip（199 MB）</a>
          <a class="btn lg" href="{REL}" target="_blank" rel="noopener">Release 说明</a>
        </div>
        <div class="download-meta"><span>v0.5.0</span><span>2026-11-08</span><span>SHA-256 1F3FDBFE…A176C</span></div>
      </div>
      <div class="role-visual"><img src="{shot}" alt="" /></div>
    </div>
    <ul><li><a href="releases.html">版本列表</a></li><li><a href="changelog.html">更新日志</a></li></ul>
  </main>"""
    return f"""<main class="wrap doc-index">
    <h1>Download</h1>
    <p class="lead">Windows 10/11 x64. Unzip and run; delete the folder to uninstall.</p>
    <div class="download-card" style="margin:30px 0 50px;">
      <div><span class="eyebrow">Latest</span><h2>Vein Launcher 0.5.0</h2>
        <p>MLC vanilla control, enchanted-book command palette, plugin capabilities, hard master switch.</p>
        <div style="display:flex;gap:12px;flex-wrap:wrap;">
          <a class="btn primary lg" href="{ZIP}">Download zip (199 MB)</a>
          <a class="btn lg" href="{REL}" target="_blank" rel="noopener">Release notes</a>
        </div>
        <div class="download-meta"><span>v0.5.0</span><span>2026-11-08</span><span>SHA-256 1F3FDBFE…A176C</span></div>
      </div>
      <div class="role-visual"><img src="{shot}" alt="" /></div>
    </div>
    <ul><li><a href="releases.html">All releases</a></li><li><a href="changelog.html">Changelog</a></li></ul>
  </main>"""


RELEASES_ZH = f"""<main class="wrap doc-index"><h1>版本</h1>
    <p class="lead">每个版本都有对应的 GitHub Release 与下载资产。</p>
    <table><thead><tr><th>版本</th><th>说明</th><th>日期</th></tr></thead><tbody>
    <tr><td><a href="{REL}" target="_blank" rel="noopener">v0.5.0</a></td><td>MLC 原版控制、附魔书指令、插件能力、总开关</td><td>2026-11-08</td></tr>
    <tr><td><a href="https://github.com/zhanjhn-studio/vein_launcher/releases/tag/v0.1.0" target="_blank" rel="noopener">v0.1.0</a></td><td>首个公开版本</td><td>2026-10-31</td></tr>
    </tbody></table>
    <p><a href="{GH}/releases" target="_blank" rel="noopener">在 GitHub 查看全部 →</a></p></main>"""

RELEASES_EN = f"""<main class="wrap doc-index"><h1>Releases</h1>
    <p class="lead">Every version has a GitHub Release and downloadable assets.</p>
    <table><thead><tr><th>Version</th><th>Notes</th><th>Date</th></tr></thead><tbody>
    <tr><td><a href="{REL}" target="_blank" rel="noopener">v0.5.0</a></td><td>MLC control, command palette, plugin capabilities, master switch</td><td>2026-11-08</td></tr>
    <tr><td><a href="https://github.com/zhanjhn-studio/vein_launcher/releases/tag/v0.1.0" target="_blank" rel="noopener">v0.1.0</a></td><td>First public release</td><td>2026-10-31</td></tr>
    </tbody></table>
    <p><a href="{GH}/releases" target="_blank" rel="noopener">View all on GitHub →</a></p></main>"""

CHANGELOG_ZH = """<main class="wrap doc-index"><h1>更新日志</h1><p class="lead">按版本倒序记录主要变化。</p>
    <h2>v0.5.0 · 2026-11-08</h2>
    <ul><li>MLC：原版 javaagent 控制层，状态 / 指令 / 事件，多实例端口</li>
    <li>MLC 总开关：关闭时后端拒绝全部相关调用</li>
    <li>指令速查：附魔书面板、Enter 发送、失败自动复制</li>
    <li>热键：Ctrl+Alt+0..9 优先走 MLC</li>
    <li>插件：game.running / app.info / versions.list / MLC 事件</li>
    <li>界面：开关对齐、禁用态、翻译层修复</li></ul>
    <h2>v0.1.0 · 2026-10-31</h2><ul><li>首个公开版本：版本下载、实例管理、皮肤、日志</li></ul></main>"""

CHANGELOG_EN = """<main class="wrap doc-index"><h1>Changelog</h1><p class="lead">Main changes, newest first.</p>
    <h2>v0.5.0 · 2026-11-08</h2>
    <ul><li>MLC: vanilla javaagent control layer — state, commands, events, per-instance ports</li>
    <li>MLC master switch: backend rejects all related calls while off</li>
    <li>Command palette: enchanted-book UI, Enter sends, clipboard fallback</li>
    <li>Hotkeys: Ctrl+Alt+0..9 prefer MLC</li>
    <li>Plugins: game.running / app.info / versions.list / MLC events</li>
    <li>UI: switch alignment, disabled states, translation fixes</li></ul>
    <h2>v0.1.0 · 2026-10-31</h2><ul><li>First public release: versions, instances, skins, logs</li></ul></main>"""

ABOUT_ZH = f"""<main class="wrap doc-index"><h1>关于</h1>
    <p class="lead">Vein Launcher 由 Zhanjhn Studio 开发与维护。</p>
    <p>项目定位是便携、可扩展的 Minecraft Java 启动器：不写注册表、数据自包含、插件与 MLC 控制层开放给二次开发。</p>
    <ul><li><a href="{GH}" target="_blank" rel="noopener">GitHub 仓库</a></li><li><a href="docs.html">文档</a></li><li><a href="download.html">下载</a></li></ul></main>"""

ABOUT_EN = f"""<main class="wrap doc-index"><h1>About</h1>
    <p class="lead">Vein Launcher is built and maintained by Zhanjhn Studio.</p>
    <p>A portable, extensible Minecraft Java launcher: no registry writes, self-contained data, plugins and MLC open for extension.</p>
    <ul><li><a href="{GH}" target="_blank" rel="noopener">GitHub</a></li><li><a href="docs.html">Docs</a></li><li><a href="download.html">Download</a></li></ul></main>"""

PRIVACY_ZH = """<main class="wrap doc-index"><h1>隐私</h1>
    <p class="lead">本地优先：账号令牌、配置、日志都不上传。</p>
    <h2>联网请求</h2>
    <ul><li>版本清单 / 客户端 / 资源：BMCLAPI 与 Mojang 官方源</li><li>皮肤：LittleSkin / authlib-injector</li>
    <li>公告与更新：GitHub、公告站</li><li>Java：Adoptium</li></ul>
    <h2>本地存储</h2>
    <p>所有数据位于 exe 同级 <code>VeinLauncher/</code>，可整体删除。</p></main>"""

PRIVACY_EN = """<main class="wrap doc-index"><h1>Privacy</h1>
    <p class="lead">Local first: tokens, config and logs never leave your machine.</p>
    <h2>Network requests</h2>
    <ul><li>Versions and assets: BMCLAPI / Mojang</li><li>Skins: LittleSkin / authlib-injector</li>
    <li>Announcements and updates: GitHub</li><li>Java: Adoptium</li></ul>
    <h2>Local storage</h2>
    <p>Everything lives in <code>VeinLauncher/</code> next to the exe.</p></main>"""


def build_lang(lang: str) -> int:
    pages = pages_for(lang)
    order = build_orders(lang)
    count = 0
    base_dir = ROOT if lang == "zh" else ROOT / "en"

    for p in pages:
        out = base_dir / p["path"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(doc_page(lang, p, order), encoding="utf-8")
        count += 1

    home_body = HOME_ZH_V6 if lang == "zh" else HOME_EN_V6.replace('src="assets/', 'src="../assets/')
    root_bodies = {
        "index.html": home_body,
        "docs.html": docs_hub(lang, order),
        "download.html": download_page(lang),
        "releases.html": RELEASES_ZH if lang == "zh" else RELEASES_EN,
        "changelog.html": CHANGELOG_ZH if lang == "zh" else CHANGELOG_EN,
        "about.html": ABOUT_ZH if lang == "zh" else ABOUT_EN,
        "privacy.html": PRIVACY_ZH if lang == "zh" else PRIVACY_EN,
    }
    titles = {
        "index.html": "Vein Launcher — Minecraft，但更干净" if lang == "zh" else "Vein Launcher — Minecraft, but cleaner",
        "docs.html": "文档 — Vein Launcher" if lang == "zh" else "Docs — Vein Launcher",
        "download.html": "下载 — Vein Launcher" if lang == "zh" else "Download — Vein Launcher",
        "releases.html": "版本 — Vein Launcher" if lang == "zh" else "Releases — Vein Launcher",
        "changelog.html": "更新日志 — Vein Launcher" if lang == "zh" else "Changelog — Vein Launcher",
        "about.html": "关于 — Vein Launcher" if lang == "zh" else "About — Vein Launcher",
        "privacy.html": "隐私 — Vein Launcher" if lang == "zh" else "Privacy — Vein Launcher",
    }
    for path, body in root_bodies.items():
        full = path if lang == "zh" else "en/" + path
        (base_dir / path).write_text(shell(lang, path=full, title=titles[path], body=body, order=order), encoding="utf-8")
        count += 1
    return count


def build_redirects() -> None:
    targets = {
        "quickstart.html": "docs.html", "player.html": "docs.html", "developer.html": "docs.html",
        "plugin.html": "docs.html", "mlc.html": "docs.html", "faq.html": "reference/faq.html",
    }
    for old, new in targets.items():
        (ROOT / old).write_text(
            f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8" />
<meta http-equiv="refresh" content="0;url={new}" /><link rel="canonical" href="{new}" />
<title>Moved — Vein Launcher</title></head><body style="font-family:system-ui;padding:40px">
<p>This page moved to <a href="{new}">{new}</a>.</p></body></html>""",
            encoding="utf-8",
        )


def main() -> None:
    zh = build_lang("zh")
    en = build_lang("en")
    build_redirects()
    print(f"generated zh={zh} en={en} pages + redirects")


if __name__ == "__main__":
    main()
