# Vein Launcher

[English](README.md) | **简体中文**

<p align="center">
  <img src="assets/logo.png" width="96" alt="Vein Launcher" />
</p>

<p align="center">
  <b>Vein，掌控 Minecraft</b><br />
  面向 Windows 的便携 Minecraft Java 启动器：安装、管理、启动，还能在不装任何 mod 的原版里直接控制游戏。
</p>

<p align="center">
  <a href="https://github.com/zhanjhn-studio/vein_launcher/releases/tag/v0.5.1"><img alt="version" src="https://img.shields.io/badge/version-0.5.1-orange" /></a>
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows%2010%2F11%20x64-2f6fe0" />
  <a href="LICENSE"><img alt="license" src="https://img.shields.io/badge/license-MIT-green" /></a>
  <img alt="tests" src="https://img.shields.io/badge/tests-51%20passing-1f9d55" />
</p>

---

## 亮点

| 能力 | 你能得到什么 |
|---|---|
| **MLC 原版控制** | 约 5 KB 的 Java agent 挂到原版实例上（不需要 Fabric/Forge）：读玩家状态、执行指令、订阅游戏事件。总开关默认关闭，关闭时后端直接拒绝。 |
| **指令速查** | `Ctrl+Alt+Q` 打开附魔书风格面板，方向键选择，`Enter` 直接发进游戏；失败自动复制到剪贴板。 |
| **全局热键** | `Ctrl+Alt+0..9` 执行绑定指令：优先走 MLC，不可用时回退复制。 |
| **插件系统** | 每个插件独立 Node 进程，权限声明、路径沙箱、30 秒超时；Lua UI 渲染在 Shadow DOM。 |
| **下载** | BMCLAPI 镜像优先、官方源回退、断点续传、SHA-1 校验、同目标串行去重。 |
| **皮肤** | LittleSkin 走 authlib-injector；本地 PNG 皮肤配 Fabric + CustomSkinLoader。 |
| **多实例** | 每个实例独立目录、独立进程、独立 MLC 端口。 |
| **界面（0.5.1）** | 默认浅色 + 橙色主题；支持圆角、界面缩放、动效开关与任意主色。 |
| **中英双语** | 启动器、日志与文档均支持简体中文与 English。 |
| **日志** | 只写文件，按 `launcher / download / mlc / plugin` 分类、按天切分，不输出到控制台。 |

## 下载

从 **[GitHub Releases](https://github.com/zhanjhn-studio/vein_launcher/releases/latest)** 获取最新版本：

| 文件 | 大小 | 说明 |
|---|---|---|
| `VeinLauncher-0.5.1-win64.zip` | 约 199 MB | Windows x64 便携包，解压运行 `VeinLauncher.exe` |
| `latest.json` | 约 0.4 KB | GitHub API 限流时的更新兜底清单 |

SHA-256（`VeinLauncher-0.5.1-win64.zip`）：

```
BD6ADBC34054DB327B12621580B9C5749FF92D5AB5657FC04255C9016E7BC5E0
```

### 环境要求

- Windows 10 / 11 x64
- **不需要手动安装 Java**：启动器会检测本机运行时或自动下载对应大版本
- 只有使用插件功能才需要 Node.js 18+

### 安装

1. 把压缩包解压到任意目录（例如 `D:\VeinLauncher`）。
2. 双击 `VeinLauncher.exe`，首次启动会在同级生成 `VeinLauncher/` 数据目录。
3. 打开「下载」安装原版或加载器版本，回到「启动」按启动。

没有安装器、不写注册表；删除目录即卸载。

## 从源码运行

```bash
git clone https://github.com/zhanjhn-studio/vein_launcher
cd vein_launcher
python -m pip install -r requirements.txt
python -m vein_launcher.presentation.main
```

改了 `webui/src` 之后必须重新构建前端（Qt 加载的是构建产物 `dist/`）：

```powershell
cd vein_launcher/presentation/webui
powershell -ExecutionPolicy Bypass -File build.ps1
```

测试：

```bash
python -m unittest discover -s tests
python tools/plugin_selftest.py
python tools/mlc_selftest.py
```

## 打包发布

```bash
python tools/build_exe.py --version 0.5.1
```

产物：`dist_exe/VeinLauncher/`、`dist_exe/VeinLauncher-0.5.1-win64.zip`、`dist_exe/latest.json`。

## 数据目录

所有运行数据都在 exe 同级，整体可迁移、可删除：

```
VeinLauncher/
  config/       配置：config.json / accounts.json / tools.json
  log/          日志：launcher / download / mlc / plugin，按天切分
  minecraft/    实例、库、资源
  plugin/       插件
  downloads/    下载缓存
  agent/        MLC agent jar
```

## 项目结构

```
vein_launcher/
  common/           事件总线、配置、日志、i18n、工具
  domain/           模型、仓储契约、领域规则
  infrastructure/   网络、下载、进程、mc2、插件宿主、MLC agent 构建
  application/      服务层（版本 / 皮肤 / 实例 / 更新 / 插件 / 游戏登记）
  mlc/              控制层协议与状态
  presentation/     Qt 窗口、JSON-RPC 桥、指令速查窗、webui/
    webui/          React 19 + TypeScript 源码与构建产物
tests/              单元测试
tools/              构建与自检脚本（agent、打包、UI 预览、文档生成）
plugins_examples/   示例插件（template / game-log / lua-ui / mlc-panel / status-panel）
assets/             启动器使用的 logo 与图标
```

架构约定：跨层只通过 `common/events/event_bus.py` 通信；UI 只经 `presentation/bridge.py` 的
JSON-RPC 调后端，不直接碰文件、网络与进程。

## 插件开发

插件放在 `VeinLauncher/plugin/`，`package.json` 里带 `vein` 字段：

```json
{
  "name": "vein-plugin-hello",
  "version": "0.1.0",
  "type": "module",
  "main": "index.js",
  "vein": {
    "displayName": "Hello",
    "activateOnStartup": false,
    "permissions": ["ui.notify", "config.read", "mlc.state"]
  }
}
```

```js
export async function activate(vein) {
  await vein.ui.notify("Hello", "插件已启动");
  vein.mlc.on("game.enter", () => vein.log("进入了世界"));
}
```

可用能力：`file`、`config`、`ui.notify/render/openPage`、`http.getJson`、`download.queueTask`、
`game.launch/running/command`、`app.info`、`versions.list` 以及整套 `mlc.*`
（受权限与 MLC 总开关双重限制）。

`plugins_examples/` 里有可直接运行的示例，其中 `status-panel` 会把启动器版本、实例、运行中游戏
与 MLC 状态展示在一个面板里。

## 参与贡献

- BUG 与需求：[Issues](https://github.com/zhanjhn-studio/vein_launcher/issues)
- 使用交流与插件分享：[Discussions](https://github.com/zhanjhn-studio/vein_launcher/discussions)
- 代码贡献：见 [CONTRIBUTING.md](CONTRIBUTING.md)。提交信息使用 Conventional Commits，保持分层边界；
  改前端要重新构建 `dist`，新增 RPC 要补测试。

安全问题请勿公开提 issue，使用 GitHub 私密漏洞报告。

## 许可证

[MIT](LICENSE) © 2026 zhanjhn studio。

Vein Launcher 与 Mojang / Microsoft 无隶属关系，Minecraft 是 Mojang Synergies AB 的商标。
