# Vein Launcher v0.1.0 — 内部文档（团队版）

> 适用对象：VL 项目团队成员。对外发布请使用 `RELEASE_NOTES.md`。
> 对应提交：`34a1dba`（插件硬化后的 main）。本文最后一次同步：2026-11-03。

---

## 1. 版本与发布

| 项 | 值 |
| --- | --- |
| 版本号 | `0.1.0` |
| Git tag | `v0.1.0` |
| 发布时间 | 2026-10-31T10:01:54Z |
| 发布页 | https://github.com/zhanjhn-studio/vein_launcher/releases/tag/v0.1.0 |
| 资产 1 | `VeinLauncher-0.1.0-win64.zip` — 249,873,131 B（≈238 MB），便携版 |
| 资产 2 | `latest.json` — 453 B，更新检查的公开兜底清单 |
| 包体 | PyInstaller onedir，解压后 615 MB（QtWebEngine 占主要体积） |

发布说明见仓库根 `RELEASE_NOTES.md`（英文 + 中文两段）。`latest.json` 内容：

```json
{ "version": "0.1.0", "asset": "VeinLauncher-0.1.0-win64.zip",
  "url": "https://github.com/.../releases/download/v0.1.0/VeinLauncher-0.1.0-win64.zip" }
```

---

## 2. 架构总览

```
React 19 (WebView)  ⇄  QWebChannel + JSON-RPC 2.0  ⇄  Python 五层
        │                                                   │
   Layui 控件层                                    Node 插件宿主（独立进程）
```

- **通信协议**：`{jsonrpc, id, method, params:{args}}`；回包 `window.__veinResult`；
  推送 `__veinProgress / __veinLog / __veinNotify / __veinNavigate`
- **五层**：Common（事件总线、配置、日志、i18n、工具）→ Domain（模型、仓储契约、
  版本解析）→ Infrastructure（HTTP、下载、进程、MC2、插件宿主）→ Application（版本/皮肤/
  实例/更新/插件等服务）→ Presentation（Qt 窗口、bridge、webui）
- **MLC**：`vein_launcher/mlc/` 承载游戏控制桥与插件能力入口
- **前端**：React 负责页面与路由；Layui 只提供表单/进度/勾选等控件结构（`styles.css` 覆盖外观）

规模：Python ≈7,790 行，前端 ≈4,641 行，JSON-RPC 方法 **60** 个。

---

## 3. 模块与状态

| 模块 | 关键文件 | 状态 | 说明 |
| --- | --- | --- | --- |
| 启动器窗口 | `presentation/main.py` | ✅ | 无边框自绘标题栏、最小化/最大化/关闭、尺寸收敛 |
| 通信桥 | `presentation/bridge.py` | ✅ | 60 个方法 + 进度/日志推送 |
| 版本与下载 | `application/services/version_service.py`、`infrastructure/download/*` | ✅ | 逐文件进度、失败可见、并发 8、断点续传、SHA-1 |
| 镜像 | `infrastructure/network/mirror.py`、`http_client.py` | ✅ | BMCLAPI 优先、官方回退；镜像证书异常时自动降级不校验并记忆 |
| 加载器 | `application/services/loader_service.py` | ✅ | Fabric / Forge / Quilt / NeoForge |
| 模组资源 | `infrastructure/network/modrinth_api.py` | ✅ | 搜索、按版本/加载器过滤、图标（远程图片已在 `file://` 下放行） |
| 账号 | `application/services/account_service.py`、`microsoft_auth.py`、`littleskin.py` | 🟡 | 离线 ✅、LittleSkin ✅、微软链路完整但被服务端 403（见 §8） |
| 皮肤 | `application/services/skin_service.py`、`skinsPage.tsx` | ✅ | 导入 PNG（64×64/64×32 校验）、读 LittleSkin 当前皮肤、公开皮肤库下载 |
| 实例管理 | `application/services/instance_service.py`、`instancePage.tsx` | ✅ | 模组/资源包/光影/数据包/整合包启停与删除、存档列表、种子扫描、删实例 |
| 世界分析 MC2 | `infrastructure/mc2/*` | 🟡 | `level.dat` 解析种子/版本/难度；群系结构尚未做成表格 |
| 插件系统 | `infrastructure/plugin_host/*`、`plugin_service.py` | ✅ | Node 独立进程、权限校验、宿主崩溃自动重启（≤3 次）、能力调用 30s 超时、`ui.openPage` |
| 一键更新 | `application/services/update_service.py` | ✅ | GitHub API → `latest.json` → 公告 `update` 字段三级回退；下载断点、zip 解包、exe 启动 |
| 公告/强制更新 | `infrastructure/network/announcement_client.py` | ✅ | 读 `zhanjhn.github.io/vl/public.js`，1h 缓存 |
| 主题/语言 | `webui/src/theme.ts`、`i18n.ts`、`prefs.ts` | ✅/🟡 | 深色/浅色/透明/跟随系统；英文默认，可切简体中文（覆盖主导航与设置） |
| 界面动效 | `webui/src/styles.css` | ✅ | 侧栏 280ms 悬停展开、文字滑入、导航悬停位移；壁纸/简洁模式/空闲淡出 |

---

## 4. 数据目录与日志

运行目录（exe 同级或仓库根）：

```
VeinLauncher/
├── config/       config.json、accounts.json、skins.json、language.json、wallpapers/
├── log/          launcher-*.log、plugin-*.log、mlc-*.log、download-*.log、error.log、crash.log
├── minecraft/    instances/、versions/、libraries/、assets/
├── downloads/    下载缓存、update/
├── plugin/       Node 插件
├── java/         自动下载的运行时
├── skins/        皮肤 PNG（按账号 id）
└── democrat/     社区数据（预留）
```

约定：**日志只写文件，不输出控制台**；插件、MLC、下载日志分文件。

---

## 5. 构建与打包

```powershell
# 1) 前端
cd vein_launcher\presentation\webui
powershell -ExecutionPolicy Bypass -File build.ps1

# 2) 测试
python -m unittest discover -s tests

# 3) 打包（PyInstaller onedir）
python -m PyInstaller --noconfirm --clean --windowed --name VeinLauncher `
  --icon "assets\logo.ico" `
  --distpath packaging\dist --workpath packaging\build --specpath packaging `
  --add-data "vein_launcher\presentation\webui\dist;webui\dist" `
  --add-data "assets;assets" packaging\entry.py

# 4) 压缩并发布
tar -a -c -f packaging\VeinLauncher-0.1.0-win64.zip -C packaging\dist VeinLauncher
gh release create v0.1.0 packaging\VeinLauncher-0.1.0-win64.zip packaging\latest.json `
  --title "Vein Launcher 0.1.0" --notes-file RELEASE_NOTES.md
```

注意：
- 打包后资源从 `_MEIPASS` 读取（`main.py` 的 `_resources_dir()` / `_webui_dir()` 已适配）
- 发布资产必须包含新的 `latest.json`，否则更新回退链只剩公告源
- **发布 Release 必须由项目负责人明确指令**，日常只提 PR/提交

---

## 6. 验证记录（v0.1.0）

| 验证项 | 方法 | 结果 |
| --- | --- | --- |
| 单元测试 | `python -m unittest discover -s tests` | 44 项通过 |
| 下载全流程 | 无头安装 1.20.1 | 3640/3640 文件，`failed=0`，71.5s（缓存命中） |
| 更新检测 | `UpdateService('0.0.3').latest()` | `available=true, version=0.1.0, source=latest.json` |
| 更新下载 | 下载 `latest.json` 资产 | 453 B，进度回调 `(453,453)` |
| 打包运行 | 运行 `packaging/dist/VeinLauncher/VeinLauncher.exe` | 版本 0.1.0，前端从 `_internal/webui/dist` 加载成功 |
| 插件系统 | `tools/plugin_selftest.py` | 9/9 PASS（队友提交 `34a1dba`） |
| 远程图片 | 最小页面 + rAF/`naturalWidth` | Modrinth 图标 96×96 加载成功 |
| 侧栏动效 | rAF 采样宽度 | 68→108→141→…→208，约 200ms 插值 |

---

## 7. 团队协作规则

1. 改动前：`git pull` → 读 `teamwork.md` 的 **In progress** → 读本文件的模块状态
2. 改动中：小步提交；边界清楚（谁改哪个目录写进任务/task）
3. 改动后：跑测试 + 前端构建 → 追加 `teamwork.md` 条目 → 与代码一起提交
4. 停下来时：把条目放进 **In progress** 并写清下一步
5. 讨论/决策：写入 [DISCUSSION.md](DISCUSSION.md)，编号 `D-xxx`，决议落下后标 `accepted`

---

## 8. 已知问题与风险

### 阻塞项

| # | 问题 | 影响 | 计划 |
| --- | --- | --- | --- |
| 1 | 微软登录 `login_with_xbox` 返回 403 `Invalid app registration` | 正版账号不可用 | 等 Minecraft Services 白名单；或经负责人同意改官方旧版授权码流程（灰色） |
| 2 | 公告站 `public.js` 仍写 `0.0.3` | 应用内公告横幅版本落后 | 需要更新 Pages 仓库 |

### 功能欠账

| # | 问题 | 现状 |
| --- | --- | --- |
| 3 | 世界分析面板直接展示 MC2 原始 JSON | 待做群系/结构表格 |
| 4 | 中文翻译只覆盖主导航与设置 | 页面正文仍英文 |
| 5 | zip 更新是「解压到 update 目录」 | 未实现关停后原地替换的更新器 |
| 6 | 安装包未签名 | SmartScreen 可能提示 |

### 风险

| # | 风险 | 说明 |
| --- | --- | --- |
| 7 | 令牌明文存 `config/` | 建议后续加 DPAPI 加密 |
| 8 | 镜像证书缺失时降级不校验 SSL | 已限定 BMCLAPI 节点，仍属权衡 |
| 9 | 微软/LittleSkin 第三方登录合规 | 官方旧版流程属灰色地带，需负责人决策 |
| 10 | 包体 615 MB | 可考虑拆分 QtWebEngine 或增量更新 |
| 11 | 插件宿主依赖本机 Node 18+ | 未内嵌 Node 运行时 |

---

## 9. 下一步建议（按优先级）

1. 世界分析表格化（种子 → 出生点群系/结构摘要）
2. 原地更新器（`updater.exe`：等待主程序退出 → 替换 → 重启）
3. 中文翻译补全（页面正文、按钮）
4. 令牌加密存储（Windows DPAPI）
5. 插件市场/示例插件扩充
6. 打包瘦身与安装器（可选 NSIS/Inno）

具体讨论见 [DISCUSSION.md](DISCUSSION.md)。
