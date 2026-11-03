# Vein Launcher 0.1.0 — 内部文档索引

面向团队的内部文档（不对外发布），对应仓库 `main` 上的 **v0.1.0** 公开版。

| 文档 | 内容 |
| --- | --- |
| [INTERNAL.md](INTERNAL.md) | 版本概览、架构、模块清单、数据与日志、构建/打包/发布流程、验证记录、已知问题与风险 |
| [DISCUSSION.md](DISCUSSION.md) | **讨论页**：待决议题、已定决议、议题模板、同步记录 |
| [../../teamwork.md](../../teamwork.md) | 日常变更日志（每次改动都要追加） |
| [../../CONTRIBUTING.md](../../CONTRIBUTING.md) | 参与规范：分层约束、编码/提交规范、工作流 |

## 一页速览

| 项 | 值 |
| --- | --- |
| 版本 | `0.1.0`（`vein_launcher/presentation/context.py`） |
| 发布 | [v0.1.0](https://github.com/zhanjhn-studio/vein_launcher/releases/tag/v0.1.0)，2026-10-31 |
| 发布资产 | `VeinLauncher-0.1.0-win64.zip`（≈238 MB）、`latest.json`（453 B） |
| 技术栈 | Python 3.13 + PySide6 6.12 WebEngine · React 19 + TypeScript（esbuild）· Layui 控件 · Node 插件宿主 |
| 规模 | Python ≈7,790 行 · 前端 ≈4,641 行 · JSON-RPC 方法 60 个 |
| 测试 | 44 项（`python -m unittest discover -s tests`） |
| 平台 | Windows 10/11 x64（PyInstaller onedir，615 MB） |

## 当前状态摘要

- 启动、下载、实例管理、皮肤、账号、插件、更新七条主链路可用
- 已知阻塞：微软登录被 Minecraft Services 拒绝（`Invalid app registration`），离线与 LittleSkin 不受影响
- 默认：英文界面 + 深色主题 + 简洁模式**关闭**
- 协作方式已固定：先读 `teamwork.md`，改动后追加记录，与代码一起提交
