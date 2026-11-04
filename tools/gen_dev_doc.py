"""生成 Vein Launcher v0.1.0 开发者文档（Word）

面向开发者/审阅者：架构、协议、模块实现、构建发布、状态与限制。
复用 gen_internal_doc.py 的排版助手（字体、表格、页眉页脚、Logo）。

用法：python tools/gen_dev_doc.py
输出：VeinLauncher_开发者文档_v0.1.0.docx（*.docx 不入库）
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gen_internal_doc as gid  # noqa: E402
from docx import Document  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK  # noqa: E402
from docx.shared import Cm, Pt, RGBColor  # noqa: E402

ROOT = gid.ROOT
OUT = ROOT / "VeinLauncher_开发者文档_v0.1.0.docx"
LOGO = gid.LOGO
STUDIO = gid.STUDIO
GREY = gid.GREY
ACCENT = gid.ACCENT

h1, h2, p, bullets, code, table = gid.h1, gid.h2, gid.p, gid.bullets, gid.code, gid.table


def cover(doc: Document) -> None:
    for _ in range(2):
        doc.add_paragraph()
    logo_para = doc.add_paragraph()
    logo_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    logo_para.add_run().add_picture(str(LOGO), width=Cm(7.6))

    doc.add_paragraph()
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("VEIN LAUNCHER")
    run.font.size = Pt(36)
    run.bold = True
    run.font.color.rgb = ACCENT

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = sub.add_run("开发者文档 · v0.1.0")
    run.font.size = Pt(17)
    run.bold = True

    doc.add_paragraph()
    studio = doc.add_paragraph()
    studio.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = studio.add_run(STUDIO)
    run.font.size = Pt(12.5)
    run.bold = True

    date_para = doc.add_paragraph()
    date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = date_para.add_run(dt.date.today().isoformat())
    run.font.size = Pt(10)
    run.font.color.rgb = GREY

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def build() -> Path:
    doc = Document()
    gid.style_document(doc)
    section = doc.sections[0]
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.0)
    gid.setup_header_footer(
        section,
        title="Vein Launcher v0.1.0 开发者文档",
        note="面向开发者",
        footer_left="Vein Launcher 开发者文档",
    )

    cover(doc)

    # ---------------- 1 文档说明 ----------------
    h1(doc, "1　文档说明")
    p(
        doc,
        "本文面向接手、审阅或二次开发 Vein Launcher 的工程师，只描述当前代码里真实存在的东西："
        "模块、协议、目录、命令，以及明确没做的部分。行文默认读者具备 Python 与前端基础，"
        "不解释语言本身。",
    )
    table(
        doc,
        ["项", "说明"],
        [
            ["对应版本", "v0.1.0（公开版），Git tag v0.1.0"],
            ["代码位置", "github.com/zhanjhn-studio/vein_launcher"],
            ["文档范围", "架构 / 协议 / 模块实现 / 构建发布 / 状态 / 限制；不含产品宣传"],
            ["阅读顺序", "第 4、5 章（架构与协议）是主干，其余章节可按需查阅"],
            ["维护方式", "以仓库 Markdown 为准；本文由 tools/gen_dev_doc.py 生成"],
        ],
        widths=[3.0, 12.8],
    )

    # ---------------- 2 竞品观察 ----------------
    h1(doc, "2　竞品观察与差异化")
    p(
        doc,
        "同一时期（10 月下旬）社区里出现了一批 Minecraft 启动器项目，多数停留在概念或早期原型。"
        "下表按公开信息整理，仅记录可核实的部分。",
        color=GREY,
    )
    table(
        doc,
        ["启动器", "日期", "已知信息"],
        [
            ["MCLR", "10-28", "Tauri / WebView 项目，作者自述「非常早期、零测试、暂不开源」"],
            ["xuyenbmc", "10-24", "启云科技出品，仅一条宣传视频，无官网 / 仓库"],
            ["MML", "10-28", "「双端 Java 版 MC 启动器」，简介为空"],
            ["Minecsay", "10-26", "号称「智能 AI 启动器，想玩的一句话搞定」"],
            ["NebulaLauncher", "10-26", "轻量化、模组管理、支持自定义皮肤站"],
            ["MinecraftLauncher.jar", "10-25", "单个 jar 分发（licm.tech），无说明"],
            ["imc-wang1 的启动器", "10-25", "网盘分发，称「可替代 PCL」"],
            ["自研核心启动器", "10-24", "宣称自研核心、全功能免费、支持下载 + 异地联机"],
            ["青梅猫猫的启动器", "10-22", "仅演示视频，无下载渠道说明"],
            ["花哨实验品", "10-25", "作者自述「做着玩玩，没啥实际用处」"],
            ["陪玩机器人启动器", "10-25", "内置陪玩机器人，信息极少"],
            ["麦块当 MinecraftLauncher", "10-25", "作者称「尚未完善，完善后发布」"],
            ["ZenithPC", "10-06 / 10-11", "两次宣布推迟发布，尚未上线"],
        ],
        widths=[4.6, 2.6, 8.6],
        font_size=8.5,
        header_size=9,
        compact=True,
    )
    h2(doc, "2.1　Vein 的差异点")
    table(
        doc,
        ["维度", "常见做法", "Vein 的做法"],
        [
            ["技术栈", "Tauri 原型 / 单 jar", "Python 五层 + PySide6 WebView + React 19 + TS"],
            ["插件系统", "基本没有", "Node 宿主 + JSON-RPC + 权限沙箱 + 热重载 + 崩溃自恢复"],
            ["游戏控制", "仅启动进程", "自研 MLC：启动 / 存档 / 事件订阅 / 种子扫描"],
            ["下载链路", "直连官方，失败即止", "BMCLAPI 优先 + 官方兜底 + 证书降级 + 断点续传 + SHA-1"],
            ["可观测性", "控制台打印", "分类日志（launcher/plugin/mlc/download/error/crash）"],
            ["交付透明度", "只有演示视频", "状态矩阵 + 方法表 + 已知限制（本文第 15/16 章）"],
            ["界面", "单窗口控件堆叠", "窄侧栏 + 三栏内容 + 下载监控 + 深色设计系统"],
        ],
        widths=[3.0, 5.4, 7.4],
    )

    # ---------------- 3 技术栈 ----------------
    h1(doc, "3　技术栈")
    table(
        doc,
        ["层", "选型", "说明"],
        [
            ["界面", "React 19 + TypeScript", "esbuild 打包为单文件 app.js，无运行时框架依赖"],
            ["控件", "Layui 2.x（仅结构）", "表单/进度/勾选等控件结构，视觉由 styles.css 覆盖"],
            ["壳", "PySide6 6.12 + QWebEngine", "无边框窗口 + 自绘标题栏 + QWebChannel 通信"],
            ["后端", "Python 3.13", "五层架构，asyncio 处理网络与下载"],
            ["网络", "aiohttp", "HTTP 客户端、并发下载、镜像重写"],
            ["数据模型", "pydantic v2", "配置与账号模型，ConfigDict 迁移完成"],
            ["插件", "Node.js 18+", "独立进程宿主，JSON-RPC over stdio"],
            ["打包", "PyInstaller onedir", "615 MB（QtWebEngine 占主要体积）"],
        ],
        widths=[2.6, 5.6, 7.6],
    )

    # ---------------- 4 分层架构 ----------------
    h1(doc, "4　分层架构")
    code(
        doc,
        "React (WebView)\n"
        "   │  QWebChannel + JSON-RPC 2.0\n"
        "   ▼\n"
        "presentation/  bridge.py · main.py · webui/\n"
        "   ▼\n"
        "application/   version / skin / instance / update / plugin / loader / modpack\n"
        "   ▼\n"
        "domain/        models · repositories（契约）· services（版本解析）\n"
        "   ▼\n"
        "infrastructure/ download · network · process · mc2 · plugin_host · storage\n"
        "   ▲\n"
        "common/        event_bus · config · logging · i18n · utils",
    )
    table(
        doc,
        ["层", "职责", "示例文件"],
        [
            ["common", "事件总线、配置、日志、i18n、路径工具", "common/events/event_bus.py"],
            ["domain", "模型与契约，不依赖框架", "domain/models/account.py"],
            ["infrastructure", "网络、下载、进程、NBT、插件宿主", "infrastructure/download/queue.py"],
            ["application", "业务编排（服务层）", "application/services/instance_service.py"],
            ["presentation", "Qt 窗口、RPC 桥、前端", "presentation/bridge.py"],
            ["mlc", "游戏控制层与插件能力入口", "vein_launcher/mlc/service.py"],
        ],
        widths=[2.8, 7.0, 6.0],
    )
    p(doc, "约束：跨层只能自上而下依赖；层间通知走 event_bus，不允许反向 import。", color=GREY)

    # ---------------- 5 前端结构 ----------------
    h1(doc, "5　前端结构")
    table(
        doc,
        ["文件", "作用"],
        [
            ["src/main.tsx", "挂载入口，初始化 bridge / i18n / theme"],
            ["src/App.tsx", "路由（hash）、侧栏、标题栏、公告、下载监控、引导"],
            ["src/pages/*.tsx", "Launch / Download / Skins / InstancePage / Settings / 其它工具页"],
            ["src/ui.tsx", "通用组件：LayuiProgress、LayuiCheckbox、RemoteIcon、LogPanel、Toast"],
            ["src/bridge.ts", "JSON-RPC 封装 + 事件订阅"],
            ["src/prefs.ts", "界面偏好（简洁模式 / 壁纸 / 空闲淡出），后端持久化"],
            ["src/theme.ts / i18n.ts", "主题与中英文切换（默认深色 / 英文）"],
            ["src/styles.css", "设计系统：token、组件、动效、无障碍"],
        ],
        widths=[5.0, 10.6],
        font_size=8.8,
    )
    h2(doc, "5.1　路由与页面")
    bullets(
        doc,
        [
            "路由：window.location.hash（#/launch、#/download…），无需 router 依赖",
            "一级导航 8 项：Launch / Skins / Download / Plugins / MLC / Multiplayer / Settings / Toolbox",
            "MLC 页同时承担「实例管理」：模组/资源包/光影/数据包/整合包启停与删除、存档与种子扫描",
            "启动页含公告区、版本卡片、快捷入口（装版本 / 管实例 / 皮肤库）",
        ],
    )
    h2(doc, "5.2　样式与动效约定")
    bullets(
        doc,
        [
            "设计 token 集中在 :root / [data-theme]，深色为默认，浅色与透明为可选项",
            "动效时长 token：--dur-fast .16s / --dur-base .24s / --dur-slow .36s",
            "侧栏选中项用滑动胶囊（transform 过渡），图标弹性缩放 + 发光",
            "支持 prefers-reduced-motion：动画降级为瞬时",
            "大面积 backdrop-filter 被移除，避免无 GPU 合成环境下的重栅格化闪烁",
        ],
    )

    # ---------------- 6 通信协议 ----------------
    h1(doc, "6　通信协议")
    p(doc, "Python ⇄ 前端走 JSON-RPC 2.0，信封由 bridge.ts 统一封装：")
    code(
        doc,
        '// 请求\n{"jsonrpc": "2.0", "id": 12, "method": "versions.install", "params": {"args": ["1.20.1"]}}\n'
        "// 回包（Python 调用 JS）\nwindow.__veinResult(12, true, { ok: 1 })\n"
        "// 推送\nwindow.__veinProgress(taskId, done, total)\n"
        "window.__veinLog(line) / __veinNotify(title, msg) / __veinNavigate(page)",
    )
    table(
        doc,
        ["能力组", "方法（示例）", "数量"],
        [
            ["应用", "app.info / app.pickDirectory / app.openUrl / i18n.set", "8"],
            ["版本", "versions.remote / info / install / delete / files / openFolder", "7"],
            ["账号", "accounts.list/add/select/remove / msStart/msLogin / littleSkin", "9"],
            ["皮肤", "skins.list/import/clear/remote/library/download", "6"],
            ["实例", "instances.contents/toggle/deleteFile/worlds/deleteWorld", "5"],
            ["下载与模组", "downloads.list / mods.search/featured/install", "4"],
            ["更新", "update.latest/download/install", "3"],
            ["插件", "plugins.state/setEnabled/reload / plugins.uiAction", "4"],
            ["MLC / 世界", "mlc.state/worlds / mc2.worlds/scan", "5"],
            ["其它", "java.*、launch、announcements、onboarding、ui.prefs 等", "9"],
        ],
        widths=[3.2, 10.4, 2.0],
        font_size=8.8,
    )
    h2(doc, "6.1　线程模型")
    bullets(
        doc,
        [
            "UI 线程：Qt 事件循环、页面交互",
            "vein-async 线程：asyncio 事件循环，所有 RPC 方法在此执行",
            "JS 执行通过 Signal 投递回 UI 线程（线程安全），页面未就绪时排队",
            "下载回调→进度推送→前端事件；失败通过 RPC 异常返回（前端 catch）",
        ],
    )

    # ---------------- 7 下载与镜像 ----------------
    h1(doc, "7　下载与镜像")
    code(
        doc,
        "客户端请求 → 镜像重写（BMCLAPI）→ 若证书异常降级为不校验会话\n"
        "          → 单文件：.part 断点续传 + 并发 8 + 去重锁\n"
        "          → 完成后 SHA-1 校验 → 失败重试（最多 3 次）\n"
        "          → 队列逐文件回调进度（done/total）→ 前端 + 侧栏监控",
    )
    table(
        doc,
        ["配置项", "默认", "说明"],
        [
            ["download.max_concurrent", "8", "并发下载数"],
            ["download.retry_count", "3", "单文件重试次数"],
            ["镜像", "BMCLAPI 优先", "节点证书链不完整时自动降级并记忆"],
            ["进度粒度", "每文件", "VersionService 转发「下载」阶段 done/total"],
            ["失败语义", "抛 DownloadError", "附带失败文件数与样例，前端红字提示"],
        ],
        widths=[4.2, 3.0, 8.4],
    )

    # ---------------- 8 插件系统 ----------------
    h1(doc, "8　插件系统")
    bullets(
        doc,
        [
            "宿主：独立 Node 进程（node host.js），stdio 上跑 JSON-RPC",
            "能力：宿主注册 capability，调用前校验权限；默认超时 30s，超时抛 CapabilityTimeoutError",
            "自恢复：宿主意外退出自动重启（最多 3 次，指数退避），重启后恢复已加载插件",
            "UI：插件可声明 UI 节点，经白名单清洗后在 closed Shadow DOM 中渲染",
            "热重载：plugins.reload；启停：plugins.setEnabled；权限弹窗由前端确认",
            "新增能力 ui.openPage(page)：插件可请求前端切换页面",
        ],
    )
    table(
        doc,
        ["权限", "说明"],
        [
            ["fs.read / fs.write", "限定在数据目录内的读写"],
            ["net.request", "发起 HTTP 请求"],
            ["game.launch", "启动游戏实例"],
            ["game.event", "订阅游戏事件"],
            ["ui.render", "渲染插件 UI"],
            ["ui.notify", "弹通知"],
            ["ui.openPage", "切换前端页面"],
        ],
        widths=[4.0, 11.6],
    )

    # ---------------- 9 实例管理 ----------------
    h1(doc, "9　MLC 与实例管理")
    table(
        doc,
        ["能力", "实现", "状态"],
        [
            ["启动游戏", "launch → LauncherService.build_command", "可用"],
            ["模组 / 资源包 / 光影 / 数据包 / 整合包", "InstanceService（.disabled 表示禁用）", "可用"],
            ["删除文件 / 删除实例", "InstanceService.delete / versions.delete", "可用"],
            ["存档列表", "解析 saves/*/level.dat", "可用"],
            ["种子与基础信息", "MC2 解析 RandomSeed / WorldGenSettings.seed", "可用"],
            ["群系 / 结构可视化", "region 扫描已有基础，UI 未做成表格", "部分"],
        ],
        widths=[5.0, 7.6, 3.0],
        font_size=8.8,
    )

    # ---------------- 10 账号与皮肤 ----------------
    h1(doc, "10　账号与皮肤")
    table(
        doc,
        ["账号类型", "认证方式", "状态"],
        [
            ["离线", "本地用户名 + 离线 UUID", "可用"],
            ["Microsoft", "设备码 → XBL → XSTS → login_with_xbox", "链路完成，服务端 403（见第 16 章）"],
            ["LittleSkin", "Yggdrasil authenticate / refresh", "可用"],
        ],
        widths=[3.2, 7.4, 5.0],
    )
    bullets(
        doc,
        [
            "令牌按账号隔离存放，MC 会话 token 过期前 10 分钟用 refresh_token 自动续期",
            "LittleSkin 启动时注入 authlib-injector（-javaagent），皮肤与在线验证依赖它",
            "皮肤：导入 PNG（64×64 / 64×32 校验）、读角色当前皮肤、公开库下载",
            "公开库接口：GET /skinlib/list → /texture/{tid} 取 hash → /textures/{hash} 取 PNG",
        ],
    )

    # ---------------- 11 更新与发布 ----------------
    h1(doc, "11　更新与发布")
    code(
        doc,
        "检查：GitHub API /releases/latest\n"
        "      → 403/限流：latest.json（发布资产，不占 API 配额）\n"
        "      → 再失败：公告站 public.js 的 update 字段\n"
        "下载：.part 断点续传 → downloads/update/\n"
        "安装：exe/msi 直接启动；zip 解压到 extracted-<ts>/",
    )
    bullets(
        doc,
        [
            "发布资产必须同时上传 zip 与 latest.json，否则回退链退化",
            "打包命令见第 14 章；PyInstaller 产物为 onedir，资源从 _MEIPASS 读取",
            "发布需要项目负责人明确指令，日常只提提交/PR",
        ],
    )

    # ---------------- 12 日志 ----------------
    h1(doc, "12　日志系统")
    table(
        doc,
        ["文件", "内容"],
        [
            ["launcher-YYYY-MM-DD.log", "启动、服务装配、RPC、页面加载"],
            ["plugin-*.log", "插件宿主生命周期与能力调用"],
            ["mlc-*.log", "游戏控制与事件"],
            ["download-*.log", "下载错误与统计"],
            ["error.log", "ERROR 级别汇总"],
            ["crash.log", "未捕获异常 / 崩溃"],
        ],
        widths=[6.0, 9.6],
    )
    p(doc, "约定：只写文件，不写控制台；按天切分；前端日志面板仅展示推送的日志行。", color=GREY)

    # ---------------- 13 数据目录 ----------------
    h1(doc, "13　数据目录")
    code(
        doc,
        "VeinLauncher/\n"
        "├── config/      config.json、accounts.json、skins.json、language.json、wallpapers/\n"
        "├── log/         分类日志\n"
        "├── minecraft/   instances/、versions/、libraries/、assets/\n"
        "├── downloads/   缓存与 update/\n"
        "├── plugin/      Node 插件\n"
        "├── java/        自动下载的运行时\n"
        "├── skins/       皮肤 PNG（按账号 id）\n"
        "└── democrat/    社区数据（预留）",
    )

    # ---------------- 14 运行与构建 ----------------
    h1(doc, "14　运行与构建")
    code(
        doc,
        "# 运行（开发态）\n"
        "python -m vein_launcher.presentation.main\n\n"
        "# 前端构建\n"
        "cd vein_launcher/presentation/webui\n"
        "powershell -ExecutionPolicy Bypass -File build.ps1\n\n"
        "# 测试\n"
        "python -m unittest discover -s tests      # 44 项\n\n"
        "# 打包\n"
        "python -m PyInstaller --noconfirm --clean --windowed --name VeinLauncher ^\n"
        "  --icon assets/logo.ico --distpath packaging/dist --workpath packaging/build ^\n"
        "  --specpath packaging ^\n"
        "  --add-data \"vein_launcher/presentation/webui/dist;webui/dist\" ^\n"
        "  --add-data \"assets;assets\" packaging/entry.py",
    )

    # ---------------- 15 当前状态 ----------------
    h1(doc, "15　当前状态")
    table(
        doc,
        ["模块", "完成度", "备注"],
        [
            ["启动 / 实例管理", "可用", "含模组启停、删除、存档种子"],
            ["下载 / 安装", "可用", "逐文件进度、失败可见、断点续传"],
            ["加载器", "可用", "Fabric / Forge / Quilt / NeoForge"],
            ["模组搜索安装", "可用", "Modrinth，按版本与加载器过滤"],
            ["皮肤", "可用", "导入、读站内皮肤、公开库下载"],
            ["账号", "部分", "微软被服务端 403 阻塞"],
            ["插件系统", "可用", "权限、超时、自恢复、自检 9/9"],
            ["自动更新", "可用", "三级回退，zip 为解压安装"],
            ["国际化", "部分", "中英文覆盖主导航与设置"],
            ["世界分析", "部分", "种子/版本可用，群系结构未表格化"],
        ],
        widths=[4.4, 2.4, 8.8],
    )

    # ---------------- 16 已知限制 ----------------
    h1(doc, "16　已知限制")
    table(
        doc,
        ["#", "限制", "影响 / 计划"],
        [
            ["1", "微软登录 login_with_xbox 返回 403 Invalid app registration", "等待白名单；离线与 LittleSkin 不受影响"],
            ["2", "公告站 public.js 版本仍为旧值", "应用内横幅版本落后，需更新 Pages 仓库"],
            ["3", "世界分析直接展示 MC2 原始 JSON", "待做群系 / 结构表格"],
            ["4", "中文翻译未覆盖页面正文", "只覆盖主导航、设置、实例页标签"],
            ["5", "zip 更新为解压而非原地替换", "计划加入 updater 脚本"],
            ["6", "安装包未签名", "SmartScreen 可能提示"],
            ["7", "包体 615 MB", "QtWebEngine 占主要体积，可考虑拆分/增量"],
            ["8", "插件宿主依赖本机 Node 18+", "未内嵌 Node 运行时"],
        ],
        widths=[0.9, 8.6, 6.1],
        font_size=8.8,
    )

    # ---------------- 附录 A ----------------
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    h1(doc, "附录 A　帖子系统（API 预留）")
    p(doc, "仅有契约与模型，服务端、鉴权、内容审核、分页缓存与 UI 均未实现。", color=GREY)
    table(
        doc,
        ["方法", "路径", "说明"],
        [
            ["GET", "/api/posts?tag=&sort=hot|new&page=", "列表，标签过滤 + 热度/时间排序"],
            ["GET", "/api/posts/{id}", "详情"],
            ["POST", "/api/posts", "发帖：title / content / tags"],
            ["POST", "/api/posts/{id}/like", "点赞（幂等）"],
            ["GET", "/api/tags", "标签列表"],
        ],
        widths=[1.8, 7.0, 6.8],
    )
    code(
        doc,
        "Post { id, title, content, author_id, tags[], likes, created_at, hot_score }\n"
        "hot_score = likes / pow(hours_since_created + 2, 1.5)",
    )

    # ---------------- 附录 B：3 页团队记录 ----------------
    for page in range(3):
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        if page == 0:
            h1(doc, "附录 B　团队记录（预留 3 页）")
            p(doc, "供项目组记录会议结论、待办与交接。", color=GREY)
        else:
            # 空白页需要一个可见元素，否则 Word 不会为末尾分页符生成页面
            p(doc, " ", space_after=0)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    return OUT


if __name__ == "__main__":
    path = build()
    print(f"saved: {path} ({path.stat().st_size} bytes)")
