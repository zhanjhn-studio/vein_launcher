# 项目进度

## Vein Launcher - Minecraft Java 启动器

**技术栈**：Python + PySide6 + aiohttp + Pydantic v2
**目标平台**：Windows
**架构**：Common / Domain / Infrastructure / Application / Presentation（五层）

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

---

## 下一步

1. `network/api_client.py` —— Mojang API 客户端（版本清单 / 版本 JSON / assets 索引）
2. `download/downloader.py` —— 断点续传下载
3. 再按架构顺序推进 application / presentation

---

## 变更记录

### 2026-10-29
- 上一轮交付整体作废（UI 风格不符预期、超出需求自行加功能）
- 工作区回滚至 Domain 基线，移除 infrastructure/application/presentation 等全部产出
- 重新从 `infrastructure/network/http_client.py` 开始，一次一个文件
