"""生成 Vein Launcher 官网 v7（中英双语、多页面、搜索、版本切换、SEO）。"""

from __future__ import annotations

import html
import re
from pathlib import Path

from site_content import PAGES
from site_content_en import PAGES_EN
from site_home_v6 import HOME_EN as HOME_EN_V6, HOME_ZH as HOME_ZH_V6
from site_pages import (
    ABOUT_EN, ABOUT_ZH, COMMUNITY_EN, COMMUNITY_ZH, CONTRIBUTE_EN, CONTRIBUTE_ZH,
    DOWNLOAD_EN, DOWNLOAD_ZH, LICENSE_EN, LICENSE_ZH, PRIVACY_EN, PRIVACY_ZH,
    ROADMAP_EN, ROADMAP_ZH, SECURITY_EN, SECURITY_ZH, SHOWCASE_EN, SHOWCASE_ZH,
)

ROOT = Path(__file__).resolve().parents[1] / "veinwebsite-don'tupdategithub"
GH = "https://github.com/zhanjhn-studio/vein_launcher"
ISSUES = f"{GH}/issues"
DISCUSS = f"{GH}/discussions"
ZIP = "https://github.com/zhanjhn-studio/vein_launcher/releases/download/v0.5.0/VeinLauncher-0.5.0-win64.zip"

VERSION = "0.5.0"

ROOT_PAGES = [
    ("index.html", "首页", "Vein Launcher — Minecraft，但更干净", "Home", "Vein Launcher — Minecraft, but cleaner"),
    ("docs.html", "文档", "文档 — Vein Launcher", "Docs", "Docs — Vein Launcher"),
    ("quickstart.html", "快速开始", "快速开始 — Vein Launcher 文档", "Quick start", "Quick start — Vein Launcher Docs"),
    ("player.html", "玩家指南", "玩家指南 — Vein Launcher 文档", "Player guide", "Player guide — Vein Launcher Docs"),
    ("developer.html", "二次开发", "二次开发 — Vein Launcher 文档", "Development", "Development — Vein Launcher Docs"),
    ("plugin.html", "插件开发", "插件开发 — Vein Launcher 文档", "Plugins", "Plugins — Vein Launcher Docs"),
    ("mlc.html", "MLC", "MLC 控制层 — Vein Launcher 文档", "MLC", "MLC — Vein Launcher Docs"),
    ("faq.html", "FAQ", "FAQ — Vein Launcher", "FAQ", "FAQ — Vein Launcher"),
    ("download.html", "下载", "下载 — Vein Launcher", "Download", "Download — Vein Launcher"),
    ("releases.html", "版本", "版本 — Vein Launcher", "Releases", "Releases — Vein Launcher"),
    ("changelog.html", "更新日志", "更新日志 — Vein Launcher", "Changelog", "Changelog — Vein Launcher"),
    ("roadmap.html", "路线图", "路线图 — Vein Launcher", "Roadmap", "Roadmap — Vein Launcher"),
    ("security.html", "安全", "安全 — Vein Launcher", "Security", "Security — Vein Launcher"),
    ("contribute.html", "贡献", "贡献指南 — Vein Launcher", "Contributing", "Contributing — Vein Launcher"),
    ("showcase.html", "展示墙", "展示墙 — Vein Launcher", "Showcase", "Showcase — Vein Launcher"),
    ("community.html", "社区", "社区 — Vein Launcher", "Community", "Community — Vein Launcher"),
    ("about.html", "关于", "关于 — Vein Launcher", "About", "About — Vein Launcher"),
    ("privacy.html", "隐私", "隐私 — Vein Launcher", "Privacy", "Privacy — Vein Launcher"),
    ("license.html", "许可证", "许可证 — Vein Launcher", "License", "License — Vein Launcher"),
]

NAV = ["index.html", "docs.html", "download.html", "community.html"]

FOOTER_GROUPS = [
    ("zh", "产品", [("docs.html", "文档"), ("download.html", "下载"), ("releases.html", "版本"), ("changelog.html", "更新日志")]),
    ("zh", "社区", [(GH, "GitHub"), (ISSUES, "Issue 反馈"), (DISCUSS, "Discussions"), ("contribute.html", "贡献指南")]),
    ("zh", "资源", [("roadmap.html", "路线图"), ("security.html", "安全"), ("showcase.html", "展示墙"), ("about.html", "关于我们")]),
    ("zh", "法务", [("license.html", "MIT 许可证"), ("privacy.html", "隐私声明"), ("community.html", "社区规范")]),
    ("en", "Product", [("docs.html", "Docs"), ("download.html", "Download"), ("releases.html", "Releases"), ("changelog.html", "Changelog")]),
    ("en", "Community", [(GH, "GitHub"), (ISSUES, "Issues"), (DISCUSS, "Discussions"), ("contribute.html", "Contributing")]),
    ("en", "Resources", [("roadmap.html", "Roadmap"), ("security.html", "Security"), ("showcase.html", "Showcase"), ("about.html", "About")]),
    ("en", "Legal", [("license.html", "MIT License"), ("privacy.html", "Privacy"), ("community.html", "Community")]),
]

GROUP_INTRO = {
    "zh": {
        "Getting started": ("few", "从下载到进入游戏，最短路径。", "开始使用"),
        "Playing": ("few", "实例、皮肤、指令与排错。", "玩家"),
        "Development": ("few", "架构、协议、构建与发布。", "二次开发"),
        "Plugins": ("few", "Node 宿主、权限、Lua UI 与示例。", "插件开发"),
        "MLC": ("few", "不装 mod 控制原版游戏的控制层。", "MLC"),
        "Reference": ("few", "配置、术语、安全与常见问题。", "参考"),
    },
    "en": {
        "Getting started": ("few", "From download to first launch.", "Getting started"),
        "Playing": ("few", "Instances, skins, commands and troubleshooting.", "Playing"),
        "Development": ("few", "Architecture, protocol, build and release.", "Development"),
        "Plugins": ("few", "Node host, permissions, Lua UI and examples.", "Plugins"),
        "MLC": ("few", "Control vanilla Minecraft without a mod.", "MLC"),
        "Reference": ("few", "Config, glossary, security and FAQ.", "Reference"),
    },
}

EN_GROUP_OF_ZH = {
    "开始使用": "Getting started", "玩家": "Playing", "二次开发": "Development",
    "插件开发": "Plugins", "MLC": "MLC", "参考": "Reference",
}

GROUP_LANDING = {
    "quickstart.html": ("Getting started", "开始使用", "快速开始", "三道最短路径：安装、首次启动、Java。"),
    "player.html": ("Playing", "玩家", "玩家指南", "实例、皮肤、指令速查、热键与排错。"),
    "developer.html": ("Development", "二次开发", "二次开发", "架构分层、JSON-RPC、前端构建、测试与打包。"),
    "plugin.html": ("Plugins", "插件开发", "插件开发", "插件运行方式、清单、权限、能力 API、Lua UI 与示例。"),
    "mlc.html": ("MLC", "MLC", "MLC 控制层", "原版 javaagent 的原理、协议、事件与排错。"),
}


def pages_for(lang: str):
    if lang == "zh":
        return PAGES
    out = []
    for p in PAGES_EN:
        q = dict(p)
        zh = next((x for x in PAGES if x["path"] == p["path"]), None)
        q["group"] = EN_GROUP_OF_ZH.get(zh["group"], p["group"]) if zh else p["group"]
        out.append(q)
    return out


def order_for(lang: str):
    return [p[0] for p in ROOT_PAGES] + [p["path"] for p in pages_for(lang)]


def depth_for(lang: str, path: str) -> str:
    logical = path[3:] if path.startswith("en/") else path
    nested = "/" in logical
    if lang == "en":
        return "../../" if nested else "../"
    return "../" if nested else ""


def nav_base_for(lang: str, path: str) -> str:
    logical = path[3:] if path.startswith("en/") else path
    return "../" if "/" in logical else ""


def is_doc_path(path: str) -> bool:
    logical = path[3:] if path.startswith("en/") else path
    return "/" in logical


# ---------------------------------------------------------------- slug / TOC
def slug(text: str) -> str:
    s = re.sub(r"<[^>]+>", "", text)
    s = re.sub(r"[^\w\u4e00-\u9fa5]+", "-", s.strip().lower()).strip("-")
    return s[:40] or "section"


def with_ids_and_toc(body: str, lang: str):
    toc = []

    def repl(m):
        level, inner = m.group(1), m.group(2)
        plain = re.sub(r"<[^>]+>", "", inner)
        hid = slug(plain)
        toc.append((level, hid, plain))
        return f'<h{level} id="{hid}">{inner}</h{level}>'

    body = re.sub(r"<h([23])>(.*?)</h\1>", repl, body, flags=re.S)
    if not toc:
        return body, ""
    title = "本页内容" if lang == "zh" else "On this page"
    links = "".join(
        f'<a class="{"sub" if lv == "3" else "main"}" href="#{hid}">{html.escape(plain)}</a>'
        for lv, hid, plain in toc
    )
    return body, f'<aside class="docs-toc"><h4>{title}</h4>{links}</aside>'


# ---------------------------------------------------------------- header/footer
def header(lang: str, path: str, order: list[str], docs_page: bool) -> str:
    base = depth_for(lang, path)
    navb = nav_base_for(lang, path)
    logical = path[3:] if path.startswith("en/") else path
    labels = (
        [("index.html", "首页"), ("docs.html", "文档"), ("download.html", "下载"), ("community.html", "社区")]
        if lang == "zh" else
        [("index.html", "Home"), ("docs.html", "Docs"), ("download.html", "Download"), ("community.html", "Community")]
    )
    navs = []
    for href, label in labels:
        active = ' aria-current="page"' if href == logical else ""
        navs.append(f'<a href="{navb}{href}" data-order="{order.index(href)}"{active}>{label}</a>')
    navs.append(f'<a href="{GH}" target="_blank" rel="noopener">GitHub</a>')

    other = "en/" + logical if lang == "zh" else logical
    if lang == "en":
        lang_href = base + logical
    else:
        lang_href = base + "en/" + logical

    search = (
        f'<button class="search-btn" type="button" data-search-open>'
        f'{"搜索文档" if lang == "zh" else "Search docs"} <kbd>Ctrl K</kbd></button>'
        if docs_page else ""
    )
    version = (
        f'<select class="ver-select" data-version aria-label="docs version">'
        f'<option value="0.5"{"" if lang == "zh" else ""}>v0.5 {"（当前）" if lang == "zh" else "(current)"}</option>'
        f'<option value="0.4" disabled>v0.4 {"（未归档）" if lang == "zh" else "(not archived)"}</option>'
        f'</select>' if docs_page else ""
    )
    return f"""<header class="site-header">
    <div class="wrap">
      <a class="brand" href="{base}index.html"><img src="{base}assets/logo.png" alt="" /><span>Vein<b>Launcher</b></span></a>
      <nav class="site-nav">
        {chr(10).join('        ' + n for n in navs)}
      </nav>
      <div class="header-actions">
        {search}{version}
        <a class="icon-btn" href="{lang_href}">{"EN" if lang == "zh" else "中文"}</a>
        <button class="icon-btn" type="button" data-theme-toggle>{"深色" if lang == "zh" else "Dark"}</button>
        <button class="icon-btn nav-toggle" type="button" data-nav-toggle aria-label="menu">≡</button>
      </div>
    </div>
  </header>"""


def footer(lang: str, path: str) -> str:
    base = depth_for(lang, path)
    sets = [g for g in FOOTER_GROUPS if g[0] == lang]
    cols = "".join(
        f'<div class="footer-col"><h5>{name}</h5>' + "".join(
            f'<a href="{h if h.startswith("http") else base + h}">{t}</a>' for h, t in links
        ) + "</div>"
        for _, name, links in sets
    )
    brand_p = ("便携、可扩展的 Minecraft Java 启动器。数据自包含，插件与 MLC 开放。" if lang == "zh"
               else "A portable, extensible Minecraft Java launcher. Self-contained data, open plugins and MLC.")
    legal = ("MIT 许可证" if lang == "zh" else "MIT License")
    return f"""<footer class="site-footer">
    <div class="wrap">
      <div class="footer-grid">
        <div class="footer-brand">
          <img src="{base}assets/logo.png" alt="" />
          <div><b>Vein Launcher</b><p>{brand_p}</p></div>
        </div>
        {cols}
      </div>
      <div class="footer-bottom">
        <span>© 2026 zhanjhn studio · <a href="{base}license.html">{legal}</a> · v{VERSION}</span>
        <span><a href="{base}privacy.html">{"隐私声明" if lang == "zh" else "Privacy"}</a> · <a href="{base}security.html">{"安全" if lang == "zh" else "Security"}</a> · <a href="{GH}" target="_blank" rel="noopener">GitHub</a> · <a href="{DISCUSS}" target="_blank" rel="noopener">Discussions</a></span>
      </div>
    </div>
  </footer>"""


def shell(lang: str, path: str, title: str, description: str, body: str, order: list[str]) -> str:
    base = depth_for(lang, path)
    docs_page = is_doc_path(path)
    return f"""<!doctype html>
<html lang="{'zh-CN' if lang == 'zh' else 'en'}" data-theme="light">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description)}" />
  <meta property="og:title" content="{html.escape(title)}" />
  <meta property="og:description" content="{html.escape(description)}" />
  <link rel="icon" href="{base}assets/favicon.ico" />
  <link rel="stylesheet" href="{base}assets/site.css" />
  <link rel="stylesheet" href="{base}assets/v7.css" />
</head>
<body data-order="{order.index(path.replace('en/', '', 1) if lang == 'en' else path)}">
  {header(lang, path, order, docs_page)}
  {body}
  {footer(lang, path)}
  <script src="{base}assets/search-index.js"></script>
  <script src="{base}assets/site.js"></script>
</body>
</html>
"""


# ---------------------------------------------------------------- docs page
def sidebar(lang: str, cur_rel: str, order: list[str]) -> str:
    pages = pages_for(lang)
    labels = (["开始使用", "玩家", "二次开发", "插件开发", "MLC", "参考"] if lang == "zh"
              else ["Getting started", "Playing", "Development", "Plugins", "MLC", "Reference"])
    out = []
    for group in labels:
        items = []
        for p in pages:
            if p["group"] != group:
                continue
            active = " active" if p["path"] == cur_rel else ""
            items.append(f'<a href="../{p["path"]}" data-order="{order.index(p["path"])}" class="{active.strip()}">{p["title"]}</a>')
        out.append('<div class="group"><h4>' + group + "</h4>" + "".join(items) + "</div>")
    return '<aside class="docs-side">' + "".join(out) + "</aside>"


def doc_page(lang: str, p: dict, order: list[str]) -> str:
    pages = pages_for(lang)
    docs = [x for x in pages if x["group"] == p["group"]]
    pos = docs.index(p)
    prev_p = docs[pos - 1] if pos > 0 else None
    next_p = docs[pos + 1] if pos + 1 < len(docs) else None

    body, toc = with_ids_and_toc(p["body"], lang)
    pager = '<div class="pager">'
    pager += (f'<a href="../{prev_p["path"]}" data-order="{order.index(prev_p["path"])}">← {prev_p["title"]}</a>'
              if prev_p else "<span></span>")
    pager += (f'<a href="../{next_p["path"]}" data-order="{order.index(next_p["path"])}">{next_p["title"]} →</a>'
              if next_p else "<span></span>")
    pager += "</div>"
    tags = "".join(f"<span>{html.escape(t)}</span>" for t in p["tags"])
    full = p["path"] if lang == "zh" else "en/" + p["path"]
    main = f"""<main class="wrap docs-wrap {'has-toc' if toc else ''}">
    {sidebar(lang, p['path'], order)}
    <article class="docs-main">
      <h1>{p["title"]}</h1>
      <p class="subtitle">{p["subtitle"]}</p>
      <div class="docs-tags">{tags}</div>
      {body}
      {pager}
    </article>
    {toc}
  </main>"""
    title = f'{p["title"]} — Vein Launcher {"文档" if lang == "zh" else "Docs"}'
    desc = re.sub(r"<[^>]+>", "", p["subtitle"])
    return shell(lang, full, title, desc, main, order)


# ---------------------------------------------------------------- root pages
def group_landing(lang: str, path: str, order: list[str]) -> str:
    en_group, zh_group, zh_title, zh_lead = GROUP_LANDING[path]
    group = en_group if lang == "en" else zh_group
    title = zh_title if lang == "zh" else path.replace(".html", "").title()
    lead = zh_lead if lang == "zh" else {
        "quickstart.html": "Three short paths: install, first launch, Java.",
        "player.html": "Instances, skins, command palette, hotkeys and troubleshooting.",
        "developer.html": "Layers, JSON-RPC, frontend build, testing and packaging.",
        "plugin.html": "Plugin host, manifest, permissions, API, Lua UI and examples.",
        "mlc.html": "How the vanilla javaagent works, the protocol, events and troubleshooting.",
    }[path]
    cards = "".join(
        f'<a class="doc-list-item" href="{p["path"]}" data-order="{order.index(p["path"])}">'
        f'<b>{p["title"]}</b><span>{p["subtitle"]}</span></a>'
        for p in pages_for(lang) if p["group"] == group
    )
    extra = ""
    if path == "quickstart.html":
        if lang == "zh":
            extra = f"""
<div class="meta-grid" style="margin:30px 0;">
  <div><b>1. 解压运行</b><span>双击 VeinLauncher.exe</span></div>
  <div><b>2. 安装版本</b><span>原版或加载器</span></div>
  <div><b>3. 开始游戏</b><span>选账号 → 启动</span></div>
  <div><b>遇到问题</b><span><a href="faq.html">看 FAQ</a></span></div>
</div>
<p><a class="btn primary" href="download.html">下载 v0.5.0</a> <a class="btn" href="getting-started/install.html">安装说明</a></p>"""
        else:
            extra = f"""
<div class="meta-grid" style="margin:30px 0;">
  <div><b>1. Unzip</b><span>Run VeinLauncher.exe</span></div>
  <div><b>2. Install</b><span>Vanilla or a loader</span></div>
  <div><b>3. Play</b><span>Pick account → launch</span></div>
  <div><b>Stuck?</b><span><a href="faq.html">Read the FAQ</a></span></div>
</div>
<p><a class="btn primary" href="download.html">Download v0.5.0</a> <a class="btn" href="../getting-started/install.html">Install guide</a></p>"""
    body = f"""<main class="wrap doc-index">
    <h1>{title}</h1>
    <p class="lead">{lead}</p>
    {extra}
    <div class="doc-list">{cards}</div>
    <p style="margin-top:28px;"><a href="docs.html" data-order="{order.index('docs.html')}">{"查看完整文档 →" if lang == "zh" else "All documentation →"}</a></p>
  </main>"""
    full = path if lang == "zh" else "en/" + path
    return shell(lang, full, f"{title} — Vein Launcher", lead, body, order)


def faq_page(lang: str, order: list[str]) -> str:
    faq = next(p for p in PAGES if p["path"] == "reference/faq.html")
    data = faq if lang == "zh" else next(p for p in PAGES_EN if p["path"] == "reference/faq.html")
    body, _ = with_ids_and_toc(data["body"], lang)
    title = "FAQ" if lang == "zh" else "FAQ"
    main = f"""<main class="wrap doc-index faq-page">
    <h1>{title}</h1>
    <p class="lead">{"按症状找答案；完整文档在文档页。" if lang == "zh" else "Answers by symptom; full docs live under Docs."}</p>
    <div class="faq-body docs-main">{body}</div>
    <p style="margin-top:30px;"><a href="docs.html" data-order="{order.index('docs.html')}">{"完整文档 →" if lang == "zh" else "Full docs →"}</a></p>
  </main>"""
    full = "faq.html" if lang == "zh" else "en/faq.html"
    return shell(lang, full, f"FAQ — Vein Launcher", "常见问题与排错", main, order)


ROOT_CONTENT = {
    "download.html": (DOWNLOAD_ZH, DOWNLOAD_EN),
    "roadmap.html": (ROADMAP_ZH, ROADMAP_EN),
    "security.html": (SECURITY_ZH, SECURITY_EN),
    "contribute.html": (CONTRIBUTE_ZH, CONTRIBUTE_EN),
    "showcase.html": (SHOWCASE_ZH, SHOWCASE_EN),
    "community.html": (COMMUNITY_ZH, COMMUNITY_EN),
    "about.html": (ABOUT_ZH, ABOUT_EN),
    "privacy.html": (PRIVACY_ZH, PRIVACY_EN),
    "license.html": (LICENSE_ZH, LICENSE_EN),
}

RELEASES_ZH = f"""<main class="wrap doc-index"><h1>版本</h1>
<p class="lead">每个版本都有对应的 GitHub Release 与下载资产。</p>
<table><thead><tr><th>版本</th><th>说明</th><th>日期</th></tr></thead><tbody>
<tr><td><a href="{ZIP.split('/releases/')[0]}/releases/tag/v0.5.0" target="_blank" rel="noopener">v0.5.0</a></td><td>MLC 原版控制、附魔书指令、插件能力、总开关</td><td>2026-11-08</td></tr>
<tr><td><a href="{ZIP.split('/releases/')[0]}/releases/tag/v0.1.0" target="_blank" rel="noopener">v0.1.0</a></td><td>首个公开版本</td><td>2026-10-31</td></tr>
</tbody></table>
<p><a href="{ZIP.split('/releases/')[0]}/releases" target="_blank" rel="noopener">在 GitHub 查看全部 →</a></p></main>"""

RELEASES_EN = RELEASES_ZH.replace("<h1>版本</h1>", "<h1>Releases</h1>").replace(
    "每个版本都有对应的 GitHub Release 与下载资产。", "Every version has a GitHub Release and downloadable assets."
).replace("说明", "Notes").replace("日期", "Date").replace("首个公开版本", "First public release")

CHANGELOG_ZH = """<main class="wrap doc-index"><h1>更新日志</h1>
<p class="lead">按版本倒序记录主要变化，升级前建议先看这里。</p>
<h2>v0.5.0 · 2026-11-08</h2>
<h3>新增</h3><ul><li>MLC：原版 javaagent 控制层，状态 / 指令 / 事件</li><li>指令速查附魔书面板、Enter 发送</li><li>插件：game.running / app.info / versions.list / MLC 事件</li></ul>
<h3>修复</h3><ul><li>MLC 总开关文案与对齐</li><li>翻译层状态切换卡旧值</li><li>速查窗抢焦点导致单机暂停</li></ul>
<h3>破坏性改动</h3><ul><li>无</li></ul>
<h2>v0.1.0 · 2026-10-31</h2>
<ul><li>首个公开版本：版本下载、实例管理、皮肤、日志</li></ul></main>"""

CHANGELOG_EN = """<main class="wrap doc-index"><h1>Changelog</h1>
<p class="lead">Main changes, newest first. Read before upgrading.</p>
<h2>v0.5.0 · 2026-11-08</h2>
<h3>Added</h3><ul><li>MLC: vanilla javaagent control layer — state, commands, events</li><li>Enchanted-book command palette; Enter sends</li><li>Plugins: game.running / app.info / versions.list / MLC events</li></ul>
<h3>Fixed</h3><ul><li>MLC master switch label and alignment</li><li>Translation layer keeping stale values</li><li>Palette focus pausing single-player</li></ul>
<h3>Breaking</h3><ul><li>None</li></ul>
<h2>v0.1.0 · 2026-10-31</h2><ul><li>First public release</li></ul></main>"""


def docs_hub(lang: str, order: list[str]) -> str:
    pages = pages_for(lang)
    labels = (["开始使用", "玩家", "二次开发", "插件开发", "MLC", "参考"] if lang == "zh"
              else ["Getting started", "Playing", "Development", "Plugins", "MLC", "Reference"])
    blocks = []
    for group in labels:
        items = "".join(
            f'<a href="{p["path"]}" data-order="{order.index(p["path"])}"><b>{p["title"]}</b><span>{p["subtitle"]}</span></a>'
            for p in pages if p["group"] == group
        )
        blocks.append(f'<section class="doc-group"><h2>{group}</h2><div class="doc-list">{items}</div></section>')
    title = "文档" if lang == "zh" else "Docs"
    lead = ("按主题拆分的完整文档。每一页都可以单独打开、单独收藏。" if lang == "zh"
            else "Complete documentation split by topic. Every page can be opened and bookmarked on its own.")
    body = f"""<main class="wrap doc-index">
    <h1>{title}</h1>
    <p class="lead">{lead}</p>
    {''.join(blocks)}
  </main>"""
    full = "docs.html" if lang == "zh" else "en/docs.html"
    return shell(lang, full, f"{title} — Vein Launcher", lead, body, order)


def build_lang(lang: str) -> list[tuple[str, str, str]]:
    pages = pages_for(lang)
    order = order_for(lang)
    base_dir = ROOT if lang == "zh" else ROOT / "en"
    written: list[tuple[str, str, str]] = []

    # docs
    for p in pages:
        out = base_dir / p["path"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(doc_page(lang, p, order), encoding="utf-8")
        written.append((lang + "/" + p["path"], p["title"], p["subtitle"]))

    root_pages = {r[0]: r for r in ROOT_PAGES}
    for path in [p[0] for p in ROOT_PAGES]:
        full = path if lang == "zh" else "en/" + path
        if path == "index.html":
            home = HOME_ZH_V6 if lang == "zh" else HOME_EN_V6
            if lang == "en":
                home = home.replace('src="assets/', 'src="../assets/')
            body = home
            title = "Vein Launcher — Minecraft，但更干净" if lang == "zh" else "Vein Launcher — Minecraft, but cleaner"
            desc = "便携 Minecraft Java 启动器" if lang == "zh" else "Portable Minecraft Java launcher"
        elif path == "docs.html":
            out = base_dir / path
            out.write_text(docs_hub(lang, order), encoding="utf-8")
            written.append((full, "Docs", "Documentation"))
            continue
        elif path in GROUP_LANDING:
            out = base_dir / path
            out.write_text(group_landing(lang, path, order), encoding="utf-8")
            written.append((full, path, "group"))
            continue
        elif path == "faq.html":
            out = base_dir / path
            out.write_text(faq_page(lang, order), encoding="utf-8")
            written.append((full, "FAQ", "FAQ"))
            continue
        elif path == "releases.html":
            body = RELEASES_ZH if lang == "zh" else RELEASES_EN
            title = "版本 — Vein Launcher" if lang == "zh" else "Releases — Vein Launcher"
            desc = "全部版本与下载"
        elif path == "changelog.html":
            body = CHANGELOG_ZH if lang == "zh" else CHANGELOG_EN
            title = "更新日志 — Vein Launcher" if lang == "zh" else "Changelog — Vein Launcher"
            desc = "版本更新内容"
        else:
            zh_body, en_body = ROOT_CONTENT[path]
            body = zh_body if lang == "zh" else en_body
            if lang == "zh":
                body = body.replace('href="../', 'href="').replace('src="../', 'src="')
            else:
                import re as _re
                body = _re.sub(r'href="\.\./([^"]+\.html)"', r'href="\1"', body)
            if not body.lstrip().startswith("<main"):
                body = '<main class="wrap doc-index">' + body + "</main>" 
            title = root_pages[path][2] if lang == "zh" else root_pages[path][4]
            desc = re.sub(r"<[^>]+>", "", body.split("</h1>")[0])[:120]
        out = base_dir / path
        out.write_text(shell(lang, full, title, desc or title, body, order), encoding="utf-8")
        written.append((full, title, desc or ""))

    # 图片路径修正（首页英文）
    return written


def build_search_index() -> None:
    entries = []
    for lang, pages in (("zh", PAGES), ("en", PAGES_EN)):
        for p in pages:
            text = re.sub(r"<[^>]+>", " ", p["body"])
            text = re.sub(r"\s+", " ", text).strip()[:140]
            url = ("../" + p["path"]) if lang == "en" else p["path"]
            entries.append({
                "t": p["title"], "s": p["subtitle"], "x": text,
                "u": url, "g": p["group"], "l": lang,
            })
    for path, zh_title, _zh, en_title, _en in ROOT_PAGES:
        entries.append({"t": zh_title, "s": "", "x": "", "u": path, "g": "页面", "l": "zh"})
        entries.append({"t": en_title, "s": "", "x": "", "u": "en/" + path, "g": "Page", "l": "en"})
    import json
    (ROOT / "assets" / "search-index.js").write_text(
        "window.VL_SEARCH=" + json.dumps(entries, ensure_ascii=False) + ";\n", encoding="utf-8"
    )


def build_sitemap() -> None:
    urls = []
    for path, *_ in ROOT_PAGES:
        urls.append(path)
        urls.append("en/" + path)
    for p in PAGES:
        urls.append(p["path"])
        urls.append("en/" + p["path"])
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        lines.append(f"  <url><loc>https://zhanjhn-studio.github.io/vein_launcher/{u}</loc></url>")
    lines.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: https://zhanjhn-studio.github.io/vein_launcher/sitemap.xml\n", encoding="utf-8")


def main() -> None:
    zh = build_lang("zh")
    en = build_lang("en")
    build_search_index()
    build_sitemap()
    # 旧链接重定向保持可用
    for old in ("quickstart.html",):
        pass
    print(f"generated zh={len(zh)} en={len(en)} + sitemap + search index")


if __name__ == "__main__":
    main()
