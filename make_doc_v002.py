"""生成 Vein Launcher 开发者文档 v0.0.2（Word）"""

from __future__ import annotations

from datetime import date

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

DOC_VERSION = "0.0.2"
BODY_FONT = "微软雅黑"
CODE_FONT = "Consolas"
ACCENT = RGBColor(0x1F, 0x4E, 0x79)


def set_font(run, name=BODY_FONT, size=None, bold=None, color=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color is not None:
        run.font.color.rgb = color


def body(doc, text, size=10.5, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    set_font(p.add_run(text), size=size)
    return p


def bullet(doc, text):
    p = doc.add_paragraph(style="List Bullet")
    set_font(p.add_run(text), size=10.5)
    return p


def code(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.6)
    p.paragraph_format.space_after = Pt(2)
    set_font(p.add_run(text), name=CODE_FONT, size=9, color=RGBColor(0x33, 0x33, 0x33))
    return p


def heading(doc, text, level=1):
    h = doc.add_heading(level=level)
    set_font(h.add_run(text), size={1: 16, 2: 12.5, 3: 11}[level], bold=True, color=ACCENT)
    return h


def table(doc, headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, text in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        set_font(cell.paragraphs[0].add_run(text), size=9.5, bold=True)
    for row in rows:
        cells = t.add_row().cells
        for i, text in enumerate(row):
            cells[i].text = ""
            set_font(cells[i].paragraphs[0].add_run(str(text)), size=9)
    if widths:
        for row in t.rows:
            for i, width in enumerate(widths):
                row.cells[i].width = Cm(width)
    doc.add_paragraph()
    return t


def main() -> None:
    doc = Document()
    section = doc.sections[0]
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)
    section.top_margin = Cm(2.3)
    section.bottom_margin = Cm(2.1)

    # 封面
    for _ in range(5):
        doc.add_paragraph()
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(title.add_run("Vein Launcher"), size=34, bold=True, color=ACCENT)
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(subtitle.add_run("Minecraft Java 启动器 · 开发者文档"), size=14, color=RGBColor(0x55, 0x55, 0x55))
    doc.add_paragraph()
    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(meta.add_run(f"文档版本 v{DOC_VERSION}　|　{date.today().isoformat()}　|　内部资料"), size=10, color=RGBColor(0x77, 0x77, 0x77))
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # 1
    heading(doc, "1　文档说明")
    body(doc, f"本文档面向 Vein Launcher 的开发者，描述 v{DOC_VERSION} 阶段的架构、接口、约定与现状。")
    body(doc, "文档只记录已经落地的实现与明确的规划边界；未实现的能力会标注「规划」或「未做」，不夸大完成度。")

    # 2
    heading(doc, "2　技术栈")
    table(doc, ["领域", "选型", "说明"], [
        ["语言", "Python 3.13", "后端与系统集成"],
        ["桌面容器", "PySide6 6.12 + QWebEngine", "WebView 承载前端，QWebChannel 通信"],
        ["前端", "React 19 + TypeScript", "esbuild 打包，无框架依赖"],
        ["网络", "aiohttp", "异步 HTTP，重试与证书降级"],
        ["数据模型", "Pydantic v2", "配置与领域模型"],
        ["插件宿主", "Node.js 22", "独立进程，JSON-RPC 双向通信"],
        ["打包", "PyInstaller", "规划中"],
    ], widths=[3.2, 5.0, 7.2])

    # 3
    heading(doc, "3　分层架构")
    body(doc, "依赖方向自上而下：Presentation → Application → Domain ← Infrastructure；跨层通信只走 event_bus。")
    table(doc, ["层", "职责", "示例"], [
        ["Common", "事件总线、配置、日志、i18n、路径工具、异常", "event_bus、settings、logger"],
        ["Domain", "版本/账号/加载器/模组/插件模型与仓储接口", "models、version_resolver"],
        ["Infrastructure", "HTTP、下载、Java 进程、存储、插件宿主", "http_client、downloader、plugin_host"],
        ["Application", "版本安装、启动编排、账号、插件服务", "version_service、launcher_service"],
        ["Presentation", "WebView 窗口、JSON-RPC 桥、React 界面", "main.py、bridge.py、webui/"],
    ], widths=[3.0, 9.2, 4.2])

    # 4
    heading(doc, "4　前端结构（v0.0.2）")
    for line in [
        "webui/src/",
        "├── main.tsx       入口：初始化桥并挂载 App",
        "├── App.tsx        外壳：7 项一级导航",
        "├── pages.tsx      页面：启动/下载/插件/MLC/联机/设置/工具箱",
        "├── ui.tsx         三栏布局、下载栏、权限弹窗、状态点",
        "├── bridge.ts      JSON-RPC 客户端与事件分发",
        "├── types.ts       接口与数据结构",
        "└── styles.css     浅色设计系统",
    ]:
        code(doc, line)
    body(doc, "一级导航：启动 / 下载 / 插件（核心）/ MLC / 联机（敬请期待）/ 设置 / 工具箱。")
    body(doc, "布局范式：下载、插件、设置采用「左侧分类 + 中间列表 + 右侧详情」三栏。")

    # 5
    heading(doc, "5　通信协议（JSON-RPC 2.0）")
    code(doc, 'JS  →  Python：bridge.call(id, \'{"jsonrpc":"2.0","id":n,"method":"...","params":{"args":[...]}}\')')
    code(doc, "Python →  JS：window.__veinResult(id, ok, payload)")
    code(doc, "推送通道：__veinProgress / __veinLog / __veinNotify / __veinNavigate")
    body(doc, "线程约束：Python 侧所有 JS 调用通过 Signal 回到 UI 线程，页面加载完成前的脚本入队，加载后统一冲刷。")
    table(doc, ["方法", "参数", "返回"], [
        ["versions.info / remote", "limit", "版本数组"],
        ["versions.install", "versionId, loader?", "安装统计或加载器结果"],
        ["versions.delete", "versionId", "{deleted}"],
        ["launch", "versionId, username", "{pid}"],
        ["accounts.list / add / select", "username / accountId", "账号列表或结果"],
        ["mods.search / featured / install", "query, type, mc, loader", "资源列表或安装结果"],
        ["plugins.state / setEnabled / reload / logs", "name, enabled", "宿主状态与插件信息"],
        ["downloads.list", "—", "全局下载任务"],
        ["mlc.state / mlc.worlds", "versionId", "连接状态与存档"],
        ["java.detect / app.info / app.openDataDir", "—", "环境信息"],
    ], widths=[5.6, 5.4, 5.4])

    # 6
    heading(doc, "6　下载与镜像")
    body(doc, "默认镜像优先：Mojang 地址改写为 BMCLAPI；镜像失败自动回退官方源。")
    table(doc, ["官方", "镜像"], [
        ["piston-meta / launchermeta", "bmclapi2.bangbang93.com"],
        ["libraries.minecraft.net", "bmclapi2.bangbang93.com/maven"],
        ["resources.download.minecraft.net", "bmclapi2.bangbang93.com/assets"],
    ], widths=[7.5, 9.0])
    bullet(doc, "证书：镜像节点证书链不完整时降级为不校验会话，文件仍按官方 SHA-1 校验。")
    bullet(doc, "资产索引：对象键可能是路径名，必须以 objects[*].hash 拼 URL（v0.0.1 的 404 根因）。")
    bullet(doc, "并发：同一目标串行下载、队列按 dest 去重、安装流程串行执行。")
    bullet(doc, "断点续传：.part + Range，SHA-1 不匹配自动重下。")

    # 7
    heading(doc, "7　插件系统（核心特性）")
    body(doc, "Node.js 独立进程 + JSON-RPC + 权限沙箱；插件以 NPM 包结构分发。")
    code(doc, "plugins/<name>/package.json   vein.permissions 声明能力")
    code(doc, "plugins/<name>/index.js      export async function activate(vein)")
    table(doc, ["权限", "能力"], [
        ["file.read / file.write", "仅限插件自身目录"],
        ["download.queue", "加入下载队列"],
        ["game.launch", "启动游戏"],
        ["ui.notify", "通知前端"],
        ["config.read / config.write", "读写启动器配置"],
        ["network.http", "经宿主发起 HTTP"],
        ["mlc.world / mlc.player / mlc.mod", "MLC 能力"],
    ], widths=[6.5, 10.0])
    body(doc, "管理能力：启用/禁用、热重载、权限确认弹窗、宿主日志、示例插件（template / game-log）。")

    # 8
    heading(doc, "8　MLC 控制层")
    table(doc, ["接口", "说明", "状态"], [
        ["mlc.launch", "启动游戏并返回 PID", "可用"],
        ["mlc.world.info", "读取存档列表", "可用"],
        ["mlc.world.create", "创建存档目录", "可用"],
        ["mlc.event.subscribe", "订阅 game.log / game.exit / download.progress", "可用"],
        ["mlc.player.info", "玩家坐标等", "需游戏侧 mod"],
        ["mlc.mod.load", "运行时加载模组", "需游戏侧 mod"],
    ], widths=[4.5, 9.0, 3.0])
    body(doc, "UI 提供连接状态指示器：由 GAME_RUNNING / GAME_EXITED 事件驱动，实时显示 PID。")

    # 9
    heading(doc, "9　日志系统")
    table(doc, ["文件", "内容"], [
        ["logs/YYYY-MM-DD.log", "按天记录 INFO 及以上"],
        ["logs/error.log", "仅 ERROR"],
        ["logs/crash.log", "faulthandler 线程栈"],
    ], widths=[6.0, 10.5])
    bullet(doc, "程序内：下载页「安装活动」显示进度；插件页显示宿主日志。")
    bullet(doc, "采集：Python 日志、Qt 消息、前端 console、未捕获异常、主线程心跳（>3s 告警）。")

    # 10
    heading(doc, "10　数据目录")
    for line in [
        "%APPDATA%\\VeinLauncher\\",
        "├── config.json",
        "├── instances\\<id>\\        版本 JSON / client jar / mods / saves",
        "├── libraries\\             多实例共享",
        "├── assets\\indexes|objects 资源索引与对象",
        "├── plugins\\<name>\\        插件与 data/",
        "└── logs\\",
    ]:
        code(doc, line)

    # 11
    heading(doc, "11　运行与构建")
    code(doc, "python -m vein_launcher.presentation.main")
    code(doc, "esbuild src/main.tsx --bundle --outfile=dist/app.js --jsx=automatic --minify")
    body(doc, "前端产物 dist/ 已随仓库提交；修改 React 源码后需要重新构建。")

    # 12
    heading(doc, "12　当前状态")
    table(doc, ["模块", "状态"], [
        ["版本安装（原版）", "可用，实测 1.20.1 完整（3598 资产 / 64 库）"],
        ["Fabric / Quilt", "可用"],
        ["Forge / NeoForge", "已实现安装器路径，待实机验证"],
        ["Modrinth 推荐与搜索", "可用，含缩略图"],
        ["插件系统", "可用，含热重载与权限弹窗"],
        ["MLC", "启动/存档/事件可用；玩家数据待游戏侧 mod"],
        ["微软登录", "未实现"],
        ["CurseForge", "客户端就绪，界面未接入"],
        ["广场 / 联机", "仅占位"],
        ["打包", "未开始"],
    ], widths=[6.5, 10.5])

    # 13
    heading(doc, "13　已知限制")
    bullet(doc, "安装中断会留下半成品实例，下次安装覆盖。")
    bullet(doc, "日志未实现 30 天自动清理。")
    bullet(doc, "镜像 SSL 不校验仅限镜像域，依赖 SHA-1 保证内容。")
    bullet(doc, "Forge 安装器依赖本机 Java 与网络，失败会回滚临时目录。")
    bullet(doc, "联机与广场未开发，仅保留导航占位。")

    doc.save("VeinLauncher_开发者文档_v0.0.2.docx")


if __name__ == "__main__":
    main()
