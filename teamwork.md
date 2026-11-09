# Teamwork Log — Vein Launcher 协作总账（可迁移）

> 目的：**这份文件 + 仓库 = 可在任意新环境/新会话接手本项目**。
> 上半部分是项目事实、团队分工、硬规则、当前状态与风险；底部是完整变更日志（最新在最后）。
> 任何改动前先读本文件，改动后必须追加一条日志。

---

## 0. 迁移三步（详细检查表见 §12）

1. `git clone https://github.com/zhanjhn-studio/vein_launcher.git`
2. `pip install -r requirements.txt` → `cd vein_launcher/presentation/webui && powershell -ExecutionPolicy Bypass -File build.ps1`
3. `python -m unittest discover -s tests`（应 51 项通过）→ `python -m vein_launcher.presentation.main`

> `webui/dist/` 被 gitignore，**不构建前端会白屏**。

---

## 1. 项目速览

| 项 | 值 |
|---|---|
| 名称 | Vein Launcher（VL） |
| 定位 | Minecraft Java 版启动器，Windows 10/11 x64，便携免安装 |
| 仓库 | github.com/zhanjhn-studio/vein_launcher（public，MIT） |
| 版本 | **0.5.0**（`vein_launcher/presentation/context.py` 的 `VERSION`；包内 `__version__ = 0.5.0`） |
| 当前 HEAD | `ccaa82c`（refactor(i18n): 汉化改用上游 i18nDom 词典，保留自定义主题色） |
| 发布 | tag `v0.1.0`（`5e66188`，**落后 main**）；资产 `VeinLauncher-0.1.0-win64.zip`（249,873,131 B）+ `latest.json` |
| 技术栈 | Python 3.13 · PySide6 6.12 + QWebEngine · React 19 + TypeScript（esbuild）· Layui 仅控件结构 · Node 18+（插件宿主）· aiohttp · pydantic v2 · PyInstaller onedir |
| 规模 | Python 70 个文件 ≈9,469 行 · 前端 17 个文件 5,017 行 · RPC 66 个方法（20 组）· 测试 51 项 |
| 包体 | onedir 615 MB；zip 238 MB（QtWebEngine 占主要体积） |

---

## 2. 代码地图

### 2.1 后端五层（依赖只能自上而下，跨层用 `event_bus`）

| 层 | 目录 | 职责 | 代表文件 |
|---|---|---|---|
| common | `vein_launcher/common/` | 事件总线、配置、日志、i18n、路径工具、异常 | `events/event_bus.py`、`config/settings.py`、`logging/logger.py`、`utils/path_utils.py`、`exceptions.py` |
| domain | `vein_launcher/domain/` | 模型与契约（不依赖框架） | `models/version.py`、`models/account.py`、`services/version_resolver.py` |
| infrastructure | `vein_launcher/infrastructure/` | 网络、下载、进程、NBT/MC2、存储、插件宿主 | `download/{downloader,queue,sha_checker}.py`、`network/{http_client,mirror,microsoft_auth,littleskin}.py`、`process/{game_process,java_detector,java_manager}.py`、`plugin_host/` |
| application | `vein_launcher/application/` | 业务编排 | `services/{version,launcher,loader,account,skin,instance,update,plugin,modpack,mlc}_service.py` |
| presentation | `vein_launcher/presentation/` | Qt 窗口、RPC 桥、全局热键、前端 | `main.py`（无边框窗口）、`bridge.py`（RPC handler）、`hotkeys.py`（Win32 全局热键）、`palette.py`（Ctrl+Alt+Q 速查小窗）、`context.py`（服务装配）、`webui/` |
| mlc | `vein_launcher/mlc/` | 游戏控制层与插件能力入口 | `service.py` |

### 2.2 前端（`vein_launcher/presentation/webui/src/`）

| 文件 | 作用 |
|---|---|
| `main.tsx` | 挂载入口：bridge / i18n / theme |
| `App.tsx` | hash 路由、侧栏、标题栏、公告、下载监控、引导（**Lead 保留区**） |
| `launchPage.tsx` | 启动页：公告、版本卡、启动面板、3 个快捷入口 |
| `downloadPage.tsx` | 一级分类 → 二级整页（Back 返回） |
| `skinsPage.tsx` | 账号列表、皮肤预览、导入 PNG、LittleSkin 公开库 |
| `instancePage.tsx` | 实例内容 tabs：mods / resourcepacks / shaderpacks / datapacks / modpacks / worlds / console |
| `settingsPage.tsx` | 外观（主题/语言/简洁模式/空闲淡出/壁纸）、账号、关于与更新 |
| `onboarding.tsx` | 5 步引导 |
| `ui.tsx` | LayuiProgress / LayuiCheckbox / RemoteIcon / LogPanel / Toast（**Lead 保留区**） |
| `bridge.ts` | JSON-RPC 封装 + 事件订阅（**Lead 保留区**） |
| `prefs.ts` / `theme.ts` / `i18n.ts` | 界面偏好、主题（默认深色）、中英文 |
| `styles.css` | 设计系统：token、组件、动效、无障碍（含末尾 v3 / v3.1 覆盖段） |
| `toolsPage.tsx` | 工具页：单卡「指令」，内含 构建器 / 快捷键 / 指令列表 三小节（默认收起） |
| `commandTree.ts` | 指令树：88 条 Java 指令 + 161 件物品 + 物品组件/实体 NBT/方块 NBT，684 前缀 / 6660 候选 |
| `accent.ts` | 自定义主色：hex→HSL→派生 5 个 CSS 变量（--accent / -2 / -soft / -glow / -faint） |
| `package.json` / `package-lock.json` | 前端构建清单（react 19 / react-dom / esbuild 0.28） |

一级导航 8 项：`launch / skins / download / plugins / mlc / multiplayer / settings / tools`（路由 `#/key`；`Toolbox` 已并入 `tools` 并删除）。

### 2.3 工具链（`tools/`）

| 脚本 | 用途 |
|---|---|
| `gen_internal_doc.py` | 内部 Word 文档（11 页：封面大 logo、每页页眉 logo、讨论页恰好 2 页）；输出 `docs/v0.1.0/VeinLauncher_v0.1.0_Internal.docx` |
| `gen_dev_doc.py` | 开发者 Word 文档（8 页：9 章 + 附录 A 帖子 API + A.1 落地建议 + 附录 B 团队记录 2 页）；输出 `VeinLauncher_开发者文档_v0.1.0.docx` |
| `ui_preview.py` | 离线预览真实前端（mock QWebChannel）→ PNG；`--expand` 看侧栏展开态 |
| `doc_facts.py` | 从代码提取事实（RPC 66 / NAV 8 / 测试 51 / 版本 / 插件能力 17 / 前端 LOC）；`check()` 尚为占位 |
| `teamlog.ps1` | ASCII 安全的日志追加助手 |
| `plugin_selftest.py` | 插件宿主自检 9/9 |

---

## 3. 命令速查

```powershell
# 依赖
pip install -r requirements.txt

# 运行（开发态）
python -m vein_launcher.presentation.main

# 前端构建（dist/ 被 gitignore，必须构建）
cd vein_launcher/presentation/webui
powershell -ExecutionPolicy Bypass -File build.ps1

# 测试（当前 51 项）
python -m unittest discover -s tests

# 语法检查
python -m py_compile vein_launcher/presentation/bridge.py

# UI 离线预览（不占桌面，输出 PNG）
python tools/ui_preview.py launch docs/preview_launch.png
python tools/ui_preview.py launch docs/preview_expanded.png --expand

# 文档（*.docx 不入库）
python tools/gen_internal_doc.py
python tools/gen_dev_doc.py

# 代码事实（文档防漂移）
python tools/doc_facts.py

# 打包（PyInstaller onedir）
python -m PyInstaller --noconfirm --clean --windowed --name VeinLauncher ^
  --icon assets/logo.ico --distpath packaging/dist --workpath packaging/build ^
  --specpath packaging ^
  --add-data "vein_launcher/presentation/webui/dist;webui/dist" ^
  --add-data "assets;assets" packaging/entry.py

# 发布（必须由负责人明确指令）
# 1) 构建 zip  2) 上传 zip + latest.json 到 Release  3) 校验
#    https://github.com/zhanjhn-studio/vein_launcher/releases/latest/download/latest.json
#    可访问（更新器三级回退依赖它）
```

---

## 4. 硬规则（不可违背）

1. **UI 默认英文**，设置内可切简体中文；不得默认中文。
2. **日志只写文件**（`VeinLauncher/log/`），禁止打印到 CMD/控制台。
3. **数据根目录**：exe 同级 `VeinLauncher/`，内含 `config/ log/ minecraft/ downloads/ plugin/ java/ skins/ democrat/`。
4. **`*.docx` 一律不入库**（已 gitignore）；Word 只做本地交付，生成脚本可入库。
5. **没有负责人明确指令，不发 Release、不动 tag、不改 release 资产**。
6. **五层依赖只能自上而下**；层间通知走 `event_bus`，禁止反向 import、禁止 domain 依赖框架。
7. 默认主题 **深色**；**简洁模式默认关闭**；空闲淡出 60 s；无壁纸。
8. 下载：**BMCLAPI 优先 + 官方兜底**；证书异常自动降级并记忆。
9. 提交使用 conventional commits（`feat/fix/docs/chore/refactor/test`），**代码与 teamwork.md 一起提交**。
10. 大面积 `backdrop-filter` 禁用（无 GPU 合成时会闪烁）。

---

## 5. 团队分工（8 角色，写入范围严格隔离）

| # | 角色 | 写入范围 | 职责 |
|---|---|---|---|
| 1 | `coder-core` | `vein_launcher/domain/`、`vein_launcher/common/` | 领域模型、通用基础结构、核心实体、常量 |
| 2 | `coder-services` | `vein_launcher/application/`、`vein_launcher/infrastructure/` | 业务逻辑、服务层、底层依赖封装 |
| 3 | `coder-platform` | `packaging/`、`tests/`、`tools/`、`plugin_host/`、`mlc/` | 构建打包、插件宿主、单元测试、工具链 |
| 4 | `docs-writer` | `docs/`、`teamwork.md`、`RELEASE_NOTES.md` | 开发/部署文档、更新日志、协作规范 |
| 5 | `ui-designer` | `webui/src/styles.css`、`assets/` | 配色、样式、图标、静态素材、视觉规范 |
| 6 | `interface-designer` | `webui/src/pages/`、`webui/index.html` | 页面组件、路由、交互、页面结构 |
| 7 | `github-manager` | `.github/`、`gh` 远端操作 | CI、issue/PR 模板、发布、标签管理 |
| 8 | `reviewer` | **无（只读）** | 全仓巡检、风险识别、bug 排查、规范校验，只出报告 |

**保留禁区（仅 Lead 可改）**：`webui/src/App.tsx`、`webui/src/ui.tsx`、`webui/src/bridge.ts`。

### 5.1 调度铁则

1. 第一轮：全员并发**只读勘察**，禁止任何写文件；统一四段报告（现状 / 问题清单 / 2~3 条优先任务 / 预估改动文件）。
2. 收齐报告后 Lead 汇总分类：Bug 风险 / UI 交互打磨 / 文档&仓库治理。
3. **同一文件同一时间只分配给一个 Agent**，派发时写明允许修改的文件路径。
4. `reviewer` 常驻只读，可随时巡检，不占写入权限。
5. 越权修改他人范围 → 直接驳回。
6. 子 Agent 不计费、可并发；Lead 控制自身轮询与汇总频率，避免上下文膨胀。

### 5.2 生命周期事实（迁移必读）

- 创建：`spawn_teammate(name, description, prompt)`，**名字全局唯一**；重名会报
  `teammate name "xxx" was already used in this Team`。
- 停止：`interrupt_agent(target)` → 状态 `inactive`（不运行、不写文件），但**记录仍在**。
- **没有删除/解散成员的工具**（只有 spawn / interrupt / send_message / list_agents）。
  要彻底清空只能结束会话或开新会话。
- 唤醒：`send_message` 会给 inactive 成员开新一轮（谨慎使用，等于启动它）。

---

## 6. 模型与计费（按项目负责人设定）

- 会话模型是**全局继承**：子 Agent 创建时取当前会话模型，**无法在 spawn 时单点指定**。
- 因此「把所有子模型改成 X」的唯一路径是：**切换会话模型 → 重建团队**。
- 禁止尝试修改已存在子 Agent 的模型。
- 负责人设定：子 Agent 用 `/workbuddy/hy4`（0 token 计费），只有 Lead 消耗 token。
  实际运行时标识会显示为 `workbuddy/hy4free` 一类，**这是运行时命名，不由 Lead 控制**。
- 若名字已被旧 inactive 成员占用，重建只能用新名字（如 `coder-core-2`）或先开新会话。

---

## 7. 架构与协议速查

### 7.1 RPC（QWebChannel + JSON-RPC 2.0）

```jsonc
// 请求（前端 → Python）
{"jsonrpc": "2.0", "id": 12, "method": "versions.install", "params": {"args": ["1.20.1"]}}
// 回包（Python → 前端，由 bridge.py 调 JS）
window.__veinResult(12, true, {ok: 1})
```

推送通道（Python → 前端）：

| 通道 | 用途 |
|---|---|
| `__veinProgress(taskId, done, total)` | 下载/安装进度 |
| `__veinLog(line)` | 日志行 |
| `__veinNotify(title, message)` | 通知 |
| `__veinNavigate(page)` | 切页 |
| `__veinGameExited(exitCode)` | 游戏进程退出（95bd910 新增，前端 `vein:gameExited`） |

方法分组（66 个）：应用/日志、版本/下载、账号/皮肤、实例/世界、模组/插件、更新/其它、MLC（`mlc.world.create`、`mlc.player.info`、`mlc.mod.load`、`mlc.plugin.search` 等）。

线程：RPC 在 `vein-async` 事件循环执行；JS 执行经 Signal 回 UI 线程；页面未就绪时脚本排队（上限 500）。

### 7.2 下载链路

```
请求 → 镜像重写（BMCLAPI）→ 证书异常降级（按 host 记忆）
     → 单文件 .part 断点续传 + 并发 8 + 目标级锁去重
     → SHA-1 校验 → 失败重试（3 次）→ 逐文件进度回调 → 前端/侧栏监控
```

- `HTTPStatusDownloadError`：408/425/429/5xx 可重试，其余 4xx 立即失败。
- 失败抛 `DownloadError`（带失败文件数与样例），前端红字提示。
- 配置：`download.max_concurrent = 8`、`download.retry_count = 3`。

### 7.3 插件系统

- Node 独立进程（`runtime/node_host.js`），stdio 上 JSON-RPC。
- 17 个能力，权限校验 + 默认 30 s 超时（`CapabilityTimeoutError`）+ 崩溃自动重启 ≤3 次。
- UI：白名单清洗后在 closed Shadow DOM 渲染；`ui.openPage(page)` 可切页。
- 自检：`python tools/plugin_selftest.py` → 9/9。

### 7.4 账号 / 皮肤 / 更新

| 类型 | 状态 |
|---|---|
| 离线 | ✅ 可用 |
| Microsoft（设备码 → XBL → XSTS → login_with_xbox） | ⛔ 服务端 403 `Invalid app registration`（等白名单） |
| LittleSkin（Yggdrasil） | ✅ 可用，启动注入 authlib-injector |

- 令牌按账号隔离，MC token 过期前 10 分钟用 refresh_token 续期。
- 皮肤：导入 PNG（64×64 / 64×32）、读站内皮肤、公开库 `/skinlib/list` → `/texture/{tid}` → `/textures/{hash}`。
- 更新：GitHub API → `latest.json` → 公告站 `update` 字段；zip 解压安装（非原地替换）。

---

## 8. 当前状态矩阵

| 模块 | 状态 | 备注 |
|---|---|---|
| 启动 / 实例管理 | ✅ 可用 | 模组启停、删除、存档、种子扫描 |
| 下载 / 安装 | ✅ 可用 | 逐文件进度、断点续传、失败可见 |
| 加载器 | ⚠️ 基本可用 | Fabric/Quilt 的 maven 库待修（见 §9-P1） |
| 模组搜索安装 | ✅ 可用 | Modrinth，按版本/加载器过滤 |
| 皮肤 | ✅ 可用 | 导入 / 站内 / 公开库 |
| 账号 | ⚠️ 部分 | 微软被 403 阻塞 |
| 插件系统 | ✅ 可用 | 权限、超时、自恢复、自检 9/9 |
| 自动更新 | ✅ 可用 | 三级回退；zip 非原地替换 |
| 国际化 | ⚠️ 部分 | 主导航/设置/实例标签；正文仍英文 |
| 世界分析 | ⚠️ 部分 | 种子/版本可用，群系结构未表格化 |
| CI | ❌ 缺失 | `.github` 无 workflow |

---

## 9. 风险登记册

### 9.1 已在 `95bd910` 修复（勿回退）

| 问题 | 位置 | 修法 |
|---|---|---|
| UI 启动必 `TypeError`：调用传 `uuid=`，服务层形参是 `auth_uuid` | `presentation/bridge.py` | 改 `auth_uuid=`；新增 AST 契约测试兜底 |
| `DownloadError(..., status=...)` 非法 kwarg，HTTP 错误绕过重试 | `infrastructure/download/downloader.py` | 新增 `HTTPStatusDownloadError`，按状态码重试 |
| `VeinError` / `get_assets_dir` 未 import（复制实例、旧版 assets 安装 `NameError`） | `application/services/version_service.py` | 补 import |
| 查询 `is_installed` 时顺手建空目录 | `infrastructure/storage/file_storage.py` | 拆 `version_path`（不落盘） |
| ≤1.12.2 缺 `--username/--version`（只有 `minecraftArguments`） | `application/services/launcher_service.py` | 支持 legacy 字符串 + 补 `java.library.path` |
| `launcher_version` 硬编码 0.0.1 | 同上 | 读 `vein_launcher.__version__` |
| `GAME_EXITED` 永不发布 → UI 卡「运行中」、二次启动被拦 | `infrastructure/process/game_process.py` | 后台 `_watch_exit`，只发布一次 |
| Java 8 被识别成 major=1 | `infrastructure/process/java_detector.py` | `1.8.0_x` → 8 |
| domain 版本模型解析不了真实 Mojang JSON（camelCase 全丢） | `domain/models/version.py` | 补 alias + 可选字段 + `assets_index` 兼容 |

### 9.2 待修（按优先级）

**P1**
1. **Fabric/Quilt 库不下载**：子版本 JSON 的 libraries 只有 `name`+`url`，无 `downloads.artifact`；`_library_tasks` / `_classpath` 只看 artifact → 实例缺 fabric-loader/intermediary，启动失败。
2. **Forge/NeoForge 安装器布局**：只在临时 cwd 造 `launcher_profiles.json`，未提供 `versions/<mc>/<mc>.jar`；且 `_download` 绕过 Downloader（无镜像/证书降级）。

**P2**

3. TLS 降级是实例级全局开关，8 并发共享 → 一个节点失败即整队列关校验（应按 host）。
4. 416 分支 `part.replace(dest)` 不校验 SHA-1；下载成功后也不再校验。
5. `queue` 每 64 KB 发一次进度事件（3620 文件 + 大 jar）→ IPC 风暴，建议 200 ms 或 1% 节流。
6. `version_service.is_installed/list_files/delete_file/delete` 只认 `instances/`，不认 `versions/` 回退。
7. `downloader._LOCKS` 无 loop 维度，多事件循环（测试/重启 loop）复用会 `RuntimeError`。
8. `UIConfig.language` 默认 `"zh_CN"`，与「UI 默认英文」硬规则及 `translator.DEFAULT_LANG="en_US"`、webui `i18n` 冲突（目前无人读，属埋雷）。
9. `common/utils/version_utils.parse_size()` 对带单位字符串全抛 `ValueError`（B 先命中），仅裸数字可用。
10. `AccountManager` pydantic 不可往返：`model_dump()` 丢子类字段、`model_validate()` 撞抽象类；缺 `account_type` 判别联合。
11. `event_bus.subscribe` 不去重；`publish_once` 是空壳；回调异常无 `exc_info`，栈丢失。
12. `get_minecraft_dir()` 每次调用 stat+读+解析 JSON（实测 4.3 ms），是安装热路径根目录。
13. `set_minecraft_dir` 只建 `instances/`，不建 `assets/libraries`。

**P3 清理项**

14. `domain` 约 1000 行无消费者代码（`models/{launcher,mod,plugin}.py`、`repositories/*`、`services/version_resolver.py`）。
15. `VRPCGameControl.launch` 返回带 `...` 的 dict，且与 `plugin_host/capabilities.py` 重复。
16. `EventNames.Game_CRASHED` 命名笔误；i18n 三套真源；`domain/__init__` 导出不一致。
17. `main.py:324` 才 `setup_logger()`，早于它的 import 日志会丢；`main.py:388` 有裸 `print()`。

### 9.3 仓库治理缺口

- **无 CI**（`actions/workflows` total_count = 0），`CONTRIBUTING` 承诺的测试/编译校验无人执行。
- tag `v0.1.0` 指向 `5e66188`，**落后 main** 十余个提交（发布内容不含后续修复）。
- `latest.json` **无 sha256 / size**；更新器依赖 `releases/latest/download/latest.json`，漏传即断链。
- 仓库 description 拼写错误（`lauhcher`）；topics / homepage 为空。
- `main` 未保护、无 rulesets；secret scanning / push protection / Dependabot 全关。
- `.github` 已有 PR 模板、issue forms、CODEOWNERS、SECURITY.md、RELEASE_CHECKLIST.md（**无 release workflow**，按规则不加自动发布）。

### 9.4 文档漂移（已知未修）

| 文档写法 | 实际 |
|---|---|
| `docs/v0.1.0/INTERNAL.md`：RPC **60** 个（2 处） | 66 |
| 同上：前端 ≈4,641 行 | 5,017 |
| `README.md` / `README-zh.md`：7 个一级页面 | 8 个（多 Multiplayer） |
| 开发者文档：`pages/*.tsx`、`host.js` | 实际扁平 `*Page.tsx` + `runtime/node_host.js` |
| 讨论页模板「六行记录」 | 实际标题 + 5 字段 |

---

## 10. 待决策（详见 `docs/v0.1.0/DISCUSSION.md`）

| 编号 | 议题 | 状态 |
|---|---|---|
| D-001 | 微软登录：等白名单 / 官方旧授权 / 只做离线+LittleSkin | blocked（倾向 C） |
| D-002 | 世界分析是否做群系/结构表格 | open |
| D-003 | 原地自动更新器（updater）是否本版本做 | open |
| D-004 | 中文翻译覆盖范围：全量 or 主要界面 | open |
| D-005 | 令牌是否用 Windows DPAPI 加密 | open |
| D-006 | 包体 615 MB 是否优化 / 换安装器 | open |
| D-007 | 公告站 `public.js` 版本号同步（仍 0.0.3） | open |
| D-008 | 插件市场是否纳入 0.2.0 | open |
| D-009 | 镜像证书异常时是否保持降级不校验 | open |
| D-010 | 简洁模式默认关闭 | accepted |
| D-011 | 默认英文界面 + 设置内切中文 | accepted |
| D-012 | 删除嵌套 v0.5 副本、只合并壁纸/简洁模式 | accepted |
| D-013 | Layui 仅用于控件层，不接管页面 | accepted |

---

## 11. 资产与文档清单（哪些入库、哪些只在本机）

**入库**
- 源码：`vein_launcher/`（含 `webui/src`）、`tests/`、`tools/`、`packaging/entry.py`、`assets/`
- 文档：`docs/v0.1.0/{README,INTERNAL,DISCUSSION}.md`、`README*.md`、`CONTRIBUTING.md`、`RELEASE_NOTES.md`、`teamwork.md`
- 治理：`.github/{pull_request_template.md, ISSUE_TEMPLATE/*, CODEOWNERS, SECURITY.md, RELEASE_CHECKLIST.md}`
- 配置样例：`packaging/latest.json`

**不入库（gitignore）**
- `*.docx`（内部文档、开发者文档、发布 PPT 等）、`docs/launch_deck/*.pptx`
- `packaging/*.zip`、`packaging/dist/`、`vein_launcher/presentation/webui/dist/`
- `logs/`、`*.log`、`.local/`、`*.png` 预览图（`docs/preview_*`）

**只在本机、迁移需自行带走**
- `VeinLauncher_开发者文档_v0.1.0.docx`（仓库根）
- `docs/v0.1.0/VeinLauncher_v0.1.0_Internal.docx`
- 数据根 `VeinLauncher/`（config/accounts、log、minecraft 实例、java 运行时、skins）
- `gh` CLI 登录态、`node` 运行时、Word 16.0（仅用于复测 docx 页数）

---

## 12. 迁移检查表

- [ ] Python 3.13，`pip install -r requirements.txt`
- [ ] `cd vein_launcher/presentation/webui && powershell -ExecutionPolicy Bypass -File build.ps1`（否则白屏）
- [ ] `python -m unittest discover -s tests` → **51 OK**
- [ ] `python -m vein_launcher.presentation.main` → 窗口正常、启动页有版本卡
- [ ] Node 18+（插件页可见宿主状态）
- [ ] `gh auth status`（发布/查仓库需要）
- [ ] 需要 Word 交付时：安装 Word 16+，跑 `python tools/gen_*.py`，用 COM `ComputeStatistics(2)` 复核页数（内部 11 页 / 开发 8 页）
- [ ] 如需发版：先读 `.github/RELEASE_CHECKLIST.md`，**必须负责人明确指令**
- [ ] 如需重建 8 人团队：见 §5.2（名字唯一、无删除接口、模型会话继承）

---

## 13. 变更日志

> 格式：`YYYY-MM-DD · area · what changed · files · verification · commit`（最新在最后）

- **2026-11-01 · domain/pydantic** — migrated 6 Pydantic models in `version.py` to
  `model_config = ConfigDict(populate_by_name=True)`; `PydanticDeprecatedSince20` warnings
  cleared · `domain/models/version.py` · tests 44 OK, 0 warnings
- **2026-11-01 · plugins** — plugin hardening: host auto-restart (≤3, backoff, reload),
  per-capability 30 s timeout, `ui.openPage`, richer `PluginService.state()`, template docs ·
  `plugin_host/*`, `runtime/node_host.js`, `plugin_service.py` · selftest 9/9, tests 44 OK
- **2026-11-01 · repo** — removed nested `vein_launcher v0.5/` (158 files), archived docs,
  dropped `src/bridge.js` + `zh_strings.txt`, moved `scan_left.py` to `tools/` · `f4391c3`
- **2026-11-01 · ui/prefs** — merged wallpaper + compact mode + idle fade · `styles.css`,
  `App.tsx`, `launchPage.tsx`, `settingsPage.tsx`, `bridge.py`, `settings.py` · build OK · `f4391c3`
- **2026-11-01 · ui/sidebar** — smoother expand (0.28 s), labels slide in · `src/styles.css` ·
  rAF sampled 68→208, tests 44 OK · `38942ad`
- **2026-11-01 · ui/defaults** — compact mode defaults **off** · `settings.py`, `prefs.ts` · `68f4961`
- **2026-10-31 · release** — v0.1.0 published (zip + latest.json), PyInstaller packaging,
  update fallback chain · `update_service.py`, `packaging/` · `cfda55c`
- **2026-10-31 · download** — per-file progress, failure surfacing, concurrency 8,
  LittleSkin skin library · `queue.py`, `version_service.py`, `littleskin.py` · 3640/3640 · `9a759ab`
- **2026-10-31 · instances** — instance detail page (mods/RP/shader/datapack/modpack, worlds,
  seed scan, delete) · `instance_service.py`, `instancePage.tsx` · tests 40 OK · `f3219dd`
- **2026-10-31 · skins** — import PNG, LittleSkin profile skin, library download · `b2786cb`
- **2026-10-31 · onboarding** — full-page 5-step wizard · `onboarding.tsx`, `styles.css` · `51b4733`
- **2026-10-31 · images** — allow remote images from `file://`, `RemoteIcon` fallback · `ebf7f6a`
- **2026-11-03 · docs** — v0.1.0 internal doc + discussion page · `docs/v0.1.0/*` · `5794fd1`
- **2026-11-04 · docs/word** — Word generator for internal doc · `tools/gen_internal_doc.py` · `c4a4566`
- **2026-11-04 · docs/branding** — cover logo, header logo on every page, About page,
  discussion condensed to 2 pages · `tools/gen_internal_doc.py` · PDF 11 pages · `b8a92f1`
- **2026-11-04 · ui/polish** — sidebar sliding pill + icon spring/glow, dark theme default fixed
  (`currentTheme()` fallback), primary gradient in dark, staggered page mount, card lift,
  version card decluttered, 3 quick-action cards, removed `backdrop-filter` · `styles.css`,
  `App.tsx`, `launchPage.tsx`, `theme.ts` · previews via `tools/ui_preview.py` · `90924f6`
- **2026-11-05 · docs/dev** — developer Word doc 8 pages: chapter 9 开发约定, appendix A.1
  落地建议, appendix B 2 blank pages, appendix A own page · `tools/gen_dev_doc.py` · `90075eb`
- **2026-11-05 · tests/contracts** — 2 AST contract tests: launch kwargs vs signature;
  `DownloadError` family constructor kwargs · 51 OK (injected old bugs to prove they fail)
- **2026-11-05 · tools/doc** — `tools/doc_facts.py`: AST/regex/subprocess extractor
  (RPC 66 / NAV 8 / tests 51 / version 0.1.0 / plugin caps 17 / LOC 5017)
- **2026-11-05 · fix/launch-chain** — 9 P0/P1 fixes (bridge kwarg, HTTPStatusDownloadError,
  version_service imports, `version_path`, legacy `minecraftArguments`, `launcher_version`,
  `GAME_EXITED`, Java 8 parsing, domain camelCase aliases) + `vein:gameExited` channel ·
  tests 51 OK, frontend build OK · `95bd910`
- **2026-11-05 · team/dismiss** — 8 teammates stopped (inactive; no delete API), Lead solo;
  leftover work reviewed, verified, committed; temp screenshots cleaned
- **2026-11-05 · docs/teamwork** — this file rewritten as a migration-ready handover:
  project map, commands, hard rules, 8-role scopes, lifecycle facts (unique names / no delete /
  session-inherited model), protocol cheatsheet, status matrix, P1–P3 risk register, repo
  governance gaps, doc drift list, decisions, asset inventory, migration checklist ·
  `teamwork.md` · tests 51 OK · `git log -- teamwork.md`
- **2026-11-07 · tools/tree** — 指令树 `commandTree.ts`：对照 minecraft.wiki/w/Commands 补全
  Java 版 **88 条**指令（7 个分组），**161 件**物品，物品组件（`[custom_name=...]` /
  `[enchantments=...]` / `[unbreakable={}]`…）、实体 NBT（`{NoAI:1b}` / `{ArmorItems:[...]}`…）、
  方块 NBT（`{Items:[...]}` / `{Lock:"..."}`）；循环批量注册节点，
  共 **684 个前缀 / 6660 条候选** · `toolsPage.tsx`、`styles.css` · build OK
- **2026-11-07 · tools/ui** — 工具页：指令构建器（输入前缀 → 列出可接项 → 点击追加、回退、清空、
  复制）+ 中英文检索（命中给出完整路径）；单卡「指令」默认收起，内含 构建器 / 快捷键 / 指令列表
  三小节；删除 `ToolboxPage` 与 `toolbox` 导航项，数据目录/日志入口合并进工具页 ·
  `toolsPage.tsx`、`App.tsx`、`pages.tsx`、`styles.css` · esbuild 354 KB
- **2026-11-07 · tools/hotkeys** — `hotkeys.py`：Win32 `RegisterHotKey` + `QAbstractNativeEventFilter`，
  `Ctrl+Alt+0..9` 直接复制指令（250 ms 去重，Qt 会投递两种原生事件），复制后
  `SetForegroundWindow` 把焦点还给游戏 · `main.py`、`bridge.py` · 实测剪贴板命中
- **2026-11-07 · tools/palette** — `palette.py`：`Ctrl+Alt+Q` 唤起无边框置顶速查小窗，
  搜索/↑↓/Enter 追加/Ctrl+Enter 复制/Esc 关闭；`AttachThreadInput` 抢焦点（否则按键进不了输入框）；
  位置按 dpr 换算；点击检索结果=填入输入框（不关窗），Enter=直接复制 ·
  `main.py`、`bridge.py`、`App.tsx` · 实测 `Ctrl+Alt+Q → kill → @e → 复制 /kill @e`
- **2026-11-07 · tools/custom** — 自定义常用指令：`config/tools.json` 持久化
  `favorites[{id,title,cmd,slot}]` + `paletteKey`；自定义优先占槽、内置让位；
  小窗唤出键可选 A–Z / F1–F12；`tools.config` / `tools.saveConfig` RPC ·
  `bridge.py`、`hotkeys.py`、`toolsPage.tsx` · 读配置兼容 BOM（`utf-8-sig`）
- **2026-11-07 · app/update** — 移除启动强制更新弹窗（`force-mask` / `min_version` 判定），
  只保留可关闭的浅色公告条与设置页手动检查更新 · `App.tsx`
- **2026-11-07 · ui/fixes** — 勾选框 `i` 被 layui.css 的 `position:absolute` 压到文字上（改回 static +
  flex order）；侧栏收起态图标居中（150% 缩放下 5 css px ≈ 7 物理像素） · `styles.css`
- **2026-11-07 · docs/teamwork** — 本次变更并入总账（速览版本 0.5.0、代码地图补
  `hotkeys.py` / `palette.py` / `toolsPage.tsx` / `commandTree.ts`、导航 8 项说明） · `teamwork.md`

- **2026-11-07 · ui/motion-v4** — 追加一层顺滑动效（只动 opacity/transform，无大面积滤镜）：
  切页用 View Transitions API 做整页交叉淡入（`startViewTransition`，`html.vt` 期间关掉
  `.page` 的重复入场，不支持或 reduced-motion 时自动退回原动画）；版本卡/快捷卡/分类卡/
  插件卡按 nth-child 35ms 错峰；日志行左滑淡入；进度条宽度 380ms 弹性过渡；标题栏滚动
  后收缩 58→50px 并加投影（捕获阶段监听 `.main-body`，因为它在启动画面后才挂载）；主题
  切换挂 340ms `theme-fade` 只过渡颜色；Toast 从右侧滑入；分类项 hover 右移 2px；
  弹窗按钮组依次浮现 · `styles.css`、`App.tsx`、`theme.ts` ·
  `python -m unittest discover -s tests` → 51 OK · frontend build OK ·
  预览页实测 `hasVT=true`、滚动后 `.main.scrolled=true` 且标题栏 50px

- **2026-11-07 · ui/icons** — 重绘坏掉的两个 16×16 图标：`chest.png` 原本是 64×64 的
  GUI 图集碎片（带透明边与残缺格线），`anvil.png` 是一团纯灰噪点、没有轮廓；改用
  字符网格 + 调色板逐像素重画（箱体/盖缝/金锁扣、铁砧顶板/腰身/底座）。两个文件被侧栏
  （MLC / Tools）、下载页（Modpacks / Forge）、加载器卡与 `RemoteIcon` 兜底共用，替换
  文件即全局生效，无需改代码 · `assets/icons/{chest,anvil}.png`、`tools/make_mc_icons.py` ·
  下载页与加载器页截图核对（16×16 全部一致，像素块大小统一）· 未提交

- **2026-11-07 · ui/icons-fix** — 纠正上一版图标的做法：`anvil.png` 原来是原版**方块贴图**
  `textures/block/anvil.png`（从 1.20.1 client.jar 里取的还是同一张灰色噪面），Minecraft
  的铁砧形状由 3D 模型提供，所以贴图放多大都看不出铁砧；手绘 16×16 在 24px 下又像“叠起来
  的三根条”。最终改为**游戏内等距渲染**（chest / anvil 均 64×64，裁边 + LANCZOS），并给
  这两个文件单独放开 `image-rendering: auto`，其余 16×16 像素图标保持 pixelated ·
  `assets/icons/{chest,anvil}.png`、`tools/fetch_render_icons.py`、`styles.css` ·
  侧栏 / 下载页 / 加载器卡截图核对（铁砧提亮 1.55 倍以适配深色背景） · 未提交

- **2026-11-07 · i18n/en** — 界面全面英文化（中文留到下一轮）：`commandTree.ts` 删除 518 条
  中文 hint（含 27 个中文 token 模板与 7 个分组名），改由 `label(token)` 运行时生成英文说明
  （选择器/游戏模式/常用指令走人话字典，其余 `minecraft:diamond_sword → Diamond Sword`）；
  `toolsPage.tsx` 74 处文案与 10 条内置指令描述译成英文；修 `App.tsx` 一处历史乱码
  `锛?`（通知拼接应为 `": "`）；下载页「设置」→「Settings」；语言选项改
  `Chinese (Simplified)` · `commandTree.ts`、`toolsPage.tsx`、`App.tsx`、`downloadPage.tsx`、
  `pages.tsx`、`settingsPage.tsx` · `python -m unittest discover -s tests` → 51 OK，
  frontend build OK（bundle 329.5 → 307 KB），src 下 i18n.ts 之外中文代码行为 0 · 未提交

- **2026-11-07 · fix/launch-jar** — 修「游戏启动报 ClassNotFoundException: net.minecraft.client.main.Main」：
  根因是 `1.20.1.jar` 下载停在 7.8/23.0 MB、只留下 `.part`，而 `is_installed()` 只检查版本 JSON，
  于是 classpath 里没有客户端 jar。`version_service.is_installed()` 现在要求 jar 真正下完
  （无 `.part` 且大小对得上 `downloads.client.size`，加载器沿 `inheritsFrom` 找父版本）；
  `launcher_service.build_command()` 在没有 jar 时抛 `GameLaunchError` 并指出 `.part` 文件，
  不再让 Java 报一个看不懂的 ClassNotFound · `application/services/{version,launcher}_service.py` ·
  本地已续传补全 jar（23,028,853 B，SHA-1 校验通过），`is_installed=True`、classpath 含
  `1.20.1.jar`、命令行可构建；51 项测试通过 · 未提交

- **2026-11-07 · fix/game-window** — 修「游戏开起来像全屏、不能缩放/最小化」：默认窗口
  `1920×1080` 与 1080p 屏幕等宽等高，标题栏被挤出屏幕，看起来像全屏。默认改为
  `1280×720`，并在配置加载时把旧默认 `1920×1080` 一次性迁移为 `1280×720`（写回 config.json）
  · `common/config/settings.py` · 实测窗口 1296×759（客户区 1280×720）、未最大化、
  可移动可缩放；51 项测试通过 · 未提交

- **2026-11-07 · feat/mlc-plugins** — MLC 与插件系统从占位变成可用：
  `player_info()` 直接解析 `playerdata/*.dat` 的 NBT（血量/食物/经验/坐标/维度/游戏模式/背包格数），
  `world_info()`/`world_detail()` 解析 `level.dat`（种子/难度/天数/最后游玩/玩家数/体积）并按最近游玩排序；
  `state()` 给出 running/pid/uptime/exit_code/版本；`mod_load()` 把 jar 复制进实例 mods；
  版本号留空时自动选最近改动的实例。插件侧新增 `mlc.state`、`mlc.world.detail` 能力，
  Node 宿主补齐 `state/worldDetail/playerInfo(versionId, world)/modLoad(...)`；`lua.js` 的 `sanitize`
  现在保留标量数组（表格 columns/rows）并兼容 `{props:{...}}` 写法；新增示例插件
  `plugins_examples/mlc-panel`（徽章 + 存档表 + 玩家属性 + 刷新按钮，全部走 ui.render） ·
  `mlc/service.py`、`plugin_service.py`、`bridge.py`、`runtime/{node_host,lua}.js`、
  `plugins_examples/mlc-panel/*`、`tools/mlc_selftest.py` ·
  `tools/mlc_selftest.py` 14 项 PASS（临时数据 + 真实宿主）、`tools/plugin_selftest.py` PASS、
  51 项单测 OK；真实存档实测：世界「新的世界」种子 -1297348265404023800、玩家血量 20/食物 20 ·
  未提交

- **2026-11-07 · feat/i18n-mlc-switch** — 界面中英全覆盖 + MLC 总开关：
  新增 `src/i18nDom.ts`（DOM 层翻译：文本节点 + placeholder/title/aria-label，切回英文逐字还原，
  MutationObserver + 切换后 4 秒补扫），词典覆盖 8 个页面、指令预设、日志占位与「N 项/N 个版本」动态计数；
  指令候选标签改为语言感知（`label/displayHint/groupLabel` 带 lang），物品名取自官方 `zh_cn` 语言资源
  （`tools/gen_cmd_labels.py` → `src/cmdLabelsZh.ts`，191 个 token）。
  MLC 加总开关：`settings.mlc.enabled`（默认关）+ `MlcService.enabled/set_enabled/_require_enabled`，
  关闭时存档/玩家/模组调用一律拒绝；新增 RPC `mlc.setEnabled`；导航栏 MLC 改为独立页面（实例管理移到隐藏路由
  `/instance`），页面顶部就是总开关卡（显示 开/关）。
  验收：英文模式 8 页 0 处中文；中文模式仅剩版本号/文件名/玩家名与 Java、PNG 等技术名词；51 项单测 + 插件自检通过 ·
  `settings.py`、`mlc/service.py`、`bridge.py`、`App.tsx`、`pages.tsx`、`i18n.ts`、`i18nDom.ts`、`commandTree.ts`、
  `cmdLabelsZh.ts`、`toolsPage.tsx`、`types.ts`、`tools/gen_cmd_labels.py` · 未提交

- **2026-11-07 · feat/game-detect-installers** — 运行中游戏检测 + 多实例 + 双安装器：
  新增 `application/services/game_registry.py`（psutil 识别 java 进程命令行中的 `net.minecraft.client.main.Main` 与各加载器主类，
  返回 pid/版本/游戏目录/内存/运行时长，支持按 pid 结束；本启动器启动的会标记 source=launcher）；
  `LauncherService` 改为每次启动独立 `GameProcess`，可同时开多个游戏，退出自动注销；bridge 新增 `game.running` / `game.kill`；
  启动页新增「运行中的游戏」卡片（3 秒轮询，显示版本/PID/内存/时长 + 结束按钮，外部启动标注「外部启动」）。
  启动时自动检测 Java：`context.startup()` 预热检测并缓存 60 秒，设置页不再每次扫盘。
  新增 `installer/`：`install-online.ps1|cmd`（从 GitHub 拉 main 分支 → venv → 依赖 → 快捷方式 → 启动，失败时打印离线步骤）、
  `install-offline.ps1|cmd`（本地 payload，不联网）、`build-payload.ps1`（生成 payload）；README 与 README-zh 都加了两种安装方式说明。
  `requirements.txt` 清理并补 psutil；`tools/build_minimal_jre.py`（jlink 最小 JRE，已验证 1.20.1 可启动，45.5 MB）；
  `tools/package_release.py`（打 zip 发布包）。51 项单测 + 插件自检通过 · 未提交

- **2026-11-07 · fix/installers-offline** — 安装器离线化：
  `.ps1` 统一补 UTF-8 BOM（PowerShell 5.1 无 BOM 会按 ANSI 读，中文注释会破坏语法，三个脚本已用 Parser 校验通过）；
  `build-payload.ps1` 默认一并 `pip download` 依赖到 `payload/wheels`（`-WithoutWheels` 可跳过）；
  `install-offline.ps1` 去掉「偷偷联网装依赖」的退路，没有 wheels 直接给明确提示；
  实测离线安装：解压 → 建 venv → 无 wheels 时按预期报错退出，安装目录结构正确；
  `codeload.github.com/.../zip/refs/heads/main` 返回 200，在线安装器下载步骤可用 · `installer/*.ps1` · 未提交

- **2026-11-07 · fix/panel-java-detect** — 停止 MLC 面板打扰 + Java 识别内置运行时：
  `plugins_examples/mlc-panel` 改为 `activateOnStartup: false` 并去掉 15 秒自动刷新（只在手动点 Refresh 时重绘），
  已从 `VeinLauncher/plugin/` 移除安装副本，重启后不再自动弹面板；
  `JavaDetector._bundled_runtimes()` 扫描 `VeinLauncher/java/**/bin/java.exe`，实测识别到 Java 24（系统）、
  Java 21 / Java 17（temurin-17 与 jre-17）共 5 个运行时 · `java_detector.py`、`plugins_examples/mlc-panel/*` · 未提交

- **2026-11-07 · feat/exe-installers-skins** — EXE 安装器 + 皮肤支持：
  `packaging/launcher_entry.py` + PyInstaller 打包出独立 `VeinLauncher.exe`（onedir，618 MB，实测可启动，数据目录落在 exe 旁）；
  `packaging/build_release_zip.py` 裁剪 translations/qml/debug 资源后压成 `VeinLauncher-win64.zip`（450 MB → 194 MB）；
  `installer/app_installer.py`（tkinter）编译成两个 EXE：`VeinLauncher-Setup-Offline.exe`（204 MB，内嵌 payload）与
  `VeinLauncher-Setup-Online.exe`（10 MB，下载 release zip）。安装到 `%LOCALAPPDATA%\VeinLauncherApp`（实测 1002 文件 / 450 MB，
  安装后启动器窗口正常）。修了两个真实问题：多实例并发解压抢同一个 staging 目录 → 改为按 PID 隔离；安装目录被占用时给出明确提示。
  皮肤 A：新增 `infrastructure/network/authlib.py`，启动时自动下载 authlib-injector（349 KB，已就位），LittleSkin 账号启动即注入；
  皮肤 B：`tools/install_skin_support.py` 创建 `fabric-1.20.1` 实例并装入 CustomSkinLoader 15.1（实测 218 KB 落盘）。
  README 安装段改为四条下载路径 · 未提交

- **2026-11-07 · feat/vanilla-mlc-input** — 原版可用的 MLC 输入桥：
  新增 `infrastructure/process/game_input.py`（EnumWindows 找窗口、AttachThreadInput + ALT 抢前台、SendInput Unicode 打字），
  提供 `game.windows` / `game.focus` / `game.command` 三个 RPC；MLC 页新增「原版控制」卡片（输入指令 → 输进游戏窗口并回车）。
  自检 `tools/input_selftest.py`：Tk 靶子窗口实测收到 `hello vein 123`（PASS）。修正 INPUT 结构体（缺 MOUSEINPUT 导致 SendInput 返回 0）。
  任务栏图标：`SetCurrentProcessExplicitAppUserModelID` + 窗口继承 `assets/logo.ico`，不再显示 pythonw 默认图标。
  本地安装器测试数据、快捷方式、EXE 产物已全部删除 · 未提交
- **2026-11-07 · i18n/zh-merge** — 与 upstream 的 i18n 架构对齐后重新落中文：
  upstream 在 `3223f23` 之后的 `i18nDom.ts` 采用「英文源码 + DOM 层运行时翻译」，
  上一版的 12 文件中文硬编码会让切英文时仍显中文，故撤回；缺失文案改为补词典
  （`i18nDom.ts` +22 条：未登录 / 还没有安装任何版本 / 宿主未运行 /
  选一个插件查看权限与日志 / 主题色 / 更换… / 导入… / 空闲淡出长说明 等）；
  修 `pages.tsx` 的 `<Empty>t('No plugins yet')</Empty>`（t() 写进了文本节点，
  页面直接显示字面量）· `App.tsx`…`ui.tsx`（恢复英文源码）、`i18nDom.ts`、`pages.tsx` ·
  逐页读 DOM innerText 核对：启动 / 皮肤 / 插件 / 设置 / MLC / 工具 全中文
- **2026-11-07 · ui/accent-merge** — 主题色区块在 rebase 到 upstream 后重新接入设置页
  （`settingsPage.tsx` 的「主题色」块 + `changeAccent()`），与 `accent.ts`、`prefs.ts`、
  `bridge.py`、`settings.py` 配套；`styles.css` 冲突按「两侧都保留」解决
  （upstream 的 anvil/chest `image-rendering:auto` 规则 + 本地的 accent 样式） ·
  实测中文界面下色板可点、切色即时生效

- **2026-11-07 · feat/vanilla-agent** — 原版 MLC Java agent（无 mod 加载器）：
  `tools/build_vanilla_agent.py`：拉官方 1.20.1 client mappings → 解析 `Minecraft`(`enn`)/`LocalPlayer`/`Entity` 等混淆名
  → 渲染 Java 源码（纯反射，不依赖 Mixin/加载器）→ javac 直接编译成 `VeinLauncher/agent/vein-agent-1.20.1.jar`（5 KB）；
  agent 在 premain 起本地 TCP（127.0.0.1:25566，JSON 行协议）：`ping` / `state` / `chat`；
  启动器 `build_command` 对原版实例自动加 `-javaagent` + 端口；MlcService 增加 `agent_state/agent_chat`；RPC `mlc.agentState/agentChat`；
  MLC 页「原版控制」卡片显示 Agent 状态（离线/菜单/游戏内坐标），发指令优先走 agent、失败回退键盘输入；
  最小 JRE 补 `java.instrument`（否则 JVM 拒绝加载 agent，实测报 "Module java.instrument may be missing"）。
  实测：带 agent 启动 1.20.1 → `ping` 返回 `{ok:true,agent:"vein"}`，`state` 返回 `{inGame:false}`（菜单态）；
  同时删除安装器（`installer/`、`packaging/`、EXE 产物）· 未提交

- **2026-11-07 · feat/agent-v3** — agent 读数修正与实测：
  反射改为支持接口默认方法（`getString` 在 `Component` 接口上，之前只找父类导致玩家名显示 `literal{Player}`）；
  维度从 `ResourceKey[minecraft:dimension / minecraft:overworld]` 清洗为 `minecraft:overworld`。
  实测（quickPlay 直接进世界）：`state` 返回 `{inGame:true,player:{name:"Player",x:-1044.7,y:64,z:-1066,health:20,dimension:"minecraft:overworld"}}`；
  `chat` 发送 `/time set day` 与 `/say hello from vein` 均返回 `{ok:true}` 且游戏内生效 ·
  `tools/build_vanilla_agent.py` · 未提交

- **2026-11-07 · feat/mlc-agent-1-2-3** — 原版 agent 三项改进（已逐项实测）：
  ① 多实例端口：`LauncherService._free_agent_port()` 从 25566 起找空闲并**预留**，`build_command` 写入 `-Dvein.agent.port`，
  `launch` 记 pid→port，退出清理；`agent_port()` 解析「最近存活实例」，RPC 传 0 自动定位（实测两次 build 分别拿到 25567/25568）。
  ② 状态扩展：agent `state` 增加 `food`（20）、`xpLevel`、`yaw`/`pitch`、`dimension`（实测 `{food:20, xpLevel:0, yaw:-40.68, pitch:19.5, dimension:minecraft:overworld}`）；
  `readField` 兼容反射异常，`getFoodData` 从 Player 继承链解析。
  ③ 事件：`MlcService.start_agent_watch()` 每秒轮询状态，变化时发布 `mlc.agent.game.enter / game.leave / player.dimension / player.death`，
  bridge 订阅后推给前端 `__veinMlcEvent`（`vein:mlcEvent`）；MLC 页挂载自动开启、卸载停止（实测 quickPlay 进世界触发 `game.enter`）。
  51 项单测通过 · 未提交

- **2026-11-07 · feat/tools-mlc + fix/switch** — 指令菜单接 MLC + 开关对齐：
  工具箱「指令」区新增 **发送到游戏**（草稿整条发送）与每行 **运行** 按钮，均走 `mlc.agentChat`（自动端口）；
  顶部显示 `MLC 离线 / 已连接 / 游戏内` 状态（徽章改用 `t()`，中文稳定显示）；
  MLC 总开关重做为独立行（标题+说明在左、状态胶囊+胶囊开关在右），CSS 新增 `.switch-row/.switch-control/.switch-state`
  与 46×26 胶囊开关样式，修掉原来小方块错位问题 · `pages.tsx`、`toolsPage.tsx`、`styles.css`、`i18n.ts`、`i18nDom.ts` · 未提交

- **2026-11-08 · feat/hotkey-mlc** — 全局热键接 MLC：
  `MainWindow._on_hotkey_fired` 改为「先通过 `mlc.agentChat` 直接发进游戏，失败再复制到剪贴板」；
  工作线程用队列回传结果，主线程 `QTimer(120ms)` 轮询 `_drain_hotkey_results` 处理（原先跨线程 `QTimer.singleShot` 不触发）；
  `push_hotkey` 增加 mode 字段，前端 `__veinHotkey` 透传，工具箱提示区分「已发送 / 已复制」，并补中文动态文案。
  实测：游戏内按 Ctrl+Alt+1 → `results [('sent','/time set day')]`；关闭游戏后 → `[('copy', ...)]` 回退正常；51 项单测 OK · 未提交

- **2026-11-08 · feat/hotkey-startup-bind** — 启动即绑定已保存的指令热键：
  `MainWindow._bind_saved_hotkeys()` 在窗口显示 1.5s 后读取 `config/tools.json` 里带 slot 的自定义指令并注册全局热键，
  不必先打开工具箱页；内置 Ctrl+Alt+0..9 预设仍在工具箱页加载时绑定 · `main.py` · 未提交

- **2026-11-08 · feat/palette-redesign** — Ctrl+Alt+Q 速查窗重做：
  左右分栏（左：说明+状态+快捷键提示；右：候选列表），窗口 780×560、圆角深色、发光主按钮；
  鼠标点击候选 = 追加（检索模式=填入），双击 = 直接发送；↑↓ 选择、Tab/→ 追加、Enter 发送（未完整时先追加）、Ctrl+Enter 强制发送、Esc 关闭；
  `send_requested` 信号接主窗口：走 `mlc.agentChat` 发进游戏；失败弹 QMessageBox「游戏没有在运行，或 MLC agent 未连接」并**自动复制指令**到剪贴板。
  修：顶层窗口 QGraphicsDropShadowEffect 导致内容裁剪/标题发虚（已移除）；固定尺寸过小导致标题被压扁（放大并设最小行高）。
  实测：面板截图正常；`send_current()` 发出 `/time set day`；失败回调把 `/say hi` 写入剪贴板 · `palette.py`、`main.py` · 未提交

- **2026-11-08 · fix/switch-i18n + feat/palette-book** — 开关文案、失焦暂停、附魔书速查窗：
  ① 翻译层缓存旧原文导致「Off→On」仍显示“关”：`i18nDom` 改为记录 {原文,译文}，当前文本与译文不一致时把新文本当来源（实测 关→开→关 正确）。
  ② 选指令不打断游戏：`LauncherService` 启动前把 `options.txt` 的 `pauseOnLostFocus` 写为 false（处理 BOM、去重，实测只剩一行 false）。
  ③ 速查窗指令中文说明：`buildPaletteEntries` 增加 `hintZh`，palette 按 `settings.ui.language` 选择（实测显示 自己/所有玩家/所有实体）。
  ④ 附魔书样式：新增 `assets/palette_book.png`（PIL 生成）与 `tools/gen_palette_book_icon.py`；列表项 26px 书本图标、42px 行高、紫色渐变选中 + 左侧高亮条。
  · `i18nDom.ts`、`launcher_service.py`、`commandTree.ts`、`palette.py` · 未提交

- **2026-11-08 · feat/mlc-hard-gate** — MLC 总开关成为硬总闸：
  关闭时 `agentState / agentChat / watchStart / launch / world / player / modLoad` 全部抛 `MlcError("MLC 总开关未开启…")`，
  `game.command`（键盘输入桥）同样拒绝；MLC 页发送/启动/世界信息按钮禁用并显示黄色提示条，
  Agent 状态显示「MLC 已关闭」；工具页徽章显示「MLC 已关闭」且发送/运行按钮禁用；
  速查窗发送失败弹窗补充「或 MLC 总开关未开启」；全局热键回退时提示「MLC 未开启，指令已复制」；
  新增 `.btn:disabled` 弱化样式。实测：关闭时 agent_state/world_info 均被拒绝，按钮 disabled=true · 未提交

- **2026-11-08 · feat/plugin-complete** — 插件系统补全：
  新增能力 `game.running`（运行中游戏，含外部启动）、`game.command`（受 MLC 总开关控制）、
  `app.info`（版本 + 数据目录）、`versions.list`（已安装实例）；Node 宿主同步暴露
  `vein.game.running()/vein.game.command()/vein.app.info()/vein.versions.list()`；
  MLC 事件转发给插件：`vein.mlc.on('game.enter'|'game.leave'|'player.dimension'|'player.death')`。
  新增示例插件 `plugins_examples/status-panel`：一个面板展示版本/实例数/运行中游戏/MLC 状态，带刷新按钮与进世界通知
  （实测渲染出 v0.5.0、3 instances、2 running、MLC on）· `plugin_service.py`、`node_host.js`、示例插件 · 未提交

- **2026-11-08 · release/0.5.0** — Windows 发布包：
  新增 `packaging/entry.py` 与 `tools/build_exe.py`（PyInstaller onedir，含 webui/dist、assets、插件宿主 runtime、locales、
  plugins_examples、随包 agent；裁剪 translations/qml 等后 495 MB，zip 199 MB，sha256 1F3FDBFE…A176C）；
  `main.py` 首次启动把 `_internal/agent/*.jar` 复制到数据目录；冒烟测试 exe 可正常启动（窗口 “Vein Launcher 0.5.0”，
  日志含速查表 660 条、Java 检测）。`packaging/RELEASE_NOTES-0.5.0.md` 提供发布说明 · 未提交

- **2026-11-09 · style/theme-align** — 启动器主题对齐官网、图片整理：
  dark accent `#6f97f0/#8a7ff0` → `#7ea6ff/#5cd3c4`，light accent → `#2563eb/#0e9488`；清除硬编码紫色 rgba；
  `accent.ts` 调色板去掉紫色预设（蓝/青/绿/橙/红/青/黄绿/金）；logo 双真源同步（assets ↔ webui/src ↔ dist）；
  删除未使用图片：bucket / experience_bottle / vanilla_anvil（webui icons 与 dist），
  及孤儿素材 wordmark.png / _slide.png / logo.svg；官网截图全部换成新主题的 0.5.0 截图；
  删除网站未引用资源 cursor-*.png / film.css / film.js / shot-mlc-off.png · 已重启验证（PID 46380）

- **2026-11-09 · docs/site-v7** — 官网补齐正规化页面与底层能力：
  新增 quickstart / player / developer / plugin / mlc 文档入口页、faq 全文页、download（SHA-256 / 平台 / 更新时间 / 历史版本）、
  releases / changelog、roadmap、security、contribute、showcase、community、about、privacy、license（MIT）；
  导航改为 首页 / 文档 / 下载 / 社区 + GitHub，页脚升级为品牌 + 产品/社区/资源/法务四栏 + MIT/版权/版本；
  文档页新增全局搜索（Ctrl+K、静态索引、按语言过滤）、版本切换选择器、右侧大纲滚动高亮；
  新增 sitemap.xml、robots.txt、每页独立 description；中英双语 98 页 · 链接缺失 0

- **2026-11-09 · release/0.5.1** — UI 自定义版本：
  默认浅色 + 橙色主题（`#f97316/#f59e0b`），深色仍可切换；新增界面自定义（圆角 小/中/大、缩放 95/100/105、动效开关，localStorage 持久化）；
  `uiCustom.ts` + 设置页新区块；`theme.ts` 默认浅色并去掉深色迁移；调色板橙色优先；
  全部启动器截图用新主题重制并同步官网；版本号 0.5.1；exe 包 199 MB，sha256 BD6ADBC3…BC5E0；
  冒烟启动窗口 “Vein Launcher 0.5.1” · 未提交

- **2026-11-09 · docs/readme-0.5.1** — 重写 README：
  英文主 README + 中文 README-zh（互链），更新到 0.5.1：卖点表（MLC / 指令速查 / 热键 / 插件 / 下载 / 皮肤 / 多实例 / 0.5.1 界面自定义 / i18n / 日志）、
  Releases 下载表与 SHA-256、环境与安装、源码运行与前端构建、测试、打包命令、数据目录、项目结构、插件示例（JSON + vein API）、
  贡献与安全入口、MIT 与商标声明。删除已废弃的安装器/旧版本说明 · 已提交
