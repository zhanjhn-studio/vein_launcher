# 项目进度

## Vein Launcher - Minecraft Java 启动器 🦋

**技术栈**：Python 3.11+ / PySide6 / aiohttp / Pydantic v2 / Node.js 18+（插件宿主）
**目标平台**：Windows
**核心特色**：内置 Node.js 插件宿主（双向 JSON-RPC + 权限沙箱）

---

## 📊 整体进度总览

| 层级 | 状态 | 完成度 | 文件数 |
|------|------|--------|--------|
| L5 Common（公共层） | ✅ 完成 | 100% | 13 |
| L3 Domain（领域层） | ✅ 完成 | 100% | 10 |
| L4 Infrastructure（基础设施层） | ✅ 完成 | 100% | 15 |
| L2 Application（应用服务层） | ✅ 完成 | 100% | 6 |
| L1 Presentation（表现层） | ✅ 完成（代码） | 95% | 10 |
| 测试 / CI / 打包 / 文档 | ✅ 完成 | 100% | 8 |

> 总计约 60 个源文件；2026-10-28 完成阶段性收束并推送 GitHub。

---

## ✅ Phase 1 - Common 公共层

- `events/event_bus.py` 线程安全事件总线（跨层通信唯一通道）
- `events/events.py` 40+ 业务事件常量，新增 8 个插件事件
- `config/settings.py` Pydantic 配置模型 + JSON 单例存储
- `i18n/` 中英语言包 + 翻译器
- `logging/logger.py` 控制台 + 按日文件 + error.log
- `utils/path_utils.py` 路径 API（新增插件目录 / 沙箱目录 / 包名净化）
- `utils/version_utils.py` 版本比较与格式化
- `exceptions.py` 业务异常体系

## ✅ Phase 2 - Domain 领域层

- `models/version.py` 版本 JSON / 库 / 资源索引模型
- `models/account.py` 离线 + 微软账号（修复 Pydantic v2 `const` 兼容）
- `models/launcher.py` Fabric/Forge/Quilt 加载器规范
- `models/mod.py` 统一 ModInfo / ModFile / 依赖图
- `models/plugin.py` 插件清单、权限枚举、RPC 接口契约
- `services/version_resolver.py` 继承链合并
- `repositories/` 文件与网络仓储抽象

## ✅ Phase 3 - Infrastructure 基础设施层

### 下载子系统
- `download/downloader.py` 断点续传 + 令牌桶限速 + 流式 SHA-1 + 原子落盘
  + 指数退避 + 镜像回退 + `Semaphore` 并发 + 事件通知

### 网络子系统
- `network/api_client.py` aiohttp 会话封装（UA/代理/超时/重试/JSON）
- `network/mojang_api.py` 版本清单、版本 JSON、资源索引
- `network/fabric_api.py` Fabric / Quilt Loader 版本与安装 profile
- `network/modrinth_api.py` 搜索 / 项目 / 版本 / 结果映射
- `network/curseforge_api.py` 搜索 / 文件（需 API Key）

### 存储与系统
- `storage/file_storage.py` Assets / Libraries / Mods 仓储实现、natives 解压
- `process/java_detector.py` 配置 → JAVA_HOME → 注册表 → PATH → 常见目录
- `process/game_process.py` 子进程 + stdout 实时广播 + terminate/kill

### 🔌 插件宿主（核心特色）
- `plugin_host/host.py` Node 子进程 + JSON-RPC 2.0（请求/响应/通知三态）
- `plugin_host/capabilities.py` 能力注册表 + 权限校验 + 路径沙箱
- `plugin_host/loader.py` 插件扫描、清单解析、npm/本地安装、启停状态
- `plugin_host/runtime/node_host.js` 插件加载、`vein` API 注入、异常隔离
- `plugins_examples/hello-world/` 示例插件

**端到端验证（2026-10-28）**：安装 → 激活 → RPC invoke → 事件桥接
→ 沙箱写入 → 越权拦截 → 权限拒绝 → 停用 → 关闭，10 项全部通过。

## ✅ Phase 4 - Application 应用层

- `services/version_service.py` 版本合并、安装编排（client/libraries/natives/assets）、卸载
- `services/launcher_service.py` 启动命令构建（占位符/规则/离线 UUID）+ 启动
- `services/account_service.py` 账号持久化、离线账号、微软设备码登录骨架
- `services/mod_service.py` Modrinth 搜索 / 一级 required 依赖解析 / 安装 / 启停
- `services/plugin_service.py` 插件编排 + 默认能力注入 + 事件桥接
- `presentation/context.py` 服务装配

## ✅ Phase 5 - Presentation 表现层

- `presentation/bridge.py` 后台 asyncio 循环 + Qt 信号桥接
- `presentation/ui/main_window.py` 侧边导航 + 页面栈 + 状态栏
- `pages/home_page.py` 版本/账号选择、启动、实时日志
- `pages/versions_page.py` 远程版本列表、安装进度、删除
- `pages/mods_page.py` 模组搜索与安装
- `pages/plugins_page.py` 插件表格、权限展示、宿主能力目录、运行日志
- `pages/settings_page.py` Java 探测、内存、分辨率、主题、语言
- `theme/dark.qss` 深色主题

## 🧪 测试与工程化

- `tests/` 20 项 unittest（下载器含真实本地 HTTP 服务、启动命令、事件总线、插件权限）
- `.github/workflows/ci.yml` Windows + Ubuntu × Py3.11/3.12，含打包 job
- `build.py` PyInstaller 打包脚本（目录/单文件，自动收集主题/QSS/locales/运行时）
- `run_launcher.py` 打包入口
- `docs/PLUGIN_DEV.md` 插件开发指南（协议、权限、事件、调试、安全建议）
- `preview.html` UI 静态预览（**本地文件，不提交 git**）

---

## ⏳ 已知限制 / 下一步

1. **GUI 未在本机运行验证**：当前环境无 PySide6 且 PyPI 不可达，
   仅通过 `compileall` 静态校验；CI 中有真实运行条件。
2. **加载器自动安装未接线**：Fabric/Quilt API 客户端已完成，
   但「创建 fabric-1.20.4 版本实例」的编排仍需补齐。
3. **CurseForge Key** 需在设置中提供（当前 API 层支持，UI 未暴露输入框）。
4. **微软登录** 仅完成设备码获取/轮询骨架，Xbox → Minecraft 令牌链未实现。
5. 下载队列的暂停/取消（`download.queue.py`）尚未抽出独立模块。

---

## 📝 变更记录

### 2026-10-28
- 修复 Domain 层 3 处编译错误（account 括号、plugin 参数顺序、version 缺 Union）
- 修复 Pydantic v2 `const` 已移除导致的账号模型加载失败
- 新增下载器、全部 API 客户端、存储、Java 探测、进程管理
- 完成 Node.js 插件宿主（Python 侧 + Node 运行时 + 沙箱 + 示例插件）
- 完成应用层 5 个服务与表现层 5 个页面
- 新增 20 项单元测试、CI、打包脚本、插件开发文档
- 首次推送 GitHub（仓库此前仅有 LICENSE）

### 2026-10-27
- 初始化 Common / Domain 层与项目文档
