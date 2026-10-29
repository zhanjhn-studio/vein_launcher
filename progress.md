# 项目进度

## Vein Launcher - Minecraft Java 启动器

**技术栈**：Python + PySide6 + aiohttp + Pydantic v2
**目标平台**：Windows
**架构**：Common / Domain / Infrastructure / Application / Presentation（五层）
**界面方案**：PySide6 `QWebEngineView` 承载 React 前端，Python↔JS 通过通信桥交互；
Node.js 仍作为独立的插件宿主（双向 RPC）。

> 开发纪律：只实现需求与架构中明确写出的内容；分片开发，一次只写一个文件；
> 跨层通信只走 event_bus；路径统一 pathlib。

---

## 进度总览

| 层级 | 状态 | 说明 |
|------|------|------|
| Common 公共层 | ✅ 完成 | 事件总线、配置、i18n、日志、路径工具、异常 |
| Domain 领域层 | ✅ 完成 | 版本/账号/加载器/模组/插件模型，解析服务，仓储接口 |
| Infrastructure 基础设施层 | 🚧 进行中 | 当前：network/http_client.py |
| Application 应用服务层 | ⏳ 未开始 | |
| Presentation 表现层 | ⏳ 未开始 | |

---

## ✅ Common

- `events/event_bus.py` 线程安全发布/订阅
- `events/events.py` 事件名常量
- `config/settings.py` Pydantic 配置 + JSON 单例
- `i18n/translator.py` + `locales/zh_CN.json`、`en_US.json`
- `logging/logger.py` 控制台 + 按日文件 + error.log
- `utils/path_utils.py`、`utils/version_utils.py`
- `exceptions.py`

## ✅ Domain

- `models/version.py` 版本 JSON / 库 / 资源索引
- `models/account.py` 离线 / 微软账号
- `models/launcher.py` Fabric / Forge / Quilt 规范
- `models/mod.py` 模组模型与依赖图
- `models/plugin.py` 插件清单、权限、RPC 契约
- `services/version_resolver.py` 继承链合并
- `repositories/file_repo.py`、`repositories/network_repo.py` 抽象接口

## 🚧 Infrastructure

- ✅ `network/http_client.py`（2026-10-29）
  - aiohttp 会话封装：User-Agent、超时、全局代理
  - `get_json()` / `get_text()`
  - 瞬时错误重试（429/5xx/网络异常，1s/2s/4s 退避）
  - 统一异常 `HttpClientError`

  实测：拉取 Mojang 版本清单成功（921 个版本）。

- ✅ `network/api_client.py`（2026-10-29）
  - `fetch_version_list()` / `fetch_latest()` / `fetch_version(id)` / `fetch_assets_index(url)`
  - 版本清单内存缓存一次

  实测：1.20.4 版本 JSON 获取成功（88 个库，assets 索引 3811 个对象）。

- ✅ `network/modrinth_api.py`、`network/curseforge_api.py`
  - 搜索 / 版本 / 文件映射；CurseForge 需 API Key

- ✅ `download/downloader.py`、`sha_checker.py`、`queue.py`
  - 断点续传、SHA-1 校验、并发队列（事件总线广播进度）

- ✅ `process/java_detector.py`、`process/game_process.py`
  - Java 探测（注册表 / JAVA_HOME / PATH / 常见目录），进程日志转发

- ✅ `storage/file_storage.py`
  - 版本目录、库路径、assets 对象路径、校验与原子写入

## ✅ Application

- `version_service.py` 版本合并、安装（client / libraries / assets）
- `launcher_service.py` 启动命令构建、natives 解压、拉起进程
- `account_service.py` 离线账号持久化

## ✅ Presentation（WebView + React）

- `main.py` QWebEngineView 主窗口（原生边框）
- `bridge.py` QWebChannel 桥：`app.info`、`versions.*`、`launch`、`accounts.*`、`mods.*`、`java.detect`
- `webui/` React 19（esbuild 本地打包，无需 npm 联网）
  - 深色科技风：左侧导航 + 面板
  - 页面：启动 / 版本 / 下载 / 模组 / 账号 / 设置

启动方式：`python -m vein_launcher.presentation.main`

---

## 下一步

1. 插件宿主（Node.js 双向 RPC）—— 项目核心特色，优先完成
2. 模组安装的实例选择与依赖处理
3. 界面细节打磨（按验收反馈）

---

## 🧠 MLC 控制层

`vein_launcher/mlc/service.py`，接口与插件宿主共享：

| 接口 | 说明 | 状态 |
|------|------|------|
| mlc.launch | 启动游戏并返回 PID | 可用 |
| mlc.world.info | 读取实例存档列表 | 可用 |
| mlc.world.create | 创建存档目录（世界生成仍需游戏内完成） | 可用 |
| mlc.event.subscribe | 订阅 game.log / game.exit / download.progress | 可用 |
| mlc.player.info | 玩家坐标等 | 未实现（需游戏侧 mod） |
| mlc.mod.load | 运行时加载模组 | 未实现 |
| mlc.plugin.search | 搜索已安装插件 | 可用 |

## 🔌 插件宿主（核心特色）

- `infrastructure/plugin_host/runtime/node_host.js`：Node 侧 JSON-RPC、`vein` API 注入、异常隔离
- `infrastructure/plugin_host/host.py`：Python 侧进程与协议、能力转发
- `capabilities.py`：能力注册 + 权限校验（未声明即拒绝）
- `loader.py`：扫描 plugins/、解析清单、内置 demo 自动安装
- `application/services/plugin_service.py`：能力实现（文件/下载/游戏/配置/UI/HTTP/MLC）+ 事件桥
- `plugins_examples/demo/`：demo 插件

**端到端实测**：宿主启动 → demo 激活 → 读取配置 → 写沙箱文件 → 调用 MLC world.info
→ 越权读取 `C:\Windows\win.ini` 被拒绝 → 就绪。

## 🌉 通信桥（与规格对齐）

`versions.info / versions.remote / versions.install / versions.delete / launch /
accounts.list|add|select / mods.search / mods.install / java.detect`

推送通道：`window.__veinProgress`（下载进度）、`window.__veinLog`（游戏日志）、
`window.__veinNotify`（插件通知）。

---

## 待完成（按规格）

1. Forge / Fabric / NeoForge 加载器安装与整合包
2. 服务器插件（Paper 等）、光影、数据包的下载入口
3. 微软账号登录
4. CurseForge 在界面中的启用（需 API Key）
5. 广场模块：仅在文档中预留，本轮不实现

## 变更记录

### 2026-10-29
- 上一轮交付整体作废（UI 风格不符预期、超出需求自行加功能）
- 工作区回滚至 Domain 基线，移除 infrastructure/application/presentation 等全部产出
- 重新从 `infrastructure/network/http_client.py` 开始
- 交付 MLC demo、插件宿主与 demo 插件、通信桥对齐、React 界面日志面板
