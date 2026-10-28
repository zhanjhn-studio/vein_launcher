# Vein Launcher - 完整项目目录结构

## 📁 目录总览

```
Vein Launcher/
├── vein_launcher/              # 主应用包（分层架构）
│   ├── __init__.py            # 包初始化
│   ├── main.py                # 程序入口点
│   │
│   ├── common/                # [第 5 层] Common 公共层
│   │   ├── __init__.py
│   │   ├── events/            # 全局事件总线
│   │   │   ├── __init__.py
│   │   │   ├── event_bus.py   # 事件中心
│   │   │   ├── events.py      # 所有事件定义
│   │   │   └── handlers.py    # 事件处理器基类
│   │   ├── config/            # 配置管理
│   │   │   ├── __init__.py
│   │   │   ├── settings.py    # 全局设置
│   │   │   └── user_config.py # 用户配置文件
│   │   ├── i18n/              # 国际化 multi-language
│   │   │   ├── __init__.py
│   │   │   ├── translator.py  # 翻译器
│   │   │   ├── locales/       # 语言文件
│   │   │   │   ├── zh_CN.json # 简体中文
│   │   │   │   └── en_US.json # 英文
│   │   │   └── i18n.py        # i18n 工具函数
│   │   ├── logging/           # 日志系统
│   │   │   ├── __init__.py
│   │   │   └── logger.py      # 日志配置
│   │   └── utils/             # 通用工具
│   │       ├── __init__.py
│   │       ├── path_utils.py  # 路径处理（Windows pathlib）
│   │       ├── version_utils.py# 版本解析
│   │       └── exceptions.py  # 异常定义
│   │
│   ├── domain/                # [第 3 层] Domain 领域层
│   │   ├── __init__.py
│   │   ├── models/            # 领域模型
│   │   │   ├── __init__.py
│   │   │   ├── version.py     # MC 版本模型
│   │   │   ├── library.py     # 依赖库模型
│   │   │   ├── account.py     # 账号模型
│   │   │   └── launcher.py    # 加载器模型（Fabric/Forge/Quilt）
│   │   ├── services/          # 领域服务
│   │   │   ├── __init__.py
│   │   │   ├── version_resolver.py  # 版本解析服务
│   │   │   ├── loader_installer.py  # 加载器安装规则
│   │   │   └── account_validator.py # 账号验证规则
│   │   └── repositories/      # 仓储接口定义
│   │       ├── __init__.py
│   │       ├── file_repo.py   # 文件仓储接口
│   │       └── network_repo.py# 网络仓储接口
│   │
│   ├── infrastructure/        # [第 4 层] Infrastructure 基础设施层
│   │   ├── __init__.py
│   │   ├── download/          # 下载管理器
│   │   │   ├── __init__.py
│   │   │   ├── downloader.py  # HTTP 断点续传
│   │   │   ├── queue.py       # 下载队列
│   │   │   └── sha_checker.py # SHA 校验
│   │   ├── storage/           # 文件存储实现
│   │   │   ├── __init__.py
│   │   │   └── file_storage.py# 本地文件仓储
│   │   ├── process/           # Java 进程管理
│   │   │   ├── __init__.py
│   │   │   ├── java_detector.py# Java 自动探测
│   │   │   └── game_process.py# 游戏启动与监控
│   │   └── network/           # 网络请求实现
│   │       ├── __init__.py
│   │       ├── api_client.py  # Mojang API 客户端
│   │       └── proxy.py       # 代理设置
│   │
│   ├── application/           # [第 2 层] Application 应用服务层
│   │   ├── __init__.py
│   │   ├── services/          # 应用服务
│   │   │   ├── __init__.py
│   │   │   ├── version_service.py  # 版本管理服务
│   │   │   ├── download_service.py # 下载编排服务
│   │   │   ├── account_service.py  # 账号服务
│   │   │   └── launcher_service.py # 启动器服务（Fabric/Forge）
│   │   └── commands/          # 应用命令
│   │       ├── __init__.py
│   │       ├── download_version.py  # 下载版本命令
│   │       ├── launch_game.py       # 启动游戏命令
│   │       └── manage_account.py    # 账号管理命令
│   │
│   └── presentation/          # [第 1 层] Presentation 表现层
│       ├── __init__.py
│       ├── ui/                # PySide6 界面
│       │   ├── __init__.py
│       │   ├── main_window.py # 主窗口
│       │   ├── pages/         # 页面模块
│       │   │   ├── __init__.py
│       │   │   ├── home_page.py      # 首页（启动按钮）
│       │   │   ├── versions_page.py  # 版本管理页
│       │   │   ├── download_page.py  # 下载页
│       │   │   ├── mods_page.py      # 模组管理页
│       │   │   ├── account_page.py   # 账号页
│       │   │   └── settings_page.py  # 设置页
│       │   ├── widgets/       # 通用组件
│       │   │   ├── __init__.py
│       │   │   ├── progress_bar.py   # 进度条
│       │   │   ├── log_panel.py      # 日志面板
│       │   │   ├── version_card.py   # 版本卡片
│       │   │   └── account_widget.py # 账号组件
│       │   └── theme/         # 主题系统
│       │       ├── __init__.py
│       │       ├── light.qss    # 浅色主题
│       │       └── dark.qss     # 深色主题
│       └── controllers/       # UI 控制器（订阅事件）
│           ├── __init__.py
│           ├── home_controller.py
│           ├── versions_controller.py
│           └── settings_controller.py
│
├── resources/                 # 静态资源
│   ├── icons/                # 图标文件
│   ├── assets/               # 启动器自身资源
│   └── qrc.qrc              # Qt 资源编译文件
│
├── tests/                     # 单元测试
│   ├── __init__.py
│   ├── test_domain/
│   ├── test_infrastructure/
│   └── test_application/
│
├── docs/                      # 文档
│   ├── architecture.md       # 架构说明
│   ├── api_reference.md     # API 参考
│   └── user_guide.md        # 用户指南
│
├──requirements.txt           # Python 依赖
├──pyinstaller.spec          # PyInstaller 打包配置
├──README.md                 # 项目说明
├──LICENSE                   # 开源协议
└──progress.md               # 开发进度跟踪（特殊文件）
```

---

## 🏗️ 分层架构详解

### 第 1 层：Presentation（表现层）
**负责人**: ui-artisan  
**职责**: PySide6 GUI、主题切换、动画效果

| 模块 | 功能 |
|------|------|
| main_window.py | 主窗口框架，导航栏 + 页内容区 |
| pages/ | 所有页面（首页、版本、下载、模组、账号、设置） |
| widgets/ | 可复用 UI 组件（进度条、日志面板、卡片） |
| theme/ | QSS 样式表（light.qss / dark.qss） |
| controllers/ | UI 控制器，仅订阅事件更新界面 |

**规则**: 禁止直接调用文件/网络/进程接口，必须通过事件总线与 Application 层通信。

---

### 第 2 层：Application（应用服务层）
**负责人**: coder  
**职责**: 任务编排、接收 UI 请求、协调领域与基础设施

| 模块 | 功能 |
|------|------|
| version_service.py | 版本获取/列表/下载编排 |
| download_service.py | 调用 Infrastructure 下载器，发布进度事件 |
| account_service.py | 离线/微软账号登录流程 |
| launcher_service.py | Fabric/Forge/Quilt 自动安装编排 |
| commands/ | CQRS 模式命令对象（download_version、launch_game） |

**规则**: 不实现业务逻辑，只协调 Domain + Infrastructure；通过事件总线发布业务事件。

---

### 第 3 层：Domain（领域层）
**负责人**: coder  
**职责**: Minecraft 核心业务模型与规则

| 模块 | 功能 |
|------|------|
| models/version.py | MC 版本 JSON 解析、版本继承树构建 |
| models/library.py | libraries 依赖管理、平台过滤 |
| models/account.py | 离线/正版账号模型 |
| models/launcher.py | Fabric/Forge/Quilt 加载器规则 |
| services/version_resolver.py | 版本继承链解析（父版本合并） |
| services/loader_installer.py | 加载器版本选择与安装规则 |

**规则**: 无外部依赖，纯 Python 业务逻辑；定义仓储接口（不实现）。

---

### 第 4 层：Infrastructure（基础设施层）
**负责人**: coder  
**职责**: HTTP 下载、Java 进程管理、文件操作、网络请求

| 模块 | 功能 |
|------|------|
| download/downloader.py | requests + stream 断点续传、限速、并发控制 |
| download/queue.py | 任务队列、优先级的待处理 |
| download/sha_checker.py | SHA-1 文件校验，损坏自动重下 |
| storage/file_storage.py | assets/libraries/mods 文件存储实现 |
| process/java_detector.py | Windows 注册表扫描 + 常见路径扫描 Java |
| process/game_process.py | subprocess 启动 Java、stdout 实时监听、强制关闭 |
| network/api_client.py | Mojang API / meta.launchmc.net 请求 |
| network/proxy.py | 全局代理设置（HTTP/SOCKS5） |

**规则**: 实现 Domain 定义的仓储接口；提供技术基础设施。

---

### 第 5 层：Common（公共层）
**负责人**: lead（我先完成）  
**职责**: 跨层共享的基础设施

| 模块 | 功能 |
|------|------|
| events/event_bus.py | 全局事件总线（publish/subscribe） |
| events/events.py | 所有业务事件定义（VersionDownloaded、GameStarted） |
| config/settings.py | Pydantic 配置模型，INI/JSON 存储 |
| i18n/translator.py | 多语言翻译器，中英文切换 |
| logging/logger.py | 统一日志配置（文件 +控制台） |
| utils/path_utils.py | Windows 路径处理（pathlib） |
| utils/exceptions.py | 全局异常定义（DownloadError、JavaNotFoundError） |

**规则**: 最底层被所有层依赖，禁止反向依赖。

---

## 📦 依赖文件

### requirements.txt
```
PySide6>=6.6.0
requests>=2.31.0
pyinstaller>=6.0.0
pydantic>=2.5.0
tqdm>=4.66.0
```

### PyInstaller 打包命令
```bash
pyinstaller --noconfirm --onefile --windowed --icon=resources/icons/vein.ico \
    --add-data "resources;resources" \
    --name "VeinLauncher" \
    vein_launcher/main.py
```

---

## 🚀 下一步开发顺序

1. ✅ Common 公共层（事件总线、日志、配置、i18n） ← 现在开始
2. ⏳ Domain 领域层（版本模型、加载器规则、账号模型）
3. ⏳ Infrastructure 基础设施层（下载器、Java 探测、进程管理）
4. ⏳ Application 应用服务层（编排逻辑）
5. ⏳ Presentation 表现层（PySide6 GUI）
6. ⏳ 集成测试与打包

---

**创建时间**: 2026-10-26  
**当前状态**: 等待 Common 层开发开始
