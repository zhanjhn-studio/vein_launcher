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
| 当前 HEAD | `ac86ef1`（feat(tools): 指令构建器 + 全局热键 + Ctrl+Alt+Q 速查小窗） |
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
