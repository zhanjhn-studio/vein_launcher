"""生成 Vein Launcher 开发者介绍文档（Word）"""

from __future__ import annotations

from datetime import date

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Cm

BODY_FONT = "微软雅黑"
CODE_FONT = "Consolas"
ACCENT = RGBColor(0x1F, 0x4E, 0x79)


def set_font(run, name: str = BODY_FONT, size: float | None = None,
             bold: bool | None = None, color: RGBColor | None = None) -> None:
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color is not None:
        run.font.color.rgb = color


def body(doc, text: str, size: float = 10.5, space_after: float = 6):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    run = p.add_run(text)
    set_font(run, size=size)
    return p


def bullet(doc, text: str):
    p = doc.add_paragraph(style="List Bullet")
    run = p.add_run(text)
    set_font(run, size=10.5)
    return p


def code(doc, text: str):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.6)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(text)
    set_font(run, name=CODE_FONT, size=9, color=RGBColor(0x33, 0x33, 0x33))
    return p


def heading(doc, text: str, level: int = 1):
    h = doc.add_heading(level=level)
    run = h.add_run(text)
    set_font(run, size={1: 16, 2: 12.5, 3: 11}[level], bold=True, color=ACCENT)
    return h


def table(doc, headers: list[str], rows: list[list[str]], widths: list[float] | None = None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    header = t.rows[0].cells
    for i, text in enumerate(headers):
        header[i].text = ""
        run = header[i].paragraphs[0].add_run(text)
        set_font(run, size=9.5, bold=True)
    for row in rows:
        cells = t.add_row().cells
        for i, text in enumerate(row):
            cells[i].text = ""
            run = cells[i].paragraphs[0].add_run(text)
            set_font(run, size=9)
    if widths:
        for row in t.rows:
            for i, width in enumerate(widths):
                row.cells[i].width = Cm(width)
    doc.add_paragraph()
    return t


def main() -> None:
    doc = Document()

    section = doc.sections[0]
    section.left_margin = Cm(2.6)
    section.right_margin = Cm(2.6)
    section.top_margin = Cm(2.4)
    section.bottom_margin = Cm(2.2)

    # ---------- 封面 ----------
    for _ in range(5):
        doc.add_paragraph()

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("Vein Launcher")
    set_font(run, size=34, bold=True, color=ACCENT)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("Minecraft Java 版启动器 · 开发者介绍")
    set_font(run, size=14, color=RGBColor(0x55, 0x55, 0x55))

    doc.add_paragraph()
    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = meta.add_run(f"版本 0.0.1　|　{date.today().isoformat()}　|　内部文档")
    set_font(run, size=10, color=RGBColor(0x77, 0x77, 0x77))

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ---------- 1 概述 ----------
    heading(doc, "1　项目概述")
    body(
        doc,
        "Vein Launcher 是面向 Windows 的 Minecraft Java 版启动器。项目采用五层架构："
        "Common（公共能力）、Domain（领域模型）、Infrastructure（基础设施）、"
        "Application（用例编排）、Presentation（界面）。",
    )
    body(
        doc,
        "界面不再使用 Qt 原生控件绘制，而是由 PySide6 的 QWebEngineView 承载 React 应用，"
        "Python 负责业务与系统能力，二者通过 QWebChannel 通信桥交互。"
        "Node.js 作为独立的插件宿主，插件通过双向 RPC 与启动器通信，是本项目的核心特色。",
    )
    body(doc, "当前阶段：后端主干与前端框架已打通，插件宿主尚未实现。", size=10.5)

    # ---------- 2 技术栈 ----------
    heading(doc, "2　技术栈与运行环境")
    table(
        doc,
        ["层级 / 领域", "选型", "说明"],
        [
            ["语言", "Python 3.11+", "后端与系统集成"],
            ["桌面容器", "PySide6 6.12", "QWebEngineView + QWebChannel"],
            ["前端", "React 19 + esbuild", "UI 全部由 React 渲染"],
            ["网络", "aiohttp", "异步 HTTP"],
            ["数据模型", "Pydantic v2", "配置与领域模型校验"],
            ["插件宿主", "Node.js 18+", "独立进程，双向 JSON-RPC（规划中）"],
            ["打包", "PyInstaller", "单机分发（未开始）"],
        ],
        widths=[3.2, 4.2, 8.0],
    )

    # ---------- 3 架构 ----------
    heading(doc, "3　分层架构")
    body(
        doc,
        "依赖方向严格自上而下：Presentation → Application → Domain ← Infrastructure。"
        "跨层通信只允许通过 event_bus 事件总线，禁止跨层直接调用。",
    )
    table(
        doc,
        ["层", "职责", "允许依赖"],
        [
            ["Common", "事件总线、配置、日志、i18n、路径工具、异常", "无"],
            ["Domain", "版本 / 账号 / 加载器 / 模组 / 插件模型与仓储接口",
             "Common"],
            ["Infrastructure", "HTTP、下载、Java 进程、文件存储、Node 宿主", "Common, Domain 接口"],
            ["Application", "版本安装、启动编排、账号与模组服务", "Domain, Infrastructure"],
            ["Presentation", "WebView 窗口、通信桥、React 界面", "Application"],
        ],
        widths=[3.0, 9.0, 4.0],
    )

    # ---------- 4 目录 ----------
    heading(doc, "4　目录结构")
    for line in [
        "vein_launcher/",
        "├── common/              事件总线、配置、日志、i18n、工具",
        "├── domain/              模型、解析服务、仓储接口",
        "├── infrastructure/",
        "│   ├── network/         http_client / api_client / modrinth / curseforge",
        "│   ├── download/        downloader / sha_checker / queue",
        "│   ├── process/         java_detector / game_process",
        "│   └── storage/         file_storage",
        "├── application/services/ version / launcher / account",
        "└── presentation/",
        "    ├── main.py          QWebEngineView 主窗口",
        "    ├── bridge.py        QWebChannel 通信桥",
        "    ├── context.py       服务装配",
        "    └── webui/           React 前端（src / dist）",
    ]:
        code(doc, line)

    # ---------- 5 模块 ----------
    heading(doc, "5　关键模块说明")

    heading(doc, "5.1　Common", level=2)
    bullet(doc, "event_bus.py：线程安全的发布/订阅，全项目唯一的跨层通信通道。")
    bullet(doc, "events.py：事件名常量，如 download.task.progress、game.log.update、game.exited。")
    bullet(doc, "settings.py：Pydantic 配置模型 + JSON 单例，存放 Java、内存、下载、UI 等设置。")
    bullet(doc, "path_utils.py：基于 pathlib 的目录约定（实例、assets、libraries）。")

    heading(doc, "5.2　Domain", level=2)
    bullet(doc, "models/version.py：Mojang 版本 JSON、库、资源索引模型。")
    bullet(doc, "models/account.py：离线与微软账号模型、账号管理器。")
    bullet(doc, "models/plugin.py：插件清单、权限枚举、RPC 契约。")
    bullet(doc, "services/version_resolver.py：沿 inheritsFrom 合并父版本。")
    bullet(doc, "repositories/：文件仓储与网络仓储的抽象接口。")

    heading(doc, "5.3　Infrastructure", level=2)
    bullet(doc, "http_client：aiohttp 会话封装（UA、超时、代理、重试）与统一异常。")
    bullet(doc, "api_client：Mojang 版本清单、版本 JSON、assets 索引。")
    bullet(doc, "modrinth / curseforge：资源搜索与文件映射。")
    bullet(doc, "downloader：单文件断点续传 + SHA-1 校验 + 原子落盘；queue 负责并发。")
    bullet(doc, "java_detector：注册表 / JAVA_HOME / PATH / 常见目录探测。")
    bullet(doc, "game_process：拉取子进程并逐行转发 stdout 到事件总线。")

    heading(doc, "5.4　Application", level=2)
    bullet(doc, "version_service：版本合并、安装（client、libraries、assets）。")
    bullet(doc, "launcher_service：构建 JVM 与游戏参数、解压 natives、启动进程。")
    bullet(doc, "account_service：离线账号的增删选与持久化。")

    # ---------- 6 通信桥 ----------
    heading(doc, "6　Python ↔ React 通信桥")
    body(
        doc,
        "前端通过 QWebChannel 获取 bridge 对象，所有调用携带自增 requestId；"
        "Python 处理完成后回调全局函数返回结果，下载进度通过独立函数推送。",
    )
    code(doc, "// JS")
    code(doc, "call('versions.install', '1.20.4')")
    code(doc, "")
    code(doc, "// Python 回调")
    code(doc, "window.__veinResult(requestId, ok, payload)")
    code(doc, "window.__veinProgress(taskId, done, total)")

    table(
        doc,
        ["方法", "参数", "返回"],
        [
            ["app.info", "—", "{version, dataDir}"],
            ["versions.remote", "limit", "[{id, type, release_time}]"],
            ["versions.installed", "—", "[{id, type}]"],
            ["versions.install", "versionId", "{files, ok, failed}"],
            ["versions.delete", "versionId", "{deleted}"],
            ["launch", "versionId, username", "{pid}"],
            ["accounts.list / add / select", "username / accountId", "账号列表或结果"],
            ["mods.search", "query, type, mcVersion, loader", "[{slug,title,...}]"],
            ["mods.install", "slug, instance, type, loader", "{installed, path}"],
            ["java.detect", "—", "[{path, major, vendor}]"],
        ],
        widths=[4.6, 6.2, 5.0],
    )

    # ---------- 7 插件 ----------
    heading(doc, "7　插件系统（核心特色）")
    body(
        doc,
        "设计目标：插件以 NPM 包分发，运行在独立 Node.js 进程中，"
        "通过 JSON-RPC 与 Python 宿主双向通信；宿主按清单中的权限声明进行能力校验与路径沙箱限制。",
    )
    bullet(doc, "协议：逐行 JSON，Python → Node 为请求，Node → Python 为能力调用与日志通知。")
    bullet(doc, "能力：文件读写、下载队列、游戏启动、UI 通知、配置读写、HTTP 代理。")
    bullet(doc, "安全：权限未声明即拒绝；文件路径限制在插件自身目录内。")
    bullet(doc, "现状：模型与契约（domain/models/plugin.py）已完成，宿主实现待开发。")

    # ---------- 8 开发环境 ----------
    heading(doc, "8　开发环境与运行")
    body(doc, "依赖安装：")
    code(doc, "python -m pip install -r requirements.txt")
    body(doc, "启动（开发模式）：")
    code(doc, "python -m vein_launcher.presentation.main")
    body(doc, "前端构建（修改 webui/src 后）：")
    code(doc, "node_modules/.bin/esbuild src/main.jsx --bundle \\")
    code(doc, "  --outfile=dist/app.js --jsx=automatic --minify")
    body(
        doc,
        "说明：前端产物 dist/ 已随仓库提交，日常运行无需重新构建；"
        "仅在修改 React 源码后才需要执行构建。",
    )

    # ---------- 9 规范 ----------
    heading(doc, "9　代码规范")
    bullet(doc, "跨层通信只走 event_bus；禁止在 UI 中直接 import 基础设施实现。")
    bullet(doc, "所有路径使用 pathlib，禁止字符串拼接路径。")
    bullet(doc, "网络一律 aiohttp 异步；阻塞操作放入线程执行。")
    bullet(doc, "业务异常继承 common/exceptions.py 中的 VeinError。")
    bullet(doc, "文件名与职责保持单一，新增模块前先确认架构中已有对应位置。")

    # ---------- 10 进度 ----------
    heading(doc, "10　当前进度与路线图")
    table(
        doc,
        ["模块", "状态"],
        [
            ["Common / Domain", "已完成"],
            ["Infrastructure（网络、下载、进程、存储）", "已完成"],
            ["Application（版本、启动、账号）", "已完成"],
            ["Presentation（WebView + React + 桥）", "已完成，待界面验收"],
            ["插件宿主（Node.js 双向 RPC）", "未开始，最高优先级"],
            ["模组依赖解析 / 多实例安装", "未开始"],
            ["打包分发（PyInstaller）", "未开始"],
        ],
        widths=[9.5, 5.5],
    )

    # ---------- 11 限制 ----------
    heading(doc, "11　已知限制")
    bullet(doc, "插件宿主未实现，插件功能暂不可用。")
    bullet(doc, "模组安装只下载主文件到选中实例，未解析前置依赖。")
    bullet(doc, "界面目前只有深色主题，未提供主题切换。")
    bullet(doc, "Java 探测的注册表分支仅在 Windows 生效。")
    bullet(doc, "尚未打包，需通过源码运行。")

    doc.save("VeinLauncher_开发者介绍.docx")


if __name__ == "__main__":
    main()
