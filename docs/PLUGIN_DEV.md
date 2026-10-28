# Vein Launcher 插件开发指南

> 版本：API v1.0 · 宿主运行时 `vein_plugin_host 1.0.0` · 需要 Node.js 18+

Vein Launcher 的插件是**标准 NPM 包**，运行在独立的 Node.js 子进程中，
通过 **JSON-RPC 2.0（stdio，逐行 JSON）** 与启动器双向通信。

```
┌──────────────────────────┐        stdio (JSON-RPC)        ┌────────────────────────┐
│  Python 主进程            │  ←──── host.call ───────────    │  Node.js 插件宿主       │
│  PluginHost              │  ───── plugin.load ────────→    │  runtime/node_host.js  │
│  CapabilityRegistry      │  ───── event.emit ─────────→    │  ┌──────────────────┐  │
│  event_bus               │  ←──── plugin.log/error ───     │  │ @scope/my-plugin │  │
└──────────────────────────┘                                  │  └──────────────────┘  │
                                                              └────────────────────────┘
```

---

## 1. 最小插件

目录结构：

```
plugins/my-plugin/
├── package.json
├── index.js
└── data/                # 运行时自动创建，插件唯一可读写目录
```

`package.json`：

```json
{
  "name": "@acme/vein-plugin-hello",
  "version": "1.0.0",
  "description": "示例插件",
  "author": "ACME",
  "type": "module",
  "main": "index.js",
  "vein": {
    "displayName": "你好插件",
    "apiVersion": "1.0",
    "pluginType": "utility",
    "activateOnStartup": true,
    "permissions": ["file.read", "file.write", "ui.notify"]
  }
}
```

`index.js`：

```js
export async function activate(vein) {
  vein.log("已激活");

  vein.on("game.launch.start", (payload) => {
    vein.ui.notify("启动中", `版本 ${payload.version_id ?? "?"}`, "info");
  });
}

export async function deactivate() {
  // 释放资源
}

// 可被宿主 invoke 的命令
export const commands = {
  async ping() {
    return { pong: true, at: Date.now() };
  },
};
```

安装：

- 图形界面：`插件页 → 从文件夹安装…`
- 代码方式：`await plugin_service.install_from_dir(Path("./my-plugin"))`
- NPM：`await plugin_service.install_from_npm("@acme/vein-plugin-hello")`

---

## 2. 生命周期

| 阶段 | 触发 | 说明 |
|------|------|------|
| `plugin.load` | 用户在插件页启用 / 启动时 `activateOnStartup` | 宿主解析入口、注入 `vein` API |
| `activate(vein)` | 加载后立即调用 | 异步，最长 10 秒，超时视为失败 |
| `event.emit` | 启动器事件发生 | 转发到 `vein.on` 注册的处理器 |
| `plugin.invoke` | 宿主主动调用插件命令 | 调用 `commands` 命名空间或模块导出 |
| `deactivate()` | 停用 / 退出 | 可选钩子 |
| `plugin.unload` | 卸载 | 清理事件订阅 |

任一插件抛异常**不会影响其他插件**：宿主捕获后上报 `plugin.error` 事件并记录日志。

---

## 3. 清单字段（`package.json` 的 `vein` 段）

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `displayName` | string | 包名 | 界面显示名 |
| `apiVersion` | string | `"1.0"` | 使用的宿主 API 版本 |
| `pluginType` | enum | `"utility"` | `mod_helper` / `theme` / `automation` / `utility` |
| `permissions` | string[] | `[]` | 权限声明，见下表 |
| `activateOnStartup` | bool | `false` | 启动器启动时自动激活 |
| `main` | string | `dist/main.js` | 入口文件（相对插件根目录） |
| `icon` | string | — | 图标相对路径 |
| `locales` | object | `{}` | `{ "zh_CN": "locales/zh_CN.json" }` |

---

## 4. 权限与能力

声明了权限才能调用对应能力，**未声明即拒绝**（错误码 `-32003`），并广播
`plugin.permission.denied` 事件供 UI 展示。

| 能力 | 所需权限 | 参数 | 说明 |
|------|----------|------|------|
| `file.readText(path)` | `file.read` | 路径 | 读取文本文件（沙箱内） |
| `file.writeText(path, content)` | `file.write` | 路径、内容 | 写入文本文件（沙箱内） |
| `file.listDir(path)` | `file.read` | 路径 | 列出目录 |
| `download.queueTask(url, savePath)` | `download.queue` | URL、保存路径 | 加入下载队列，返回 taskId |
| `download.cancel(taskId)` | `download.cancel` | 任务 ID | 取消下载 |
| `game.launch(versionId, memoryMb)` | `game.launch` | 版本、内存 | 启动游戏，返回 `{ pid, ... }` |
| `ui.notify(title, message, type)` | `ui.notify` | 标题、正文、类型 | 全局通知 |
| `config.get()` | `config.read` | — | 读取启动器配置 |
| `config.set(key, value)` | `config.write` | 键、值 | 修改配置（落盘） |
| `http.getJson(url)` | `network.http` | URL | 经宿主代理的 GET |

### 路径沙箱

`file.*` 的路径会被 `resolve()` 后与允许根目录比对：

- `plugins/<plugin-id>/`（插件自身目录）
- `plugins/<plugin-id>/data/`（插件数据目录，推荐写这里）

任何越界路径都会抛 `PluginPermissionError`，例如 `C:\Windows\win.ini` 会被拒绝：

```
[host] 🚫 越权拦截：插件 @vein/plugin-hello 尝试读取 C:\Windows\win.ini
```

---

## 5. 事件

`vein.on(topic, handler)` 订阅启动器事件；`handler(payload, topic)` 可 async。

| 事件 | payload 关键字段 |
|------|------------------|
| `version.download.start` | `version_id` |
| `version.download.progress` | `version_id, phase, done, total, percent` |
| `version.download.complete` | `version_id` |
| `version.download.error` | `version_id, errors` |
| `download.task.progress` | `url, path, downloaded, total, speed` |
| `download.task.complete` | `url, path, bytes_written` |
| `game.launch.start` | `command, cwd` |
| `game.running` | `pid` |
| `game.log.update` | `line` |
| `game.exited` | `exit_code, pid` |
| `account.selected` | `account_id` |
| `mods.updated` | `version_id` |
| `settings.updated` | `key` |
| `theme.changed` | `theme` |

---

## 6. RPC 协议

**Python → Node**（请求）：

```json
{"jsonrpc":"2.0","id":1,"method":"plugin.load","params":{"pluginId":"@acme/x","entry":"...","manifest":{...},"dataDir":"..."}}
```

**Node → Python**（能力调用）：

```json
{"jsonrpc":"2.0","id":9,"method":"host.call","params":{"pluginId":"@acme/x","api":"file.readText","args":["data/a.json"]}}
```

**通知**（无 `id`，不需响应）：

```json
{"jsonrpc":"2.0","method":"plugin.log","params":{"pluginId":"@acme/x","level":"info","message":"hi"}}
```

约定：
- `stdout` **只允许** JSON-RPC 行；插件里的 `console.log` 被重定向到 `stderr`。
- 能力调用默认 30 秒超时；`game.launch` 为 60 秒。
- 错误码：`-32603` 内部错误，`-32003` 权限/沙箱拒绝。

---

## 7. 调试

- 图形界面 → 插件页 → **运行日志** 标签页，实时查看宿主日志与拦截记录。
- 也可直接调用 Python 侧：

```python
from vein_launcher.application.services.plugin_service import PluginService

svc = PluginService()
await svc.start(autoload=False)
await svc.enable("@acme/vein-plugin-hello")
print(await svc.invoke("@acme/vein-plugin-hello", "ping"))
print(svc.host.recent_logs(50))
await svc.stop()
```

- 单独验证宿主：`node vein_launcher/infrastructure/plugin_host/runtime/node_host.js`

---

## 8. 安全建议

1. 最小权限：只声明真正需要的权限。
2. 数据只写 `vein.plugin.dataDir`。
3. 不要在内置 `http` 能力之外自行发起网络请求（企业环境可据此审计）。
4. 发布前自检：确认没有 `shell` 执行、没有读取宿主配置外路径的逻辑。
