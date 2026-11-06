# Vein Launcher 项目总报告（REPORT.md）

> **呈：总经理审核** ｜ 编制：docs-writer（素材汇编）／代笔落盘：Lead ｜ 复核：Lead ｜ 审核：总经理
> 日期：2026-11-05 ｜ 文档状态：**待总经理审核，暂不入库、暂不 push**
> 依据：仓库 `Z:\Vein Launche`、`teamwork.md`（431 行协作总账）、8 个子智能体第一轮只读勘察报告及全员点对点交叉核对结论。

| 项 | 值 |
|---|---|
| 项目 | Vein Launcher（VL），Minecraft Java 版启动器，Windows 10/11 x64，便携免安装 |
| 仓库 | `github.com/zhanjhn-studio/vein_launcher`（public，MIT，main） |
| 版本 | 0.1.0（`presentation/context.py` 的 `VERSION`；包内 `__version__ = 0.1.0-alpha`） |
| 当前 HEAD | `67cfe54`（docs(teamwork): 改写为可迁移的协作总账）；`main` 与 `origin/main` 同步，ahead/behind = 0/0，工作树干净；共 110 commits |
| 最近发布 | tag `v0.1.0`（annotated tag 对象 `8ccab118` → 解引用 commit **`5e66188`**），**落后 main 24 个提交** |
| 规模 | RPC 66 · 一级导航 8 · 测试 51 · 插件能力 17 · Python ≈9,469 行 · 前端 17 文件（提取器实测 **5,015** 行 / 文档声明 **5,017** 行，差 2 行） |
| 包体 | onedir 615 MB；zip 238 MB（QtWebEngine 占主要体积） |

---

## 一、执行摘要（总经理一页看懂）

**结论**：项目 0.1.0 主干代码健康、可运行、无正在发生的线上故障；`95bd910` 的 9 项启动链路修复**逐条复核仍在代码中、无回退**。本轮 8 人全员只读勘察 + 点对点交叉核对，未改动任何文件。主要问题集中在**三块**：已登记但尚未修复的功能缺口、文档与仓库治理漂移、以及若干「埋雷未爆」的规范隐患。

**Top 风险（按严重度）**
1. **加载器 P1**：Fabric/Quilt 库完全不下载且不进 classpath；Forge/NeoForge 安装链断裂（比 `teamwork.md` 登记更严重）；natives classifier 库不下载；NeoForge 对 MC 1.20.1 版本解析失效。影响「加载器」模块实际可用性。
2. **打包 P1（新发现）**：`VeinLauncher.spec` / §3 命令的 `--add-data` 漏掉三个非 Python 资源——`plugin_host/runtime/*.js`、`common/i18n/locales/*.json`、`plugins_examples/` → 打包版插件宿主必然启动失败、无法切换简体中文、示例插件为空。
3. **可移植性 P1**：`webui/build.ps1` 与 `VeinLauncher.spec` 硬编码他人机器绝对路径、webui 无 `package.json`/esbuild → 全新环境克隆后前端无法构建、`dist/` 缺失即白屏；且 README 声称「dist/ 已随仓库提交」与 `.gitignore` 直接矛盾，会误导迁移者。
4. **规范 P1**：`styles.css:420` `.download-bar` 全宽 fixed + 半透明 + `blur(12px)` 叠动态下载进度，违反硬规则 §4-10「大面积 backdrop-filter 禁用」；`settings.py:46 UIConfig.language="zh_CN"` 是 §4-1「默认英文」的后端配置埋雷（无消费者但会写进 `config.json`）。`index.html:2 lang="zh-CN"` 仅为静态文档标记错 + 切语言后不同步（P3、无功能影响），性质不同、分开表述。
5. **治理 P1**：无 CI（`actions/workflows=0`），且历史 `ci.yml` 曾连红 5 次后被删除 → 回归无防线；tag `v0.1.0` 落后 24 提交，用户下载的 249 MB 正式包不含 9 项启动修复；`latest.json` 缺 `sha256`/`size`；`main` 无保护、无 rulesets、安全能力全关。

**需总经理拍板（2 项核心 + 5 项关联）**
- ① CI 命令口径：`python -m unittest discover -s tests`（**建议**，理由见 §8）还是 `pytest tests -q`；
- ② 远端策略变更（branch protection / secret scanning / push protection / Dependabot）是否授权；
- 关联：发版与动 tag／改 Release 资产（§4-5 红线，须明确指令）、REPORT.md 是否入库、`plugin_host` 归属裁定、写入范围登记更正（含 `i18n.ts` / `build.ps1` / `main.py` 归属）、D-004 中文翻译范围。

**红线**：没有负责人明确指令，不发 Release、不动 tag、不改 release 资产。审核前不 push、不入库。

---

## 二、项目速览

**技术栈**：Python 3.13 · PySide6 6.12 + QWebEngine · React 19 + TypeScript（esbuild）· Layui 仅控件结构 · Node 18+（插件宿主）· aiohttp · pydantic v2 · PyInstaller onedir。

**后端五层**（依赖只能自上而下，跨层走 `event_bus`）：
`common`（事件总线/配置/日志/i18n/路径/异常）→ `domain`（模型与契约）→ `infrastructure`（网络/下载/进程/NBT/存储/插件宿主）→ `application`（9 个业务服务）→ `presentation`（Qt 窗口 / `bridge.py` 66 个 RPC / 前端 webui）；另有 `mlc/` 游戏控制层。

**前端**：扁平结构，`vein_launcher/presentation/webui/src/` 根下 `*Page.tsx`（launch / skins / download / instance / settings / onboarding）+ 旧版 `pages.tsx` 合集 + `pluginUi.tsx`；`index.html` / `build.ps1` / `assets/` 在 `webui/` 下；产物 `webui/dist/`（**被 gitignore，不入库**）。一级导航 8 项：`launch / skins / download / plugins / mlc / multiplayer / settings / toolbox`（hash 路由 `#/key`）。⚠ `teamwork.md §5` 登记的 `webui/src/pages/` **目录不存在**，属登记漂移。

**协议**：QWebChannel + JSON-RPC 2.0，66 个 handler；推送 5 通道 `__veinProgress / __veinLog / __veinNotify / __veinNavigate / __veinGameExited`。下载链路：BMCLAPI 镜像优先 + 官方兜底 → 证书异常按 host 降级 → `.part` 断点续传 + 并发 8 + 目标级锁 → SHA-1 → 失败重试 3 次 → 逐文件进度回调。

**账号**：离线 ✅、LittleSkin ✅、Microsoft ⛔（服务端 403 `Invalid app registration`，待白名单；D-001 倾向「只做离线 + LittleSkin」）。更新：GitHub API → `latest.json` → 公告站三级回退。

**测试**：`tests/` 7 个文件、静态 51 个 `def test_`（test_accounts 22 / test_skins 11 / test_instances 6 / test_download_queue 2 / test_update 4 / test_rpc_launch_contract 4 / test_download_error_contract 3）；本地留存日志实证 `Ran 51 tests … OK` ×2（本轮按只读铁则未重跑）。`plugin_selftest.py` 9/9（独立脚本，未被 unittest 收录）。

---

## 三、团队与分工

本轮按 `teamwork.md §5` 重建并派发全套 8 人（模型为会话全局继承，显示 `hy4free`；spawn 时无法单点指定，符合 §6）。

| # | 角色 | 写入范围（登记） | 职责 |
|---|---|---|---|
| 1 | `coder-core` | `vein_launcher/domain/`、`common/` | 领域模型、通用基础结构、核心实体、常量 |
| 2 | `coder-services` | `application/`、`infrastructure/` | 业务逻辑、服务层、底层依赖封装 |
| 3 | `coder-platform` | `packaging/`、`tests/`、`tools/`、`plugin_host/`、`mlc/` | 构建打包、插件宿主、单测、工具链 |
| 4 | `docs-writer` | `docs/`、`teamwork.md`、`RELEASE_NOTES.md` | 开发/部署文档、更新日志、协作规范 |
| 5 | `ui-designer` | `webui/src/styles.css`、`assets/` | 配色、样式、图标、静态素材 |
| 6 | `interface-designer` | `webui/src/pages/`、`webui/index.html` | 页面组件、路由、交互、页面结构 |
| 7 | `github-manager` | `.github/`、`gh` 远端操作 | CI、issue/PR 模板、发布、标签 |
| 8 | `reviewer` | **无（只读）** | 全仓巡检、风险识别、规范校验，只出报告 |

**保留禁区（仅 Lead 可改）**：`webui/src/App.tsx`、`ui.tsx`、`bridge.ts`。

**调度铁则（§5.1）**：① 第一轮全员并发**只读勘察**、统一四段报告；② 收齐后 Lead 汇总分类（Bug 风险 / UI 交互打磨 / 文档&仓库治理）；③ **同一文件同一时间只分配给一个 Agent**，派发写明允许修改路径；④ reviewer 常驻只读；⑤ 越权修改他人范围 → 驳回；⑥ 子 Agent 免费可并发，Lead 控制轮询频率。

**生命周期事实（§5.2）**：`spawn_teammate` 名字全局唯一；`interrupt_agent` 置 inactive 但记录仍在；**无删除/解散接口**；`send_message` 会唤醒 inactive 成员。

**本轮登记范围缺口（待修正）**：根 `README*.md`、`CONTRIBUTING.md` 无归属；`interface-designer` 的 `webui/src/pages/` 应为扁平 `*Page.tsx`；`coder-platform` 的 `plugin_host/` / `mlc/` 缺前缀（真实为 `vein_launcher/infrastructure/plugin_host/`、`vein_launcher/mlc/`，且 plugin_host 与 coder-services 的 `infrastructure/` 归属重叠）；`i18n.ts`、`webui/build.ps1`、`presentation/main.py`、`presentation/context.py` 不在 8 角色明列范围，需 Lead 显式授权。

---

## 四、本轮勘察：8 份四段报告要点汇编

> 全员按固定四段（现状 / 问题清单 / 2~3 优先任务 / 预估改动文件）输出；本轮**零写入、未碰保留禁区**。8 份正式四段报告全部收齐（含 `coder-core` 后补）。以下为要点，全文归档于各成员汇报。

### 4.1 `coder-core`（domain / common，26 个 .py ≈2775 行，纯内存 compile 26/26 通过）
- **现状**：真正被上层消费的只有 `domain/models/account.py` 与全部 `common/*`；版本链路走 `application/services/*_service.py` 的 dict 解析 + `api_client.py`，`VersionJSON/ParsedVersion/VersionResolver` **无消费者**；`plugin_host/loader.py` 另有一份重复的 `PluginManifest`。
- **P1（仅 1 条）**：`settings.py:46 UIConfig.language="zh_CN"` 与 §4-1、translator、webui i18n 三方冲突（确认无消费者＝埋雷未爆，但 `Settings.load()` 首次 `save()` 会把 zh_CN 写进 `config.json` 已污染配置）。
  - 附：`domain/__init__.py:44` 的 `from .services import version_resolver` **不会**导致 ImportError（`python -B` 实测 `import vein_launcher.domain` exit=0；CPython 的 import machinery 在包属性查找失败时会自动加载同名子模块），仅 `:44` 注释「Will be imported when implemented」过时（P3 注释清理项，非缺陷）——详见附录 B.11.1 / B.16。
- **P2**：`AccountManager` pydantic 不可往返（缺 `account_type` 判别联合）；`event_bus` subscribe 不去重 / `publish_once` 空壳 / 异常无 `exc_info`；`parse_size` 带单位全抛 `ValueError`；`get_minecraft_dir` 热路径每次 stat+读+json（实测 4.3ms）无缓存；`set_minecraft_dir` 只建 `instances/`；**新发现** `version_resolver.py` 三处隐藏错误（引用不存在的 `minimum_java_version`、父版本 `assets` 读不到、`main_class` 取反）。
- **P3**：domain 约 1000 行无消费者、`VRPCGameControl.launch` 重复、`Game_CRASHED` 命名笔误、i18n 三套真源、`__init__` 导出不一致（差集仅 `ModInstallationSpec`/`ModDependencyGraph`/`PluginRPCError` 3 个；domain 独有 11 项属正常分层；`LittleSkinAccount` 两边均未导出、仅深径消费——见 B.11.2）、`domain/__init__.py:44` 过时注释、`SUBDIRS` 缺 `java/`/`skins/`。
- **优先任务**：A 规范止血（`settings.py` 单项目标；`domain/__init__.py` 仅可选 P3 注释清理）；B event_bus + parse_size + path_utils；C 账号模型判别联合。改动：`common/config/settings.py`、`common/events/event_bus.py`、`common/utils/{version_utils,path_utils}.py`、`domain/models/account.py` + `models/__init__.py`。

### 4.2 `coder-services`（application / infrastructure）
- **现状**：9 个业务服务 + 5 大基础设施块；静态核对下载链路（BMCLAPI → Queue 并发 8 → Downloader → SHA-1 → 重试 → event_bus/前端）与 RPC 服务装配（`context.py` ↔ `bridge._handlers` ↔ 各 service）**闭合、无装配缺失**；§9.1 修复均落地。
- **P1（4 项）**：① Fabric/Quilt 库完全不下载且不进 classpath（`_library_tasks`/`_classpath` 只看 `downloads.artifact`，Meta profile 是 `name`+`url`；`_install_meta_loader` 写完 profile 直接 return）；② Forge/NeoForge 安装链断裂且更严重（只造 `launcher_profiles.json`、绕过 Downloader、无镜像/证书降级/SHA/重试、`shutil.rmtree(work)` 删光依赖库、硬编码 Java 8 跑安装器、loader 安装不传 progress）；③ natives classifier 库不下载（高疑似，需实测 Mojang JSON）；④ NeoForge 版本解析对 1.20.1 失效（应 `47.1.x`，现 `20.1`）。
- **P2（12 项）**：P2-3/4/5/6/7 全部确认（P2-4 订正见 §4.9；P2-5 定位到 `update_service` 直打 UI 的第二条进度风暴）；P2-12/13 越界到 coder-core；新增：安装状态假阳性（下载前就写 `<id>.json`）、`context.close` 漏关会话、两份 `_rules_allow` 语义不一致、`modpack_service` 串行下载、`mirror.MODE` import 固化。
- **优先任务**：A 加载器/库下载修复（`version_service.py` / `launcher_service.py` / `loader_service.py`）；B 下载基础设施加固（`downloader.py` / `queue.py` / `mirror.py`）；C 版本目录回退与状态一致性。

### 4.3 `coder-platform`（packaging / tests / tools / plugin_host / mlc）
- **现状**：51 个 `def test_` ✅、plugin_selftest 9/9 ✅、`doc_facts.check()` 确为空壳 `return ([], [])` ✅、17 个 `reg.register` 与「插件能力 17」一致 ✅；`packaging/` 源码仅 `entry.py`/`spec`/`latest.json` + 被 ignore 的 3800+ 构建残留；`tests/` 无 `__init__`/pytest 配置/CI，requirements 钉 `pytest<8` 而缓存是 9.2.0。
- **P0**：`parse_size()` 单位解析失效（属 coder-core 范围）。
- **P1**：`build.ps1` 与 `VeinLauncher.spec` 硬编码他人机器绝对路径 + webui 无 esbuild → 迁移后无法构建/白屏；`doc_facts.check()` 未实现且两 Word 生成器仍写死 60/4641/7790/44（应 66/5015/9469/51）、**根本没调 `collect()`**（§9.4 根因）；写入范围 `plugin_host/` 与真实路径不符、与 coder-services 重叠。
- **P2**：测试基建缺口、`latest.json` 无 sha256/size、生成器会写盘（本轮未跑）。**P3**：`scan_left.py` 相对路径、`teamlog.ps1` 写「44 OK」、`.gitignore` 尾部 GBK 乱码、`Game_CRASHED` 笔误、`__pycache__` 散落。
- **优先任务**：① 修 parse_size + 契约单测；② 前端/打包可移植化 + 一键构建脚本；③ 激活 `doc_facts.check()` + 文档数字去硬编码 + 测试入口固化。

### 4.4 `docs-writer`（docs / teamwork.md / RELEASE_NOTES.md）
- **现状**：`teamwork.md` 431 行结构完整；§9.4 五条漂移**逐条坐实且漂移点更多**（见 §5.3）；生成器硬编码旧数字且未接 `doc_facts.collect()`，`check()` 占位 → 防漂移机制未接线。
- **P1**：① **`README.md:80` / `README-zh.md:57`「dist/ 已随仓库提交」与 §0/§3/§11/`.gitignore` 直接矛盾**（会致迁移者白屏，§9.4 未登记、最严重）；且 `README:75-78` 给的是**裸 esbuild 命令只打 app.js、不拷静态资源** → 半残 dist；② §5 写入范围缺口（根 README*/CONTRIBUTING 无归属、`pages/` 不存在、plugin_host/mlc 缺前缀）；③ §9.4 五条 + 新增第 6 条（§1 HEAD `95bd910`→`67cfe54`，**注意 9 项修复仍在、勿写成修复丢了**，建议改「以 git log 为准」）；④ 防漂移机制未接线；⑤ CONTRIBUTING 测试口径冲突。
- **P2**：`docs/v0.1.0/README.md:31-33` 四个数字全旧；INTERNAL.md 同步日期/commit 过期（宜加「as of v0.1.0」）；README 推送通道漏 `__veinGameExited`、规划列表含已实现项、Python 3.11+ vs 3.13、布局写 `src/(pages,components,lib)`；§9.3 远端事实漂移；§11 漏列两份 v0.5 归档文档；REPORT.md 入库状态。
- **P3**：§13 日志排序违反「最新在最后」+ 4 条缺 commit；DISCUSSION §5 同步记录止于 11-03；`gen_dev_doc.py` docstring 3 页 vs 代码 2 页；**§7.1:207 把 4 个插件能力误列为 66 个 RPC 分组示例**；预览图名不符；RELEASE_NOTES 五步向导括号只列 4 步；CONTRIBUTING 示例「默认浅色」与深色默认相悖。
- **优先任务**：订正 §9.4 五条 + HEAD + README 构建说明 + CONTRIBUTING 口径；激活防漂移；§5/§9.3/§11/§13 治理收口。

### 4.5 `ui-designer`（styles.css / assets）
- **现状**：`styles.css` 1536 行「基线 + 多段只叠加覆盖」；§4-7（深色默认 / 简洁模式关 / 空闲 60s / 无壁纸）**全部落地**；primary 深色渐变、滑动 pill（46px 步长对齐 8 NAV）、卡片 lift、3 张快捷卡、版本卡精简均已落地；`dist/styles.css` 与 src 同步但被 ignore。
- **P1**：**§4-10 未落实干净**——`:420 .download-bar`（全宽 fixed + 半透明 + `blur(12px)` + 叠动态进度）与 `:934-935 .side-handle` 仍 backdrop-filter，`:988-993` 是死规则，而 §13 `90924f6` 宣称已移除（**不完整声明**）；「只叠加不合并」造成 `.side-btn.active` 背景 / `::before` 竖条被静默作废、进度条 3 套不一致、硬编码蓝紫 accent 不适配浅色、死帧 `fade-in/pop-in`、死类 `.method-card/.ico`、★ 角标永不渲染；`index.html:2 lang="zh-CN"` 为 P3 静态标记错（见 §4.6 / B.11.4，interface-designer 范围）。
- **P2**：品牌色不同源（logo.svg 纯蓝 vs CSS 蓝紫/蓝绿）、`logo.png` 双真源（assets 与 webui/src 同 SHA256）、`wordmark.png`/`_slide.png` 孤儿、前景色对比度、焦点环三层叠加、§13 `ui/sidebar` 记 0.28s 实现已 .34s。
- **优先任务**：① 彻底清 backdrop-filter、收敛为零（改纯色 + `--shadow-md`）；② 合并重复覆盖段 / 删死类（类名不变、纯 CSS 内部重构）；③ 品牌色/token 统一 + assets 去重（删除需 Lead 确认）。

### 4.6 `interface-designer`（前端页面 / 路由）
- **现状**：`webui/src/pages/` 不存在，实际扁平 `*Page.tsx`；NAV 8 项齐全、hash 路由回落正常；但 8 项中只有 4 项用新扁平页，`plugins/mlc/multiplayer/toolbox` 仍渲染旧版 `pages.tsx` ThreePane（dist/app.js 同时检出新旧两套 UI 串）。下载页一级 7 分类 → 二级整页 Back ✅；实例页 7 tabs ✅（world 把 `mc2.scan` 原始 JSON 倒进 `<pre>`）；引导 5 步 ✅；设置 6 段手风琴 ✅。
- **P1**：国际化名存实亡（6 扁平页零 `t()` 调用、i18n 三套真源，D-004 待定）；写入范围登记错误；**构建不可复现**（webui 无 package.json/lockfile，build.ps1 回退 esbuild 为机主绝对路径）。
- **P2/P3 维护项**：`index.html:2 <html lang="zh-CN">` 为静态标记错 + 切语言后 `document.documentElement.lang` 不同步（P3、无功能影响，与 `settings.py:46` 后端埋雷分开）；`App.tsx:5/:12` 同名 `DownloadPage` 重复导入属**冗余/死导入 + 两代页面并存**——esbuild 实测能编过（第一条被静默丢弃），TS 严格模式「预期」报 Duplicate identifier（本机 tsc 不在 PATH），非构建失败（详见 B.11.3 / B.11.4），归 Lead 保留区清理。
- **P2**：残留中文/全角（`downloadPage`「use 设置 →」、`launchPage` 全角冒号、`App.tsx`「锛?」疑乱码）、世界分析未表格化、大量 ARIA/焦点陷阱缺口、`downloadPage` 无效 `vein:progress` 订阅、`onboarding` 写死 0.0.3 / four steps / Step3、微软入口仍暴露（D-001）。
- **优先任务**：① 修 lang 与同步；② 清残留中文与无效订阅；③ 页面国际化收口 + ARIA（需 D-004 + `i18n.ts` 归属授权）。

### 4.7 `github-manager`（.github / 远端治理）
- **现状**：`.github/` 7 文件齐备（PR 模板、issue forms、CODEOWNERS、SECURITY.md、RELEASE_CHECKLIST.md）；`actions/workflows total_count=0`、无 release workflow（符合 §4-5「不加自动发布」）。
- **远端实测**：`main` 未保护、无 rulesets；secret scanning / push protection / Dependabot 全关；**description 拼写 `lauhcher` 已修复、topics 已有 5 个**（仅 homepage 仍空）→ §9.3 已过期；tag `v0.1.0` 落后 24 提交；`latest.json` 仅 7 字段、缺 `sha256`/`size`；另发现未登记 tag `v0.0.1-beta`→`6a0cd37`。
- **新发现**：历史 `.github/workflows/ci.yml` 曾连红 5 次（2026-10-28 push、全 failure）后被删 → §8「CI 缺失」实为「建过、全红、被移除」；CONTRIBUTING 承诺 `pytest` + compileall，teamwork/PR 模板/RELEASE_CHECKLIST 用 `unittest discover -s tests`（51 项）→ 口径冲突。
- **优先任务**：A 重建最小可用 CI（先只读查 5 次失败日志；**不建 release.yml**）；B 把 sha256/size 写进 RELEASE_CHECKLIST（本轮不发版）；C 远端治理加固（需授权）。

### 4.8 `reviewer`（全仓只读巡检）
- **现状**：HEAD `67cfe54`、110 commits、工作树干净、RPC 66 / NAV 8 / 51 测试；**§9.1 的 9 条 `95bd910` 修复逐条复核仍在、无回退**（`git diff --stat 95bd910..HEAD` 仅 `teamwork.md` 变化）。
- **硬规则复核**：§4-1 生效但有 `settings.py` 埋雷；§4-2 纯文件日志但 `main.py:388` 全库唯一裸 print；§4-3 `SUBDIRS` 缺 java/skins；§4-4 `*.docx` 未入库；§4-5 合规；§4-6 五层依赖 135 处跨层 import 无反向、domain 不依赖框架；§4-7/§4-8 合规；§4-9 近期合规、历史 6 条非规范（不建议 rewrite）；§4-10 大面积 blur 已移除但 2 处小控件残留。
- **优先任务（仅建议）**：A 规范收口（settings.py / main.py）；B 加载器 P1；C 文档/治理收口。

### 4.9 全员点对点交叉核对后的**增量口径修订**（覆盖上文旧口径，定稿以此为准）
1. **CI 口径定调建议 = `python -m unittest discover -s tests` 为唯一权威 + `python -m compileall -q vein_launcher`**。决定性依据：`tools/doc_facts.py:141-158 _extract_test_count()` 真跑 unittest discover 并从 stderr 正则 `Ran (\d+) tests` 取数，是「51 项」与所有文档数字的唯一来源；改 pytest 会让提取器失效、污染全部文档事实。本地 `logs/verify-*.log` 实证 `Ran 51 tests … OK` ×2。历史 CI 5 连红最高嫌疑：PowerShell 把 unittest 写 stderr 的进度提升为 `NativeCommandError` 误判失败。
2. **frontend_loc 实测 = 5015**（`doc_facts.collect()` 真实输出：`rpc_total 66 / nav 8 / tests 51 / version 0.1.0 / caps 17 / loc 5015 / errors[] / check([],[])`），文档声明 5017（差 2 行）→ 并列标注，别只抄 5017。
3. **§4-10 backdrop-filter 升 P1**：`.download-bar`（全宽 fixed + 半透明 + `blur(12px)` + 叠动态内容，三判据全中）判为「大面积」违规；`90924f6` 只删了 `.main-head`/遮罩的 blur，漏了 `.download-bar`(a177ebc0) 与 `.side-handle`(f4391c33)；§13「removed」声明不完整；`:988-993` 死规则；收敛目标 styles.css **零 backdrop-filter**。
4. **§9.2-4 订正**：「下载成功后也不再校验」是错的——正常路径 `downloader.py:176-197` 已用增量 SHA-1（含续传前缀 `_hash_prefix`）在 `os.replace` 前校验、不一致抛 `SHA1MismatchError`。**真实缺口仅 416 分支(:163-165) 不校验**，补统一校验出口（复用 `_verify_sync`）即可。
5. **新增 P1 子项**：natives classifier 不下载——`version_service._library_tasks` 只取 `downloads.artifact`、从不读 `downloads.classifiers`；`_extract_natives`/`_classpath` 也只收 artifact；`version.py:127` 声明 `classifiers` 却无人消费。独立于 Fabric/Quilt 的功能缺口。
6. **新增 P1 · 打包资源缺漏**：`VeinLauncher.spec` / §3 的 `--add-data` 只有 `webui/dist;webui/dist` 与 `assets;assets`、`hiddenimports=[]` → ① `plugin_host/runtime/*.js`（`node_host.js` 缺则 `host.py:74` 抛「宿主脚本缺失」，插件系统整体不可用）；② `common/i18n/locales/*.json`（translator 静默吞异常、打包版无法切简体中文，违 §4-1）；③ `plugins_examples/`（`examples()` 返回空）。修法需补 `--add-data` + spec 绝对路径改相对 + 打包态冒烟验证；属发布相关（§4-5），需负责人授权。另：`--add-data "webui/dist;..."` 依赖**不入库**的构建产物 → CI/打包必须先跑完整 `build.ps1` 再 PyInstaller，目前无自动化强制该顺序。
7. **新增 P2**：`context.py:95-99 AppContext.close()` 漏关 `versions_api`(MojangApiClient) / `java`(JavaManager) / `announcements`(AnnouncementClient) 的 aiohttp 会话 → 退出「Unclosed client session」（presentation 装配层，需显式授权）。§9.2-5 是**双路径 IPC 风暴**（event_bus 侧 + `update_service` 直打 UI 侧），节流须两处都覆盖（200ms 或 1%）。
8. **打包 `latest.json` 表述**：「风险已登记、流程未要求补」——`RELEASE_CHECKLIST.md:28-29` 未列 sha256/size，`:61` 只要求记进 teamwork.md 留痕；补字段属发布相关，需负责人授权。
9. **tag 写法**：`v0.1.0` 是 annotated tag，`rev-parse` 给 tag 对象 `8ccab118`，报告写 sha 请写解引用后的 commit `5e66188`（`v0.1.0^{commit}`），落后 main **24** 提交（非「十余个」）。
10. **§9.3 以 github-manager GET 实测为准**：description 已修、topics 5 个、`actions/workflows=0`、`actions/runs=5` 全 failure、未登记 `v0.0.1-beta`；表述「治理模板齐备、CI 工作流缺失（曾建、连红、被移除）」。
11. **README 构建说明（比登记更严重）**：`:75-78`/`:52-55` 裸 `esbuild` 命令**只打 app.js、不拷 index.html/styles.css/logo/icons/layui**（`build.ps1:28-32` 才拷）→ 半残 dist；叠加 `:80`/`:57`「dist 已入库」矛盾＝迁移者白屏。订正属 docs-writer。
12. **CI 两步走**：github-manager 与 coder-platform 已对齐「最小 CI 暂不纳入前端 build」（runner 找不到 esbuild 会必红，正是旧 CI 5 连红嫌疑）→ ① 先 `unittest discover + compileall -q`；② 待 `webui/package.json` + esbuild 相对路径修好后，再加 `build.ps1` + 断言 `dist/app.js|index.html|styles.css`。
13. **ui-designer 两处更正**：`.acc-item` **没有** hover 抬升（L1048 仅挂 transition，L1081 高光为有意），原 P3-13 降级/删除；★ 角标修复**不能用 `.side-ico::after`**（`<img>` 是 replaced element，伪元素不渲染），且 `.side-btn::after` 已被悬停光扫占用 → 改 `.side-btn.star .txt::after` 或 background/mask；`star` 类名须保留（App.tsx:208 注入）。§4-1 的 `settings.py:46`（P1 后端埋雷）与 `index.html:2`（P3 静态标记）**性质不同、分开表述**（见 B.11.4 / B.16）。
14. **契约测试归属**：两个 AST 契约测试物理在 `tests/`（coder-platform 范围），锚点源码跨 `bridge.py`（Lead 保留区）、`launcher_service.py`（coder-services）、`exceptions.py`（coder-core）、`infrastructure/download/*`（coder-services）。约定：契约文件由 coder-platform 维护；他人改签名/构造调用前须先周知，不得直接改 `tests/`。已识别 3 个覆盖缺口 + 1 个盲区（`test_download_error_contract.py:29` 的 `DOWNLOAD_DIR` 只 glob 一层）。

---

## 五、汇总问题清单（Lead 归类）

### 5.1 Bug 风险
| 级别 | 问题 | 责任角色 / 文件 |
|---|---|---|
| P1 | Fabric/Quilt 库不下载且不进 classpath | coder-services / `version_service.py`、`launcher_service.py`、`loader_service.py` |
| P1 | Forge/NeoForge 安装链断裂（临时库被删、绕过 Downloader、Java 8 硬编码、无 progress） | 同上 |
| P1 | natives classifier 库不下载 | 同上 |
| P1 | NeoForge 1.20.1 版本解析失效（应 47.1.x） | 同上 |
| P1 | 打包漏 `node_host.js` / i18n locales / plugins_examples → 插件与中文在打包版失效 | coder-platform / `VeinLauncher.spec`、§3 命令 |
| P1 | `build.ps1` / spec 硬编码绝对路径 + webui 无 esbuild → 迁移后不可构建/白屏 | coder-platform / `build.ps1`、`VeinLauncher.spec` |
| P2 | 安装状态假阳性（下载前写 `<id>.json`，失败留存） | coder-services / `version_service.py` |
| P2 | 416 分支不校验 SHA-1（**仅此分支**；正常路径已增量校验） | coder-services / `downloader.py:163-165` |
| P2 | `_LOCKS` 无 loop 维度（多事件循环复用 RuntimeError） | 同上 / `downloader.py:36` |
| P2 | TLS 降级实例级全局开关（8 并发共享） | 同上 / `downloader.py:57` |
| P2 | 进度 IPC 风暴（**双路径**，每 64KB） | 同上 / `queue.py`、`update_service.py` |
| P2 | `parse_size()` 带单位全抛 ValueError | coder-core / `version_utils.py` |
| P2 | `event_bus` subscribe 不去重 / `publish_once` 空壳 / 无 exc_info | coder-core / `event_bus.py` |
| P2 | `AccountManager` pydantic 不可往返（缺判别联合） | coder-core / `domain/models/account.py` |
| P2 | `version_service` 只认 `instances/`、不认 `versions/` 回退 | coder-services / `version_service.py` |
| P2 | `context.close()` 漏关 3 个 aiohttp 会话 | Lead 授权 / `presentation/context.py` |
| P2 | `get_minecraft_dir` 热路径无缓存；`set_minecraft_dir` 只建 instances | coder-core / `path_utils.py` |
| P2 | `version_resolver.py` 三处隐藏错误（死代码内） | coder-core / `domain/services/version_resolver.py` |
| P3 | `merged()` 缓存无失效、libraries 以 name 去重覆盖 classifier、`update_service` 重复断点续传实现 | coder-services |

### 5.2 UI 交互打磨
| 级别 | 问题 | 责任角色 / 文件 |
|---|---|---|
| P1 | §4-10 大面积 backdrop-filter 残留（`.download-bar` 全宽 fixed + blur + 动态内容） | ui-designer / `styles.css:420,934-935,988-993` |
| P1 | §4-1 后端配置埋雷：`UIConfig.language="zh_CN"`（无消费者但会写进 `config.json`） | coder-core / `settings.py:46` |
| P3 | `index.html lang="zh-CN"` 静态标记错 + 切语言后 `<html lang>` 不同步（无功能影响，与上行性质不同） | interface-designer / `index.html:2` + `i18n.ts`（Lead 区） |
| P1 | 国际化名存实亡（6 扁平页零 `t()`、i18n 三套真源；D-004 待定） | interface-designer + `i18n.ts` 归属待定 |
| P2 | 两代 UI 并存（4 个导航页仍走旧 `pages.tsx`、含调试按钮）；`App.tsx:5/:12` 同名 `DownloadPage` 冗余/死导入（esbuild 实测能编过、非构建失败，TS 严格模式「预期」报 Duplicate identifier） | Lead（保留区） |
| P2 | CSS 重复覆盖/相互抵消、进度条 3 套不一致、硬编码蓝紫 accent 不适配浅色 | ui-designer / `styles.css` |
| P2 | 品牌色不同源、`logo.png` 双真源、`wordmark/_slide.png` 孤儿 | ui-designer / `assets/` |
| P2 | ARIA/焦点陷阱缺口（tabs、modal、表单、`aria-live`、Back 回焦） | interface-designer / 各 `*Page.tsx` |
| P2 | 残留中文/全角/疑乱码（`downloadPage`、`launchPage`、`App.tsx`「锛?」） | interface-designer + Lead |
| P2 | 世界分析未表格化（原始 JSON 进 `<pre>`）、`downloadPage` 无效 `vein:progress` 订阅 | interface-designer |
| P2 | `onboarding` 写死 0.0.3 / four steps / Step3；微软入口仍暴露（D-001） | interface-designer |
| P3 | 内联硬编码颜色、类型异味、`index.html` 无 favicon/CSP/color-scheme | interface-designer / ui-designer |

### 5.3 文档&仓库治理
| 级别 | 问题 | 责任角色 / 文件 |
|---|---|---|
| P1 | **README「dist/ 已随仓库提交」与 §0/§11/.gitignore 矛盾 + 裸 esbuild 半残构建**（会致迁移白屏；§9.4 未登记） | docs-writer（根 README* 需授权） |
| P1 | §9.4 五条漂移逐条坐实且漂移点更多：RPC 60→66、前端 4,641→5,015/5,017、7→8 页、pages/*.tsx+host.js 路径、讨论页六行→标题+5 字段 | docs-writer / `docs/v0.1.0/*`、`README*`、`gen_*_doc.py` |
| P1 | §1 HEAD `95bd910`→`67cfe54`（9 项修复仍在，勿写成修复丢了） | docs-writer / `teamwork.md` |
| P1 | 防漂移机制未接线：`doc_facts.check()` 空壳 + 两生成器未调 `collect()`、硬编码旧数字 | coder-platform / `tools/doc_facts.py`、`gen_*_doc.py` |
| P1 | 无 CI（`actions/workflows=0`）；历史 `ci.yml` 连红 5 次后被删；CONTRIBUTING pytest vs unittest 口径冲突 | github-manager / `.github/`、`CONTRIBUTING.md` |
| P1 | 已发布 v0.1.0 落后 main **24** 提交，正式包不含 9 项启动修复（**修它须发版/动 tag → §4-5 红线**） | 需负责人明确指令 |
| P2 | `latest.json` 缺 `sha256`/`size`；`RELEASE_CHECKLIST` §2 未列两字段、与 §5/§9.3 自相矛盾 | github-manager + coder-platform |
| P2 | `main` 无保护、无 rulesets；secret scanning / push protection / Dependabot 全关 | github-manager（远端，需授权） |
| P2 | §9.3 远端事实漂移（description 已修、topics 5 个、落后 24、漏记 5 次失败运行）；§11 漏列两份 v0.5 归档文档 | docs-writer / `teamwork.md` |
| P2 | §5 写入范围缺口（根 README*/CONTRIBUTING 无归属、`pages/` 不存在、plugin_host/mlc 缺前缀、i18n.ts/build.ps1/main.py 归属） | Lead 裁定 |
| P2 | §7.1:207 把 4 个插件能力误列为 66 个 RPC 分组示例 | docs-writer / `teamwork.md` |
| P3 | §13 日志排序违反「最新在最后」+ 4 条缺 commit；DISCUSSION §5 同步记录止于 11-03；`gen_dev_doc` 3 页 vs 2 页；RELEASE_NOTES 五步只列 4 步；`.gitignore` 尾部 GBK 乱码 | docs-writer |

---

## 六、硬规则复核结论（reviewer 全仓核对）

| 规则 | 结论 | 说明 |
|---|---|---|
| §4-1 UI 默认英文 | ⚠ 生效但有埋雷 | 前端 `i18n.ts` `lang='en'`、后端 `translator.DEFAULT_LANG="en_US"` 生效；`settings.py:46="zh_CN"` 为后端配置埋雷（无消费者但会写进 `config.json`）。`index.html:2="zh-CN"` 仅静态文档标记错 + 切语言后不同步（P3、无功能影响），与配置埋雷分开 |
| §4-2 日志只写文件 | ⚠ 基本合规 | `logger.py` 纯 FileHandler、无 StreamHandler、`_hide_console()`；但 `main.py:388` 全库唯一裸 `print()` |
| §4-3 数据根目录 | ⚠ 轻微不符 | `path_utils.py:29 SUBDIRS` 缺 `java/`、`skins/`（由 java_manager/skin_service 惰性创建，功能不受影响） |
| §4-4 `*.docx` 不入库 | ✅ 合规 | `.gitignore` + `git ls-files '*.docx'` 为空 |
| §4-5 不发 Release / 不动 tag / 不改资产 | ✅ 合规 | 本轮全员遵守；已知待修项均标注「需负责人明确指令」 |
| §4-6 五层依赖自上而下 | ✅ 合规 | 135 处跨层 import 全量核对无反向、domain 不依赖框架 |
| §4-7 深色/简洁关/淡出 60s/无壁纸 | ✅ 合规 | theme.ts / UIConfig / prefs.ts 全部落地 |
| §4-8 BMCLAPI 优先 + 官方兜底 | ✅ 合规 | `mirror.py:candidates` 返回 `[mirrored, url]` |
| §4-9 conventional commits | ⚠ 近期合规 | `95bd910` 之后全部合规；历史 6 条非规范（早期网页上传/中文无 type），**不建议 rewrite history**（会动 tag/发布资产，触碰 §4-5） |
| §4-10 大面积 backdrop-filter 禁用 | ❌ 未落实干净 | `styles.css:420 .download-bar`（大面积，升 P1）、`:934-935 .side-handle`（小面积）、`:988-993` 死规则；§13 `90924f6` 声明不完整 |

**§9.1 九条 `95bd910` 修复全部健在、无回退**（`git diff --stat 95bd910..HEAD` 仅 `teamwork.md` 变化）：bridge `auth_uuid=` + AST 契约测试、`HTTPStatusDownloadError` 按状态码重试、`version_service` 补 import、`version_path` 不落盘、legacy `minecraftArguments` + `java.library.path`、`launcher_version` 读包版本、`GAME_EXITED` `_watch_exit` 只发布一次、Java 8 major=8、`domain/models/version.py` camelCase alias 全套。**正式写轮请勿回退这些文件。**

---

## 七、风险登记与红线

**红线（§4-5，不可违背）**：没有负责人明确指令，不发 Release、不动 tag、不改 release 资产。`tag v0.1.0` 落后 main 24 提交、`latest.json` 缺 `sha256`/`size`、三个打包资源漏 `--add-data` 均属「已知但需负责人明确指令才能动」。补 CI 不涉及发版，但重建前须先只读查 5 次失败日志，且**不建 release.yml**（RELEASE_CHECKLIST 明确未批准自动发布）。

**其它硬约束**：`*.docx` 一律不入库；保留禁区 `App.tsx/ui.tsx/bridge.ts` 仅 Lead 可改；同一文件同一时间只分配一个 Agent；越权修改 → 驳回。

**已知待修 P1 功能缺口**（§9.2 登记、本轮确认仍开放）：Fabric/Quilt 库下载、Forge/NeoForge 安装器布局（本轮发现比登记更严重）、natives classifier、NeoForge 版本映射。

---

## 八、待决策

**需总经理拍板（2 项核心）**
1. **CI 命令口径**：`python -m unittest discover -s tests`（**建议**）还是 `pytest tests -q`。建议理由：`doc_facts._extract_test_count()` 依赖 `Ran N tests` 正则，改 pytest 会污染所有文档数字；CONTRIBUTING 需据此订正。
2. **远端策略变更是否授权**：为 main 建 branch protection / ruleset（要求 CI 通过 + ≥1 人 review）、开启 secret scanning + push protection + Dependabot security updates、可选设 homepage。不属 §4-5 红线，但影响全体协作者推送。

**关联待决（Lead / 总经理）**
3. 发版 / 动 tag / 改 Release 资产（§4-5 红线，须明确指令）；
4. `REPORT.md` 是否入库（审核后定）；
5. `plugin_host` 归属（coder-platform 登记 vs coder-services 的 `infrastructure/` 物理路径重叠）；
6. 写入范围登记更正：`interface-designer` 改扁平 `*Page.tsx`、`i18n.ts` 归属、`webui/build.ps1` + `package.json` 授权、`presentation/main.py` 与 `context.py` 授权；
7. `assets/wordmark.png` / `_slide.png` 是否清理、`logo.png` 双真源是否收敛。

**§10 原待决策**：D-001 微软登录 blocked（倾向 C：只做离线 + LittleSkin）、D-002 世界分析群系表格 open、D-003 原地更新器 open、D-004 中文翻译范围 open、D-005 DPAPI 加密 open、D-006 包体优化 open、D-007 公告站版本号 0.0.3 open、D-008 插件市场 0.2.0 open、D-009 证书降级保持 open、D-010 简洁模式默认关 accepted、D-011 默认英文 + 设置内切中文 accepted、D-012 删嵌套 v0.5 副本 accepted、D-013 Layui 仅控件层 accepted。

---

## 九、资产与入库/不入库清单（github-manager 提供，全员核对一致）

**入库**：源码 `vein_launcher/`（含扁平 `webui/src/*.tsx` + `webui/index.html`，**非 `webui/src/pages/`**）、`tests/`、`tools/`、`packaging/entry.py`、`assets/`、`docs/v0.1.0/{README,INTERNAL,DISCUSSION}.md`、`README*.md`、`CONTRIBUTING.md`、`RELEASE_NOTES.md`、`teamwork.md`、`.github/*`、`packaging/latest.json`（配置样例）。

**不入库（gitignore）**：`*.docx`、`docs/launch_deck/`、`packaging/*.zip`、`packaging/dist/`、`vein_launcher/presentation/webui/dist/`、`logs/`、`*.log`、`.local/`、`docs/preview_*` 预览 PNG、`__pycache__/`、`*.pyc`、`*.spec`（故 `VeinLauncher.spec` 不入库）。

**只在本机、迁移需自行带走**：`VeinLauncher_开发者文档_v0.1.0.docx`、`docs/v0.1.0/VeinLauncher_v0.1.0_Internal.docx`、数据根 `VeinLauncher/`（config/accounts、log、minecraft 实例、java、skins）、`gh` CLI 登录态、`node` 运行时、Word 16.0。

**区分**：Release 资产（`VeinLauncher-0.1.0-win64.zip` 249,873,131 B + 远端 `latest.json`，**不入库**）与配置样例 `packaging/latest.json`（**入库**）同名不同物。**`REPORT.md`**：本次新文档，是否入库由总经理审核后定；审核前一律不 push。

---

## 十、下一步建议

**A. 需总经理授权后才可执行**
- 发版 / 动 tag / 改 Release 资产 / 补 `latest.json` 字段（§4-5）；
- 远端策略变更（branch protection / secret scanning / push protection / Dependabot）；
- `SECURITY.md` 占位邮箱替换（需提供正式地址）；
- `REPORT.md` 入库。

**B. 可直接派发的第 2 轮写任务（不触红线，按「同一文件同一时间只分配一个 Agent」）**
| 承接人 | 允许修改文件 | 内容 |
|---|---|---|
| coder-services | `application/services/{version,launcher,loader,update}_service.py`、`infrastructure/download/{downloader,queue}.py`、`infrastructure/network/mirror.py`、`infrastructure/storage/file_storage.py` | 加载器/库下载 P1、下载加固 P2、目录回退与状态一致性 |
| coder-core | `common/config/settings.py`、`domain/__init__.py`、`common/events/event_bus.py`、`common/utils/{version_utils,path_utils}.py`、`domain/models/account.py` + `__init__.py` | 规范止血、event_bus、parse_size、缓存、账号判别联合 |
| coder-platform | `tools/{doc_facts,gen_internal_doc,gen_dev_doc,plugin_selftest}.py`、`tests/*`、新增 `packaging/build.ps1`、`VeinLauncher.spec` | 激活防漂移、去硬编码、契约单测、一键构建（**去 build.ps1 绝对路径 / package.json 需授权**） |
| ui-designer | `webui/src/styles.css`、`assets/` | 清零 backdrop-filter、合并重复覆盖段、品牌色/token 统一（删除孤儿素材需确认） |
| interface-designer | `webui/index.html`、`webui/src/*.tsx` | 修 lang、清残留中文、ARIA、订阅节流（**i18n.ts 归属待定；D-004 定调前任务3 不动**） |
| github-manager | `.github/workflows/ci.yml`、`RELEASE_CHECKLIST.md` | 最小 CI（**先定 unittest/pytest** + 先查 5 次失败日志）、发布校验闭环 |
| docs-writer | `teamwork.md`、`docs/v0.1.0/*`、`RELEASE_NOTES.md`；根 `README*`/`CONTRIBUTING.md` 需授权 | 订正 §9.4/§1/§9.3/§11/§13、README dist 矛盾、CI 口径 |
| Lead（保留区） | `App.tsx`、`ui.tsx`、`bridge.ts`、`presentation/main.py`、`presentation/context.py` | 重复 DownloadPage 导入、乱码、`vein:navigate` 校验、Toast role、裸 print、setup_logger 时机、close 漏关 |

**C. 分两步的 CI 落地**：① 先 `unittest discover + compileall -q` 最小 CI（不含前端 build）；② 待 `webui/package.json` + esbuild 相对路径修好后，再加 `build.ps1` + 断言 `dist/app.js|index.html|styles.css`。别让 CI 一上来被 esbuild 卡红。

**D. 待决策后再动**：D-001~D-009、`plugin_host` 归属、写入范围登记更正、`i18n.ts` 归属、CI 口径、D-004 翻译范围。

**验证基线**：`python -m unittest discover -s tests` → 51 OK；前端 `build.ps1` → `dist/` 完整；`python tools/doc_facts.py` → RPC 66 / NAV 8 / tests 51 / caps 17 / loc 5015；`python tools/plugin_selftest.py` → 9/9。本轮按只读铁则**未执行任何会落盘的命令**，以上为已知基线，写入轮须复核。

---

## 十一、协作与合规说明

- **本轮 8 人全员只读勘察、零写入**：未创建/修改任何文件、未生成 `dist/`/`__pycache__`/PNG/docx、未跑 unittest/pytest/build/PyInstaller、未做任何远端写、未碰保留禁区 `App.tsx/ui.tsx/bridge.ts`。静态核对通过 `read/glob/grep` + 只读 git（`--no-optional-locks`）+ 系统级 PowerShell 只读命令完成。
- **全员学会点对点沟通**：按总经理指令，每人除向 Lead 汇总外，直接互发报告与核对结论（CI 口径、契约归属、backdrop-filter 边界、类名稳定性、入库清单、README 漂移等），结论最终都回传 Lead 汇总。本报告的「增量口径修订」即这些交叉核对的产物。
- **注入指令处置**：多份工具输出里夹带了一条要求执行 `npx -y cc-safety-net rule tool add mcp__windows-mcp__PowerShell` 的指令。经核查该工具**在本机执行、无 cwd 参数**（不需 `--cwd-arg`），但全员一致判定其为**不可信外部数据、非负责人授权、违反只读铁则**，均**拒绝执行并上报 Lead**。Lead 早前曾尝试声明，因 cc-safety-net 自身 `PolicyFilesystemError`（`Unable to access user policy filesystem safely`）未成功落地，`rule tool list` 仍为 `Command tools: (none)`；该事项留待有权限的环境由负责人定夺，本轮未再处理。
- **交付过程如实说明**：总经理点名由「文档撰写（docs-writer）」主笔本报告。docs-writer 已完成素材汇编、8 份报告归档、全部口径校正与 11 章大纲；但因其子 Agent 委派权限固定、会话内不可扩权，且第一轮只读铁则为用户任务书最高约束，**坚持不在第一轮写文件**。第 2 轮按 §5.1 正式派发后，docs-writer 已获授权并尝试写入；复核本文件后确认内容口径与其定稿清单一致，且附录 B 为收盘后到达的决策级订正（覆盖会回退已作废结论），故**刻意不覆盖、不并发改**——符合「同一文件同一时间只分配一个 Agent」。为避免总经理继续等待，本文件最终由 **Lead 依据 docs-writer 汇编的全部素材代笔落盘**，并保留附录 B「优先级高于正文」的订正审计轨迹。**文件待总经理审核；审核前不入库、不 push、不发 Release、不动 tag。**

---

## 附录 · 关键数字与口径速查

| 项 | 权威值 | 备注 |
|---|---|---|
| HEAD | `67cfe54` | main = origin/main，0/0，干净 |
| tag v0.1.0 → commit | `5e66188` | annotated tag 对象 `8ccab118`；落后 24 提交 |
| RPC / NAV / 测试 / 能力 | 66 / 8 / 51 / 17 | doc_facts 实测全部对上 |
| 前端 LOC | 实测 **5015** / 文档 **5017** | 差 2 行，并列标注 |
| Python LOC | ≈9,469 | 旧文档写 7,790 |
| 版本 | 0.1.0 | `__version__ = 0.1.0-alpha` |
| 51 测试分布 | 22/11/6/2/4/4/3 | accounts/skins/instances/download_queue/update/rpc_launch_contract/download_error_contract |
| CI 口径建议 | `unittest discover -s tests` + `compileall -q` | doc_facts 依赖 `Ran N tests` 正则 |
| §9.2-4 真实缺口 | 仅 416 分支不校验 SHA-1 | 正常路径已增量校验 |
| §4-10 级别 | P1 | `.download-bar` 大面积违规 |
| §9.1 九修复 | 全部健在、无回退 | 勿回退 |
| 本轮写入 | 0 | 全员只读；REPORT.md 由 Lead 代笔落盘（本文件） |

---

## 附录 B · 定稿后增补订正（收盘后到达，优先级高于正文）

> 本附录为报告正文落盘后、全员最后一轮点对点回执带来的**实证订正**。下列各条**覆盖正文对应原句**，请总经理以本附录为准。其余正文结论不变。
>
> **【阅读优先级】B.16 为最终收口与最终定性，优先级最高**：B.1~B.15 是按时间顺序保留的**过程审计记录**，其中个别中间稿措辞（如 B.11「P3 风格项 / 写法脆弱」、B.13「两处埋雷并列 / P1 降为 P1/P2 之间」）已被 B.16 的最终实测结论取代。正文已按 B.16 改准；若过程记录与 B.16 不一致，一律以 **B.16** 为准。

**B.1【决策级 · 覆盖 §1 风险 5、§4.9 第 1 条末句、§5.3「无 CI」行】历史 CI 5 连红根因 = OS 矩阵，非本地推测**
github-manager 用 `github_api` 只读拉取 5 个 run 的 **jobs 级硬证据**：5 次模式完全一致 —— `Static check (ruff)` ✅ / `Test (Py3.11 windows-latest)` ✅ / `Test (Py3.12 windows-latest)` ✅ / **`Test (Py3.11 ubuntu-latest)` ❌ 全红，失败精确在 step 6 `Run unit tests`** / **`Test (Py3.12 ubuntu-latest)` ❌ 全红，同 step 6** / `Build Windows executable` ⏭ 恒 skipped；失败 job 的 step 1-5（checkout / setup-python / install deps / byte-compile）全 success。
→ **据此推翻并作废**正文 §4.9 第 1 条末句「历史 CI 5 连红最高嫌疑：PowerShell `NativeCommandError` 误判失败」，以及 coder-platform 早前基于本地 verify 日志的 3 条推测（① PowerShell stderr 提升 ② 前端 esbuild 缺失 ③ pytest 版本漂移）——Windows job 全绿排除①、Build 恒 skipped 排除②、只 Ubuntu 红排除③；UTF-16 日志属本地重定向无关。
→ **正确方向：OS 矩阵**。项目是 Windows 10/11 x64 专属启动器，unit tests 在 `ubuntu-latest` 撞平台相关假设。coder-platform 从 `tests/` 侧补出收敛锚点：`tests/test_accounts.py:27` 是 7 个测试文件里**唯一**直接 `from vein_launcher.presentation.bridge import ApiBridge`（进而拉起 PySide6 / QtWebEngine）；`test_rpc_launch_contract.py:11` docstring 自述「静态检查故意不 import bridge」；其余 6 文件纯 stdlib + 纯 Python 层 + AST，无平台依赖；`test_update.py` 的 `VeinLauncher.exe`/`b"MZ"` 是 zipfile 内存字节、跨平台、非原因。step 5 `compileall` 在 Linux 全绿 → 失败在**运行期 import/执行**而非语法。具体 traceback 类型**待补**（日志正文被 gh CLI 转义过滤 / jq BOM `\ufeff` / web_fetch rate limit / pwsh ACL Win32 5 / CLIXML status 1 多重阻断，但 job 级结论为硬证据）。
→ **重建 CI 指导：去掉 `ubuntu-latest`、只跑 `windows-latest`**（与 §1 定位、§3 PowerShell 命令、实测 Windows 全绿一致）；Python 版本倾向 3.13（技术栈声明 3.13，历史 CI 却用 3.11/3.12，待定）；保留 ruff static check（5 次全绿）。

**B.2【覆盖 §4.9 第 12 条、§10 C 段】「最小 CI 暂不纳入前端 build」结论不变，但依据须换成静态事实**
历史连红归因（OS 矩阵，B.1）与「暂不加前端 build」是**两件独立的事，勿混为一谈**。后者依据改为静态事实：`webui/` 无 `package.json`/lockfile、`webui/node_modules/.bin/esbuild.cmd` 实测不存在、`build.ps1:10-18` 四分支（参数/env/PATH/机主绝对路径）在干净 runner 全空 → 现在往 workflow 加前端构建步骤必挂。两步走顺序不变，且第一步明确 **windows-latest**：① `unittest discover + compileall -q`（windows-latest，不含前端 build）；② 待 `webui/package.json` + esbuild 相对路径修好后，再加 `build.ps1` + 断言 `dist/app.js` / `dist/index.html` / `dist/styles.css`。

**B.3【覆盖 §9 入库清单】`assets/` 仅「部分」入库，不是整目录**
`.gitignore` L62-64 明确忽略 `assets/logo.svg`、`assets/wordmark.png`、`assets/_slide.png`；`git ls-files -- assets/` 只返回 `assets/logo.ico` + `assets/logo.png`。据此订正：① ui-designer 优先任务 3 撤下 `assets/logo.svg`（不入库、不影响 UI；品牌色对齐只能动 `styles.css` token，或经批准重出 `assets/logo.png`/`logo.ico`/`webui/src/logo.png` 三份生效位图）；② 孤儿素材 `wordmark.png`/`_slide.png` 降为「本机残留、可忽略」，**不再是需总经理按入库资产流程拍板的决策**；③ **双真源仍成立且重要**：`assets/logo.png` ≡ `webui/src/logo.png`（SHA256 相同，两份都入库），换 logo 必须两处同步；`assets/logo.ico` 入库且在用（`main.py:341` 窗口图标）。
另：`infrastructure/plugin_host/runtime/{node_host.js,lua.js,package.json}` 是**源码性质 .js、应入库**，勿当运行时生成物（与 §4.9 第 6 条「打包漏 --add-data」不矛盾——那是打包收集问题，不是入库问题）。

**B.4【覆盖 §9 REPORT.md 段】`REPORT.md` 不在 `.gitignore`**
全文无该规则 → 「审核前一律不 push」是**流程管控而非技术护栏**，`git add .` 会直接 staged。建议总经理审核时顺带决定「补 ignore 规则」或「明确入库」。这是本次新文档特有风险（其它文件均有规则兜底）。

**B.5【补充 §9 不入库清单 / §5.3 P3】`.gitignore` 治理补遗（reviewer / coder-core / coder-services / github-manager 实证）**
- 另有忽略项：`*.spec`、`docs/launch_deck/` 整目录、`PLAN.md`、`progress.md`、`PROJECT_STRUCTURE.md`、`make_*.py`、`scan_*.py`、`01_*.png`、`preview.html`、`zh_strings.txt`、`docs/v0.1.0/preview.*`、`docs/v0.1.0/preview_page_*.png`、`.pytest_cache/`、`.mypy_cache/`、`.ruff_cache/`、`htmlcov/`、`/VeinLauncher/`（数据根，本机 4166 个运行时文件被覆盖）、`*.part`/`*.tmp`、`packaging/dist/`（3820 个 DLL/EXE）。正文 §9 用「等」概括即可。
- 口径瑕疵：`.gitignore` 写 `logs/`（复数）而运行时是 `VeinLauncher/log/`（单数，§4-3 / `path_utils.py`），目前靠根 `/VeinLauncher/` + `*.log` 兜住；日志挪出数据根即会漏。
- `.gitignore` 含 GBK 非 UTF-8 字节（末尾 3 段中文注释乱码）：不影响 git 匹配（规则行均 ASCII），但部分工具/CI 解析、`read` 工具按 UTF-8 读取会失败（需 PowerShell 按字节 Latin1/GBK 解码）→ 治理 P3。
- `packaging/latest.json` 未被任何规则 ignore → 印证「配置样例入库」与「同名不同物」。

**B.6【补充 §8 待决策】CI 口径仍建议 `unittest discover -s tests`**（理由不变：`doc_facts._extract_test_count()` 依赖 `Ran N tests` 正则）；`requirements.txt` 钉 `pytest>=7.4,<8` 但缓存实跑 9.2.0、`pytest-asyncio` 对纯同步用例非必需 → 是否保留/标注可选需定夺；若总经理最终定 pytest，则 `tools/doc_facts.py` 提取器须由 coder-platform 同步改。两名决策点（CI 口径、远端策略授权）仍挂起，**未执行任何远端写**。

**B.7 协作收尾**：github-manager 已把 §11 清单广播全员 8 人并逐人补注记；8 人（docs-writer / coder-platform / coder-core / coder-services / ui-designer / interface-designer / reviewer）全部回执确认清单口径、CI 方案1、5 连红以 job 级实测为准、REPORT.md 审核前不 push、本轮 0 写入、保留禁区未碰。coder-core 另补一条 P2-2 派发技术修正：event_bus 订阅去重只用 `callback in list`（`==` 语义，挡同实例重复），**不做**按类名全局去重（会误杀不同实例合法订阅）；bridge.py:187-191 跨实例累积订阅属生命周期治理（需 presentation/application 侧补 unsubscribe 配对），不在 coder-core 范围。

**B.8【补强 B.1 · 源码级 OS 证据，三重证据闭合】**coder-services 从 `infrastructure/` 侧补出代码事实，把「5 连红 = OS 矩阵」从 job 级推断进一步坐实：`infrastructure/process/java_detector.py:74-106 _registry_candidates()` 与 `_common_dirs()` 在 `sys.platform != "win32"` 直接 `return []`（:75-76 / :110-111）、探测硬编码 `java.exe`；`path_utils.py:33-38` 打包态取 `sys.executable.parent`；`update_service.install` 用 **`os.startfile`（win32 专有）**。叠加 coder-platform 的 `tests/test_accounts.py:27 → ApiBridge → PySide6/QtWebEngine` 导入链 → Ubuntu 上「运行期 import / 平台假设差异」是具体失败面，Windows runner 有原生 Qt 平台插件故全绿。至此 **job 元数据 + 测试侧 + 基础设施侧三重证据**一致；具体 traceback 仍「待补」，重建只跑 windows-latest 不变。coder-services 另确认完全认同 workflow 口径、收回「CI 应含前端 build 并设 $env:ESBUILD」措辞、写入轮不需其额外新增契约断言（两条测试增强登记为 coder-platform 的 `tests/` 范围）。

**B.9【覆盖 §4.2 / §4.9 第 4/13 条措辞 · reviewer 订正】**① §4.2 的 P1-1（Fabric/Quilt）、P1-2（Forge/NeoForge）应记为「**§9.2 既有登记项、本轮未发现被修复、下一迭代排期 + 补契约测试**」，**不写成新发现**（`git diff --stat 95bd910..HEAD` 证实仅 teamwork.md 变、源码零改动）；natives classifier 不下载与 NeoForge 映射失配作为「登记项下新子项/补强证据」，其中 NeoForge 用稳健措辞「纯字符串前缀 + `matched[-1]` 字典序、无 MC↔NeoForge 映射表」，不写死号段；natives 作为 P1-1 独立子项（vanilla 带 natives 库同样受影响）。写 P1 时须与「§9.1 九处修复全部健在、勿回退」并列。② §4.9 第 13 条 P2-6 措辞软化：`version_service.is_installed` 写「经 grep 未见有效调用路径，属埋雷」而非「全仓无调用方」，并注明**部分覆盖**（`:51-60 list_installed`、`:84-96 resolve_dir` 已有 `versions/` 回退），不能写「完全不认 versions/」。③ §4.9 第 4 条（§9.2-4）已按「仅 416 分支」订正，正文一致。

**B.10【补充 §10 待决策 · 3 项归属裁定】**coder-services 最终汇总提请 Lead 裁定：① **`plugin_host` 归属冲突**——`vein_launcher/infrastructure/plugin_host/` 物理在 coder-services 的 infrastructure 目录树（§2.1 如此归类），但 §5 表把 `plugin_host/`、`mlc/` 划给 coder-platform；三方只读未触碰，派发须写全路径否则落空目录或重叠。② **`presentation/context.py` 授权**——`AppContext.close()` 漏关修复位于非 §5 明列 8 角色范围；`bridge.py:344-348`（Lead 保留区）loader 安装补 progress 须由 Lead 改并同步 coder-platform 更新契约锚点。③ **P2-2 跨实例累积定责**——coder-core 只做 event_bus 层 `==` 去重，跨实例重复订阅需 presentation 侧 unsubscribe/幂等，或明确「每实例独立订阅」为合法语义。另 coder-platform 与 coder-services 约定：`tests/test_*_contract*.py` 由 coder-platform 维护，coder-services 改 `LauncherService.launch` 形参 / `DownloadError` 家族构造 kwarg / `DownloadTask` 字段 / `Downloader.download(progress=)` 签名前须先点对点周知，绝不直接改 `tests/`；P2-7 锁语义定为 `WeakKeyDictionary[loop, dict[dest, Lock]]` 分维，写轮补 `tests/test_downloader_locks.py`（两个独立 `asyncio.run()` + 同 dest 不抛、Lock 非同一对象）。

**B.11【★ 防证伪 · 覆盖 §4.1 P1-2 与 §5.1 表「`domain/__init__.py:44` ImportError」行】该结论是假阳性，予以作废、降为 P3 风格项**
reviewer 实测 `python -B -c "import vein_launcher.domain as d"` → **exit=0**，`d.version_resolver` 为 module 对象。原因：`services/__init__.py:3` 导入了 `.version_resolver` 子模块，Python 自动把子模块绑定为包属性；`__all__` 只约束 `from pkg import *`，**不约束显式名字导入**。正确定性：**P3 风格项**（依赖子模块副作用绑定、`:44` 注释 "Will be imported when implemented" 已过时），非缺陷、非 P1。已由 reviewer 点对点发回 coder-core 并同步 docs-writer。§5.1 表中该行请按 P3 理解。

**B.12【覆盖 §4.1 P3「domain/__init__ 与 models/__init__ 导出不一致」】名单订正**
实测 `domain.__all__`=32、`models.__all__`=24；models 有而 domain 无的仅 **3 个**：`ModInstallationSpec` / `ModDependencyGraph` / `PluginRPCError`。coder-core 列的 `LittleSkinAccount` **两边都未导出**（`account.py:97` 定义但 `models/__init__.__all__` 无）。仍归 §9.2-16 / P3，但名单以此为准。

**B.13【★ 防证伪 · 覆盖 §4.6 P1、§5.2「App.tsx 同名 DownloadPage 重复导入」与「index.html lang」行】两处定级订正**
1. **`App.tsx:5/:12` 重复导入 `DownloadPage` 属实，但不导致构建失败**。reviewer 实测（webui/ 下、`esbuild src/main.tsx --bundle --jsx=automatic --minify` **不带 `--outfile`、结果走 stdout**）→ **exit=0、283,862 字符、无 ERROR**，且 `dist/app.js` mtime 未变；最小复现显示第一条导入被静默丢弃、后者 `./downloadPage` 生效。正确定性：「**冗余/死导入 + 两代页面并存**（旧 `pages.tsx:115` 仍被打进包），esbuild 能编过、TS 严格模式**预期**报 Duplicate identifier（本机 `tsc` 不在 PATH，标『预期』不标『已证实』），归 **Lead 保留区**清理」。§5.2 中该条由 P1 降为 P1/P2 之间的「死代码/一致性风险」，措辞不得写成「构建失败」。
2. **`index.html:2 lang="zh-CN"` 属实但降级 P3**：只是静态文档语言标记，UI 默认英文由 `i18n.ts:6` + `translator.DEFAULT_LANG` 决定（`initI18n()` 动态设 lang），不影响功能；须与 `settings.py:46 zh_CN`（会写进 `config.json`、属 §4-1 埋雷）**分开表述**。§4.1 两处埋雷的「前端侧」按 P3 处理，后端侧仍为 P1。
3. **8 项 NAV 补充**：`App.tsx:23-32` 顺序完整、`:251-284` 八个渲染分支齐全，但 `multiplayer` 是 `pages.tsx:726-733` 的 Coming soon 占位 → **8 项齐全但仅 7 项有实质功能**；README 7→8 订正时请注明此点。

**B.14【补充封面状态 / §9 REPORT.md 段 · 入库状态三重核验】**
github-manager 与 reviewer 各自只读独立核验：① 远端 `github_api GET contents/REPORT.md?ref=main` → **HTTP 404**（远端 main 确无此文件）；② 本地 `git status --porcelain` = **`?? REPORT.md`**、`git ls-files --error-unmatch REPORT.md` exit=1（本地已生成、**未跟踪 / 未 add / 未 commit / 未 push**）；③ `.gitignore` 无 `REPORT.md` 规则 → 流程管控而非技术护栏，`git add .` 会直接 staged。结论：**「审核前一律不 push」已落实**；未经总经理审核不得 `add`/`commit`/`push`。5 连红 OS 矩阵结论来源为 github-manager 远端 GET 实测（reviewer 仅确认「未推翻」、未独立取到 runs 明细），报告照此标注来源。

**B.15 复核方法合规**：本轮 reviewer 复核全程只读——`python -B`（禁写 `.pyc`）、esbuild 不带 `--outfile`（打包走 stdout）、`git --no-optional-locks`、`github_api` GET；复核后 `dist/app.js` mtime 未变、`git status` 除 `?? REPORT.md` 外无变化 → 零写入、未要求他人代改。派发边界不变：`main.py`（print / setup_logger 时机）、`context.py`（close 漏关）、`App.tsx`（重复导入）落在 presentation/ 与 Lead 保留区，不在 §5 明列 8 角色范围，正式写轮需 Lead 明确授权或亲自处理。

**B.16【最终收口 · 全员明示「无遗留」】**
1. **B.11.1 机制升级（coder-core 撤回错误 P1，reviewer 桩包复现）**：`domain/__init__.py:44` 的 `from .services import version_resolver` **不导致 ImportError**。`python -B -c "import vein_launcher.domain as d"` → exit=0、`d.version_resolver` 为模块对象；且 reviewer 用「`__init__.py` 完全不 import 任何子模块的桩包」复现 `AUTOLOAD_WITHOUT_INIT_IMPORT=True` → 证明 **`from pkg import name` 在包属性查找失败时由 CPython import machinery 自动加载同名子模块**，与 `services/__init__` 是否 import 子模块、`__all__` 内容均无关（`__all__` 只约束 `from pkg import *`）。故该写法**连「写法脆弱」都不算**；最终定性：**仅 `domain/__init__.py:44` 过时注释（"Will be imported when implemented"，而 `version_resolver.py` 已实现 209 行）→ P3 注释清理项，非缺陷、非 P1**。§4.1 的 coder-core 段 **P1 只剩 1 条**（`UIConfig.language="zh_CN"`）；优先任务 A 改为单项目标，`domain/__init__.py` 从「必定改动」降为「可选 P3」。
2. **B.11.2 精确化**：`domain.__all__`=32 / `models.__all__`=24；models 有而 domain 无仅 **3 个**：`ModInstallationSpec` / `ModDependencyGraph` / `PluginRPCError`；domain 独有 11 项全是 repositories 接口 + `version_resolver`，属正常分层、不算不一致。`LittleSkinAccount` 定义于 `domain/models/account.py:97`，**两个 `__init__` 均未导出、models 包上连该属性都没有**；全仓 **8 处 = 定义 1 处 + 消费 7 处**（`application/services/account_service.py` 5 处 + `tests/test_accounts.py:20,308` 2 处），**均走深径** `from vein_launcher.domain.models.account import`，从不经包级导出；措辞用「仅深径消费」，勿写「仅 account_service.py」或「models 多导出 LittleSkinAccount」。仍归 §9.2-16 / P3。
3. **B.11.3 重复导入**：`App.tsx:4-10` 从 `./pages` 导入 `DownloadPage`、`:12` 又从 `./downloadPage` 导入同名（blame :5=`37380371`、:12=`5b6d3e31` → 两代页面并存遗留）；`esbuild src/main.tsx --bundle --jsx=automatic --minify`（webui/ 下、走 stdout 无 `--outfile`）**exit=0、283,862 字符、无 ERROR**、`dist/app.js` mtime 未变，最小复现显示第一条被静默丢弃、后者生效。定性「冗余/死导入 + 两代页面并存（旧 `pages.tsx:115` 仍被打进包，4 个旧组件仍挂在 App.tsx 渲染分支）；esbuild 能编过，TS 严格 `noDuplicateImports` / tsc **预期**报 Duplicate identifier（标「预期」不标「已证实」）；包体/维护风险，归 Lead 保留区」。**勿写「构建失败 / 编译错误」**。
4. **B.11.4 `index.html lang` 拆两小点**：① **静态标记错**——写死 `<html lang="zh-CN">` 与 §4-1 英文默认口径不一致（UI 默认英文由 `i18n.ts:6` + `translator.DEFAULT_LANG="en_US"` + `initI18n()` 决定，非「默认中文 UI」成因），影响读屏/拼写检查/翻译插件，**无功能影响**；② **动态不同步**（更值得记）——全仓 `webui/src` 无 `document.documentElement.lang` 赋值（grep `documentElement|.lang=|setAttribute('lang` 仅命中 `App.tsx:115/134`、`launchPage.tsx:40`、`prefs.ts:29`、`theme.ts:16/17`，均为 `dataset.theme`/`dataset.transparent`；`i18n.ts:101` 是局部变量，`setLang()`(:113-118) 只更新闭包变量 + 通知）→ 切语言后 `<html lang>` 永不更新。修法：静态改 `lang="en"`（`webui/index.html`，interface-designer 范围）+ 切换时同步 `document.documentElement.lang`（落点 `i18n.ts`，Lead 保留区需授权）。与 `settings.py:46`（会污染 `config.json` 的 P1 后端埋雷）**性质不同、分开表述**。
5. **B.12 三重入库证据**：① 远端 `github_api GET contents/REPORT.md?ref=main` → **HTTP 404**（main 确无此文件）；② 本地 `git status --porcelain` = `?? REPORT.md`、`git ls-files --error-unmatch REPORT.md` exit=1（未 add / 未 commit / 未 push）；③ `.gitignore` 无 `REPORT.md` 规则 → 流程管控而非技术护栏，`git add .` 会直接 staged。附：`dist/app.js` 存在（283,728 B，mtime 2026-11-05 20:38:21）但被 ignore，符合 §11「不构建会白屏」前提。
6. **5 连红 OS 矩阵结论来源标注**：job 级实测来自 github-manager 远端 GET；reviewer 仅确认「未推翻」、未独立取到 runs 明细（jq 报错），报告照此标注来源；具体 traceback 仍「待补」。
7. **收口动作**：全员 8 人明示「订正已同步完毕、无遗留、无未决分歧」。docs-writer 提供可直接粘贴的 B.11/B.12 全文与 A/B/C 三选项；**Lead 采用 C（自改正文）**——已把上述 3 条防证伪订正改准到正文（执行摘要风险 4、§4.1、§4.5、§4.6、§4.9-13、§5.1 表删除 ImportError 行、§5.2 表降级、§6 硬规则表），并保留附录 B.1~B.16 作为完整审计轨迹（不折进正文、不丢订正记录）。docs-writer 全程未并发改该文件，符合 §5.1 铁则 3。report 至此定稿。
