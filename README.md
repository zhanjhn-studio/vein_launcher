# Vein Launcher 🦋

面向 Windows 的 Minecraft Java 启动器，核心差异点是**内置 Node.js 插件宿主**：
插件以 NPM 包形式分发，通过双向 JSON-RPC 与启动器通信，并受权限声明 + 路径沙箱约束。

技术栈：Python 3.11+ / PySide6 / aiohttp / Pydantic v2 / Node.js 18+

---

## ✨ 已实现能力

| 模块 | 状态 | 说明 |
|------|------|------|
| 版本清单 / 版本 JSON 合并 | ✅ | Mojang manifest + `inheritsFrom` 链式合并 |
| 断点续传下载器 | ✅ | HTTP Range、令牌桶限速、流式 SHA-1、原子落盘、镜像回退 |
| 版本安装 | ✅ | client jar + libraries + natives + assets objects 全量下载 |
| 启动命令构建 | ✅ | JVM/游戏参数占位符替换、规则过滤、离线 UUID |
| Java 探测 | ✅ | 配置 / JAVA_HOME / 注册表 / PATH / 常见目录 |
| 游戏进程管理 | ✅ | 子进程 + stdout 实时转发 + 退出码事件 |
| Modrinth 模组市场 | ✅ | 搜索、版本过滤、required 依赖自动补全、安装到实例 mods/ |
| CurseForge API | ✅ 客户端 | 需在调用处提供 API Key |
| **Node.js 插件宿主** | ✅ | 进程管理、双向 RPC、权限沙箱、事件桥接、崩溃隔离 |
| 插件安装 | ✅ | 本地目录安装 / `npm install --prefix` 安装 |
| GUI（PySide6） | ✅ 代码完成 | 主页 / 版本 / 模组 / 插件 / 设置 五页 |
| 单元测试 | ✅ 20 项 | 下载器、启动命令、事件总线、插件权限沙箱 |
| CI / 打包 | ✅ | GitHub Actions 双平台测试 + PyInstaller 脚本 |

> 说明：Fabric/Quilt 的 Meta API 客户端已实现（版本查询 + 安装 profile 获取），
> 但「模组版本自动安装编排」尚未接入版本服务，属下一阶段工作。

---

## 🚀 快速开始

```bash
git clone https://github.com/zhanjhn-studio/vein_launcher.git
cd vein_launcher
python -m pip install -r requirements.txt

# 运行
python -m vein_launcher
# 或
python run_launcher.py
```

需要本机安装 **Node.js 18+**（插件宿主依赖；未安装时启动器仍可正常使用）。

### 打包

```bash
python build.py            # 目录模式，产物在 dist/VeinLauncher/
python build.py --onefile  # 单文件模式
```

---

## 🧱 五层架构

```
vein_launcher/
├── common/            # 常量、异常、事件总线、配置、i18n、日志、路径工具
├── domain/            # 领域模型（version/account/launcher/mod/plugin）、服务、仓储接口
├── infrastructure/    # aiohttp 客户端、Mojang/Fabric/Modrinth/CF API、下载器、
│   │                  # 文件仓储、Java 探测、进程管理
│   └── plugin_host/   # Node.js 宿主：host.py / loader.py / capabilities.py / runtime/
├── application/       # 用例编排：版本、启动、账号、模组、插件服务
└── presentation/      # PySide6：async 桥、主窗口、五个页面、主题 QSS
```

硬性规则：
- 跨层通信只通过 `event_bus`（`common/events/event_bus.py`）。
- 路径统一 `pathlib`，禁止字符串拼接。
- 网络使用 `aiohttp`，下载/网络全部异步。

---

## 🔌 插件系统（核心特色）

```js
// plugins/my-plugin/index.js
export async function activate(vein) {
  vein.log("插件已激活");

  vein.on("game.launch.start", (p) => vein.ui.notify("启动中", "正在进入世界", "info"));

  const data = await vein.file.readText(`${vein.plugin.dataDir}/config.json`)
    .catch(() => "{}");
  vein.log(`配置：${data}`);
}
```

插件能力：`file` / `download` / `game` / `ui` / `config` / `http` / `on` / `off`。
所有能力调用都会在宿主侧做**权限校验**与**路径沙箱**检查，越权调用会被拦截并广播
`plugin.permission.denied` 事件。

完整开发指南见 [docs/PLUGIN_DEV.md](docs/PLUGIN_DEV.md)；示例插件见
[plugins_examples/hello-world](plugins_examples/hello-world)。

---

## 🧪 测试

```bash
python -m unittest discover -s tests -t . -v
```

覆盖：下载器（真实本地 HTTP 服务，含续传/校验/短路）、启动命令构建、
事件总线隔离、插件权限与路径沙箱。

---

## 📁 数据目录

```
%APPDATA%\VeinLauncher\
├── config.json          # 设置
├── accounts.json        # 账号
├── plugins/             # 插件（每个包一个目录 + data/ 沙箱）
├── libraries/           # Maven 依赖
├── assets/              # 资源文件与索引
└── instances/<版本ID>/  # 版本 JSON、client jar、mods/、natives/
```

---

## 🤝 贡献

- 提交前请确保 `python -m compileall -q vein_launcher` 与单元测试通过。
- 新增跨层调用请走 `event_bus`，不要直接 import 上层模块。
- 新增插件能力需在 `capabilities.py` 注册并绑定权限标识。

## 📄 License

MIT
