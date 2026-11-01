# 贡献指南 / Contributing

Vein Launcher 是一个基于 **Python + PySide6** 的 Minecraft Java 版启动器，采用五层分层架构。
提交代码前请先阅读本文件。

## 一、环境准备

```powershell
# 1. 安装依赖
pip install -r requirements.txt

# 2. 验证包可导入
python -c "import vein_launcher; print('OK')"

# 3. 运行测试
python -m pytest tests -q

# 4. 启动程序
python -m vein_launcher.presentation.main
```

前端（React）如需修改：

```powershell
cd vein_launcher\presentation\webui
powershell -ExecutionPolicy Bypass -File build.ps1
```

> `build.ps1` 需要 `esbuild`：已安装到 PATH、设置 `$env:ESBUILD`，或用 `-Esbuild <path>` 指定。
> `node_modules/` 与 `dist/` 均不入库，本地构建后再启动程序。

## 二、架构约束（强约束，PR 会被据此审查）

依赖方向只有一条，不许反向：

```
Presentation → Application → Domain ← Infrastructure
                    ↑
                  Common（被所有层依赖）
```

| 层 | 目录 | 允许 | 禁止 |
|---|---|---|---|
| Presentation | `vein_launcher/presentation/` | 渲染 UI、订阅事件总线 | 直接调用文件 / 网络 / 进程接口 |
| Application | `vein_launcher/application/` | 编排任务、协调 Domain 与 Infrastructure | 实现业务规则、直接操作 UI 控件 |
| Domain | `vein_launcher/domain/` | 纯 Python 业务模型与规则 | 引入 aiohttp / PySide6 / 文件 IO |
| Infrastructure | `vein_launcher/infrastructure/` | HTTP、文件仓储、进程、外部 API | 引用 Application / Presentation |
| Common | `vein_launcher/common/` | 事件总线、日志、i18n、配置、工具 | 依赖任何上层 |

**跨模块通信统一走事件总线**（`vein_launcher/common/events/event_bus.py`），禁止模块间直接硬依赖调用。

## 三、编码规范

- 路径统一使用 `pathlib.Path`，**禁止**字符串拼接路径。
- 网络请求统一异步（`aiohttp`），不要在新代码里引入阻塞 IO。
- 每个文件职责单一，模块顶部写清用途注释。
- 公开函数 / 类补充 docstring；复杂分支补行内注释。
- 不擅自新增需求之外的功能、页面或配置项。

## 四、提交规范

使用 Conventional Commits：

```
feat(ui): 默认浅色主题 + PCL2 风蓝绿配色
fix(download): 修复并发下载 .part 文件占用冲突
docs(readme): 补充构建步骤
refactor(domain): 拆分版本解析逻辑
```

- 一个提交只做一件事，避免混合重构与功能。
- 提交前确保 `python -m pytest tests -q` 通过、`python -m compileall vein_launcher` 无错误。
- 同步更新 [teamwork.md](teamwork.md) 的变更记录。

## 五、工作流

1. `git pull` 取最新代码
2. 阅读 [teamwork.md](teamwork.md) 确认当前进行中的工作，避免冲突
3. 新建分支开发：`git checkout -b feat/your-feature`
4. 完成后跑测试与自检
5. 提 PR 到 `main`，说明改动范围与验证方式

## 六、不入库的文件

以下内容仅本地保留，已在 `.gitignore` 中排除：

- 运行时数据：`VeinLauncher/`、日志、下载缓存
- 前端依赖与构建产物：`node_modules/`、`dist/`
- 打包产物：`packaging/build/`、`dist/`、`*.spec`
- 个人文档与脚本：`.local/`、`*.docx`、`make_*.py`