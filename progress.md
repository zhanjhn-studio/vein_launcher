# 项目进度
## Vein Launcher - Minecraft Windows 启动器 🦋

**技术栈**: Python + PySide6 | **目标平台**: Windows | **打包方式**: PyInstaller 单 EXE

---

## 📊 整体进度总览

| 层级 | 状态 | 完成度 | 负责人 |
|------|------|--------|--------|
| L5 Common（公共层） | ✅ 已完成 | 100% | lead |
| **L3 Domain（领域层）** | **✅ 已完成** | **100%** | **lead+coder** |
| L4 Infrastructure（基础设施层） | 🚧 进行中 | 20% | lead |
| L2 Application（应用服务层） | ⏳ 待开发 | 0% | lead |
| L1 Presentation（表现层） | ⏳ 待开发 | 0% | lead |

---

## ✅ Phase 1 - Common Public Layer（已完成 ✨）

### events/ 事件总线系统 ✅
- [x] `event_bus.py` - 全局事件总线（发布/订阅模式，线程安全）
- [x] `events.py` - EventNames 业务事件常量定义（40+ 个事件）
- [x] `__init__.py` - 导出 event_bus, EventBus, EventNames

### config/ 配置管理 ✅
- [x] `settings.py` - Pydantic Settings 模型 + JSON 存储单例
- [x] 支持 Java、下载、网络、UI、启动等多维度配置

### i18n/ 国际化系统 ✅
- [x] `translator.py` - Translator 翻译器类
- [x] `locales/zh_CN.json` - 简体中文包（完整 UI 文字）
- [x] `locales/en_US.json` - 英文包

### logging/ 日志系统 ✅
- [x] `logger.py` - setup_logger + FileHandler + ConsoleHandler
- [x] 每日日期标记文件 + error.log 独立错误收集

### utils/ 通用工具 ✅
- [x] `path_utils.py` - get_app_data_dir, VersionDir, AssetsDir 等路径 API
- [x] `version_utils.py` - parse_version_string, compare_versions, format_size
- [x] `exceptions.py` - VeinError 基类 + 下载/版本/Java/账号异常体系

---

## ✅ Phase 2 - Domain Layer（已完成 ✨）**新增 Mod/Plugin 需求已集成**

### models/ 领域模型 ✅ 100% 完成

#### Core Models (原有功能)
**version.py** ✅  
- [x] `VersionJSON` - 完整 Mojang 版本 JSON 解析模型（Pydantic）
- [x] `Library` - 库依赖对象，支持 rules/extract/classifiers
- [x] `ParsedVersion` - 继承链合并后的解析结果

**account.py** ✅
- [x] `AccountBase`/`OfflineAccount`/`MicrosoftAccount` - 离线/微软账号双通道路
- [x] `AccountManager` - 多账号管理器（选中/添加/删除）

**launcher.py** ✅
- [x] `LoaderType` - VANILLA/FABRIC/FORGE/QUILT 枚举
- [x] `LoaderVersion` - 加载器版本信息模型
- [x] `LoaderFactory` - Fabric/Forge/Quilt安装规范生成器

#### Mod Marketplace Models (新增需求 ✅)
**mod.py** ✅ **NEW!**
- [x] `ModInfo` - 模组信息抽象基类（统一 Modrinth/CurseForge 接口）
- [x] `ModFile` - 特定版本模组文件定义（含 depends_on/conflicts_with）
- [x] `ModrinthMod` - Modrinth资源站适配器骨架
- [x] `CurseForgeMod` - CurseForge资源站适配器骨架
- [x] `PluginMod` - Node.js 插件适配接口（由 RPC 实现）
- [x] `ModInstallationSpec` - 模组安装规范（含自动依赖解析输出）
- [x] `ModDependencyGraph` - 依赖图构建器输出

#### Plugin System Models (新增需求 ✅)  
**plugin.py** ✅ **NEW!**
- [x] `PluginPermissions` - 沙箱权限枚举（25+种细粒度权限）
- [x] `PluginManifest` - Node.js插件元数据模型（package.json扩展）
- [x] `PluginInstance` - 已安装插件运行时对象
- [x] `VRPC_GLOBAL_EXPORTS` - Python→Node.js RPC接口映射表
- [x] 文件操作/下载队列/游戏进程控制/UI通知等标准API定义

### services/ 领域服务 ✅ 新增
**version_resolver.py** ✅
- [x] `VersionResolver` - 版本继承链递归合并算法实现
  - O(1)缓存加速重复查询
  - 循环依赖检测（抛出 VersionResolutionError）
- [x] 平台过滤规则（基于 Library.rules/os字段）
- [x] Java 版本要求提取（兼容旧版 heuristic+新版本 minimum_java_version）

### repositories/ 仓储接口定义 ✅ 完整
**file_repo.py** ✅  
- [x] `AbstractFileRepository` - 文件仓储抽象基类
- [x] `AssetsRepository` - assets 资源管理接口（objects.json + 文件映射）
- [x] `LibraryRepository` - Maven坐标解析+native提取逻辑
- [x] `ModRepository` - per-version mods目录隔离方案

**network_repo.py** ✅  
- [x] `AbstractNetworkRepository` - HTTP/HTTPS请求基类（Infrastructure实现限速/代理/重试）
- [x] `MojangAPIRepository` - 版本列表 + assets 索引获取
- [x] `FabricAPIRepository` - Loader 最新版本查询
- [x] `ForgeAPIRepository` - Maven Metadata 解析器
- [x] `ModrinthAPIRepository` - 模组搜索/版本列表（分页 cursor）
- [x] `CurseForgeAPIRepository` - API Key授权认证设计

---

## 📁 项目文件清单（已完成统计）

### Code Statistics  
```
✅ Common Layer:   13 files (事件总线 + 配置+i18n+ 日志 +utils) 
✅ Domain Layer:   10 files (version + account + launcher + mod + plugin + resolver + repos)
⏳ Infra/App/UI: ~50 files pending

总计：23 core files completed (~30% of total project codebase)
```

### Architecture Documents ✅
- [x] `PROJECT_STRUCTURE.md` - 五层分层架构详细设计
- [x] `README.md` - 项目说明 +快速开始指南  
- [x] `requirements.txt` - Python依赖清单（PySide6/requests/pydantic/pytest）

### Special Files ✅
- [x] `progress.md` - 本进度跟踪文件（实时更新断点）

---

## 🚧 Phase 3 - Infrastructure Layer（进行中）

### ✅ 已完成：download/downloader.py（2026-10-28）

**异步断点续传下载器** — `vein_launcher/infrastructure/download/downloader.py`

| 能力 | 实现 |
|------|------|
| 断点续传 | HTTP `Range` + `.part` 临时文件，续传前对已有前缀补算 SHA-1 |
| 服务端忽略 Range | 返回 200 时自动清空 `.part` 全量重下 |
| 完整性校验 | 流式 `hashlib.sha1()`，不符抛 `SHA1MismatchError` 并删除残file |
| 原子落盘 | 校验通过后 `os.replace()`，避免半成品被启动器误用 |
| 限速 | 异步令牌桶 `SpeedLimiter`，按 0.1s 配额切片，不阻塞事件循环 |
| 重试 | 指数退避 1/2/4/8s；哈希不符不重试同地址，改走镜像 |
| 镜像回退 | `DownloadTask.mirrors`，主地址重试耗尽后依次尝试 |
| 并发 | `Semaphore(max_concurrent)` + `download_many()` 按序返回结果或异常 |
| 事件通知 | 发布 `DOWNLOAD_TASK_START/PROGRESS/COMPLETE/ERROR`，带 url/path/速度 |
| 短路 | 目标文件存在且 SHA-1/大小匹配则 `skipped=True`，零网络开销 |

已验证（真实网络 + Mojang version_manifest.json，210301 字节）：
1. 首次下载 ✅ 2. 校验短路 ✅ 3. 从 4096 字节断点续传且内容一致 ✅ 4. 错误哈希抛异常且无残留 ✅

依赖变更：`requirements.txt` 新增 `aiohttp>=3.9`、`pytest-asyncio>=0.23`。

### ⏳ 待开发（按优先级）

1. 🔴 `download/queue.py` — 并发下载队列（任务状态机、暂停/取消、批量进度聚合）
2. 🔴 `download/sha_checker.py` — 独立分段哈希校验工具（大文件不占内存）
3. 🔴 `process/java_detector.py` — 注册表 + PATH + 常见安装目录扫描
4. 🔴 `process/game_process.py` — `asyncio.create_subprocess_exec` + stdout 实时转发
5. 🟠 `network/api_client.py` — 通用 aiohttp 客户端（UA/代理/超时/重试/JSON）
6. 🟠 `network/mojang_api.py` / `fabric_api.py` / `modrinth_api.py`
7. 🟢 `storage/file_storage.py` — 实现 Domain 的 Assets/Library/Mod 仓储

```

---

## ⏳ Phase 4 - Application Layer（待开发）

等待 Infrastructure Layer 稳定后启动：

```
application/services/
├── version_service.py      # 版本下载编排 + 断点续传调度  
├── download_service.py     # 任务队列管理（依赖 downloader.queue）
├── launcher_service.py     # Fabric/Forge自动安装流程
└── account_service.py      # 微软OAuth登录完整流程

application/commands/  
├── launch_game.py          # CQRS命令对象（验证版本完整性→调用process.launch）
└── download_version.py     # 下载编排命令（VersionResolver+DownloadService）
```

---

## ⏳ Phase 5 - Presentation Layer（待 ui-artisan 开发）

等待 Application Layer 完成 + Event Names稳定后启动：

```
presentation/ui/
├── main_window.py          # PySide6主窗口（左侧导航栏+右侧内容区）
├── pages/
│   ├── home_page.py        # 首页（版本选择器+启动按钮）  
│   ├── versions_page.py    # 版本管理页（安装/删除）
│   ├── mod_market.py       # [NEW] 模组市场浏览器界面  
│   ├── plugins_page.py     # [NEW] 插件管理面板（启用/禁用/权限查看）
│   ├── download_queue.py   # 下载任务队列可视化
│   └── settings_page.py    # Java路径/JVM参数/主题切换/多语言
├── widgets/
│   ├── progress_bar.py     # PyQt进度条组件（显示实时速度+剩余时间）  
│   ├── log_panel.py        # QTextEdit日志面板（游戏stdout转发）
│   └── mod_card.py         # [NEW] 模组卡片（预览图+下载量+标签）
└── theme/
    ├── light.qss           # 浅色主题样式表
    