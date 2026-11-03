"""生成 Vein Launcher v0.1.0 内部文档（Word）

用法：python tools/gen_internal_doc.py
输出：docs/v0.1.0/VeinLauncher_v0.1.0_Internal.docx
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "v0.1.0" / "VeinLauncher_v0.1.0_Internal.docx"
LOGO = ROOT / "assets" / "logo.png"
STUDIO = "ZHANJHN Studio"

ACCENT = RGBColor(0x2D, 0x6C, 0xF0)
DARK = RGBColor(0x1F, 0x2A, 0x3A)
GREY = RGBColor(0x5B, 0x66, 0x75)
BODY_FONT = "微软雅黑"
MONO_FONT = "Consolas"


# ----------------------------------------------------------------------
def set_cell_shading(cell, hex_color: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def setup_header_footer(section) -> None:
    """除封面外每页：左上角 logo + 页眉说明；页脚：机密提示 + 页码"""
    section.different_first_page_header_footer = True

    header = section.header
    header.is_linked_to_previous = False
    para = header.paragraphs[0]
    para.text = ""
    para.paragraph_format.space_after = Pt(2)
    para.paragraph_format.tab_stops.add_tab_stop(Cm(16.6), WD_TAB_ALIGNMENT.RIGHT)
    logo_run = para.add_run()
    logo_run.add_picture(str(LOGO), height=Cm(0.72))
    tab = para.add_run("\t")
    tab.font.size = Pt(8)
    text = para.add_run(f"{STUDIO}　|　Vein Launcher v0.1.0 内部文档　|　内部资料，请勿上传 GitHub")
    text.font.size = Pt(8)
    text.font.color.rgb = GREY
    text.font.name = BODY_FONT
    text._element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)

    footer = section.footer
    footer.is_linked_to_previous = False
    fpara = footer.paragraphs[0]
    fpara.text = ""
    fpara.paragraph_format.tab_stops.add_tab_stop(Cm(16.6), WD_TAB_ALIGNMENT.RIGHT)
    left = fpara.add_run("内部资料 · 禁止外传")
    left.font.size = Pt(8)
    left.font.color.rgb = GREY
    fpara.add_run("\t").font.size = Pt(8)
    r = fpara.add_run()
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    r._r.addnext(fld)
    fpara.add_run(" / ").font.size = Pt(8)
    r2 = fpara.add_run()
    fld2 = OxmlElement("w:fldSimple")
    fld2.set(qn("w:instr"), "NUMPAGES")
    r2._r.addnext(fld2)
    for run in fpara.runs:
        run.font.size = Pt(8)
        run.font.color.rgb = GREY


def style_document(doc: Document) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = BODY_FONT
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = DARK
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
    normal.paragraph_format.line_spacing = 1.35
    normal.paragraph_format.space_after = Pt(4)

    for name, size, color, before, after in (
        ("Heading 1", 16, ACCENT, 18, 8),
        ("Heading 2", 12.5, DARK, 12, 5),
        ("Heading 3", 11, DARK, 8, 4),
    ):
        st = doc.styles[name]
        st.font.name = BODY_FONT
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = color
        st._element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)


def h1(doc, text):
    doc.add_heading(text, level=1)


def h2(doc, text):
    doc.add_heading(text, level=2)


def p(doc, text="", *, size=10.5, bold=False, color=None, italic=False, space_after=4):
    para = doc.add_paragraph()
    para.paragraph_format.space_after = Pt(space_after)
    run = para.add_run(text)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color is not None:
        run.font.color.rgb = color
    return para


def bullets(doc, items, style="List Bullet"):
    for item in items:
        para = doc.add_paragraph(style=style)
        para.paragraph_format.space_after = Pt(2)
        run = para.add_run(item)
        run.font.size = Pt(10)


def code(doc, text):
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(4)
    para.paragraph_format.space_after = Pt(8)
    para.paragraph_format.left_indent = Cm(0.3)
    run = para.add_run(text)
    run.font.name = MONO_FONT
    run._element.rPr.rFonts.set(qn("w:eastAsia"), MONO_FONT)
    run.font.size = Pt(8.5)
    run.font.color.rgb = GREY
    p_pr = para._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), "F3F5F9")
    p_pr.append(shd)
    return para


def table(doc, headers, rows, widths=None, font_size=9.0, header_size=9.5, compact=False):
    tbl = doc.add_table(rows=1, cols=len(headers))
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = tbl.rows[0].cells
    for i, text in enumerate(headers):
        hdr[i].text = ""
        run = hdr[i].paragraphs[0].add_run(str(text))
        run.bold = True
        run.font.size = Pt(header_size)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        set_cell_shading(hdr[i], "2D6CF0")
    for row in rows:
        cells = tbl.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = ""
            run = cells[i].paragraphs[0].add_run(str(value))
            run.font.size = Pt(font_size)
    if widths:
        for row in tbl.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    # 表头跨页重复 + 单行不跨页拆分
    hdr_pr = tbl.rows[0]._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    hdr_pr.append(tbl_header)
    for row in tbl.rows:
        tr_pr = row._tr.get_or_add_trPr()
        cant_split = OxmlElement("w:cantSplit")
        tr_pr.append(cant_split)
    if compact:
        for row in tbl.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    para.paragraph_format.space_after = Pt(0)
                    para.paragraph_format.space_before = Pt(0)
                    para.paragraph_format.line_spacing = 1.05
        gap = doc.add_paragraph()
        gap.paragraph_format.space_after = Pt(0)
        gap.paragraph_format.line_spacing = 0.6
    else:
        doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return tbl


# ----------------------------------------------------------------------
def build() -> Path:
    doc = Document()
    style_document(doc)
    section = doc.sections[0]
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.0)
    setup_header_footer(section)

    # ---------------- 封面（开篇页：只有 logo、版本与归属） ----------------
    for _ in range(2):
        doc.add_paragraph()
    logo_para = doc.add_paragraph()
    logo_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    logo_para.add_run().add_picture(str(LOGO), width=Cm(8.4))

    doc.add_paragraph()
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("VEIN LAUNCHER")
    run.font.size = Pt(38)
    run.bold = True
    run.font.color.rgb = ACCENT

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = sub.add_run("v0.1.0 · 内部版本")
    run.font.size = Pt(18)
    run.bold = True

    warn = doc.add_paragraph()
    warn.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = warn.add_run("内部版本 · 请勿上传至 GitHub")
    run.font.size = Pt(12)
    run.bold = True
    run.font.color.rgb = RGBColor(0xC0, 0x39, 0x2B)

    doc.add_paragraph()
    studio = doc.add_paragraph()
    studio.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = studio.add_run(STUDIO)
    run.font.size = Pt(13)
    run.bold = True

    date_para = doc.add_paragraph()
    date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = date_para.add_run(dt.date.today().isoformat())
    run.font.size = Pt(10)
    run.font.color.rgb = GREY

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ---------------- 关于我们 ----------------
    h1(doc, "关于我们")
    h2(doc, "我们是做什么的")
    p(
        doc,
        f"{STUDIO}（GitHub 组织 zhanjhn-studio）是一支做 Minecraft Java 版工具链的小团队。"
        "Vein Launcher 是我们的主线产品：一个面向 Windows 的轻量启动器，"
        "目标是把「装游戏、管实例、看存档、接插件」这些事做得干净利落。",
    )
    bullets(
        doc,
        [
            "产品：Vein Launcher — Python 五层后端 + React 19 界面 + Node 插件宿主 + 自研 MLC 控制层",
            "当前版本：v0.1.0（公开版），Windows 10/11 x64，便携免安装",
            "团队仓库：github.com/zhanjhn-studio/vein_launcher",
            "本文档性质：内部版本，包含未公开的构建、风险与讨论内容，请勿上传至 GitHub 或对外分发",
        ],
    )
    h2(doc, "这份文档包含什么")
    table(
        doc,
        ["章节", "内容", "读者"],
        [
            ["一、版本与发布", "版本号、tag、发布资产、包体信息", "全员"],
            ["二、架构总览", "五层结构、通信协议、前后端边界", "开发"],
            ["三、模块与状态", "14 个模块的当前状态与关键文件", "开发 / 测试"],
            ["四、数据目录与日志", "运行时目录、日志分类约定", "开发 / 运维"],
            ["五、构建、打包与发布", "前端构建、测试、PyInstaller、gh release", "开发 / 发布负责人"],
            ["六、验证记录", "测试与实测结果（下载、更新、打包、插件）", "测试"],
            ["七、团队协作规则", "改动流程、记录方式、提交规范", "全员"],
            ["八、已知问题与风险", "阻塞项、功能欠账、风险清单", "全员 / 负责人"],
            ["九、下一步建议", "按优先级排列的后续工作", "负责人"],
            ["十、讨论页（两页）", "议题看板、待决详情、已定决议、模板、同步记录", "全员"],
        ],
        widths=[4.2, 8.6, 3.0],
    )
    h2(doc, "文档使用约定")
    bullets(
        doc,
        [
            "Word 版仅供团队评审与分发，内容以仓库 docs/v0.1.0/*.md 为准",
            "内部版本不要上传到 GitHub Release、网盘或公开群",
            "每次改动后同步更新 teamwork.md，并在讨论页追加/关闭议题",
        ],
    )
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ---------------- 目录（手动） ----------------
    h1(doc, "目录")
    bullets(
        doc,
        [
            "一、版本与发布",
            "二、架构总览",
            "三、模块与状态",
            "四、数据目录与日志",
            "五、构建、打包与发布",
            "六、验证记录",
            "七、团队协作规则",
            "八、已知问题与风险",
            "九、下一步建议",
            "十、讨论页（议题看板 · 决议 · 模板 · 同步记录）",
        ],
        style="List Number",
    )

    # ---------------- 一 ----------------
    h1(doc, "一、版本与发布")
    table(
        doc,
        ["项", "值"],
        [
            ["版本号", "0.1.0"],
            ["Git tag", "v0.1.0"],
            ["发布时间", "2026-10-31T10:01:54Z"],
            ["发布页", "github.com/zhanjhn-studio/vein_launcher/releases/tag/v0.1.0"],
            ["资产 1", "VeinLauncher-0.1.0-win64.zip — 249,873,131 B（≈238 MB）"],
            ["资产 2", "latest.json — 453 B（更新检查的公开兜底清单）"],
            ["包体", "PyInstaller onedir，解压后 615 MB"],
        ],
        widths=[3.2, 12.6],
    )
    p(doc, "发布说明见仓库根 RELEASE_NOTES.md（英文 + 中文两段）。latest.json 内容：")
    code(
        doc,
        '{\n  "version": "0.1.0",\n'
        '  "asset": "VeinLauncher-0.1.0-win64.zip",\n'
        '  "url": "https://github.com/.../releases/download/v0.1.0/VeinLauncher-0.1.0-win64.zip"\n}',
    )

    # ---------------- 二 ----------------
    h1(doc, "二、架构总览")
    code(
        doc,
        "React 19 (WebView)  <->  QWebChannel + JSON-RPC 2.0  <->  Python 五层\n"
        "        |                                                   |\n"
        "   Layui 控件层                                    Node 插件宿主（独立进程）",
    )
    bullets(
        doc,
        [
            "通信协议：{jsonrpc, id, method, params:{args}}；回包 window.__veinResult；"
            "推送 __veinProgress / __veinLog / __veinNotify / __veinNavigate",
            "五层：Common（事件总线、配置、日志、i18n、工具）→ Domain（模型、仓储契约、版本解析）"
            "→ Infrastructure（HTTP、下载、进程、MC2、插件宿主）→ Application（版本/皮肤/实例/更新/插件服务）"
            "→ Presentation（Qt 窗口、bridge、webui）",
            "MLC：vein_launcher/mlc/ 承载游戏控制桥与插件能力入口",
            "前端：React 负责页面与路由；Layui 只提供表单/进度/勾选等控件结构，外观由 styles.css 覆盖",
        ],
    )
    p(doc, "规模：Python ≈7,790 行，前端 ≈4,641 行，JSON-RPC 方法 60 个。")

    # ---------------- 三 ----------------
    h1(doc, "三、模块与状态")
    table(
        doc,
        ["模块", "关键文件", "状态", "说明"],
        [
            ["启动器窗口", "presentation/main.py", "可用", "无边框自绘标题栏、最小化/最大化/关闭"],
            ["通信桥", "presentation/bridge.py", "可用", "60 个方法 + 进度/日志推送"],
            ["版本与下载", "version_service.py、download/*", "可用", "逐文件进度、失败可见、并发 8、断点续传"],
            ["镜像", "mirror.py、http_client.py", "可用", "BMCLAPI 优先、官方回退、证书异常降级"],
            ["加载器", "loader_service.py", "可用", "Fabric / Forge / Quilt / NeoForge"],
            ["模组资源", "modrinth_api.py", "可用", "搜索、版本/加载器过滤、远程图标"],
            ["账号", "account_service.py 等", "部分", "离线✅ LittleSkin✅ 微软被 403 阻塞"],
            ["皮肤", "skin_service.py", "可用", "导入 PNG、读 LittleSkin、公开皮肤库下载"],
            ["实例管理", "instance_service.py", "可用", "模组/资源包/光影/数据包/整合包、存档、删实例"],
            ["世界分析 MC2", "infrastructure/mc2/*", "部分", "解析种子/版本/难度；结构表格待做"],
            ["插件系统", "plugin_host/*", "可用", "崩溃重启、30s 超时、ui.openPage"],
            ["一键更新", "update_service.py", "可用", "GitHub → latest.json → 公告三级回退"],
            ["主题/语言", "theme.ts、i18n.ts", "部分", "深/浅/透明/跟随系统；中文覆盖主导航"],
            ["界面动效", "styles.css", "可用", "侧栏 280ms 展开、文字滑入、壁纸/简洁模式"],
        ],
        widths=[2.4, 5.0, 1.6, 6.8],
    )

    # ---------------- 四 ----------------
    h1(doc, "四、数据目录与日志")
    code(
        doc,
        "VeinLauncher/\n"
        "├── config/       config.json、accounts.json、skins.json、language.json、wallpapers/\n"
        "├── log/          launcher-*.log、plugin-*.log、mlc-*.log、download-*.log、error.log、crash.log\n"
        "├── minecraft/    instances/、versions/、libraries/、assets/\n"
        "├── downloads/    下载缓存、update/\n"
        "├── plugin/       Node 插件\n"
        "├── java/         自动下载的运行时\n"
        "├── skins/        皮肤 PNG（按账号 id）\n"
        "└── democrat/     社区数据（预留）",
    )
    p(doc, "约定：日志只写文件，不输出控制台；插件、MLC、下载日志分文件。")

    # ---------------- 五 ----------------
    h1(doc, "五、构建、打包与发布")
    code(
        doc,
        "# 1) 前端\n"
        "cd vein_launcher\\presentation\\webui\n"
        "powershell -ExecutionPolicy Bypass -File build.ps1\n\n"
        "# 2) 测试\n"
        "python -m unittest discover -s tests\n\n"
        "# 3) 打包（PyInstaller onedir）\n"
        "python -m PyInstaller --noconfirm --clean --windowed --name VeinLauncher ^\n"
        "  --icon assets\\logo.ico --distpath packaging\\dist --workpath packaging\\build ^\n"
        "  --specpath packaging ^\n"
        "  --add-data \"vein_launcher\\presentation\\webui\\dist;webui\\dist\" ^\n"
        "  --add-data \"assets;assets\" packaging\\entry.py\n\n"
        "# 4) 压缩并发布\n"
        "tar -a -c -f packaging\\VeinLauncher-0.1.0-win64.zip -C packaging\\dist VeinLauncher\n"
        "gh release create v0.1.0 packaging\\VeinLauncher-0.1.0-win64.zip packaging\\latest.json ^\n"
        "  --title \"Vein Launcher 0.1.0\" --notes-file RELEASE_NOTES.md",
    )
    bullets(
        doc,
        [
            "打包后资源从 _MEIPASS 读取（main.py 的 _resources_dir() / _webui_dir() 已适配）",
            "发布资产必须包含新的 latest.json，否则更新回退链只剩公告源",
            "发布 Release 必须由项目负责人明确指令，日常只提 PR / 提交",
        ],
    )

    # ---------------- 六 ----------------
    h1(doc, "六、验证记录")
    table(
        doc,
        ["验证项", "方法", "结果"],
        [
            ["单元测试", "python -m unittest discover -s tests", "44 项通过"],
            ["下载全流程", "无头安装 1.20.1", "3640/3640，failed=0，71.5s"],
            ["更新检测", "UpdateService('0.0.3').latest()", "available=true, 0.1.0, latest.json"],
            ["更新下载", "下载 latest.json 资产", "453 B，进度回调 (453,453)"],
            ["打包运行", "运行 dist/VeinLauncher.exe", "版本 0.1.0，前端从 _internal 加载"],
            ["插件系统", "tools/plugin_selftest.py", "9/9 PASS（提交 34a1dba）"],
            ["远程图片", "最小页面 + naturalWidth", "Modrinth 图标 96×96"],
            ["侧栏动效", "rAF 采样宽度", "68→108→…→208，约 200ms"],
        ],
        widths=[2.6, 6.4, 6.8],
    )

    # ---------------- 七 ----------------
    h1(doc, "七、团队协作规则")
    bullets(
        doc,
        [
            "改动前：git pull → 读 teamwork.md 的 In progress → 读本文档模块状态",
            "改动中：小步提交，写清自己负责的目录/文件，避免与他人重叠",
            "改动后：跑测试 + 前端构建 → 追加 teamwork.md 条目 → 与代码一起提交",
            "停下来时：把条目放进 In progress 并写清下一步",
            "讨论/决策：写入讨论页（D-xxx 编号），定案后标 accepted 并写结论",
        ],
        style="List Number",
    )

    # ---------------- 八 ----------------
    h1(doc, "八、已知问题与风险")
    h2(doc, "阻塞项")
    table(
        doc,
        ["#", "问题", "影响", "计划"],
        [
            ["1", "微软 login_with_xbox 返回 403 Invalid app registration", "正版账号不可用",
             "等 Minecraft Services 白名单，或经同意改官方旧版流程"],
            ["2", "公告站 public.js 仍写 0.0.3", "应用内横幅版本落后", "更新 Pages 仓库"],
        ],
        widths=[0.9, 7.2, 3.4, 4.3],
    )
    h2(doc, "功能欠账")
    table(
        doc,
        ["#", "问题", "现状"],
        [
            ["3", "世界分析面板直接展示 MC2 原始 JSON", "待做群系/结构表格"],
            ["4", "中文翻译只覆盖主导航与设置", "页面正文仍英文"],
            ["5", "zip 更新是解压到 update 目录", "未实现关停后原地替换"],
            ["6", "安装包未签名", "SmartScreen 可能提示"],
        ],
        widths=[0.9, 8.0, 6.9],
    )
    h2(doc, "风险")
    table(
        doc,
        ["#", "风险", "说明"],
        [
            ["7", "令牌明文存 config/", "建议后续用 Windows DPAPI 加密"],
            ["8", "镜像证书缺失时降级不校验 SSL", "已限定 BMCLAPI 节点，仍属权衡"],
            ["9", "微软/LittleSkin 第三方登录合规", "官方旧版流程属灰色地带，需负责人决策"],
            ["10", "包体 615 MB", "可考虑拆分 QtWebEngine 或增量更新"],
            ["11", "插件宿主依赖本机 Node 18+", "未内嵌 Node 运行时"],
        ],
        widths=[0.9, 6.0, 8.9],
    )

    # ---------------- 九 ----------------
    h1(doc, "九、下一步建议")
    bullets(
        doc,
        [
            "世界分析表格化（种子 → 出生点群系 / 结构摘要）",
            "原地更新器（等待主程序退出 → 替换 → 重启）",
            "中文翻译补全（页面正文、按钮）",
            "令牌加密存储（Windows DPAPI）",
            "插件市场 / 示例插件扩充",
            "打包瘦身与安装器（可选 NSIS / Inno）",
        ],
        style="List Number",
    )

    # ---------------- 十、讨论页 ----------------
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    h1(doc, "十、讨论页")
    p(
        doc,
        "所有需要团队决策的事情都记在这里，避免在聊天里丢结论。规则：先编号（D-xxx）→ "
        "写清背景与选项 → 记录倾向 → 定案后标 accepted 并写结论。讨论可在 GitHub Discussions "
        "或群聊进行，结论必须回填本页。",
        color=GREY,
    )
    h2(doc, "10.1 议题看板")
    table(
        doc,
        ["编号", "议题", "状态", "负责人"],
        [
            ["D-001", "微软登录通道：等白名单 / 官方旧版授权码 / 只做离线+LittleSkin", "blocked", "lead"],
            ["D-002", "世界分析面板要不要做群系/结构表格", "open", "—"],
            ["D-003", "原地自动更新器（updater.exe）是否本版本做", "open", "—"],
            ["D-004", "中文翻译覆盖范围：全量 or 主要界面", "open", "—"],
            ["D-005", "令牌是否用 Windows DPAPI 加密", "open", "—"],
            ["D-006", "包体 615 MB 是否优化 / 换安装器", "open", "—"],
            ["D-007", "公告站 public.js 版本号同步", "open", "—"],
            ["D-008", "插件市场是否纳入 0.2.0", "open", "—"],
            ["D-009", "镜像证书异常时是否保持降级不校验", "open", "—"],
            ["D-010", "简洁模式默认关闭", "accepted", "lead"],
            ["D-011", "默认英文界面 + 设置内切换中文", "accepted", "lead"],
            ["D-012", "删除嵌套 v0.5 副本、只合并壁纸/简洁模式", "accepted", "lead"],
            ["D-013", "Layui 仅用于控件层，不接管页面", "accepted", "lead"],
        ],
        widths=[1.6, 9.6, 2.0, 2.6],
        font_size=8.5,
        header_size=8.5,
        compact=True,
    )

    h2(doc, "10.2 待讨论议题详情")
    table(
        doc,
        ["议题", "背景 / 现状", "倾向 / 待定"],
        [
            [
                "D-001 微软登录通道 · blocked",
                "XBL/XSTS 全通，login_with_xbox 403 Invalid app registration（服务端应用白名单）。",
                "倾向 C：只保留离线 + LittleSkin，微软入口标注等待开放；B（官方旧版授权）需负责人书面同意。",
            ],
            [
                "D-002 世界分析表格化 · open",
                "点存档展示 mc2.scan 原始 JSON。",
                "顶部种子/版本/难度 + 出生点群系、结构卡片；是否引入 region 扫描待定。",
            ],
            [
                "D-003 原地更新器 · open",
                "zip 更新解压到 downloads/update/extracted-<ts>/，需手动覆盖。",
                "生成 updater：退出后替换 _internal 并重启，失败回滚；是否需管理员权限待定。",
            ],
            [
                "D-004 中文覆盖率 · open",
                "ZH 词表覆盖主导航、设置、实例标签，正文仍英文。",
                "A 全量 t() 包裹（回归风险大）/ B 只补高频路径（启动、下载、设置）。",
            ],
            [
                "D-005 令牌加密 · open",
                "config/accounts.json 明文存 access/refresh token。",
                "Windows DPAPI 加密，跨机器不可解密；是否影响跨平台待定。",
            ],
            [
                "D-006 包体与安装器 · open",
                "onedir 615 MB，zip 238 MB。",
                "拆分 QtWebEngine / 增量更新 / NSIS 安装器；是否接受安装器待定。",
            ],
            [
                "D-007 公告站版本 · open",
                "public.js 仍写 0.0.3，应用内横幅版本落后。",
                "更新 Pages 仓库到 0.1.0。",
            ],
            [
                "D-008 插件市场 · open",
                "宿主、权限、示例插件可用，没有市场页。",
                "0.2.0 是否做浏览 / 安装 / 更新最小闭环。",
            ],
            [
                "D-009 镜像 SSL 降级 · open",
                "BMCLAPI 部分节点证书链不完整 → 自动改用不校验会话并记住。",
                "可用性↑、中间人风险↑；评估 CA 补全或固定公钥。",
            ],
        ],
        widths=[4.0, 6.3, 5.9],
        font_size=8.5,
        header_size=8.5,
        compact=True,
    )

    h2(doc, "10.3 已定决议")
    table(
        doc,
        ["编号", "决议", "依据", "日期"],
        [
            ["D-010", "简洁模式默认关闭；配置缺省按 False", "用户明确要求；settings.py / prefs.ts", "2026-11-01"],
            ["D-011", "UI 默认英文，设置内可切简体中文", "项目硬性规范", "长期"],
            ["D-012", "删除嵌套 v0.5 副本，仅合并壁纸/简洁模式", "仓库整洁需求；差异比对", "2026-11-01"],
            ["D-013", "Layui 只用于控件层，页面由 React 掌控", "架构约定", "长期"],
        ],
        widths=[1.6, 7.4, 4.6, 2.2],
        font_size=8.5,
        header_size=8.5,
        compact=True,
    )

    h2(doc, "10.4 新议题模板")
    p(
        doc,
        "新议题按「编号 D-xxx / 背景 / 选项 / 影响 / 倾向 / 待定」六行记录，"
        "定案后把状态改为 accepted 并补一行结论。",
        size=9,
        color=GREY,
    )

    h2(doc, "10.5 同步记录")
    table(
        doc,
        ["日期", "参与", "结论摘要"],
        [
            ["2026-10-31", "lead", "v0.1.0 发布；更新系统三级回退通过；打包版可运行"],
            ["2026-11-01", "lead", "仓库清理；壁纸/简洁模式合并；侧栏动效修复；teamwork.md 启用"],
            ["2026-11-01", "macbo2013", "插件系统硬化（重启/超时/openPage）+ Pydantic v2 迁移，自检 9/9"],
            ["2026-11-03", "lead", "建立 v0.1.0 内部文档与讨论页"],
        ],
        widths=[2.2, 2.6, 11.0],
        font_size=8.5,
        header_size=8.5,
        compact=True,
    )
    p(doc, "下一次同步请在此表追加一行，并把有结论的议题移到 10.3。", color=GREY, italic=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    return OUT


if __name__ == "__main__":
    path = build()
    print(f"saved: {path} ({path.stat().st_size} bytes)")
