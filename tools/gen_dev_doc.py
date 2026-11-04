"""生成 Vein Launcher v0.1.0 开发者文档（精简版 Word）

内容原则：只留开发者真正需要的表与命令，章节合并、表格紧凑，控制在 8 页左右
（含附录 A 与 3 页团队记录）。排版助手复用 gen_internal_doc.py。

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
    logo_para.add_run().add_picture(str(LOGO), width=Cm(7.4))

    doc.add_paragraph()
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("VEIN LAUNCHER")
    run.font.size = Pt(34)
    run.bold = True
    run.font.color.rgb = ACCENT

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = sub.add_run("开发者文档 · v0.1.0")
    run.font.size = Pt(16)
    run.bold = True

    doc.add_paragraph()
    studio = doc.add_paragraph()
    studio.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = studio.add_run(STUDIO)
    run.font.size = Pt(12)
    run.bold = True

    date_para = doc.add_paragraph()
    date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = date_para.add_run(dt.date.today().isoformat())
    run.font.size = Pt(9.5)
    run.font.color.rgb = GREY

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def build() -> Path:
    doc = Document()
    gid.style_document(doc)
    section = doc.sections[0]
    section.top_margin = Cm(1.7)
    section.bottom_margin = Cm(1.5)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(1.8)
    gid.setup_header_footer(
        section,
        title="Vein Launcher v0.1.0 开发者文档",
        note="面向开发者",
        footer_left="Vein Launcher 开发者文档",
    )

    cover(doc)

    # ---------------- 1 说明 ----------------
    h1(doc, "1　说明")
    p(
        doc,
        "面向接手与二次开发 Vein Launcher 的工程师，只写代码里真实存在的东西。"
        "对应 v0.1.0（tag v0.1.0），仓库 github.com/zhanjhn-studio/vein_launcher；"
        "本文由 tools/gen_dev_doc.py 生成，内容以仓库 Markdown 为准。",
        color=GREY,
    )

    # ---------------- 2 竞品 ----------------
    h1(doc, "2　竞品与差异化")
    table(
        doc,
        ["启动器", "日期", "已知信息"],
        [
            ["MCLR", "10-28", "Tauri/WebView，早期、零测试、暂不开源"],
            ["xuyenbmc", "10-24", "仅宣传视频，无官网/仓库"],
            ["MML", "10-28", "「双端 Java 版 MC 启动器」，简介为空"],
            ["Minecsay", "10-26", "一句话 AI 概念"],
            ["NebulaLauncher", "10-26", "轻量化、模组管理、自定义皮肤站"],
            ["MinecraftLauncher.jar", "10-25", "单 jar 分发，无说明"],
            ["imc-wang1 的启动器", "10-25", "网盘分发，称「可替代 PCL」"],
            ["自研核心启动器", "10-24", "宣称自研核心、全功能免费"],
            ["青梅猫猫的启动器", "10-22", "仅演示视频"],
            ["花哨实验品", "10-25", "作者自述「做着玩玩」"],
            ["陪玩机器人启动器", "10-25", "内置陪玩机器人，信息极少"],
            ["麦块当 MinecraftLauncher", "10-25", "称「尚未完善」"],
            ["ZenithPC", "10-06/10-11", "两次推迟，尚未上线"],
        ],
        widths=[4.4, 2.8, 7.6],
        font_size=8.0,
        header_size=8.2,
        compact=True,
    )
    table(
        doc,
        ["维度", "常见做法", "Vein"],
        [
            ["技术栈", "Tauri 原型 / 单 jar", "Python 五层 + PySide6 WebView + React 19 + TS"],
            ["插件", "基本没有", "Node 宿主 + 权限沙箱 + 热重载 + 崩溃自恢复"],
            ["游戏控制", "仅启动进程", "MLC：启动 / 存档 / 事件 / 种子扫描"],
            ["下载", "直连官方，失败即止", "镜像优先 + 官方兜底 + 断点续传 + SHA-1"],
            ["观测", "控制台打印", "分类日志 + error + crash"],
            ["交付", "演示视频", "状态矩阵 + 已知限制（第 8 章）"],
        ],
        widths=[3.0, 5.2, 7.4],
        font_size=8.5,
        header_size=8.6,
        compact=True,
    )

    # ---------------- 3 架构与技术栈 ----------------
    h1(doc, "3　架构与技术栈")
    code(
        doc,
        "React (WebView) ──QWebChannel/JSON-RPC──▶ presentation(bridge,webui)\n"
        "   application(version/skin/instance/update/plugin)  ▶ domain(models,contracts)\n"
        "   ▶ infrastructure(download/network/process/mc2/plugin_host)\n"
        "   common(event_bus/config/logging/i18n/utils)   ·   mlc(游戏控制)",
    )
    table(
        doc,
        ["层 / 项", "选型或职责", "关键文件"],
        [
            ["壳", "PySide6 6.12 WebEngine，无边框窗口", "presentation/main.py"],
            ["界面", "React 19 + TS，esbuild 单文件打包", "webui/src"],
            ["控件", "Layui 仅结构，样式由 styles.css 覆盖", "webui/styles.css"],
            ["后端", "Python 3.13 / asyncio / aiohttp / pydantic v2", "application/*"],
            ["插件", "Node 18+ 独立进程，stdio JSON-RPC", "infrastructure/plugin_host"],
            ["打包", "PyInstaller onedir，615 MB", "packaging/entry.py"],
        ],
        widths=[2.8, 8.0, 5.0],
        font_size=8.5,
        header_size=8.6,
        compact=True,
    )

    # ---------------- 4 前端与协议 ----------------
    h1(doc, "4　前端与协议")
    table(
        doc,
        ["文件", "作用"],
        [
            ["App.tsx", "hash 路由、侧栏、公告、下载监控、引导"],
            ["pages/*.tsx", "Launch / Download / Skins / Instance / Settings 等"],
            ["ui.tsx", "LayuiProgress / LayuiCheckbox / RemoteIcon / LogPanel"],
            ["bridge.ts", "JSON-RPC 封装 + 事件订阅"],
            ["prefs.ts / theme.ts / i18n.ts", "界面偏好、主题（默认深色）、中英文"],
            ["styles.css", "设计 token、组件、动效、无障碍"],
        ],
        widths=[4.8, 10.6],
        font_size=8.5,
        header_size=8.6,
        compact=True,
    )
    p(doc, "一级导航 8 项：Launch / Skins / Download / Plugins / MLC / Multiplayer / Settings / Toolbox。")
    code(
        doc,
        '{"jsonrpc":"2.0","id":12,"method":"versions.install","params":{"args":["1.20.1"]}}\n'
        "window.__veinResult(12, true, {ok:1})\n"
        "window.__veinProgress(taskId, done, total) / __veinLog / __veinNotify / __veinNavigate",
    )
    table(
        doc,
        ["组", "示例方法", "数"],
        [
            ["应用/日志", "app.info, app.pickDirectory, i18n.set", "8"],
            ["版本/下载", "versions.remote/install/delete, downloads.list", "11"],
            ["账号/皮肤", "accounts.list/add/msStart/msLogin/littleSkin, skins.*", "15"],
            ["实例/世界", "instances.contents/toggle/deleteFile/worlds, mc2.scan", "10"],
            ["模组/插件", "mods.search/featured/install, plugins.state/reload", "8"],
            ["更新/其它", "update.latest/download/install, launch, java.*", "8"],
        ],
        widths=[3.4, 10.4, 1.6],
        font_size=8.5,
        header_size=8.6,
        compact=True,
    )
    p(doc, "线程：RPC 在 vein-async 事件循环执行，JS 通过 Signal 回 UI 线程；下载进度走推送通道。", color=GREY)

    # ---------------- 5 下载 / 插件 / 实例 ----------------
    h1(doc, "5　下载 · 插件 · 实例")
    code(
        doc,
        "下载：BMCLAPI 重写 → 证书异常降级 → .part 续传 + 并发 8 + 去重锁 → SHA-1 → 逐文件进度",
        size=8.5,
    )
    table(
        doc,
        ["主题", "要点"],
        [
            ["下载配置", "max_concurrent=8，retry=3；失败抛 DownloadError（带样例），前端红字提示"],
            ["插件能力", "宿主注册 + 权限校验；默认 30s 超时；崩溃自动重启 ≤3 次并恢复插件"],
            ["插件新增", "ui.openPage(page)，Node 侧 vein.ui.openPage()"],
            ["实例内容", "mods / resourcepacks / shaderpacks / datapacks / modpacks；.disabled = 禁用"],
            ["实例操作", "启用/禁用改名、删除文件、删除实例、存档列表、种子解析（MC2）"],
        ],
        widths=[3.2, 12.2],
        font_size=8.5,
        header_size=8.6,
        compact=True,
    )

    # ---------------- 6 账号 · 皮肤 · 更新 ----------------
    h1(doc, "6　账号 · 皮肤 · 更新")
    table(
        doc,
        ["类型", "认证", "状态"],
        [
            ["离线", "用户名 + 离线 UUID", "可用"],
            ["Microsoft", "设备码 → XBL → XSTS → login_with_xbox", "链路完成，服务端 403"],
            ["LittleSkin", "Yggdrasil authenticate / refresh", "可用"],
        ],
        widths=[3.0, 8.2, 4.2],
        font_size=8.5,
        header_size=8.6,
        compact=True,
    )
    bullets(
        doc,
        [
            "令牌按账号隔离；MC token 过期前 10 分钟用 refresh_token 续期；LittleSkin 启动注入 authlib-injector",
            "皮肤：导入 PNG（64×64/64×32）、读角色当前皮肤、公开库 /skinlib/list → /texture/{tid} → /textures/{hash}",
            "更新：GitHub API → latest.json → 公告 update 字段；zip 解压安装，exe/msi 直接启动",
        ],
    )

    # ---------------- 7 日志与目录 ----------------
    h1(doc, "7　日志与数据目录")
    table(
        doc,
        ["文件", "内容"],
        [
            ["launcher-*.log", "启动、装配、RPC、页面加载"],
            ["plugin-*.log / mlc-*.log", "插件宿主 / 游戏控制"],
            ["download-*.log", "下载错误与统计"],
            ["error.log / crash.log", "ERROR 汇总 / 未捕获异常"],
        ],
        widths=[5.0, 10.4],
        font_size=8.5,
        header_size=8.6,
        compact=True,
    )
    code(
        doc,
        "VeinLauncher/  config/ log/ minecraft/{instances,versions,libraries,assets}\n"
        "              downloads/ plugin/ java/ skins/ democrat/",
        size=8.5,
    )

    # ---------------- 8 构建与状态 ----------------
    h1(doc, "8　构建、状态与限制")
    code(
        doc,
        "python -m vein_launcher.presentation.main            # 开发运行\n"
        "cd vein_launcher/presentation/webui && powershell -File build.ps1   # 前端\n"
        "python -m unittest discover -s tests                 # 44 项\n"
        "python -m PyInstaller --windowed --name VeinLauncher --add-data \"...;webui/dist\" packaging/entry.py",
        size=8.0,
    )
    table(
        doc,
        ["模块", "状态", "说明"],
        [
            ["启动 / 实例 / 下载 / 加载器", "可用", "逐文件进度、断点续传、启停与删除"],
            ["模组 / 皮肤", "可用", "Modrinth；导入 / 站内 / 公开库"],
            ["插件 / 自动更新", "可用", "权限、超时、自恢复；三级回退"],
            ["账号", "部分", "微软被服务端 403 阻塞"],
            ["国际化 / 世界分析", "部分", "中英文覆盖主导航；群系结构未表格化"],
        ],
        widths=[5.4, 1.8, 8.4],
        font_size=8.2,
        header_size=8.4,
        compact=True,
    )
    table(
        doc,
        ["#", "限制", "影响 / 计划"],
        [
            ["1", "微软 login_with_xbox 403 Invalid app registration", "等白名单；离线/LittleSkin 不受影响"],
            ["2", "public.js 版本仍为旧值", "应用内横幅落后，需更新 Pages"],
            ["3", "世界分析展示原始 JSON", "待做群系/结构表格"],
            ["4", "中文未覆盖页面正文", "仅主导航/设置/实例标签"],
            ["5", "zip 更新为解压非原地替换", "计划 updater 脚本"],
            ["6", "包体 615 MB / 未签名", "QtWebEngine 占主要体积"],
            ["7", "插件依赖本机 Node 18+", "未内嵌运行时"],
        ],
        widths=[0.8, 8.8, 6.8],
        font_size=8.2,
        header_size=8.4,
        compact=True,
    )

    # ---------------- 9 开发约定 ----------------
    h1(doc, "9　开发约定与常见任务")
    table(
        doc,
        ["要做什么", "改哪里（按顺序）"],
        [
            ["新增一个 RPC 方法", "① bridge.py 的 _handlers 注册 ② 写 async 方法 ③ 需要进度就调 self._progress ④ 前端 rpc<T>('x.y', [args])"],
            ["新增一个页面", "① App.tsx 的 NAV 加项 ② 加 page 分支渲染 ③ 组件放 pages/ ④ 需要深链用 hash #/key"],
            ["新增一个插件能力", "① capabilities.py 注册 + 权限名 ② host.js 暴露 vein.* ③ 更新示例插件与权限弹窗文案"],
            ["改 UI 样式", "只动 styles.css 的 token/组件段；先跑 tools/ui_preview.py 看效果，再重启验证"],
            ["改版本相关逻辑", "version_service 只做编排；下载细节在 download/，网络在 network/"],
        ],
        widths=[4.2, 11.2],
        font_size=8.2,
        header_size=8.4,
        compact=True,
    )
    p(
        doc,
        "提交前：python -m unittest discover -s tests（44 项）→ build.ps1 构建前端 → "
        "在 teamwork.md 追加一条记录 → 与代码一起提交。跨层依赖一律自上而下，层间用 event_bus。",
        size=9,
        color=GREY,
    )
    table(
        doc,
        ["现象", "先查什么"],
        [
            ["窗口白屏 / 前端未构建", "dist/index.html 是否存在；先跑 build.ps1"],
            ["下载全部失败", "镜像是否可达；日志里是 HTTP 还是证书错误（会自动降级）"],
            ["插件不加载", "node -v ≥ 18；plugin/*/package.json 是否合法；plugin 日志"],
            ["界面卡住", "launcher 日志里的 JS 错误；rpc 是否 resolve（bridge.call）"],
            ["更新检查失败", "GitHub API 403 → 看 latest.json 是否可下载；公告站是否可访问"],
        ],
        widths=[5.0, 10.4],
        font_size=8.2,
        header_size=8.4,
        compact=True,
    )

    # ---------------- 附录 A ----------------
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    h1(doc, "附录 A　帖子系统（API 预留）")
    p(doc, "仅有契约与模型；服务端、鉴权、审核、分页缓存与 UI 均未实现。", color=GREY)
    table(
        doc,
        ["方法", "路径", "说明"],
        [
            ["GET", "/api/posts?tag=&sort=hot|new&page=", "列表：标签过滤 + 热度/时间"],
            ["GET", "/api/posts/{id}", "详情"],
            ["POST", "/api/posts", "发帖：title / content / tags"],
            ["POST", "/api/posts/{id}/like", "点赞（幂等）"],
            ["GET", "/api/tags", "标签列表"],
        ],
        widths=[1.8, 7.2, 6.4],
        font_size=8.5,
        header_size=8.6,
        compact=True,
    )
    code(
        doc,
        "Post { id, title, content, author_id, tags[], likes, created_at, hot_score }\n"
        "hot_score = likes / pow(hours_since_created + 2, 1.5)",
        size=8.5,
    )
    h2(doc, "A.1　落地建议（按顺序做）")
    table(
        doc,
        ["阶段", "要做的事", "验收"],
        [
            ["1 存储", "SQLite 建 posts / tags / post_tags / likes 四表", "本地 CRUD 单测通过"],
            ["2 接口", "按上表实现 5 个端点，分页默认 20 条", "curl 全部 200"],
            ["3 鉴权", "复用账号体系签 JWT，发帖/点赞要求登录", "未登录 401"],
            ["4 内容", "标题长度、标签白名单、敏感词过滤", "越界输入被拒"],
            ["5 前端", "广场页：列表 + 详情 + 发帖弹窗", "与设计稿一致"],
            ["6 缓存", "热点列表 30s 进程内缓存，点赞后失效", "压测 QPS 达标"],
        ],
        widths=[2.2, 9.6, 3.6],
        font_size=8.2,
        header_size=8.4,
        compact=True,
    )
    bullets(
        doc,
        [
            "热度排序可直接用 SQL 计算，不必存 hot_score 字段；数据量上来后再做离线重算",
            "点赞用 (post_id, user_id) 唯一索引保证幂等，重复点赞返回当前总数",
            "帖子正文只存纯文本/Markdown 源，渲染放前端，避免服务端 XSS 过滤遗漏",
        ],
    )

    # ---------------- 附录 B：2 页团队记录 ----------------
    for page in range(2):
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        if page == 0:
            h1(doc, "附录 B　团队记录（预留 2 页）")
            p(doc, "供项目组记录会议结论、待办与交接。", color=GREY)
        else:
            p(doc, " ", space_after=0)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    return OUT


if __name__ == "__main__":
    path = build()
    print(f"saved: {path} ({path.stat().st_size} bytes)")
