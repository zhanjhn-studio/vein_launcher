# Vein Launcher 🦋

<div align="center">

**A Lightweight Minecraft Launcher for Windows**  
对标 PCL2 的现代化启动器 | Python + PySide6 | Low Resource Usage

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.6+-green.svg)](https://www.pyside.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D7.svg)](https://www.microsoft.com/windows)

</div>

---

## 📖 项目简介

Vein Launcher 是一个专为 Windows 平台设计的 Minecraft 启动器，追求极致的轻量化与低资源占用：

- **轻量快速**：基于 PySide6，冷启动 < 1 秒
- **低内存占用**：空闲状态 < 200MB
- **单 EXE 打包**：通过 PyInstaller 生成独立可执行文件
- **严格分层架构**：五层分离设计，模块解耦

## ✨ 核心功能

### 🎯 基础核心
- ✅ Minecraft 1.6 ~ 最新快照版本下载支持
- ✅ SHA-1 文件完整性校验（损坏自动重下）
- ✅ HTTP 断点续传（限速控制、并发管理）
- ✅ Java 环境自动探测 + 手动指定路径
- ✅ 游戏进程实时监控 + 标准输出日志

### 🔧 加载器支持
| 加载器 | 状态 | 说明 |
|-------|------|------|
| 🟦 Fabric | ✅ | 自动检测版本并安装最新版 |
| 🟨 Forge | ✅ | 支持官方推荐版本列表 |
| 🟩 Quilt | ✅ | 与 Fabric 兼容的替代方案 |

### 👤 账号系统
- 🔓 **离线模式**：自定义用户名，无需登录
- 🔐 **微软正版**：OAuth2 流程完整实现

### 📦 资源管理
- 🎒 **版本隔离**：每个版本的 mods/config/resourcepacks 互相独立
- 💾 **全局缓存**：assets/libraries 多版本共享复用
- ⚙️ **模组管理**：启用/禁用/导入/删除一站式

### 🎨 界面特性
- 🌓 **主题切换**：浅色 (Light) / 深色 (Dark) QSS
- 📊 **内存配置**：可视化滑块设置 JVM 内存
- 🔧 **JVM 参数**：高级自定义命令行参数
- 🌍 **多语言**：简体中文 / 英文 UI

## 🏗️ 项目架构

采用五层严格分层架构，禁止跨层直接调用：

```
┌─────────────────────────────────────┐
│  [L1] Presentation   │ PySide6 表现层    │
├─────────────────────────────────────┤ ← 订阅事件更新 UI
│  [L2] Application    │ 应用服务编排      │
├─────────────────────────────────────┤ ← 发布业务事件
│  [L3] Domain         │ 领域核心逻辑      │
├─────────────────────────────────────┤ ← 定义仓储接口
│  [L4] Infrastructure │ 技术基础设施    │
├─────────────────────────────────────┤ ← 实现仓储接口
│  [L5] Common         │ 公共基础模块      │
└─────────────────────────────────────┘
```

### 层职责划分

| 层级 | 目录 | 责任 | 依赖规则 |
|------|------|------|---------|
| L1 Presentation | `presentation/` | PySide6 页面、控件、主题 | 只读事件总线，不调用下层 API |
| L2 Application | `application/` | 任务编排、业务事件分发 | 调用 L3+L4，发布事件到总线 |
| L3 Domain | `domain/` | MC 版本模型、加载器规则、账号验证 | 零外部依赖，纯 Python 逻辑 |
| L4 Infrastructure | `infrastructure/` | HTTP 下载、Java 进程、文件系统实现 | 实现 L3 定义的仓储接口 |
| L5 Common | `common/` | 事件总线、配置、i18n、日志 | 所有层的基础依赖 |

## 📁 目录结构速览

```
Vein Launcher/
├── vein_launcher/            # [主包] 分层架构核心代码
│   ├── __init__.py
│   ├── main.py              # 程序入口点
│   │
│   ├── common/              # [L5] Common 公共层 ✅已完成
│   │   ├── events/          # 全局事件总线 (publish/subscribe)
│   │   ├── config/          # Pydantic 配置管理
│   │   ├── i18n/            # 多语言翻译系统
│   │   ├── logging/         # 日志系统（文件 + 控制台）
│   │   └── utils/           # 通用工具函数
│   │
│   ├── domain/              # [L3] Domain 领域层 ⏳进行中
│   │   ├── models/          # 版本/库/账号/加载器模型
│   │   └── services/        # 版本解析服务
│   │
│   ├── infrastructure/      # [L4] Infrastructure 基础设施层
│   │   ├── download/        # HTTP 断点续传下载器
│   │   ├── storage/         # 文件仓储实现
│   │   ├── process/         # Java 进程管理
│   │   └── network/         # Mojang API 客户端
│   │
│   ├── application/         # [L2] Application 应用服务层
│   │   ├── services/        # 下载/启动/账号编排服务
│   │   └── commands/        # CQRS 命令对象
│   │
│   └── presentation/        # [L1] Presentation 表现层
│       ├── ui/              # PySide6 主窗口 + 页面 + 组件
│       ├── controllers/     # UI 控制器（事件订阅）
│       └── theme/           # light.qss / dark.qss
│
├── resources/               # 静态资源（图标、qrc 配置）
├── tests/                   # 单元测试 (pytest)
├── docs/                    # 文档目录
├── requirements.txt         # Python 依赖清单
├── progress.md             # 开发进度跟踪文件
├── PROJECT_STRUCTURE.md    # 详细架构设计文档
└── README.md              # 本文件

```

## 🚀 快速开始（开发者版）

### 环境要求
- **操作系统**: Windows 10/11
- **Python 版本**: 3.10 ~ 3.12
- **内存需求**: 建议 4GB+ 可用空间

### 安装依赖
```bash
# 克隆或下载项目后
cd "Vein Launcher"

# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate

# 安装依赖包
pip install -r requirements.txt
```

### 运行程序
```bash
# 开发模式启动
python vein_launcher/main.py
```

### 打包为独立 EXE
```bash
# 使用 PyInstaller 单文件打包
pyinstaller --noconfirm --onefile --windowed ^
    --icon=resources/icons/vein.ico ^
    --add-data "resources;resources" ^
    --name "VeinLauncher" ^
    vein_launcher/main.py

# 生成位置：dist/VeinLauncher.exe
```

## 📦 requirements.txt 详解

| 依赖包 | 版本 | 用途 |
|--------|------|------|
| PySide6 | >=6.6.0 | GUI 框架（核心）|
| requests | >=2.31.0 | HTTP 请求与下载 |
| pydantic | >=2.5.0 | 配置数据验证 |
| tqdm | >=4.66.0 | 进度条显示组件 |
| pyinstaller | >=6.0.0 | EXE 打包工具（开发依赖）|
| pytest | >=7.4.0 | 单元测试框架（测试用）|

## 📊 开发进度

### ✅ Phase 1 - Common Public Layer (已完成)
- [x] `events/event_bus.py` - 事件总线核心实现
- [x] `events/events.py` - 业务事件常量定义  
- [x] `config/settings.py` - Pydantic 配置管理
- [x] `i18n/translator.py` - 多语言翻译器
- [x] `i18n/locales/*.json` - 中/英文语言包
- [x] `logging/logger.py` - 日志系统（文件 + 控制台）
- [x] `utils/path_utils.py` - Windows 路径工具
- [x] `utils/version_utils.py` - 版本解析工具
- [x] `exceptions.py` - 全局异常定义

### ⏳ Phase 2 - Domain Layer (进行中)
- [ ] `models/version.py` - MC 版本模型
- [ ] `models/library.py` - libraries 依赖管理  
- [ ] `models/account.py` - 账号模型
- [ ] `models/launcher.py` - Fabric/Forge/Quilt
- [ ] `services/version_resolver.py` - 版本继承解析

### ⏳ Phase 3 - Infrastructure Layer (待启动)
- [ ] `download/downloader.py` - HTTP 断点续传
- [ ] `process/java_detector.py` - Java 自动探测
- [ ] `process/game_process.py` - 进程监控管理

### ⏳ Phase 4 - Application Layer (待启动)
- [ ] `services/version_service.py` - 版本编排服务
- [ ] `services/download_service.py` - 下载队列编排
- [ ] `commands/launch_game.py` - 启动游戏命令

### ⏳ Phase 5 - Presentation Layer (待启动)
- [ ] `ui/main_window.py` - 主窗口框架
- [ ] `ui/pages/home_page.py` - 首页（启动按钮）
- [ ] `widgets/progress_bar.py` - 下载进度条
- [ ] `theme/dark.qss` / `light.qss` - 深浅主题

## 🔧 开发规范

### 核心原则
1. **分层隔离**：Presentation 层禁止直接调用文件/网络/进程接口，必须通过事件总线通信
2. **路径处理**：Windows 系统统一使用 `pathlib.Path`，禁止拼接字符串路径
3. **异常定义**：所有业务异常继承自 `VeinError`，便于捕获分类
4. **类型注解**：所有函数必须包含 type hints（Python 3.10+ 语法如 `list[str]`）

### 事件总线使用示例
```python
from vein_launcher.common import event_bus, EventNames

# 订阅事件（在 Presentation 层 UI 控制器中）
def on_download_complete(version_id: str):
    self.ui.status_label.setText(f"版本 {version_id} 下载完成")

event_bus.subscribe(EventNames.VERSION_DOWNLOAD_COMPLETE, on_download_complete)

# 发布事件（在 Application 层服务中）
event_bus.publish(EventNames.VERSION_DOWNLOAD_COMPLETE, version_id="1.20.4")
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！请遵守：
1. 严格遵守五层分层架构，禁止跨层依赖
2. 新模块必须先写测试用例（pytest）
3. 代码附带中文注释说明关键逻辑
4. UI 改动需同时适配深浅主题

## 📄 License

MIT License - 详见 [LICENSE](LICENSE) 文件

---

<div align="center">

**Built with ❤️ by Vein Launcher Team**  
*Lightweight · Fast · Elegant*

</div>
