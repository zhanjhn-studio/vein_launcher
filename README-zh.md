# Vein Launcher

[English](README.md) | **简体中文**

面向 Windows 的 Minecraft Java 版启动器。设计取向是实用：Python 严格分层、React + TypeScript
界面、Node.js 插件宿主，以及自研的 MLC 控制层（插件据此操控游戏）。

---

## 特性概览

| 方向 | 做法 |
|---|---|
| 架构 | Python（Common / Domain / Infrastructure / Application / Presentation）+ PySide6 WebView |
| 前端 | React 19 + TypeScript、JSON-RPC 2.0 桥、7 项一级导航、三栏布局 |
| 插件 | Node.js 独立进程宿主、双向 JSON-RPC、权限校验、路径沙箱、热重载 |
| MLC | 启动游戏、读取存档、订阅游戏事件，按权限开放给插件 |
| 下载 | 优先 BMCLAPI 镜像、失败回退官方、SHA-1 校验、断点续传、同目标串行 |
| 日志 | 只写文件（不进控制台）：`launcher/plugin/mlc/download` 分类按天存放 |
| 目录 | 与 exe 同级生成 `VeinLauncher/`：`plugin/ log/ config/ minecraft/ downloads/ democrat/` |

## 环境要求

- Windows 10/11
- Python 3.11+
- Node.js 18+（插件宿主）

## 从源码运行

```bash
python -m pip install -r requirements.txt
python -m vein_launcher.presentation.main
```

首次启动会创建数据根目录：

```
<exe 或仓库>/VeinLauncher/
├── democrat/     社区数据（预留）
├── plugin/       Node 插件
├── log/          按类别、按天存放日志
├── config/       启动器配置
├── minecraft/    版本、库、资源
└── downloads/    下载缓存
```

## 前端构建

```bash
cd vein_launcher/presentation/webui
esbuild src/main.tsx --bundle --outfile=dist/app.js --jsx=automatic --minify
```

`dist/` 已随仓库提交；仅在修改 `src/` 后需要重新构建。

## 通信协议

前端与 Python 通过 QWebChannel 上的 JSON-RPC 2.0 通信：

```json
{"jsonrpc": "2.0", "id": 12, "method": "versions.install", "params": {"args": ["1.20.1", "fabric"]}}
```

推送通道：`__veinProgress`、`__veinLog`、`__veinNotify`、`__veinNavigate`。

## 插件最小示例

```js
export async function activate(vein) {
  vein.log(`hello from ${vein.plugin.displayName}`);
  await vein.file.writeText(`${vein.plugin.dataDir}/hello.txt`, 'hi');
  vein.mlc.on('game.log', (e) => vein.log(e.line));
}
```

`package.json` 的 `vein.permissions` 声明能力，未声明的调用会被宿主拒绝。

## 当前进度

已实现：原版与 Fabric/Quilt 安装、Modrinth 浏览与安装（含缩略图）、插件宿主与管理界面、
MLC 启动/存档/事件、镜像下载、分类文件日志。

规划中：公告与强制更新（zhanjhn.github.io）、Java 自动下载、MC2 种子与世界分析、
Lua UI 沙箱、插件市场。

## 许可证

见 [LICENSE](LICENSE)。
